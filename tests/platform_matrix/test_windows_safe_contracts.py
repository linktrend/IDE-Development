"""Windows-safe contracts + portable equivalents for excluded symlink tests."""

from __future__ import annotations

import json
import shutil
import stat
import tempfile
import unittest
from pathlib import Path

from ide_development.constants import EXIT_OK
from ide_development.engine import run_install_or_update, run_rollback
from ide_development.hashing import sha256_file
from ide_development.io_atomic import atomic_write_bytes, read_file_bytes
from ide_development.lock import exclusive_transaction_lock, lock_path
from ide_development.paths import git_meta_dir, path_is_symlink, resolve_git_dir
from ide_development_tests import TempRepoTestCase

from platform_matrix.platform_assertions import (
    assert_bytes_and_mode_portable,
    assert_mode_portable,
    assert_physical_file,
    can_create_symlinks,
    is_windows,
)


class WindowsSafeContractsTests(TempRepoTestCase):
    def test_path_is_symlink_false_for_physical(self) -> None:
        path = Path(self._tmp.name) / "physical.txt"
        path.write_bytes(b"ok\n")
        self.assertFalse(path_is_symlink(path))
        self.assertFalse(path.is_symlink())
        self.assertTrue(sha256_file(path).startswith("sha256:"))
        self.assertEqual(read_file_bytes(path), b"ok\n")

    def test_atomic_write_physical_roundtrip_portable(self) -> None:
        dest = Path(self._tmp.name) / "out.txt"
        atomic_write_bytes(dest, b"hello\n", mode="0644")
        assert_bytes_and_mode_portable(self, dest, b"hello\n", 0o644)

    def test_physical_install_never_symlink(self) -> None:
        result = run_install_or_update(
            target=self.target,
            package=self.package,
            command="install",
            dry_run=False,
        )
        self.assertEqual(result.exit_code, EXIT_OK, result.payload)
        for rel in (
            ".ide-development/CORE.txt",
            ".cursor/rules/sample-rule.mdc",
            ".ide-development/assets/file-with-spaces.txt",
            "AGENTS.md",
        ):
            assert_physical_file(self, self.target / Path(rel), label=rel)
            self.assertFalse(path_is_symlink(self.target / Path(rel)))

    def test_install_modes_portable(self) -> None:
        result = run_install_or_update(
            target=self.target,
            package=self.package,
            command="install",
            dry_run=False,
        )
        self.assertEqual(result.exit_code, EXIT_OK, result.payload)
        core = self.target / ".ide-development" / "CORE.txt"
        # IDE-managed files are read-only after installation. A scoped write
        # lease is the only supported way to make them temporarily writable.
        assert_mode_portable(self, core, 0o444, label="CORE.txt")

    def test_physical_cursor_tree_after_install(self) -> None:
        """Equivalent to symlink-migration success path when symlink privilege is absent.

        Proves managed ``.cursor`` content is a physical directory/files tree.
        """
        result = run_install_or_update(
            target=self.target,
            package=self.package,
            command="install",
            dry_run=False,
        )
        self.assertEqual(result.exit_code, EXIT_OK, result.payload)
        cursor = self.target / ".cursor"
        self.assertTrue(cursor.is_dir())
        self.assertFalse(cursor.is_symlink())
        rule = cursor / "rules" / "sample-rule.mdc"
        assert_physical_file(self, rule)

    def test_lock_path_physical_after_acquire(self) -> None:
        expected = git_meta_dir(self.target) / "lock"
        with exclusive_transaction_lock(self.target) as held:
            self.assertEqual(held, expected)
            self.assertEqual(lock_path(self.target), expected)
            assert_physical_file(self, expected, label="lock")
            self.assertFalse(path_is_symlink(expected))

    def test_rollback_restores_bytes_portable_modes(self) -> None:
        run_install_or_update(
            target=self.target,
            package=self.package,
            command="install",
            dry_run=False,
        )
        core = self.target / ".ide-development" / "CORE.txt"
        original = core.read_bytes()
        original_mode = stat.S_IMODE(core.stat().st_mode)

        mutated_pkg = Path(self._tmp.name) / "mutated-package"
        shutil.copytree(self.package, mutated_pkg)
        mutated_core = mutated_pkg / "core/managed-core/files/CORE.txt"
        mutated_core.write_text("managed-core fixture MUTATED\n", encoding="utf-8")
        _rewrite_manifest_hash(mutated_pkg, "managed-core-readme", mutated_core)

        updated = run_install_or_update(
            target=self.target,
            package=mutated_pkg,
            command="update",
            dry_run=False,
        )
        self.assertEqual(updated.exit_code, EXIT_OK, updated.payload)

        rolled = run_rollback(target=self.target)
        self.assertEqual(rolled.exit_code, EXIT_OK, rolled.payload)
        assert_bytes_and_mode_portable(self, core, original, original_mode if not is_windows() else 0o644)

    def test_worktree_gitfile_meta_under_real_gitdir(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            real_git = Path(td) / "gitdir"
            real_git.mkdir()
            worktree = Path(td) / "consumer-worktree-ü"
            worktree.mkdir()
            (worktree / ".git").write_text(f"gitdir: {real_git}\n", encoding="utf-8")
            (worktree / "README.md").write_text("# wt\n", encoding="utf-8")
            self.assertEqual(resolve_git_dir(worktree), real_git.resolve())
            result = run_install_or_update(
                target=worktree,
                package=self.package,
                command="install",
                dry_run=False,
            )
            self.assertEqual(result.exit_code, EXIT_OK, result.payload)
            meta = git_meta_dir(worktree)
            self.assertTrue(meta.is_dir())
            self.assertTrue(str(meta).startswith(str(real_git.resolve())))
            self.assertTrue((meta / "last-transaction").is_dir())
            self.assertFalse((worktree / ".git").is_dir())
            assert_physical_file(self, worktree / ".ide-development" / "CORE.txt")

    def test_symlink_capability_documented(self) -> None:
        """Record whether this host can create symlinks (informational assert)."""
        ok = can_create_symlinks()
        if is_windows() and not ok:
            self.skipTest(
                "Windows symlink privilege unavailable — symlink-creation tests "
                "excluded by platform_matrix.exclusions; physical equivalents above"
            )
        self.assertTrue(ok)


def _rewrite_manifest_hash(package: Path, entry_id: str, source: Path) -> None:
    from ide_development.hashing import sha256_file as _sha

    manifest_path = package / "core/managed-core/MANIFEST.json"
    data = json.loads(manifest_path.read_text(encoding="utf-8"))
    digest = _sha(source)
    for entry in data["files"]:
        if entry["id"] == entry_id:
            entry["sourceHash"] = digest
    data["packageVersion"] = "2.1.1"
    manifest_path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    (package / "core/managed-core/VERSION").write_text("2.1.1\n", encoding="utf-8")


if __name__ == "__main__":
    unittest.main()
