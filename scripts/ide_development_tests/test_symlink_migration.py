"""Unit tests for physical .cursor symlink migration (Issue #66 Track 1)."""

from __future__ import annotations

import os
import unittest
from pathlib import Path

from ide_development.constants import EXIT_OK
from ide_development.engine import run_install_or_update, run_plan, run_rollback
from ide_development.plan import OpKind
from ide_development.symlink_migrate import detect_cursor_symlink
from ide_development_tests import TempRepoTestCase


class SymlinkMigrationTests(TempRepoTestCase):
    def _plant_external_cursor(self, *, relative: bool = False) -> Path:
        outside = Path(self._tmp.name) / "outside-cursor-tree"
        outside.mkdir()
        secret = outside / "secret.txt"
        secret.write_text("OUTSIDE_MUST_STAY\n", encoding="utf-8")
        (outside / "nested").mkdir()
        (outside / "nested" / "keep.txt").write_text("keep\n", encoding="utf-8")

        link = self.target / ".cursor"
        if link.exists() or link.is_symlink():
            link.unlink()
        if relative:
            rel_target = os.path.relpath(outside, start=self.target)
            os.symlink(rel_target, link)
        else:
            os.symlink(str(outside), link)
        return outside

    def _outside_fingerprint(self, outside: Path) -> tuple[bytes, frozenset[str]]:
        secret = (outside / "secret.txt").read_bytes()
        listing = frozenset(
            p.relative_to(outside).as_posix()
            for p in outside.rglob("*")
            if p.is_file() or p.is_dir()
        )
        return secret, listing

    def test_detect_cursor_symlink_readlink_only(self) -> None:
        outside = self._plant_external_cursor()
        info = detect_cursor_symlink(self.target)
        self.assertIsNotNone(info)
        assert info is not None
        self.assertEqual(info.path, ".cursor")

        def _norm(path: str) -> str:
            # Windows may prefix extended-length paths (\\?\).
            if path.startswith("\\\\?\\"):
                return path[4:]
            return path

        self.assertEqual(_norm(info.target), _norm(str(outside)))
        # Detection must not create anything under outside.
        self.assertEqual({p.name for p in outside.iterdir()}, {"secret.txt", "nested"})

    def test_plan_includes_migrate_symlink(self) -> None:
        self._plant_external_cursor()
        (self.target / "CONSUMER.md").write_text("consumer owned\n", encoding="utf-8")
        plan = run_plan(target=self.target, package=self.package)
        self.assertEqual(plan.exit_code, EXIT_OK, plan.payload)
        self.assertFalse(plan.payload["conflicts"])
        ops = [(a["op"], a["path"]) for a in plan.payload["actions"]]
        self.assertIn((OpKind.MIGRATE_SYMLINK.value, ".cursor"), ops)
        migrate = next(a for a in plan.payload["actions"] if a["op"] == "migrate_symlink")
        self.assertTrue(migrate.get("symlinkTarget"))
        # Creates under .cursor are planned without PATH_ESCAPE.
        self.assertTrue(
            any(
                a["op"] == "create" and a["path"].startswith(".cursor/")
                for a in plan.payload["actions"]
            )
        )

    def test_dry_run_writes_nothing(self) -> None:
        outside = self._plant_external_cursor()
        before_secret, before_listing = self._outside_fingerprint(outside)
        before_link = os.readlink(self.target / ".cursor")
        before_consumer = (self.target / "README.md").read_bytes()

        dry = run_install_or_update(
            target=self.target,
            package=self.package,
            command="install",
            dry_run=True,
        )
        self.assertEqual(dry.exit_code, EXIT_OK, dry.payload)
        self.assertFalse(dry.payload.get("applied"))
        self.assertTrue((self.target / ".cursor").is_symlink())
        self.assertEqual(os.readlink(self.target / ".cursor"), before_link)
        self.assertFalse((self.target / ".ide-development").exists())
        self.assertFalse((self.target / ".git" / "ide-development").exists())
        self.assertEqual((outside / "secret.txt").read_bytes(), before_secret)
        self.assertEqual(self._outside_fingerprint(outside)[1], before_listing)
        self.assertEqual((self.target / "README.md").read_bytes(), before_consumer)

    def test_migrate_success_outside_untouched_consumer_preserved(self) -> None:
        outside = self._plant_external_cursor()
        before_secret, before_listing = self._outside_fingerprint(outside)
        consumer = self.target / "CONSUMER.md"
        consumer.write_text("consumer owned docs\n", encoding="utf-8")
        consumer_bytes = consumer.read_bytes()

        result = run_install_or_update(
            target=self.target,
            package=self.package,
            command="install",
            dry_run=False,
        )
        self.assertEqual(result.exit_code, EXIT_OK, result.payload)

        cursor = self.target / ".cursor"
        self.assertFalse(cursor.is_symlink())
        self.assertTrue(cursor.is_dir())
        sample = cursor / "rules" / "sample-rule.mdc"
        self.assertTrue(sample.is_file())
        self.assertFalse(sample.is_symlink())

        self.assertEqual(consumer.read_bytes(), consumer_bytes)
        self.assertEqual((outside / "secret.txt").read_bytes(), before_secret)
        self.assertEqual(self._outside_fingerprint(outside)[1], before_listing)
        self.assertFalse((outside / "rules").exists())
        self.assertFalse((outside / "sample-rule.mdc").exists())

        # Physical managed tree also installed.
        self.assertTrue((self.target / ".ide-development" / "CORE.txt").is_file())

    def test_relative_symlink_migrate(self) -> None:
        outside = self._plant_external_cursor(relative=True)
        before_secret, before_listing = self._outside_fingerprint(outside)
        original = os.readlink(self.target / ".cursor")
        self.assertFalse(os.path.isabs(original))

        result = run_install_or_update(
            target=self.target,
            package=self.package,
            command="install",
            dry_run=False,
        )
        self.assertEqual(result.exit_code, EXIT_OK, result.payload)
        self.assertTrue((self.target / ".cursor").is_dir())
        self.assertFalse((self.target / ".cursor").is_symlink())
        self.assertEqual((outside / "secret.txt").read_bytes(), before_secret)
        self.assertEqual(self._outside_fingerprint(outside)[1], before_listing)

    def test_rollback_restores_symlink(self) -> None:
        outside = self._plant_external_cursor()
        before_secret, before_listing = self._outside_fingerprint(outside)
        original_target = os.readlink(self.target / ".cursor")
        consumer = self.target / "CONSUMER.md"
        consumer.write_text("preserve me\n", encoding="utf-8")
        consumer_bytes = consumer.read_bytes()

        installed = run_install_or_update(
            target=self.target,
            package=self.package,
            command="install",
            dry_run=False,
        )
        self.assertEqual(installed.exit_code, EXIT_OK, installed.payload)
        self.assertTrue((self.target / ".cursor").is_dir())

        rolled = run_rollback(target=self.target)
        self.assertEqual(rolled.exit_code, EXIT_OK, rolled.payload)

        cursor = self.target / ".cursor"
        self.assertTrue(cursor.is_symlink())
        self.assertEqual(os.readlink(cursor), original_target)
        self.assertEqual(consumer.read_bytes(), consumer_bytes)
        self.assertEqual((outside / "secret.txt").read_bytes(), before_secret)
        self.assertEqual(self._outside_fingerprint(outside)[1], before_listing)
        self.assertFalse((outside / "rules").exists())
        # Installer-created physical tree under .cursor must be gone.
        self.assertFalse((self.target / ".cursor" / "rules").exists())

    def test_file_symlink_elsewhere_still_fail_closed(self) -> None:
        """Non-.cursor unsafe links remain fail-closed (migrate is .cursor-only)."""
        from ide_development.constants import EXIT_CONFLICT

        # Physical .cursor dir with a symlink at a managed destination.
        rules = self.target / ".cursor" / "rules"
        rules.mkdir(parents=True)
        escape = rules / "sample-rule.mdc"
        real = Path(self._tmp.name) / "outside-file.txt"
        real.write_text("secret\n", encoding="utf-8")
        os.symlink(str(real), escape)

        result = run_install_or_update(
            target=self.target,
            package=self.package,
            command="install",
            dry_run=False,
        )
        self.assertEqual(result.exit_code, EXIT_CONFLICT, result.payload)
        self.assertTrue(escape.is_symlink())
        self.assertEqual(real.read_text(encoding="utf-8"), "secret\n")


if __name__ == "__main__":
    unittest.main()
