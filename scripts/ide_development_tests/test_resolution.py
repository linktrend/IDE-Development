"""Adversarial tests for the v2 managed upgrade receipt boundary."""

from __future__ import annotations

import json
import unittest
from pathlib import Path

from ide_development.errors import InvalidPackageError
from ide_development.resolution import KIND, _path, load_and_validate_resolution
from ide_development_tests import TempRepoTestCase


class ResolutionTests(TempRepoTestCase):
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
