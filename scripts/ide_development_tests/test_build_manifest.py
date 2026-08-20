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
        self.assertEqual(data.get("packageVersion"), "2.4.0")
        managed = bm.VERSION_PATH.read_text(encoding="utf-8").strip().lstrip("v")
        self.assertEqual(managed, "2.4.0")

    def test_required_cursor_materialization_sources_are_packaged(self) -> None:
        manifest = bm.build_manifest_object()
        destinations = {row["destination"] for row in manifest["files"]}
        materialization = json.loads(
            (bm.MANAGED / "platforms" / "cursor" / "materialization-manifest.json").read_text(
                encoding="utf-8"
            )
        )
        missing = []
        missing_cursor = []
        for row in materialization["entries"]:
            if not row.get("required"):
                continue
            package_source = f'.ide-development/{row["source"]}'
            if package_source not in destinations:
                missing.append(package_source)
            cursor_destination = row["destination"]
            if cursor_destination not in destinations:
                missing_cursor.append(cursor_destination)
        self.assertEqual(missing, [])
        self.assertEqual(missing_cursor, [])

    def test_library_vendor_rename_has_exact_removal_migrations(self) -> None:
        catalog = json.loads(
            (bm.MANAGED / "migrations" / "catalog.json").read_text(encoding="utf-8")
        )
        removals = {
            row["path"]: row["contentHash"]
            for row in catalog["entries"]
            if row.get("action") == "remove"
        }
        hashes = {
            "NOTICE.md": "sha256:8bb0aa96c38ee65660037f50f4768f08861bc00665fe3efd284aea5ca57f4b0e",
            "spdx-exceptions.json": "sha256:05079063787565a9c14278d09144df3430cd353aab5c2db2a372b9230cf04594",
            "spdx-expression-validate.mjs": "sha256:b159caceed95671aacfa6adb939856cd9df800b327cf01590f0f439b73075d9c",
            "spdx-license-ids-deprecated.json": "sha256:58657e9b38a85b4ab2ea56115738590ee06d28c87667efaa5b83737657d43094",
            "spdx-license-ids.json": "sha256:01229f894127ed2c09222de370817e7128340d89fc10a521f0d309dd89647873",
        }
        expected = {
            f"{root}/library/vendor/{name}": digest
            for root in (".cursor", ".ide-development")
            for name, digest in hashes.items()
        }
        self.assertEqual({path: removals.get(path) for path in expected}, expected)

    def test_hosted_defaults_and_redacted_cleanup_inventory_are_packaged(self) -> None:
        config = json.loads(
            (bm.MANAGED / "config" / "delivery.json").read_text(encoding="utf-8")
        )
        self.assertEqual(config["schemaVersion"], 2)
        self.assertEqual(config["compute"]["provider"], "github-hosted")
        self.assertEqual(config["compute"]["runner"], "ubuntu-24.04-arm")
        self.assertFalse(config["compute"]["checkpointCI"])
        expected = [
            ["python3", "-m", "py_compile", "scripts/gitops/run_delivery_profile.py", "scripts/gitops/gate_receipt.py", "scripts/gitops/secret_scan.py", "scripts/gitops/repository_ci_contract.py", "scripts/gitops/receipt_seal.py"],
            ["python3", "scripts/gitops/secret_scan.py"],
        ]
        self.assertEqual(config["profiles"]["fast"]["commands"], expected)
        self.assertEqual(config["profiles"]["full"]["commands"], expected)
        self.assertTrue(config["profiles"]["full"]["required"])

        cleanup = json.loads(
            (bm.MANAGED / "migrations" / "external-cleanup-plan.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual(len(cleanup["repositories"]), 9)
        self.assertEqual(cleanup["applyAuthority"], "W3")
        self.assertFalse(any("value" in row for row in cleanup["targets"]))

        manifest = bm.build_manifest_object()
        sources = {row["source"] for row in manifest["files"]}
        self.assertIn("core/managed-core/config/delivery.json", sources)
        self.assertIn("core/managed-core/migrations/external-cleanup-plan.json", sources)
        self.assertNotIn("scripts/gitops/resolve_automation_token.sh", sources)
        self.assertIn("scripts/gitops/packager_coordinator.py", sources)
        self.assertIn("scripts/gitops/independent_review_convergence.py", sources)
        self.assertIn("scripts/gitops/secret_scan.py", sources)
        self.assertIn("scripts/gitops/secret_scan_migrate.py", sources)
        self.assertIn("scripts/gitops/repository_ci_contract.py", sources)
        self.assertNotIn("scripts/gitops/packager_discover.py", sources)

    def test_cleanroom_extract_fixture_ships_repository_ci_contract(self) -> None:
        fixture = bm.CLEANROOM_FIXTURE_ROOT
        contract = fixture / bm.CI_CONTRACT_SOURCE
        self.assertTrue(contract.is_file(), bm.CI_CONTRACT_SOURCE)
        errors = bm._cleanroom_fixture_errors()
        self.assertEqual(errors, [], errors)


if __name__ == "__main__":
    unittest.main()
