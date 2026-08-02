"""Cross-process exclusive lock contention and TOCTOU / symlink-refuse proofs.

Issue #66 Track 2: proves ``exclusive_transaction_lock`` fails closed across
processes (not only same-process nesting), and covers symlink-refuse paths in
hashing / atomic IO that can be simulated hermetically.
"""

from __future__ import annotations

import os
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path

from ide_development.constants import EXIT_CONFLICT
from ide_development.errors import ConflictError
from ide_development.hashing import sha256_file
from ide_development.io_atomic import atomic_write_bytes, read_file_bytes
from ide_development.lock import exclusive_transaction_lock, lock_path
from ide_development.paths import git_meta_dir
from ide_development_tests import REPO_ROOT, TempRepoTestCase, make_git_repo

# Child holder: acquire lock, signal ready via file, wait for release signal, exit.
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


def _wait_for_file(path: Path, *, timeout: float = 10.0) -> None:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if path.exists():
            return
        time.sleep(0.02)
    raise TimeoutError(f"Timed out waiting for {path}")


class CrossProcessLockContentionTests(TempRepoTestCase):
    def test_cross_process_exclusive_lock_fail_closed(self) -> None:
        """Child holds lock; parent fails closed with ConflictError; then re-acquires."""
        if sys.platform == "win32":
            # Windows msvcrt path is covered by lock.py unit paths; this proof
            # targets POSIX fcntl cross-process semantics (macOS CI / Darwin).
            self.skipTest("cross-process fcntl proof is POSIX-focused; skip on win32")

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
            _wait_for_file(ready, timeout=15.0)
            self.assertEqual(ready.read_text(encoding="utf-8"), str(expected_lock))
            self.assertTrue(expected_lock.is_file())
            self.assertFalse(expected_lock.is_symlink())

            # Parent must fail closed quickly — no blocking wait on flock.
            started = time.monotonic()
            with self.assertRaises(ConflictError) as ctx:
                with exclusive_transaction_lock(self.target):
                    pass  # pragma: no cover - must not enter
            elapsed = time.monotonic() - started
            self.assertLess(
                elapsed,
                2.0,
                f"contention acquire hung ({elapsed:.3f}s); expected non-blocking fail-closed",
            )
            self.assertIn("exclusive lock", str(ctx.exception).lower())
            self.assertEqual(ctx.exception.exit_code, EXIT_CONFLICT)

            # Release child and prove parent can acquire afterward.
            release.write_text("go", encoding="utf-8")
            _wait_for_file(done, timeout=15.0)
            stdout, stderr = child.communicate(timeout=15.0)
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

    def test_lock_refuses_symlink_lock_path(self) -> None:
        meta = git_meta_dir(self.target)
        meta.mkdir(parents=True, exist_ok=True)
        real = Path(self._tmp.name) / "lock-real"
        real.write_bytes(b"\0")
        lock = meta / "lock"
        if lock.exists() or lock.is_symlink():
            lock.unlink()
        lock.symlink_to(real)
        with self.assertRaises(ConflictError) as ctx:
            with exclusive_transaction_lock(self.target):
                pass  # pragma: no cover
        self.assertIn("symlink", str(ctx.exception).lower())
        self.assertEqual(ctx.exception.exit_code, EXIT_CONFLICT)
        # Symlink target must not be flocked open via follow.
        self.assertTrue(real.is_file())


class SymlinkRefuseAndToctouTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_sha256_and_read_refuse_symlink(self) -> None:
        real = self.root / "secret.txt"
        real.write_bytes(b"secret-payload\n")
        link = self.root / "alias.txt"
        link.symlink_to(real)
        with self.assertRaises(OSError) as ctx:
            sha256_file(link)
        self.assertIn("symlink", str(ctx.exception).lower())
        with self.assertRaises(OSError) as ctx2:
            read_file_bytes(link)
        self.assertIn("symlink", str(ctx2.exception).lower())
        self.assertTrue(sha256_file(real).startswith("sha256:"))
        self.assertEqual(read_file_bytes(real), b"secret-payload\n")

    def test_atomic_write_refuses_symlink_dest_without_following(self) -> None:
        real = self.root / "target.txt"
        real.write_text("keep-me\n", encoding="utf-8")
        link = self.root / "dest-link.txt"
        link.symlink_to(real)
        with self.assertRaises(OSError) as ctx:
            atomic_write_bytes(link, b"clobber\n", mode="0644")
        self.assertIn("symlink", str(ctx.exception).lower())
        self.assertEqual(real.read_text(encoding="utf-8"), "keep-me\n")
        self.assertTrue(link.is_symlink())

    def test_atomic_write_physical_roundtrip(self) -> None:
        dest = self.root / "out.txt"
        atomic_write_bytes(dest, b"hello\n", mode="0644")
        self.assertFalse(dest.is_symlink())
        self.assertEqual(read_file_bytes(dest), b"hello\n")
        self.assertTrue(sha256_file(dest).startswith("sha256:"))

    def test_simulated_symlink_swap_before_open_refuses(self) -> None:
        """Simulate race-ish case: path is a symlink at call time (pre-open).

        True mid-check races rely on O_NOFOLLOW + post-fail recheck in
        hashing/io_atomic; this proves the refuse path for a swapped alias.
        """
        victim = self.root / "victim.txt"
        victim.write_text("private\n", encoding="utf-8")
        path = self.root / "mutable.txt"
        path.write_text("benign\n", encoding="utf-8")
        # Swap: replace physical file with symlink to victim (attacker race).
        path.unlink()
        path.symlink_to(victim)
        with self.assertRaises(OSError) as ctx:
            sha256_file(path)
        self.assertIn("symlink", str(ctx.exception).lower())
        with self.assertRaises(OSError) as ctx2:
            read_file_bytes(path)
        self.assertIn("symlink", str(ctx2.exception).lower())
        self.assertEqual(victim.read_text(encoding="utf-8"), "private\n")

    def test_atomic_write_refuses_when_dest_swapped_to_symlink_before_call(self) -> None:
        dest = self.root / "out.bin"
        secret = self.root / "secret.bin"
        secret.write_bytes(b"SECRET")
        dest.write_bytes(b"old")
        dest.unlink()
        dest.symlink_to(secret)
        with self.assertRaises(OSError) as ctx:
            atomic_write_bytes(dest, b"NEW", mode="0644")
        self.assertIn("symlink", str(ctx.exception).lower())
        self.assertEqual(secret.read_bytes(), b"SECRET")


class CrossProcessLockInGitRepoTests(unittest.TestCase):
    """Hermetic git repo + subprocess holder (extra isolation from TempRepoTestCase)."""

    def test_contention_under_fresh_temp_git_repo(self) -> None:
        if sys.platform == "win32":
            self.skipTest("POSIX fcntl cross-process proof; skip on win32")

        with tempfile.TemporaryDirectory() as tmp:
            target = make_git_repo(Path(tmp) / "repo")
            ready = Path(tmp) / "ready"
            release = Path(tmp) / "release"
            done = Path(tmp) / "done"
            child = subprocess.Popen(
                [
                    sys.executable,
                    "-c",
                    _HOLDER_SCRIPT,
                    str(REPO_ROOT),
                    str(target),
                    str(ready),
                    str(release),
                    str(done),
                ],
                env={**os.environ, "PYTHONPATH": str(REPO_ROOT)},
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            try:
                _wait_for_file(ready, timeout=15.0)
                with self.assertRaises(ConflictError):
                    with exclusive_transaction_lock(target):
                        pass  # pragma: no cover
                release.write_text("go", encoding="utf-8")
                _, stderr = child.communicate(timeout=15.0)
                self.assertEqual(child.returncode, 0, msg=stderr)
                with exclusive_transaction_lock(target):
                    pass
            finally:
                if child.poll() is None:
                    release.write_text("go", encoding="utf-8")
                    try:
                        child.communicate(timeout=5.0)
                    except subprocess.TimeoutExpired:
                        child.kill()
                        child.communicate(timeout=5.0)


if __name__ == "__main__":
    unittest.main()
