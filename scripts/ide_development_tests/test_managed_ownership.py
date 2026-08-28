"""Focused MNG-02..MNG-05, MNG-09 and MNG-10 proofs."""

from __future__ import annotations

import json
import os
import shutil
import stat
import unittest
from pathlib import Path
from unittest.mock import patch

from ide_development.constants import EXIT_DRIFT, EXIT_OK
from ide_development.engine import run_drift, run_install_or_update
from ide_development.errors import ConflictError, InvalidPackageError
from ide_development.hashing import sha256_file
from ide_development.managed_write_guard import (
    export_candidate,
    managed_write_lease,
    read_only_mode,
)
from ide_development.manifest import load_manifest
from ide_development.plan import OpKind, PlanAction
from ide_development.state import load_installed_state
from ide_development.transaction import BackupRecord, apply_action, restore_backup, write_backup_file
from ide_development_tests import FIXTURE_PACKAGE, TempRepoTestCase


class ManagedOwnershipTests(TempRepoTestCase):
    def test_transaction_managed_writes_require_an_active_exact_lease(self) -> None:
        action = PlanAction(op=OpKind.NOOP, path=".ide-development/CORE.txt")
        record = BackupRecord(
            path=".ide-development/CORE.txt",
            existed=False,
            mode=None,
            content_hash=None,
            backup_name=None,
        )

        with self.assertRaises(ConflictError):
            apply_action(
                target_root=self.target,
                package_root=self.package,
                action=action,
                entries={},
            )
        with self.assertRaises(ConflictError):
            write_backup_file(
                self.target / "tx",
                self.target,
                record,
            )
        with self.assertRaises(ConflictError):
            restore_backup(self.target, self.target / "tx", record)

    def test_lease_preflights_destinations_before_chmod(self) -> None:
        target_file = self.target / ".ide-development/CORE.txt"
        target_file.parent.mkdir(parents=True)
        target_file.write_text("managed\n", encoding="utf-8")
        os_mode = stat.S_IMODE(target_file.stat().st_mode)
        invalid_destination = self.target / "invalid-destination"
        invalid_destination.mkdir()

        with self.assertRaises(ConflictError):
            with managed_write_lease(
                target_root=self.target,
                paths=[".ide-development/CORE.txt", "invalid-destination"],
                operation="repair",
                package_version="2.1.0",
                manifest_digest="sha256:" + "0" * 64,
                transaction_id="preflight-destination",
            ):
                self.fail("lease acquisition should reject the non-file destination")

        self.assertEqual(stat.S_IMODE(target_file.stat().st_mode), os_mode)

    def test_lease_restores_modes_when_chmod_fails_during_acquisition(self) -> None:
        paths = [
            self.target / ".ide-development/CORE.txt",
            self.target / ".ide-development/assets/file-with-spaces.txt",
        ]
        for path in paths:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("managed\n", encoding="utf-8")
            path.chmod(0o444)

        real_chmod = os.chmod
        calls = 0

        def fail_on_second_chmod(path: Path, mode: int) -> None:
            nonlocal calls
            calls += 1
            if calls == 2:
                raise OSError("synthetic chmod failure")
            real_chmod(path, mode)

        with patch("ide_development.managed_write_guard.os.chmod", side_effect=fail_on_second_chmod):
            with self.assertRaises(OSError):
                with managed_write_lease(
                    target_root=self.target,
                    paths=[
                        ".ide-development/CORE.txt",
                        ".ide-development/assets/file-with-spaces.txt",
                    ],
                    operation="repair",
                    package_version="2.1.0",
                    manifest_digest="sha256:" + "0" * 64,
                    transaction_id="chmod-rollback",
                ):
                    self.fail("lease acquisition should fail on the synthetic chmod error")

        self.assertEqual(calls, 3)
        for path in paths:
            self.assertEqual(stat.S_IMODE(path.stat().st_mode), 0o444)

    def test_install_is_read_only_and_persists_ownership(self) -> None:
        result = run_install_or_update(
            target=self.target, package=self.package, command="install", dry_run=False
        )
        self.assertEqual(result.exit_code, EXIT_OK, result.payload)
        state = load_installed_state(self.target)
        assert state is not None
        self.assertTrue(state.manifest_hash)
        for rel, file_state in state.files.items():
            path = self.target / rel
            if path.is_file() and not path.is_symlink():
                self.assertEqual(
                    stat.S_IMODE(path.stat().st_mode),
                    int(read_only_mode(path.stat().st_mode), 8),
                    rel,
                )
            self.assertEqual(file_state.mutability_policy, "read-only")
            self.assertTrue(file_state.owner)
            self.assertEqual(file_state.package_version, "2.1.0")
            self.assertEqual(file_state.source_hash, file_state.to_dict()["sourceDigest"])
            self.assertEqual(file_state.content_hash, file_state.to_dict()["installedDigest"])

    def test_lease_is_scoped_and_candidate_export_preserves_source(self) -> None:
        run_install_or_update(
            target=self.target, package=self.package, command="install", dry_run=False
        )
        target_file = self.target / ".ide-development/CORE.txt"
        original = target_file.read_bytes()
        manifest_digest = sha256_file(self.package / "core/managed-core/MANIFEST.json")
        with managed_write_lease(
            target_root=self.target,
            paths=[".ide-development/CORE.txt"],
            operation="repair",
            package_version="2.1.0",
            manifest_digest=manifest_digest,
            transaction_id="focused-lease",
        ) as lease:
            with self.assertRaises(ConflictError):
                lease.assert_authorized(".ide-development/assets/file-with-spaces.txt")
            target_file.write_bytes(original + b"candidate\n")
        self.assertEqual(stat.S_IMODE(target_file.stat().st_mode), 0o444)
        exported = export_candidate(
            self.target,
            ".ide-development/CORE.txt",
            package_version="2.1.0",
            classification="candidate_central_ide_improvement",
        )
        self.assertEqual(exported["candidateDigest"], sha256_file(target_file))
        self.assertEqual(target_file.read_bytes(), original + b"candidate\n")
        quarantine = self.target / ".git" / "ide-development" / "quarantine" / str(exported["exportId"])
        self.assertEqual((quarantine / str(exported["blob"])).read_bytes(), target_file.read_bytes())
        self.assertEqual(json.loads((quarantine / "receipt.json").read_text())["path"], ".ide-development/CORE.txt")

    def test_obsolete_residue_is_classified_without_deletion(self) -> None:
        obsolete = self.target / ".cursor/rules/obsolete-generic.mdc"
        obsolete.parent.mkdir(parents=True)
        obsolete.write_bytes(
            (self.package / "core/managed-core/files/obsolete-generic.txt").read_bytes()
        )
        result = run_drift(target=self.target, package=self.package)
        self.assertEqual(result.exit_code, EXIT_DRIFT)
        self.assertIn("obsolete_residue", {item["kind"] for item in result.payload["drift"]})
        self.assertTrue(obsolete.exists())

    def test_same_version_different_bytes_fail_closed(self) -> None:
        run_install_or_update(
            target=self.target, package=self.package, command="install", dry_run=False
        )
        package = Path(self._tmp.name) / "collision-package"
        shutil.copytree(self.package, package)
        source = package / "core/managed-core/files/CORE.txt"
        source.write_text("different bytes\n", encoding="utf-8")
        manifest_path = package / "core/managed-core/MANIFEST.json"
        manifest = json.loads(manifest_path.read_text())
        for entry in manifest["files"]:
            if entry["id"] == "managed-core-readme":
                entry["sourceHash"] = sha256_file(source)
        manifest_path.write_text(json.dumps(manifest, indent=2) + "\n")
        with self.assertRaises(InvalidPackageError):
            run_install_or_update(
                target=self.target, package=package, command="update", dry_run=False
            )

    def test_capability_dependency_must_be_present(self) -> None:
        package = Path(self._tmp.name) / "capability-package"
        shutil.copytree(self.package, package)
        manifest_path = package / "core/managed-core/MANIFEST.json"
        manifest = json.loads(manifest_path.read_text())
        manifest["capabilities"] = [
            {"id": "delivery", "version": "1", "requires": ["missing-component"]}
        ]
        manifest_path.write_text(json.dumps(manifest, indent=2) + "\n")
        with self.assertRaises(InvalidPackageError):
            load_manifest(package)


if __name__ == "__main__":
    unittest.main()
