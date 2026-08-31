"""Focused packaging checks for build_manifest / CONTENT_DOCTRINE sync."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from ide_development import build_manifest as bm
from ide_development import release_candidate as rc

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

    def test_full_root_workflow_is_packaged_onto_consumer_github(self) -> None:
        destinations = {row["destination"] for row in bm.build_manifest_object()["files"]}
        self.assertIn(".ide-development/workflows/linktrend-integrator-merge.yml", destinations)
        self.assertIn(".github/workflows/linktrend-integrator-merge.yml", destinations)

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
        self.assertEqual(data.get("packageVersion"), "2.5.2")
        managed = bm.VERSION_PATH.read_text(encoding="utf-8").strip().lstrip("v")
        self.assertEqual(managed, "2.5.2")

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

    def test_runtime_manifest_missing_source_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory(prefix="runtime-manifest-") as tmp:
            root = Path(tmp)
            runtime_manifest = root / "core" / "github" / "managed-runtime" / "MANIFEST.json"
            runtime_manifest.parent.mkdir(parents=True)
            runtime_manifest.write_text(
                json.dumps(
                    {
                        "files": list(bm.REQUIRED_RUNTIME_PACKAGE_SOURCES),
                    }
                ),
                encoding="utf-8",
            )
            with mock.patch.object(bm, "REPO_ROOT", root):
                with self.assertRaises(FileNotFoundError):
                    bm._gitops_script_sources()

    def test_runtime_manifest_declares_contract_dependencies(self) -> None:
        sources = set(bm._gitops_script_sources())
        self.assertTrue(
            set(bm.REQUIRED_RUNTIME_PACKAGE_SOURCES).issubset(sources),
            "runtime manifest must export the CI contract and its package dependency",
        )

    def test_release_candidate_exports_contract_dependencies(self) -> None:
        package_paths = set(rc.collect_package_paths())
        self.assertTrue(
            set(bm.REQUIRED_RUNTIME_PACKAGE_SOURCES).issubset(package_paths),
            "release-candidate package paths must include the CI contract dependency closure",
        )

    def test_application_canary_runtime_is_installable(self) -> None:
        manifest = bm.build_manifest_object()
        destinations = {row["destination"] for row in manifest["files"]}
        required = {
            ".ide-development/runtime/scripts/ide_development/app_canary.mjs",
            ".ide-development/runtime/core/managed-core/platforms/codex/adapter.mjs",
            ".ide-development/runtime/core/managed-core/platforms/cursor/adapter.mjs",
            ".ide-development/runtime/core/link-integrations/errors.mjs",
            ".ide-development/runtime/core/link-integrations/clients.mjs",
            ".ide-development/runtime/core/link-integrations/index.mjs",
        }
        self.assertEqual(required - destinations, set())

    def test_execution_manifest_contract_is_installable(self) -> None:
        manifest = bm.build_manifest_object()
        destinations = {row["destination"] for row in manifest["files"]}
        required = {
            ".ide-development/execution/CODING-EXECUTION-PROTOCOL.md",
            ".ide-development/contracts/EXECUTION-CONTROL-CONTRACT.md",
            ".ide-development/contracts/EXECUTION-MANIFEST.schema.json",
        }
        self.assertEqual(required - destinations, set())

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

    def test_hosted_defaults_are_packaged_without_portfolio_rollout_data(self) -> None:
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

        manifest = bm.build_manifest_object()
        sources = {row["source"] for row in manifest["files"]}
        self.assertIn("core/managed-core/config/delivery.json", sources)
        self.assertNotIn(
            "core/managed-core/migrations/external-cleanup-plan.json", sources
        )
        self.assertNotIn("scripts/gitops/resolve_automation_token.sh", sources)
        self.assertIn("scripts/gitops/packager_coordinator.py", sources)
        self.assertIn("scripts/gitops/independent_review_convergence.py", sources)
        self.assertIn("scripts/gitops/secret_scan.py", sources)
        self.assertIn("scripts/gitops/secret_scan_migrate.py", sources)
        self.assertIn("scripts/gitops/repository_ci_contract.py", sources)
        self.assertNotIn("scripts/gitops/packager_discover.py", sources)

        forbidden = (
            "openclaw_prime",
            "LiNKplatform",
            "LiNKskills",
            "LiNKbrain",
            "LiNKsites",
            "LiNKdeveloper",
            "LiNKlibraries",
            "LiNKautowork",
            "LiNKtrading-codebase",
        )
        rollout_boundary_files = [
            bm.MANAGED / "content" / "doctrine" / "MANAGED-CORE-V2.md",
            *(bm.MANAGED / "migrations").glob("*.json"),
            *(bm.MANAGED / "migrations").glob("*.md"),
        ]
        active_text = "\n".join(
            path.read_text(encoding="utf-8", errors="ignore")
            for path in rollout_boundary_files
        )
        for repository in forbidden:
            self.assertNotIn(repository, active_text)

        catalog = json.loads(
            (bm.MANAGED / "migrations" / "catalog.json").read_text(encoding="utf-8")
        )
        cleanup_removal = next(
            (
                row
                for row in catalog["entries"]
                if row["path"]
                == ".ide-development/migrations/external-cleanup-plan.json"
            ),
            None,
        )
        self.assertEqual(
            cleanup_removal,
            {
                "identity": ".ide-development/migrations/external-cleanup-plan.json",
                "path": ".ide-development/migrations/external-cleanup-plan.json",
                "contentHash": "sha256:8404f3c27f84d54539a9c928ce35a08180d67341c288fc4373b210a84727e53a",
                "action": "remove",
                "reason": "Remove the exact v2.5.0 portfolio-specific rollout cleanup plan from the reusable package.",
                "sincePackageVersion": "2.5.1",
            },
        )

    def test_pkt08_closure_and_persistence_contracts_are_packaged(self) -> None:
        manifest = bm.build_manifest_object()
        sources = {row["source"] for row in manifest["files"]}
        for rel in (
            "core/managed-core/content/config/generated-output-closure.consumer.json",
            "core/managed-core/content/config/manifest-persistence.json",
            "core/managed-core/schemas/generated-output-closure.schema.json",
            "core/managed-core/schemas/manifest-persistence.schema.json",
            "core/execution/manifest_persistence.py",
            "scripts/gitops/generated_output_closure.py",
            "scripts/tests/test_generated_output_closure.py",
            "scripts/tests/test_manifest_persistence_recovery.py",
            ".githooks/pre-push",
            "scripts/install-git-hooks.sh",
        ):
            self.assertIn(rel, sources)
        closure = json.loads(
            (bm.REPO_ROOT / "core/managed-core/config/generated-output-closure.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertIn("DOGFOOD_IMPROVEMENT_CLOSURE", closure["audits"])
        self.assertIn("LEAN_DESIGN", closure["audits"])
        destinations = {row["source"]: row["destination"] for row in manifest["files"]}
        self.assertEqual(
            destinations["core/managed-core/content/config/generated-output-closure.consumer.json"],
            ".ide-development/config/generated-output-closure.json",
        )
        consumer_closure = json.loads(
            (
                bm.REPO_ROOT
                / "core/managed-core/content/config/generated-output-closure.consumer.json"
            ).read_text(encoding="utf-8")
        )
        self.assertEqual(
            [row["id"] for row in consumer_closure["outputs"]],
            ["secret-scan-fixtures"],
        )
        self.assertFalse(
            any(
                "build_manifest.py" in part
                for row in consumer_closure["outputs"]
                for part in row["generator"]
            )
        )

    def test_pkt08_persistence_adversarial_runtime_is_in_managed_package(self) -> None:
        manifest = bm.build_manifest_object()
        rows = [
            row
            for row in manifest["files"]
            if isinstance(row.get("source"), str)
        ]
        runtime = next(
            row
            for row in rows
            if row["source"] == "core/execution/manifest_persistence.py"
            and row["destination"] == ".ide-development/execution/manifest_persistence.py"
        )
        self.assertEqual(
            runtime["destination"],
            ".ide-development/execution/manifest_persistence.py",
        )
        self.assertEqual(
            runtime["sourceHash"],
            bm._hash_rel("core/execution/manifest_persistence.py"),
        )
        source = (bm.REPO_ROOT / "core/execution/manifest_persistence.py").read_text(
            encoding="utf-8"
        )
        self.assertIn("MANIFEST_PERSISTENCE_FAILURE", source)
        self.assertIn("_validate_transition_event", source)
        self.assertTrue(
            any(
                row["source"] == "scripts/tests/test_manifest_persistence_recovery.py"
                and row["destination"] == ".ide-development/tests/test_manifest_persistence_recovery.py"
                for row in rows
            )
        )

    def test_hosted_portability_regression_inputs_are_packaged(self) -> None:
        manifest = bm.build_manifest_object()
        destinations = {
            row["source"]: row["destination"]
            for row in manifest["files"]
            if isinstance(row.get("source"), str)
        }
        self.assertEqual(
            destinations.get("scripts/tests/test_candidate_baseline_resolution.py"),
            ".ide-development/tests/test_candidate_baseline_resolution.py",
        )
        self.assertIn("scripts/gitops/generated_output_closure.py", destinations)
        self.assertIn("scripts/gitops/secret_scan.py", destinations)

    def test_pkt08_revision_60_final_controls_are_packaged(self) -> None:
        manifest = bm.build_manifest_object()
        sources = {row["source"] for row in manifest["files"]}
        for rel in (
            "core/contracts/PKT08-REVISION-60-FINAL-CONTROLS.md",
            "core/execution/transactional_dispatch.py",
            "core/execution/cursor_cloud_dispatch.py",
            "core/contracts/CURSOR-CLOUD-DISPATCH-CONTRACT.md",
            "core/managed-core/content/config/cursor-cloud-dispatch.json",
            "core/managed-core/content/doctrine/CURSOR-CLOUD-DISPATCH-CONTRACT.md",
            "core/managed-core/schemas/cursor-cloud-dispatch.schema.json",
            "core/managed-core/content/config/transactional-dispatch.json",
            "core/managed-core/content/doctrine/PKT08-REVISION-60-FINAL-CONTROLS.md",
            "core/managed-core/schemas/transactional-dispatch.schema.json",
        ):
            self.assertIn(rel, sources)

    def test_v252_packet_payloads_are_packaged(self) -> None:
        manifest = bm.build_manifest_object()
        sources = {row["source"] for row in manifest["files"]}
        for rel in (
            "core/managed-core/content/config/portfolio-control-loop.json",
            "core/managed-core/content/config/routing-registry.json",
            "core/managed-core/content/config/toolchain-manifest.json",
            "core/managed-core/schemas/managed-ownership.schema.json",
            "core/managed-core/schemas/mutation-declaration.schema.json",
            "core/managed-core/schemas/portfolio-control-loop.schema.json",
            "core/managed-core/schemas/provider-consumer-handoff.schema.json",
            "core/managed-core/schemas/routing-registry.schema.json",
            "core/managed-core/schemas/toolchain-manifest.schema.json",
            "core/managed-core/schemas/transition-receipt.schema.json",
            "core/managed-core/schemas/evidence-rebind-receipt.schema.json",
            "scripts/gitops/mutation_guard.py",
            "scripts/gitops/portfolio_control_loop.py",
            "scripts/gitops/receipt_loop_detector.py",
            "scripts/gitops/evidence_rebind.py",
            "scripts/gitops/runtime_preflight.py",
        ):
            self.assertIn(rel, sources)


if __name__ == "__main__":
    unittest.main()
