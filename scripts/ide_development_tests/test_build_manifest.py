"""Focused packaging checks for build_manifest / CONTENT_DOCTRINE sync."""

from __future__ import annotations

import json
import unittest
from pathlib import Path

from ide_development import build_manifest as bm

REQUIRED_DOCTRINE = {
    "AGENT-COMPLETION.md",
    "MANAGED-CORE-V2.md",
    "REPOSITORY-PROTECTION.md",
    "0003-autonomous-ship-pull-promote.md",
    "0004-portable-managed-core-v2.md",
    "AUTONOMOUS-GIT-OPERATIONS.md",
}


class BuildManifestPackagingTests(unittest.TestCase):
    def test_content_doctrine_covers_required_contracts(self) -> None:
        names = {Path(dest).name for _, dest in bm.CONTENT_DOCTRINE}
        self.assertEqual(REQUIRED_DOCTRINE, names & REQUIRED_DOCTRINE)
        missing = REQUIRED_DOCTRINE - names
        self.assertFalse(missing, f"CONTENT_DOCTRINE missing: {sorted(missing)}")

    def test_content_doctrine_sources_exist(self) -> None:
        for src_rel, dest_rel in bm.CONTENT_DOCTRINE:
            self.assertTrue((bm.REPO_ROOT / src_rel).is_file(), src_rel)
            self.assertTrue(
                dest_rel.startswith("content/doctrine/"),
                f"unexpected dest {dest_rel}",
            )

    def test_version_alignment_helpers(self) -> None:
        errors = bm._version_alignment_errors()
        self.assertEqual(errors, [], errors)

    def test_manifest_package_version_identity(self) -> None:
        path = bm.MANIFEST_PATH
        self.assertTrue(path.is_file())
        data = json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual(data.get("packageVersion"), "2.1.3")
        managed = bm.VERSION_PATH.read_text(encoding="utf-8").strip().lstrip("v")
        self.assertEqual(managed, "2.1.3")

    def test_required_cursor_materialization_sources_are_packaged(self) -> None:
        manifest = bm.build_manifest_object()
        destinations = {row["destination"] for row in manifest["files"]}
        materialization = json.loads(
            (bm.MANAGED / "platforms" / "cursor" / "materialization-manifest.json").read_text(
                encoding="utf-8"
            )
        )
        missing = []
        for row in materialization["entries"]:
            if not row.get("required"):
                continue
            package_source = f'.ide-development/{row["source"]}'
            if package_source not in destinations:
                missing.append(package_source)
        self.assertEqual(missing, [])


if __name__ == "__main__":
    unittest.main()
