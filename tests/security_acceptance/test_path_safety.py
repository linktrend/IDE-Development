"""Path traversal, absolute injection, symlink/junction escapes, link-swap."""

from __future__ import annotations

import json
import os
import shutil
import sys
import unittest
from pathlib import Path

from harness import DisposableRepoTestCase, load_manifest, write_manifest

from ide_development.constants import EXIT_CONFLICT, EXIT_INVALID_PACKAGE
from ide_development.errors import ConflictError, InvalidPackageError
from ide_development.hashing import sha256_file
from ide_development.io_atomic import atomic_write_bytes, read_file_bytes
from ide_development.paths import as_posix_rel, join_under
from ide_development.engine import run_install_or_update, run_plan


class PathTraversalTests(DisposableRepoTestCase):
    def test_rejects_parent_traversal(self) -> None:
        with self.assertRaises(InvalidPackageError):
            as_posix_rel("../outside")
        with self.assertRaises(InvalidPackageError):
            as_posix_rel(".ide-development/../../etc/passwd")

    def test_rejects_absolute_posix(self) -> None:
        with self.assertRaises(InvalidPackageError):
            as_posix_rel("/etc/passwd")
        with self.assertRaises(InvalidPackageError):
            as_posix_rel("~/secret")

    def test_rejects_drive_letter(self) -> None:
        with self.assertRaises(InvalidPackageError):
            as_posix_rel("C:/Windows/System32")

    def test_manifest_destination_traversal_fail_closed(self) -> None:
        data = load_manifest(self.package)
        data["files"][0]["destination"] = "../escape.txt"
        write_manifest(self.package, data)
        payload = self.assert_cli_refusal(
            "plan",
            "--package",
            str(self.package),
            "--target",
            str(self.target),
            expected_exit=EXIT_INVALID_PACKAGE,
        )
        self.assertIn("error", payload)
        self.assertEqual(payload["exitCode"], EXIT_INVALID_PACKAGE)

    def test_manifest_source_absolute_fail_closed(self) -> None:
        data = load_manifest(self.package)
        data["files"][0]["source"] = "/tmp/evil.txt"
        write_manifest(self.package, data)
        payload = self.assert_cli_refusal(
            "plan",
            "--package",
            str(self.package),
            "--target",
            str(self.target),
            expected_exit=EXIT_INVALID_PACKAGE,
        )
        self.assertIn("Absolute", payload["error"])


class SymlinkEscapeTests(DisposableRepoTestCase):
    def test_managed_destination_symlink_fail_closed(self) -> None:
        outside = self.root / "outside-victim"
        outside.mkdir()
        secret = outside / "secret.txt"
        secret.write_text("MUST_STAY\n", encoding="utf-8")
        before = secret.read_bytes()

        dest_parent = self.target / ".ide-development"
        dest_parent.mkdir(parents=True, exist_ok=True)
        link = dest_parent / "CORE.txt"
        link.symlink_to(secret)

        result = run_install_or_update(
            target=self.target,
            package=self.package,
            command="install",
            dry_run=False,
        )
        self.assertEqual(result.exit_code, EXIT_CONFLICT, result.payload)
        kinds = {c["kind"] for c in result.payload.get("conflicts") or []}
        self.assertIn("symlink", kinds)
        self.assertEqual(secret.read_bytes(), before)
        self.assertTrue(link.is_symlink())

    def test_package_source_symlink_refused(self) -> None:
        """In-package symlink source → InvalidPackageError (physical-file rule)."""
        real = self.package / "core/managed-core/files/CORE.txt"
        backup = real.read_bytes()
        decoy = self.package / "core/managed-core/files/decoy-physical.txt"
        decoy.write_bytes(backup)
        real.unlink()
        real.symlink_to(decoy.name)  # relative symlink inside package
        with self.assertRaises(InvalidPackageError) as ctx:
            run_plan(target=self.target, package=self.package)
        self.assertIn("symlink", str(ctx.exception).lower())

    def test_package_source_symlink_escape_fail_closed(self) -> None:
        """Out-of-package symlink source refuses as InvalidPackage (physical-file rule)."""
        real = self.package / "core/managed-core/files/CORE.txt"
        backup = real.read_bytes()
        real.unlink()
        decoy = self.root / "decoy-source.txt"
        decoy.write_bytes(backup)
        real.symlink_to(decoy)
        with self.assertRaises(InvalidPackageError) as ctx:
            run_plan(target=self.target, package=self.package)
        self.assertEqual(ctx.exception.exit_code, EXIT_INVALID_PACKAGE)
        self.assertIn("symlink", str(ctx.exception).lower())

    def test_symlink_ancestor_non_cursor_fail_closed(self) -> None:
        """Non-.cursor symlink ancestor must fail closed (never follow outside).

        Current path: load_installed_state → join_under raises ConflictError
        (PATH_ESCAPE) before plan conflict classification — still fail-closed.
        """
        outside = self.root / "escape-tree"
        outside.mkdir()
        marker = outside / "sentinel.txt"
        marker.write_text("OUTSIDE\n", encoding="utf-8")
        before = marker.read_bytes()
        ide = self.target / ".ide-development"
        if ide.exists() or ide.is_symlink():
            if ide.is_dir() and not ide.is_symlink():
                shutil.rmtree(ide)
            else:
                ide.unlink()
        ide.symlink_to(outside)
        with self.assertRaises(ConflictError) as ctx:
            run_plan(target=self.target, package=self.package)
        self.assertEqual(ctx.exception.exit_code, EXIT_CONFLICT)
        payload = self.assert_cli_refusal(
            "install",
            "--package",
            str(self.package),
            "--target",
            str(self.target),
            expected_exit=EXIT_CONFLICT,
        )
        self.assertIn("escapes", payload.get("error", "").lower())
        self.assertEqual(marker.read_bytes(), before)
        self.assertTrue(ide.is_symlink())

    def test_link_swap_sha256_and_atomic_write_refuse(self) -> None:
        victim = self.root / "victim.bin"
        victim.write_bytes(b"PRIVATE")
        path = self.root / "mutable.bin"
        path.write_bytes(b"benign")
        path.unlink()
        path.symlink_to(victim)
        with self.assertRaises(OSError) as ctx:
            sha256_file(path)
        self.assertIn("symlink", str(ctx.exception).lower())
        with self.assertRaises(OSError):
            read_file_bytes(path)
        with self.assertRaises(OSError):
            atomic_write_bytes(path, b"NEW", mode="0644")
        self.assertEqual(victim.read_bytes(), b"PRIVATE")

    @unittest.skipUnless(sys.platform == "win32", "Windows junction proof only")
    def test_windows_junction_escape(self) -> None:
        # Placeholder: junction creation requires win32 APIs; skip elsewhere.
        self.fail("junction harness not implemented on this runner")  # pragma: no cover


class JoinUnderEscapeTests(DisposableRepoTestCase):
    def test_join_under_stays_inside_root(self) -> None:
        dest = join_under(self.target, ".ide-development/CORE.txt")
        self.assertTrue(str(dest.resolve()).startswith(str(self.target.resolve())))

    def test_intermediate_symlink_escape_detected(self) -> None:
        outside = self.root / "out"
        outside.mkdir()
        mid = self.target / "mid"
        mid.symlink_to(outside)
        # Logical join without .. still resolves outside via symlink.
        with self.assertRaises(ConflictError) as ctx:
            join_under(self.target, "mid/escape.txt")
        self.assertEqual(ctx.exception.exit_code, EXIT_CONFLICT)


if __name__ == "__main__":
    unittest.main()
