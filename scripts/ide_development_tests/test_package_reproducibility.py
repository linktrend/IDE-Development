"""Reproducibility proofs for managed-core manifest and RC archives."""

from __future__ import annotations

import unittest
from pathlib import Path

from ide_development import build_manifest as bm
from ide_development import release_candidate as rc
from ide_development.constants import PACKAGE_VERSION_TARGET
from ide_development.hashing import sha256_bytes


class ManifestReproducibilityTests(unittest.TestCase):
    def test_consecutive_write_manifest_byte_identical(self) -> None:
        first_obj = bm.write_manifest()
        first_bytes = bm.MANIFEST_PATH.read_bytes()
        second_obj = bm.write_manifest()
        second_bytes = bm.MANIFEST_PATH.read_bytes()
        self.assertEqual(first_bytes, second_bytes)
        self.assertEqual(first_obj["packageVersion"], PACKAGE_VERSION_TARGET)
        self.assertEqual(second_obj["packageVersion"], PACKAGE_VERSION_TARGET)
        self.assertEqual(sha256_bytes(first_bytes), sha256_bytes(second_bytes))

    def test_verify_manifest_clean_after_write(self) -> None:
        bm.write_manifest()
        errors = bm.verify_manifest()
        self.assertEqual(errors, [], errors)

    def test_release_candidate_schemas_listed_in_generated_manifest(self) -> None:
        bm.write_manifest()
        obj = bm.build_manifest_object()
        destinations = {row["destination"] for row in obj["files"]}
        self.assertIn(
            ".ide-development/schemas/release-candidate.schema.json",
            destinations,
        )
        self.assertIn(
            ".ide-development/schemas/release-candidate-checksums.schema.json",
            destinations,
        )


class ArchiveReproducibilityHelperTests(unittest.TestCase):
    def test_collect_package_paths_are_repo_relative(self) -> None:
        # Ensure MANIFEST exists and is current for path collection.
        bm.write_manifest()
        paths = rc.collect_package_paths()
        self.assertTrue(paths)
        for rel in paths:
            self.assertFalse(rel.startswith("/"), rel)
            self.assertNotIn("..", Path(rel).parts)
            self.assertFalse(rel.startswith("build/"), rel)
            self.assertFalse(rel.startswith(".git/"), rel)


if __name__ == "__main__":
    unittest.main()
