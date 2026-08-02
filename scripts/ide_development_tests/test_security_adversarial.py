"""Adversarial security unit suite (Lane E) — discoverable under ide_development_tests.

Primary acceptance matrix lives in ``tests/security_acceptance/``. This module
mirrors the highest-risk installer refusal classes for
``python3 -m unittest scripts.ide_development_tests.test_security_adversarial``
and existing ide_development_tests runners.
"""

from __future__ import annotations

import json
import os
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

from ide_development.constants import (
    EXIT_CONFLICT,
    EXIT_INVALID_PACKAGE,
    EXIT_OK,
    EXIT_ROLLBACK_FAILURE,
)
from ide_development.engine import run_install_or_update, run_plan, run_rollback
from ide_development.errors import ConflictError, InvalidPackageError
from ide_development.hashing import sha256_file
from ide_development.io_atomic import atomic_write_bytes
from ide_development.lock import exclusive_transaction_lock
from ide_development.manifest import load_manifest
from ide_development.paths import as_posix_rel, git_meta_dir, join_under
from ide_development_tests import FIXTURE_PACKAGE, TempRepoTestCase

SECURITY_FIXTURES = Path(__file__).resolve().parent / "fixtures" / "security"


class SecurityAdversarialTests(TempRepoTestCase):
    def test_path_traversal_refused(self) -> None:
        with self.assertRaises(InvalidPackageError):
            as_posix_rel("../escape")
        with self.assertRaises(InvalidPackageError):
            as_posix_rel("/absolute/path")

    def test_destination_symlink_fail_closed(self) -> None:
        outside = Path(self._tmp.name) / "victim"
        outside.mkdir()
        secret = outside / "secret.txt"
        secret.write_text("STAY\n", encoding="utf-8")
        parent = self.target / ".ide-development"
        parent.mkdir(parents=True, exist_ok=True)
        link = parent / "CORE.txt"
        link.symlink_to(secret)
        result = run_install_or_update(
            target=self.target,
            package=self.package,
            command="install",
            dry_run=False,
        )
        self.assertEqual(result.exit_code, EXIT_CONFLICT)
        self.assertEqual(secret.read_text(encoding="utf-8"), "STAY\n")

    def test_source_symlink_in_package_refused(self) -> None:
        pkg = Path(self._tmp.name) / "pkg-symlink"
        shutil.copytree(FIXTURE_PACKAGE, pkg)
        core = pkg / "core/managed-core/files/CORE.txt"
        data = core.read_bytes()
        decoy = pkg / "core/managed-core/files/decoy-physical.txt"
        decoy.write_bytes(data)
        core.unlink()
        core.symlink_to(decoy.name)
        with self.assertRaises(InvalidPackageError) as ctx:
            load_manifest(pkg)
        self.assertIn("symlink", str(ctx.exception).lower())

    def test_wrong_hash_invalid_package(self) -> None:
        pkg = Path(self._tmp.name) / "bad-hash"
        shutil.copytree(FIXTURE_PACKAGE, pkg)
        manifest_path = pkg / "core/managed-core/MANIFEST.json"
        data = json.loads(manifest_path.read_text(encoding="utf-8"))
        data["files"][0]["sourceHash"] = "sha256:" + ("c" * 64)
        manifest_path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
        with self.assertRaises(InvalidPackageError):
            run_plan(target=self.target, package=pkg)

    def test_duplicate_destination_refused(self) -> None:
        pkg = Path(self._tmp.name) / "dup-dest"
        shutil.copytree(FIXTURE_PACKAGE, pkg)
        manifest_path = pkg / "core/managed-core/MANIFEST.json"
        data = json.loads(manifest_path.read_text(encoding="utf-8"))
        clone = dict(data["files"][0])
        clone["id"] = "clone-id"
        clone["destination"] = data["files"][1]["destination"]
        data["files"].append(clone)
        manifest_path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
        with self.assertRaises(InvalidPackageError):
            load_manifest(pkg)

    def test_lock_symlink_refused(self) -> None:
        meta = git_meta_dir(self.target)
        meta.mkdir(parents=True, exist_ok=True)
        real = Path(self._tmp.name) / "lock-real"
        real.write_bytes(b"\0")
        lock = meta / "lock"
        lock.symlink_to(real)
        with self.assertRaises(ConflictError):
            with exclusive_transaction_lock(self.target):
                pass  # pragma: no cover

    def test_consumer_owned_preserved(self) -> None:
        owned = self.target / ".cursor" / "rules" / "mine.mdc"
        owned.parent.mkdir(parents=True, exist_ok=True)
        owned.write_text("mine\n", encoding="utf-8")
        collide = self.target / ".cursor" / "rules" / "sample-rule.mdc"
        collide.write_text("foreign\n", encoding="utf-8")
        result = run_install_or_update(
            target=self.target,
            package=self.package,
            command="install",
            dry_run=False,
        )
        self.assertEqual(result.exit_code, EXIT_CONFLICT)
        self.assertEqual(owned.read_text(encoding="utf-8"), "mine\n")

    def test_rollback_without_tx_exit_code(self) -> None:
        from contextlib import redirect_stdout, redirect_stderr
        import io
        from ide_development.cli import main

        buf = io.StringIO()
        with redirect_stdout(buf), redirect_stderr(buf):
            code = main(["rollback", "--target", str(self.target), "--json"])
        self.assertEqual(code, EXIT_ROLLBACK_FAILURE)

    def test_security_fixture_wrong_repo_present(self) -> None:
        path = SECURITY_FIXTURES / "cleanup" / "wrong-repo-evidence.json"
        self.assertTrue(path.is_file())
        payload = json.loads(path.read_text(encoding="utf-8"))
        self.assertNotEqual(payload.get("repository"), "linktrend/IDE-Development")
        self.assertTrue(payload.get("applyForbidden"))

    def test_atomic_write_refuses_symlink_dest(self) -> None:
        real = Path(self._tmp.name) / "real.txt"
        real.write_text("keep\n", encoding="utf-8")
        link = Path(self._tmp.name) / "link.txt"
        link.symlink_to(real)
        with self.assertRaises(OSError):
            atomic_write_bytes(link, b"nope\n", mode="0644")
        self.assertEqual(real.read_text(encoding="utf-8"), "keep\n")


if __name__ == "__main__":
    unittest.main()
