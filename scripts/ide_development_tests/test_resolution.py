"""Adversarial tests for the v2 managed upgrade receipt boundary."""

from __future__ import annotations

import json
import unittest
from pathlib import Path

from ide_development.errors import InvalidPackageError
from ide_development.resolution import (
    ALLOWED_CONFLICT_PATHS,
    KIND,
    _canonical_digest,
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
            ".ide-development/schemas/secret-scan-result.schema.json",
            ".ide-development/tests/test_fixture_aware_secret_scan.py",
            ".ide-development/tests/test_phase_packager_coordinator.py",
            "scripts/gitops/packager_coordinator.py",
            "scripts/gitops/phase_integrator.py",
            "scripts/gitops/secret_scan.py",
        }
        self.assertEqual(ALLOWED_CONFLICT_PATHS, expected)
        schema_path = (
            Path(__file__).resolve().parents[2]
            / "core/managed-core/schemas/managed-upgrade-resolution.schema.json"
        )
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
        self.assertEqual(schema["properties"]["allowedConflictPaths"]["const"], sorted(expected))
        self.assertEqual(schema["$defs"]["conflict"]["properties"]["path"]["enum"], sorted(expected))
        self.assertEqual(schema["properties"]["conflicts"]["minItems"], 1)

    def test_observed_conflicts_may_be_a_nonempty_allowlisted_subset_only(self) -> None:
        seven_paths = [
            ".ide-development/schemas/phase-handoff.schema.json",
            ".ide-development/schemas/phase-record.schema.json",
            ".ide-development/schemas/secret-scan-result.schema.json",
            ".ide-development/tests/test_phase_packager_coordinator.py",
            "scripts/gitops/packager_coordinator.py",
            "scripts/gitops/phase_integrator.py",
            "scripts/gitops/secret_scan.py",
        ]
        observed = _validate_observed_conflict_paths(seven_paths)
        self.assertEqual(len(observed), 7)
        self.assertEqual(_validate_observed_conflict_paths(ALLOWED_CONFLICT_PATHS), ALLOWED_CONFLICT_PATHS)
        with self.assertRaises(InvalidPackageError):
            _validate_observed_conflict_paths([])
        with self.assertRaises(InvalidPackageError):
            _validate_observed_conflict_paths(["consumer-owned.txt"])

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
