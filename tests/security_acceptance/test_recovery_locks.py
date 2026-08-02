"""Locks, interrupted writes, corrupt journals/backups, rollback failure."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import time
import unittest
from pathlib import Path

from harness import DisposableRepoTestCase, REPO_ROOT, SCRIPTS_DIR, rewrite_entry_hash

from ide_development.constants import (
    EXIT_CONFLICT,
    EXIT_OK,
    EXIT_ROLLBACK_FAILURE,
)
from ide_development.engine import run_install_or_update, run_rollback
from ide_development.errors import ConflictError
from ide_development.hashing import sha256_file
from ide_development.io_atomic import atomic_write_bytes
from ide_development.lock import exclusive_transaction_lock, lock_path
from ide_development.paths import encode_backup_name, git_meta_dir
from ide_development.transaction import (
    backups_dir,
    current_tx_dir,
    last_tx_dir,
    write_journal,
)

_HOLDER_SCRIPT = r"""
import sys
import time
from pathlib import Path

scripts_dir = Path(sys.argv[1])
sys.path.insert(0, str(scripts_dir))
from ide_development.lock import exclusive_transaction_lock

target = Path(sys.argv[2])
ready = Path(sys.argv[3])
release = Path(sys.argv[4])
with exclusive_transaction_lock(target) as held:
    ready.write_text(str(held), encoding="utf-8")
    deadline = time.monotonic() + 30.0
    while time.monotonic() < deadline:
        if release.exists():
            break
        time.sleep(0.02)
    else:
        sys.exit(2)
sys.exit(0)
"""


def _wait_for(path: Path, *, timeout: float = 15.0) -> None:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if path.exists():
            return
        time.sleep(0.02)
    raise TimeoutError(path)


class LockAndRecoveryTests(DisposableRepoTestCase):
    def test_stale_symlink_lock_refused(self) -> None:
        meta = git_meta_dir(self.target)
        meta.mkdir(parents=True, exist_ok=True)
        real = self.root / "lock-real"
        real.write_bytes(b"\0")
        lock = meta / "lock"
        if lock.exists() or lock.is_symlink():
            lock.unlink()
        lock.symlink_to(real)
        with self.assertRaises(ConflictError) as ctx:
            with exclusive_transaction_lock(self.target):
                pass  # pragma: no cover
        self.assertEqual(ctx.exception.exit_code, EXIT_CONFLICT)
        self.assertIn("symlink", str(ctx.exception).lower())

    def test_concurrent_lock_fail_closed(self) -> None:
        if sys.platform == "win32":
            self.skipTest("POSIX fcntl cross-process proof")
        ready = self.root / "ready"
        release = self.root / "release"
        child = subprocess.Popen(
            [
                sys.executable,
                "-c",
                _HOLDER_SCRIPT,
                str(SCRIPTS_DIR),
                str(self.target),
                str(ready),
                str(release),
            ],
            env={**os.environ, "PYTHONPATH": str(SCRIPTS_DIR)},
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        try:
            _wait_for(ready)
            started = time.monotonic()
            with self.assertRaises(ConflictError) as ctx:
                with exclusive_transaction_lock(self.target):
                    pass  # pragma: no cover
            self.assertLess(time.monotonic() - started, 2.0)
            self.assertEqual(ctx.exception.exit_code, EXIT_CONFLICT)
            release.write_text("go", encoding="utf-8")
            child.communicate(timeout=15)
            self.assertEqual(child.returncode, 0)
        finally:
            if child.poll() is None:
                release.write_text("go", encoding="utf-8")
                try:
                    child.communicate(timeout=5)
                except subprocess.TimeoutExpired:
                    child.kill()
                    child.communicate(timeout=5)

    def test_interrupted_transaction_recovers_on_next_update(self) -> None:
        first = run_install_or_update(
            target=self.target,
            package=self.package,
            command="install",
            dry_run=False,
        )
        self.assertEqual(first.exit_code, EXIT_OK, first.payload)
        core = self.target / ".ide-development" / "CORE.txt"
        original = core.read_bytes()

        tx = current_tx_dir(self.target)
        tx.mkdir(parents=True, exist_ok=True)
        (tx / "backups").mkdir(parents=True, exist_ok=True)
        backup_name = encode_backup_name(".ide-development/CORE.txt")
        atomic_write_bytes(tx / "backups" / backup_name, original, mode="0644")
        core.write_text("partial-write\n", encoding="utf-8")
        write_journal(
            tx,
            {
                "schemaVersion": 1,
                "transactionId": "lane-e-interrupted",
                "command": "update",
                "packageVersion": "2.0.0",
                "phase": "apply",
                "backups": [
                    {
                        "path": ".ide-development/CORE.txt",
                        "existed": True,
                        "mode": "0644",
                        "contentHash": sha256_file(
                            self.package / "core/managed-core/files/CORE.txt"
                        ),
                        "backupName": backup_name,
                    }
                ],
                "applied": [".ide-development/CORE.txt"],
            },
        )
        result = run_install_or_update(
            target=self.target,
            package=self.package,
            command="update",
            dry_run=False,
        )
        self.assertEqual(result.exit_code, EXIT_OK, result.payload)
        self.assertEqual(core.read_bytes(), original)
        self.assertFalse(current_tx_dir(self.target).exists())

    def test_corrupt_journal_json_surfaces_error(self) -> None:
        run_install_or_update(
            target=self.target,
            package=self.package,
            command="install",
            dry_run=False,
        )
        tx = current_tx_dir(self.target)
        tx.mkdir(parents=True, exist_ok=True)
        (tx / "journal.json").write_text("{broken", encoding="utf-8")
        # Mutating path reads journal via recover — JSONDecodeError → EXIT_ERROR
        from ide_development.cli import main
        from ide_development.constants import EXIT_ERROR
        from contextlib import redirect_stdout, redirect_stderr
        import io

        buf = io.StringIO()
        with redirect_stdout(buf), redirect_stderr(buf):
            code = main(
                [
                    "update",
                    "--package",
                    str(self.package),
                    "--target",
                    str(self.target),
                    "--json",
                ]
            )
        self.assertEqual(code, EXIT_ERROR)

    def test_corrupt_backup_rollback_failure(self) -> None:
        run_install_or_update(
            target=self.target,
            package=self.package,
            command="install",
            dry_run=False,
        )
        # Mutate package and update so last-transaction has backups
        mutated = self.root / "mutated"
        shutil.copytree(self.package, mutated)
        core_src = mutated / "core/managed-core/files/CORE.txt"
        core_src.write_text("MUTATED\n", encoding="utf-8")
        rewrite_entry_hash(mutated, "managed-core-readme", core_src)
        updated = run_install_or_update(
            target=self.target,
            package=mutated,
            command="update",
            dry_run=False,
        )
        self.assertEqual(updated.exit_code, EXIT_OK, updated.payload)

        last = last_tx_dir(self.target)
        bdir = backups_dir(last)
        self.assertTrue(bdir.is_dir())
        removed = 0
        for blob in list(bdir.iterdir()):
            if blob.is_file() and not blob.is_symlink():
                blob.unlink()
                removed += 1
        self.assertGreater(removed, 0, "expected at least one backup blob to remove")
        # run_rollback catches RollbackError and returns EngineResult (no raise)
        rolled = run_rollback(target=self.target)
        self.assertEqual(rolled.exit_code, EXIT_ROLLBACK_FAILURE, rolled.payload)
        self.assertFalse(rolled.payload.get("ok", True))

        from ide_development.cli import main
        from contextlib import redirect_stdout, redirect_stderr
        import io

        buf = io.StringIO()
        with redirect_stdout(buf), redirect_stderr(buf):
            code = main(["rollback", "--target", str(self.target), "--json"])
        self.assertEqual(code, EXIT_ROLLBACK_FAILURE)

    def test_incomplete_last_journal_rollback_failure(self) -> None:
        run_install_or_update(
            target=self.target,
            package=self.package,
            command="install",
            dry_run=False,
        )
        last = last_tx_dir(self.target)
        journal_path = last / "journal.json"
        data = json.loads(journal_path.read_text(encoding="utf-8"))
        data["phase"] = "apply"
        journal_path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
        from ide_development.cli import main
        from contextlib import redirect_stdout, redirect_stderr
        import io

        buf = io.StringIO()
        with redirect_stdout(buf), redirect_stderr(buf):
            code = main(["rollback", "--target", str(self.target), "--json"])
        self.assertEqual(code, EXIT_ROLLBACK_FAILURE)


if __name__ == "__main__":
    unittest.main()
