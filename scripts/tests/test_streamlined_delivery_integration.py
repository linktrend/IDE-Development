"""W3-P1 package and integration invariants."""

from __future__ import annotations

import json
import unittest
from pathlib import Path

from scripts.ide_development import build_manifest as bm
from scripts.ide_development.constants import PACKAGE_VERSION_TARGET
from scripts.ide_development.release_candidate import collect_package_paths


class StreamlinedDeliveryIntegrationTests(unittest.TestCase):
    def test_version_and_managed_doctrine_are_current(self) -> None:
        self.assertEqual(PACKAGE_VERSION_TARGET, "2.2.0")
        self.assertEqual((bm.REPO_ROOT / "VERSION").read_text().strip(), "v2.2.0")
        self.assertEqual((bm.VERSION_PATH).read_text().strip(), "2.2.0")
        doctrine = {source for source, _ in bm.CONTENT_DOCTRINE}
        self.assertIn("docs/contracts/STREAMLINED-DELIVERY.md", doctrine)
        self.assertIn("docs/adr/0005-streamlined-delivery-coordinator.md", doctrine)

    def test_shared_runtime_sources_are_packaged_but_host_code_is_not(self) -> None:
        runtime = json.loads(
            (bm.REPO_ROOT / "core/github/managed-runtime/MANIFEST.json").read_text()
        )
        required = {
            "scripts/gitops/coordinator/__init__.py",
            "scripts/gitops/coordinator/config.py",
            "scripts/gitops/coordinator/receipts.py",
            "scripts/gitops/coordinator/state.py",
            "scripts/gitops/gate_receipt.py",
            "scripts/gitops/phase_integrator.py",
            "scripts/gitops/promotion_receipt_gate.py",
            "scripts/gitops/ruleset_plan.py",
        }
        self.assertTrue(required.issubset(set(runtime["files"])))
        self.assertFalse(any(path.startswith("host/") for path in runtime["files"]))

        manifest = bm.build_manifest_object()
        sources = {row["source"] for row in manifest["files"]}
        self.assertTrue(required.issubset(sources))
        destinations = [row["destination"] for row in manifest["files"]]
        self.assertEqual(len(destinations), len(set(destinations)))
        self.assertLessEqual(len(sources), len(manifest["files"]))

    def test_release_candidate_paths_are_repo_relative_and_safe(self) -> None:
        paths = collect_package_paths(bm.REPO_ROOT)
        self.assertTrue(paths)
        self.assertTrue(all(not Path(path).is_absolute() for path in paths))
        self.assertTrue(all(".." not in Path(path).parts for path in paths))
        self.assertIn("core/managed-core/MANIFEST.json", paths)
        self.assertIn("scripts/gitops/coordinator/config.py", paths)


if __name__ == "__main__":
    unittest.main()
