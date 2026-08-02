"""Unicode + spaces path coverage for the platform matrix."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from ide_development.constants import EXIT_OK
from ide_development.engine import run_install_or_update, run_plan, run_verify
from ide_development.paths import encode_backup_name, decode_backup_name, join_under
from ide_development_tests import FIXTURE_PACKAGE, make_git_repo

from platform_matrix.platform_assertions import assert_physical_file


class UnicodePathMatrixTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        # Spaces + Unicode in the consumer root (Windows + POSIX).
        self.target = make_git_repo(
            Path(self._tmp.name) / "消费者 repo with spaces and üñîçødé"
        )
        self.package = FIXTURE_PACKAGE

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_unicode_and_spaces_join(self) -> None:
        rel = ".ide-development/assets/文件 with spaces ü.txt"
        dest = join_under(self.target, rel)
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text("unicode-ok\n", encoding="utf-8")
        assert_physical_file(self, dest, label=rel)
        enc = encode_backup_name(rel)
        self.assertNotIn("/", enc)
        self.assertNotIn("\\", enc)
        self.assertEqual(decode_backup_name(enc), rel)

    def test_unicode_target_install_verify(self) -> None:
        result = run_install_or_update(
            target=self.target,
            package=self.package,
            command="install",
            dry_run=False,
        )
        self.assertEqual(result.exit_code, EXIT_OK, result.payload)
        core = self.target / ".ide-development" / "CORE.txt"
        spaced = self.target / ".ide-development" / "assets" / "file-with-spaces.txt"
        assert_physical_file(self, core)
        assert_physical_file(self, spaced)
        verify = run_verify(target=self.target, package=self.package)
        self.assertEqual(verify.exit_code, EXIT_OK, verify.payload)

    def test_plan_dry_run_no_writes_unicode_target(self) -> None:
        def inventory() -> list[str]:
            # Ignore Git's private object/maintenance noise (e.g. maintenance.lock).
            files: list[str] = []
            for p in self.target.rglob("*"):
                if not p.is_file():
                    continue
                try:
                    rel = p.relative_to(self.target).as_posix()
                except ValueError:
                    continue
                if rel == ".git" or rel.startswith(".git/"):
                    continue
                files.append(p.as_posix())
            return sorted(files)

        before = inventory()
        plan = run_plan(target=self.target, package=self.package)
        self.assertEqual(plan.exit_code, EXIT_OK, plan.payload)
        dry = run_install_or_update(
            target=self.target,
            package=self.package,
            command="install",
            dry_run=True,
        )
        self.assertEqual(dry.exit_code, EXIT_OK, dry.payload)
        after = inventory()
        self.assertEqual(before, after)
        self.assertFalse((self.target / ".ide-development").exists())


if __name__ == "__main__":
    unittest.main()
