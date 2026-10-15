"""Rollback dry-run must remain read-only, including Git metadata."""

from __future__ import annotations

import contextlib
import io
import json
import os
import stat
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from ide_development.cli import main  # noqa: E402
from ide_development.engine import run_install_or_update, run_rollback  # noqa: E402
from ide_development.transaction import current_tx_dir  # noqa: E402
from ide_development_tests import FIXTURE_PACKAGE, TempRepoTestCase  # noqa: E402


def _tree_snapshot(root: Path) -> dict[str, tuple[object, ...]]:
    root_stat = root.lstat()
    snapshot: dict[str, tuple[object, ...]] = {
        "": ("directory", stat.S_IMODE(root_stat.st_mode), root_stat.st_mtime_ns)
    }
    for current, dirs, files in os.walk(root, topdown=True, followlinks=False):
        base = Path(current)
        dirs.sort()
        files.sort()
        for name in [*dirs, *files]:
            path = base / name
            rel = path.relative_to(root).as_posix()
            info = path.lstat()
            common = (stat.S_IMODE(info.st_mode), info.st_mtime_ns)
            if stat.S_ISLNK(info.st_mode):
                snapshot[rel] = ("symlink", os.readlink(path), *common)
            elif stat.S_ISDIR(info.st_mode):
                snapshot[rel] = ("directory", *common)
            else:
                snapshot[rel] = ("file", path.read_bytes(), *common)
    return snapshot


class RollbackDryRunTests(TempRepoTestCase):
    def _install(self) -> None:
        result = run_install_or_update(
            target=self.target, package=FIXTURE_PACKAGE, command="install"
        )
        self.assertEqual(result.exit_code, 0, result.payload)

    def test_cli_dry_run_preserves_full_repository_and_git_metadata(self) -> None:
        self._install()
        before = _tree_snapshot(self.target)
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            exit_code = main(
                ["rollback", "--target", str(self.target), "--dry-run", "--json"]
            )
        self.assertEqual(exit_code, 0, output.getvalue())
        payload = json.loads(output.getvalue())
        self.assertTrue(payload["dryRun"], payload)
        self.assertFalse(payload["applied"], payload)
        self.assertTrue(payload["result"]["preview"], payload)
        self.assertEqual(_tree_snapshot(self.target), before)

    def test_pending_transaction_dry_run_is_read_only_and_fails_closed(self) -> None:
        self._install()
        pending = current_tx_dir(self.target)
        pending.mkdir(parents=True)
        (pending / "journal.json").write_text(
            json.dumps({"phase": "apply", "transactionId": "pending-test"}) + "\n",
            encoding="utf-8",
        )
        before = _tree_snapshot(self.target)
        result = run_rollback(target=self.target, dry_run=True)
        self.assertNotEqual(result.exit_code, 0, result.payload)
        self.assertTrue(result.payload["dryRun"], result.payload)
        self.assertFalse(result.payload["applied"], result.payload)
        self.assertEqual(_tree_snapshot(self.target), before)
        self.assertTrue((pending / "journal.json").is_file())

    def test_actual_rollback_still_restores_managed_files(self) -> None:
        self._install()
        result = run_rollback(target=self.target)
        self.assertEqual(result.exit_code, 0, result.payload)
        self.assertTrue(result.payload["applied"], result.payload)
        self.assertFalse((self.target / ".ide-development/CORE.txt").exists())
        self.assertFalse((self.target / ".ide-development/MANIFEST.json").exists())


if __name__ == "__main__":
    unittest.main()
