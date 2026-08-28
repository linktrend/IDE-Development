"""Adversarial tests for the v2 managed upgrade receipt boundary."""

from __future__ import annotations

import json
import unittest
from pathlib import Path

from ide_development.errors import InvalidPackageError
from ide_development.resolution import (
    ALLOWED_CONFLICT_PATHS,
    KIND,
    PROVIDER_COMMIT,
    PROVIDER_TREE,
    _canonical_digest,
    _package_source_digest,
    _validate_provider_entry,
    _validate_provider_source_identity,
    _path,
    _validate_observed_conflict_paths,
    _validate_change_scoped_binding,
    load_and_validate_resolution,
)
from ide_development_tests import TempRepoTestCase


class ResolutionTests(TempRepoTestCase):
    def test_managed_upgrade_allowlist_matches_schema_union(self) -> None:
        expected = {
            ".ide-development/schemas/managed-upgrade-resolution.schema.json",
            ".ide-development/schemas/phase-handoff.schema.json",
            ".ide-development/schemas/phase-record.schema.json",
            ".ide-development/tests/test_delivery_controller.py",
            ".ide-development/tests/test_fixture_aware_secret_scan.py",
            ".ide-development/tests/test_phase_packager_coordinator.py",
            ".ide-development/tests/test_receipt_seal_and_recovery.py",
            ".ide-development/workflows/linktrend-integrator-merge.yml",
            "scripts/gitops/completion_gate.py",
            "scripts/gitops/delivery_controller.py",
            "scripts/gitops/github_auth.py",
            "scripts/gitops/issue_checkpoint.py",
            "scripts/gitops/packager_coordinator.py",
            "scripts/gitops/phase_integrator.py",
            "scripts/gitops/receipt_seal.py",
            "scripts/gitops/secret_scan.py",
            "scripts/ide_development/resolution.py",
        }
        self.assertEqual(ALLOWED_CONFLICT_PATHS, expected)
        schema_path = (
            Path(__file__).resolve().parents[2]
            / "core/managed-core/schemas/managed-upgrade-resolution.schema.json"
        )
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
        self.assertEqual(
            schema["properties"]["provider"]["properties"]["commit"]["const"],
            PROVIDER_COMMIT,
        )
        self.assertEqual(
            schema["properties"]["provider"]["properties"]["tree"]["const"],
            PROVIDER_TREE,
        )
        self.assertEqual(schema["properties"]["allowedConflictPaths"]["const"], sorted(expected))
        self.assertEqual(schema["$defs"]["conflict"]["properties"]["path"]["enum"], sorted(expected))
        self.assertEqual(schema["properties"]["conflicts"]["minItems"], 1)
        manifest = json.loads(
            (Path(__file__).resolve().parents[2] / "core/managed-core/MANIFEST.json").read_text(
                encoding="utf-8"
            )
        )
        entries = {entry["destination"]: entry for entry in manifest["files"]}
        for path in expected:
            entry = entries[path]
            self.assertIn(entry["ownershipClass"], {"managed", "managed-core", "managed-entrypoint"})
            self.assertEqual(entry["mergeStrategy"], "replace")

    def test_observed_conflicts_may_be_a_nonempty_allowlisted_subset_only(self) -> None:
        for path in sorted(ALLOWED_CONFLICT_PATHS):
            self.assertEqual(_validate_observed_conflict_paths([path]), {path})
        observed = _validate_observed_conflict_paths(sorted(ALLOWED_CONFLICT_PATHS))
        self.assertEqual(observed, ALLOWED_CONFLICT_PATHS)
        with self.assertRaises(InvalidPackageError):
            _validate_observed_conflict_paths([])
        with self.assertRaises(InvalidPackageError):
            _validate_observed_conflict_paths(["consumer-owned.txt"])

    def test_extracted_package_provider_identity_is_digest_bound(self) -> None:
        package_root = Path(self._tmp.name) / "official-extracted-package"
        from ide_development.release_candidate import collect_package_paths, stage_package_tree
        from ide_development.hashing import sha256_file

        package_root.mkdir()
        stage_package_tree(
            repo_root=Path(__file__).resolve().parents[2],
            staging_root=package_root,
            paths=collect_package_paths(Path(__file__).resolve().parents[2]),
        )
        self.assertFalse((package_root / ".git").exists())
        manifest_path = package_root / "core/managed-core/MANIFEST.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        provider = {
            "repository": "linktrend/IDE-Development",
            "authoritativeRef": "phase/ide-v2.5.2",
        }
        digest = sha256_file(manifest_path)
        provider_digest = _package_source_digest(
            package_root,
            manifest,
            manifest_digest=digest,
            provider=provider,
            provider_commit=PROVIDER_COMMIT,
            provider_tree=PROVIDER_TREE,
        )
        bound_provider = {**provider, "packageSourceDigest": provider_digest}
        self.assertEqual(
            _validate_provider_source_identity(
                package_root,
                manifest,
                manifest_digest=digest,
                provider=bound_provider,
                provider_commit=PROVIDER_COMMIT,
                provider_tree=PROVIDER_TREE,
            ),
            provider_digest,
        )
        with self.assertRaisesRegex(InvalidPackageError, "repository/ref identity"):
            _validate_provider_source_identity(
                package_root,
                manifest,
                manifest_digest=digest,
                provider={**bound_provider, "repository": "owner/consumer"},
                provider_commit=PROVIDER_COMMIT,
                provider_tree=PROVIDER_TREE,
            )
        with self.assertRaisesRegex(InvalidPackageError, "commit/tree identity"):
            _validate_provider_source_identity(
                package_root,
                manifest,
                manifest_digest=digest,
                provider=bound_provider,
                provider_commit="d" * 40,
                provider_tree=PROVIDER_TREE,
            )
        source = package_root / "scripts/ide_development/resolution.py"
        source.write_text("stale provider bytes\n", encoding="utf-8")
        with self.assertRaisesRegex(InvalidPackageError, "source identity is stale"):
            _validate_provider_source_identity(
                package_root,
                manifest,
                manifest_digest=digest,
                provider=bound_provider,
                provider_commit=PROVIDER_COMMIT,
                provider_tree=PROVIDER_TREE,
            )

    def test_unauthorized_paths_and_non_provider_entries_are_rejected(self) -> None:
        with self.assertRaises(InvalidPackageError):
            _validate_observed_conflict_paths(["scripts/gitops/*.py"])
        with self.assertRaises(InvalidPackageError):
            _validate_observed_conflict_paths(["consumer-owned.txt"])
        with self.assertRaises(InvalidPackageError):
            _validate_provider_entry(
                {"ownershipClass": "consumer-preserve", "mergeStrategy": "replace"},
                "scripts/gitops/secret_scan.py",
            )
        with self.assertRaises(InvalidPackageError):
            _validate_provider_entry(
                {"ownershipClass": "managed", "mergeStrategy": "marker-upsert"},
                "scripts/gitops/secret_scan.py",
            )

    def test_change_scoped_binding_is_digest_bound_and_rejects_missing_input(self) -> None:
        evidence = {
            "schemaVersion": 1,
            "kind": "change-scoped-secret-scan-evidence",
            "repository": "example/consumer",
            "authoritativeRemoteRef": "origin/development",
            "baselineCommit": "a" * 40,
            "baselineTree": "b" * 40,
            "candidateCommit": "c" * 40,
            "candidateGitTree": "d" * 40,
            "scannerPolicyVersion": "secret-scan-policy/1",
            "managedPaths": ["scripts/gitops/secret_scan.py"],
            "configDigest": "sha256:" + "e" * 64,
            "findings": [],
        }
        binding = {"evidence": evidence, "evidenceDigest": _canonical_digest(evidence)}
        _validate_change_scoped_binding({"changeScopedSecretScan": binding})
        stale = {"changeScopedSecretScan": {**binding, "evidenceDigest": "sha256:" + "0" * 64}}
        with self.assertRaises(InvalidPackageError):
            _validate_change_scoped_binding(stale)
        with self.assertRaises(InvalidPackageError):
            _validate_change_scoped_binding({"changeScopedSecretScan": {"evidence": evidence}})

    def test_rejects_legacy_or_ambiguous_resolution_shape(self) -> None:
        path = Path(self._tmp.name) / "legacy.json"
        path.write_text(json.dumps({"kind": KIND, "schemaVersion": 1}), encoding="utf-8")
        with self.assertRaises(InvalidPackageError):
            load_and_validate_resolution(path, target_root=self.target, package_root=Path(__file__).resolve().parents[2], package_version="2.5.1", package_manifest_digest="sha256:" + "0" * 64, prior_package_version="2.5.0", observed_conflicts=[])

    def test_rejects_traversal_and_wildcards(self) -> None:
        for value in ("../escape", "scripts/../escape", "*"):
            with self.assertRaises(InvalidPackageError):
                _path(value)

    def test_rejects_resolution_without_exact_conflict_set(self) -> None:
        path = Path(self._tmp.name) / "incomplete.json"
        path.write_text(json.dumps({"kind": KIND, "schemaVersion": 2, "targetWorktree": str(self.target), "consumer": {"commit": "0" * 40, "tree": "0" * 40}, "provider": {}, "allowedConflictPaths": [], "conflicts": [], "verification": {}, "backupAndRollback": {}, "resolution": {}}), encoding="utf-8")
        with self.assertRaises(InvalidPackageError):
            load_and_validate_resolution(path, target_root=self.target, package_root=Path(__file__).resolve().parents[2], package_version="2.5.1", package_manifest_digest="sha256:" + "0" * 64, prior_package_version="2.5.0", observed_conflicts=[])


if __name__ == "__main__":
    unittest.main()
