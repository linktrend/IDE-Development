"""True cross-process exclusive-lock contention on every supported platform.

Existing ``scripts/ide_development_tests/test_lock_contention.py`` skips the
fcntl proof on ``win32``. This matrix test runs the same fail-closed contract
using the platform lock implementation (POSIX fcntl or Windows msvcrt).
"""

from __future__ import annotations

import os
import subprocess
import sys
import time
import unittest
from pathlib import Path

from ide_development.constants import EXIT_CONFLICT
from ide_development.errors import ConflictError
from ide_development.lock import exclusive_transaction_lock, lock_path
from ide_development.paths import git_meta_dir
from ide_development_tests import REPO_ROOT, TempRepoTestCase

_HOLDER_SCRIPT = r"""
import sys
import time
from pathlib import Path

scripts_dir = Path(sys.argv[1])
sys.path.insert(0, str(scripts_dir))

from ide_development.lock import exclusive_transaction_lock  # noqa: E402

target = Path(sys.argv[2])
ready = Path(sys.argv[3])
release = Path(sys.argv[4])
done = Path(sys.argv[5])

with exclusive_transaction_lock(target) as held:
    ready.write_text(str(held), encoding="utf-8")
    deadline = time.monotonic() + 30.0
    while time.monotonic() < deadline:
        if release.exists():
            break
        time.sleep(0.02)
    else:
        sys.stderr.write("holder timed out waiting for release\n")
        sys.exit(2)
done.write_text("released", encoding="utf-8")
sys.exit(0)
"""


def _wait_for_file(path: Path, *, timeout: float = 15.0) -> None:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if path.exists():
            return
        time.sleep(0.02)
    raise TimeoutError(f"Timed out waiting for {path}")


class CrossProcessLockMatrixTests(TempRepoTestCase):
    def test_cross_process_exclusive_lock_all_platforms(self) -> None:
        """Child holds lock; parent fails closed; parent re-acquires after release.

        Runs on Darwin, Linux, and Windows (msvcrt.LK_NBLCK). This is the
        Lane A equivalent for the POSIX-only skip in ide_development_tests.
        """
        ready = Path(self._tmp.name) / "holder-ready"
        release = Path(self._tmp.name) / "holder-release"
        done = Path(self._tmp.name) / "holder-done"
        for p in (ready, release, done):
            if p.exists():
                p.unlink()

        expected_lock = git_meta_dir(self.target) / "lock"
        self.assertEqual(lock_path(self.target), expected_lock)

        child = subprocess.Popen(
            [
                sys.executable,
                "-c",
                _HOLDER_SCRIPT,
                str(REPO_ROOT),
                str(self.target),
                str(ready),
                str(release),
                str(done),
            ],
            cwd=str(self._tmp.name),
            env={**os.environ, "PYTHONPATH": str(REPO_ROOT)},
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        try:
            _wait_for_file(ready, timeout=20.0)
            self.assertEqual(ready.read_text(encoding="utf-8"), str(expected_lock))
            self.assertTrue(expected_lock.is_file())
            self.assertFalse(expected_lock.is_symlink())

            started = time.monotonic()
            with self.assertRaises(ConflictError) as ctx:
                with exclusive_transaction_lock(self.target):
                    pass  # pragma: no cover - must not enter
            elapsed = time.monotonic() - started
            self.assertLess(
                elapsed,
                3.0,
                f"contention acquire hung ({elapsed:.3f}s); expected non-blocking fail-closed",
            )
            self.assertIn("exclusive lock", str(ctx.exception).lower())
            self.assertEqual(ctx.exception.exit_code, EXIT_CONFLICT)

            release.write_text("go", encoding="utf-8")
            _wait_for_file(done, timeout=20.0)
            stdout, stderr = child.communicate(timeout=20.0)
            self.assertEqual(
                child.returncode,
                0,
                msg=f"stdout={stdout!r} stderr={stderr!r}",
            )

            with exclusive_transaction_lock(self.target) as held:
                self.assertEqual(held, expected_lock)
        finally:
            if child.poll() is None:
                try:
                    release.write_text("go", encoding="utf-8")
                except OSError:
                    pass
                try:
                    child.communicate(timeout=5.0)
                except subprocess.TimeoutExpired:
                    child.kill()
                    child.communicate(timeout=5.0)


if __name__ == "__main__":
    unittest.main()
