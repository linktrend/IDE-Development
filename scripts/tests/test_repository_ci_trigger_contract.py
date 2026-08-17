"""Focused tests for WP-U07 repository-owned CI trigger contract."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from scripts.gitops.repository_ci_contract import (
    CLASS_APPLICATION,
    CLASS_MIXED,
    CLASS_TRUSTED,
    CLASS_UNKNOWN,
    EVENT_CHECKPOINT_PUSH,
    EVENT_PHASE_PR,
    EVENT_PROMOTION,
    EVENT_SEALED_FULL,
    PROFILE_FAST,
    PROFILE_FULL,
    PROFILE_NONE,
    PROFILE_PROMOTION,
    PROFILE_TRUSTED,
    ContractError,
    audit_workflow_triggers,
    authorize_omission,
    classify_changed_paths,
    compute_cache_key,
    default_contract,
    digest_json,
    digest_text,
    evaluate_aggregate_gate,
    evaluate_cache_advisory,
    expand_reverse_dependencies,
    innermost_diagnostic,
    installer_audit_repository_ci_triggers,
    load_contract,
    run_component_preflight,
    select_profile,
    validate_artifact_file,
    validate_contract,
    validate_coverage_manifest,
)

ROOT = Path(__file__).resolve().parents[2]
CONTRACT_PATH = ROOT / ".github" / "linktrend-repository-ci-contract.json"
SCHEMA_PATH = ROOT / "core" / "managed-core" / "schemas" / "repository-ci-contract.schema.json"
MANIFEST_SCHEMA = ROOT / "core" / "managed-core" / "schemas" / "ci-component-manifest.schema.json"
EVIDENCE_SCHEMA = ROOT / "core" / "managed-core" / "schemas" / "ci-evidence.schema.json"
MODULE = ROOT / "scripts" / "gitops" / "repository_ci_contract.py"


def _head(n: int = 1) -> str:
    return f"{n:040x}"


def _tree(n: int = 2) -> str:
    return f"{n:040x}"


class RepositoryCiTriggerContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.contract = load_contract(ROOT)
        self.assertEqual(self.contract["kind"], "repository-ci-contract")

    def test_packaged_schemas_and_repo_contract_exist(self) -> None:
        self.assertTrue(CONTRACT_PATH.is_file())
        self.assertTrue(SCHEMA_PATH.is_file())
        self.assertTrue(MANIFEST_SCHEMA.is_file())
        self.assertTrue(EVIDENCE_SCHEMA.is_file())
        self.assertTrue(MODULE.is_file())
        validate_contract(json.loads(CONTRACT_PATH.read_text(encoding="utf-8")))

    def test_checkpoint_push_consumes_no_managed_compute(self) -> None:
        decision = select_profile(
            event=EVENT_CHECKPOINT_PUSH,
            branch="issue/320-wp-u07-repository-owned-ci-trigger-contract",
            changed_paths=["src/app.ts"],
            contract=self.contract,
        )
        self.assertEqual(decision.profile, PROFILE_NONE)
        self.assertFalse(decision.startsManagedCompute)

    def test_phase_runs_fast_and_sealed_head_runs_full(self) -> None:
        fast = select_profile(
            event=EVENT_PHASE_PR,
            branch="phase/next-ide-development-v2.4.0",
            changed_paths=["src/app.ts"],
            contract=self.contract,
        )
        self.assertEqual(fast.profile, PROFILE_FAST)
        self.assertTrue(fast.startsManagedCompute)
        full = select_profile(
            event=EVENT_SEALED_FULL,
            branch="phase/next-ide-development-v2.4.0",
            changed_paths=["src/app.ts"],
            contract=self.contract,
        )
        self.assertEqual(full.profile, PROFILE_FULL)
        self.assertTrue(full.startsManagedCompute)

    def test_unchanged_promotion_receipt_only_and_changed_fails(self) -> None:
        ok = select_profile(
            event=EVENT_PROMOTION,
            branch="promote/staging/demo",
            changed_paths=[],
            contract=self.contract,
            promotion_tree_unchanged=True,
        )
        self.assertEqual(ok.profile, PROFILE_PROMOTION)
        self.assertFalse(ok.startsManagedCompute)
        with self.assertRaises(ContractError) as ctx:
            select_profile(
                event=EVENT_PROMOTION,
                branch="promote/main/demo",
                changed_paths=["x"],
                contract=self.contract,
                promotion_tree_unchanged=False,
            )
        self.assertEqual(ctx.exception.code, "promotion_content_changed")

    def test_repository_commands_preserved_in_contract_profiles(self) -> None:
        fast_cmds = self.contract["profiles"]["fast"]["commands"]
        self.assertTrue(fast_cmds)
        self.assertTrue(all(isinstance(cmd, list) and cmd for cmd in fast_cmds))

    def test_trusted_governance_vs_full_selection(self) -> None:
        trusted = select_profile(
            event=EVENT_SEALED_FULL,
            branch="issue/1-gov",
            changed_paths=[".github/workflows/ci.yml", "scripts/gitops/repository_ci_contract.py"],
            contract=self.contract,
        )
        self.assertEqual(trusted.profile, PROFILE_TRUSTED)
        mixed = select_profile(
            event=EVENT_SEALED_FULL,
            branch="issue/1-mixed",
            changed_paths=[".github/workflows/ci.yml", "apps/web/page.tsx"],
            contract=self.contract,
        )
        self.assertEqual(mixed.profile, PROFILE_FULL)
        self.assertEqual(mixed.classification, CLASS_MIXED)

    def test_aggregate_gate_trusted_and_fail_closed_cases(self) -> None:
        proofs = list(self.contract["trustedGovernance"]["requiredProofs"])
        ok = evaluate_aggregate_gate(
            contract=self.contract,
            selected_profile=PROFILE_TRUSTED,
            classification=CLASS_TRUSTED,
            governance_proofs=proofs,
        )
        self.assertTrue(ok.ok)
        self.assertFalse(ok.labeledAsFull)

        incomplete = evaluate_aggregate_gate(
            contract=self.contract,
            selected_profile=PROFILE_TRUSTED,
            classification=CLASS_TRUSTED,
            governance_proofs=proofs[:-1],
        )
        self.assertFalse(incomplete.ok)
        self.assertEqual(incomplete.code, "governance_profile_incomplete")

        forged = classify_changed_paths(["../escape/app.ts"], self.contract)
        self.assertEqual(forged["classification"], CLASS_UNKNOWN)

        mixed_as_trusted = evaluate_aggregate_gate(
            contract=self.contract,
            selected_profile=PROFILE_TRUSTED,
            classification=CLASS_MIXED,
            governance_proofs=proofs,
        )
        self.assertFalse(mixed_as_trusted.ok)

        raw = evaluate_aggregate_gate(
            contract=self.contract,
            selected_profile=PROFILE_FULL,
            classification=CLASS_APPLICATION,
            required_raw_full_context=True,
        )
        self.assertEqual(raw.code, "raw_full_context_forbidden")

    def test_full_requires_coverage_manifest_and_rejects_missing_component(self) -> None:
        head, tree = _head(11), _tree(22)
        receipt = {
            "conclusion": "success",
            "profile": PROFILE_FULL,
            "candidateHead": head,
            "candidateIdentity": {"headCommit": head, "gitTree": tree},
        }
        manifest = {
            "schemaVersion": 1,
            "kind": "ci-component-manifest",
            "candidateHead": head,
            "candidateTree": tree,
            "components": [
                {"id": "governance-gate-contract", "status": "passed"},
                {"id": "secret-scan", "status": "passed"},
                {"id": "application-tests", "status": "passed"},
                # production-resolution intentionally omitted without authorization
            ],
        }
        bad = evaluate_aggregate_gate(
            contract=self.contract,
            selected_profile=PROFILE_FULL,
            classification=CLASS_APPLICATION,
            application_receipt=receipt,
            coverage_manifest=manifest,
            candidate_head=head,
        )
        self.assertFalse(bad.ok)
        self.assertIn(bad.code, {"coverage_component_absent", "coverage_incomplete"})

        manifest["components"].append({"id": "production-resolution", "status": "passed"})
        good = evaluate_aggregate_gate(
            contract=self.contract,
            selected_profile=PROFILE_FULL,
            classification=CLASS_APPLICATION,
            application_receipt=receipt,
            coverage_manifest=manifest,
            candidate_head=head,
        )
        self.assertTrue(good.ok)
        self.assertTrue(good.labeledAsFull)

        stale = evaluate_aggregate_gate(
            contract=self.contract,
            selected_profile=PROFILE_FULL,
            classification=CLASS_APPLICATION,
            application_receipt=receipt,
            coverage_manifest=manifest,
            candidate_head=_head(99),
        )
        self.assertEqual(stale.code, "application_receipt_stale")

    def test_preflight_bindings_and_retention(self) -> None:
        component = {
            "id": "browser-e2e",
            "runtime": [
                {
                    "id": "chromium",
                    "kind": "browser",
                    "allowedVersions": ["120.0"],
                    "binding": {
                        "variable": "PLAYWRIGHT_BROWSER",
                        "executablePath": "/opt/browsers/chromium",
                    },
                }
            ],
        }
        missing = run_component_preflight(
            component=component,
            environ={},
            present_executables={},
            successful_component_ids=["unit-tests"],
        )
        self.assertFalse(missing["ok"])
        self.assertEqual(missing["classification"], "infrastructure")
        self.assertEqual(missing["retainedComponentIds"], ["unit-tests"])

        sibling_only = run_component_preflight(
            component=component,
            environ={"OTHER_BROWSER": "/opt/browsers/chromium"},
            present_executables={"chromium": "120.0"},
            successful_component_ids=["unit-tests"],
        )
        self.assertFalse(sibling_only["ok"])
        self.assertEqual(sibling_only["detail"], "binding_mismatch")
        self.assertFalse(sibling_only["bindings"][0]["matched"])

        ok = run_component_preflight(
            component=component,
            environ={"PLAYWRIGHT_BROWSER": "/opt/browsers/chromium"},
            present_executables={"chromium": "120.0"},
            successful_component_ids=["unit-tests"],
        )
        self.assertTrue(ok["ok"])

    def test_artifact_stdout_and_wrong_schema_head_fail(self) -> None:
        artifact = {
            "id": "coverage-json",
            "producer": "tests",
            "path": "build/coverage.json",
            "schemaVersion": 1,
            "consumer": "aggregate-gate",
            "stdoutCannotSatisfy": True,
        }
        stdout_only = validate_artifact_file(
            artifact=artifact,
            file_path=None,
            candidate_head=_head(1),
            stdout_json={"schemaVersion": 1, "candidateHead": _head(1)},
        )
        self.assertFalse(stdout_only["ok"])
        self.assertTrue(stdout_only["stdoutOnlyRejected"])

        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "coverage.json"
            path.write_text(
                json.dumps({"schemaVersion": 2, "candidateHead": _head(1)}),
                encoding="utf-8",
            )
            wrong_schema = validate_artifact_file(
                artifact=artifact,
                file_path=path,
                candidate_head=_head(1),
            )
            self.assertEqual(wrong_schema["code"], "artifact_wrong_schema")
            path.write_text(
                json.dumps({"schemaVersion": 1, "candidateHead": _head(2)}),
                encoding="utf-8",
            )
            wrong_head = validate_artifact_file(
                artifact=artifact,
                file_path=path,
                candidate_head=_head(1),
            )
            self.assertEqual(wrong_head["code"], "artifact_wrong_head")

    def test_innermost_diagnostic_retained(self) -> None:
        diag = innermost_diagnostic(
            [
                {"component": "recovery", "phase": "wrapper", "exit": 1, "message": "bash exited 1"},
                {
                    "component": "recovery",
                    "phase": "nested",
                    "exit": 17,
                    "message": "restore failed: volume missing",
                    "evidencePath": "build/recovery.err",
                    "stderrTail": "volume missing",
                },
            ]
        )
        self.assertEqual(diag["message"], "restore failed: volume missing")
        self.assertEqual(diag["evidencePath"], "build/recovery.err")

    def test_authorized_omission_and_fail_closed(self) -> None:
        good = authorize_omission(
            classifier_digest=digest_text("classifier"),
            inputs_digest=digest_json(["a.ts"]),
            authorized=True,
        )
        self.assertTrue(good["ok"])
        self.assertFalse(authorize_omission(classifier_digest=None, inputs_digest=None, authorized=True)["ok"])
        self.assertEqual(
            authorize_omission(
                classifier_digest=digest_text("x"),
                inputs_digest=digest_text("y"),
                authorized=True,
                forged=True,
            )["code"],
            "omission_forged",
        )
        self.assertEqual(
            authorize_omission(
                classifier_digest=digest_text("x"),
                inputs_digest=digest_text("y"),
                authorized=True,
                stale=True,
            )["code"],
            "omission_stale",
        )
        omitted = validate_coverage_manifest(
            self.contract,
            {
                "schemaVersion": 1,
                "kind": "ci-component-manifest",
                "candidateHead": _head(3),
                "candidateTree": _tree(4),
                "components": [
                    {"id": "governance-gate-contract", "status": "passed"},
                    {"id": "secret-scan", "status": "passed"},
                    {"id": "application-tests", "status": "passed"},
                    {
                        "id": "production-resolution",
                        "status": "omitted",
                        "omission": good["omission"],
                    },
                ],
            },
            candidate_head=_head(3),
            candidate_tree=_tree(4),
        )
        self.assertTrue(omitted["ok"])

    def test_monorepo_reverse_dependency_requires_production_probes(self) -> None:
        result = expand_reverse_dependencies(
            changed_paths=["packages/ui/src/index.ts", "packages/ui/package.json"],
            dependency_graph={"packages/ui": ["apps/web", "apps/admin"]},
            package_export_paths=["packages/ui/src/index.ts"],
        )
        self.assertEqual(result["reverseDependencies"], ["apps/admin", "apps/web"])
        self.assertIn("production-resolution", result["requiredProbes"])
        self.assertIn("docker-import-build", result["requiredProbes"])
        self.assertTrue(result["typecheckInsufficient"])
        self.assertNotIn("typecheck", result["requiredProbes"])

    def test_cache_key_fixed_before_mutation_and_advisory(self) -> None:
        key = compute_cache_key(
            candidate_head=_head(5),
            tracked_manifest_digest=digest_text("tracked"),
            lockfile_digest=digest_text("lock"),
            workspace_mutated=False,
        )
        self.assertTrue(key["keyFixedBeforeMutation"])
        self.assertTrue(key["advisory"])
        with self.assertRaises(ContractError):
            compute_cache_key(
                candidate_head=_head(5),
                tracked_manifest_digest=digest_text("tracked"),
                lockfile_digest=digest_text("lock"),
                workspace_mutated=True,
            )
        advisory = evaluate_cache_advisory(
            cache_key=key["cacheKey"],
            restore_status="error",
            save_status="error",
            required_profile_ok=True,
            required_component_failed=False,
        )
        self.assertTrue(advisory["correctnessUnchanged"])
        self.assertTrue(advisory["ok"])
        self.assertIn("cache_restore_failed", advisory["warnings"])

        still_blocks = evaluate_cache_advisory(
            cache_key=key["cacheKey"],
            restore_status="hit",
            save_status="saved",
            required_profile_ok=False,
            required_component_failed=True,
        )
        self.assertFalse(still_blocks["ok"])

        broad = evaluate_cache_advisory(
            cache_key=key["cacheKey"],
            restore_status="miss",
            save_status="skipped",
            required_profile_ok=True,
            required_component_failed=False,
            broad_post_job_hash=True,
        )
        self.assertTrue(broad["rejectedBroadHash"])
        self.assertFalse(broad["ok"])

    def test_installer_audit_detects_broad_expensive_triggers(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            wf = root / ".github" / "workflows"
            wf.mkdir(parents=True)
            (wf / "expensive.yml").write_text(
                "\n".join(
                    [
                        "name: Full matrix",
                        "on:",
                        "  pull_request:",
                        "  push:",
                        "jobs:",
                        "  build-and-test:",
                        "    runs-on: ubuntu-latest",
                        "    steps:",
                        "      - run: echo e2e browser matrix",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )
            (wf / "promotion-safe.yml").write_text(
                "\n".join(
                    [
                        "name: Receipt gate",
                        "on:",
                        "  pull_request:",
                        "    branches: ['promote/staging/**']",
                        "jobs:",
                        "  verify:",
                        "    runs-on: ubuntu-latest",
                        "    steps:",
                        "      - run: echo ok",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )
            (root / ".github" / "linktrend-repository-ci-contract.json").write_text(
                json.dumps(default_contract()),
                encoding="utf-8",
            )
            result = installer_audit_repository_ci_triggers(root)
            self.assertFalse(result["ok"])
            self.assertEqual(result["scanned"], 2)
            self.assertEqual(result["conflicts"][0]["code"], "promotion_expensive_retrigger")
            self.assertFalse(result["mayModify"])
            with self.assertRaises(ContractError):
                installer_audit_repository_ci_triggers(root, mutate=True, rollout_scope=False)

    def test_audit_live_ide_development_workflows_report(self) -> None:
        # Factory CI currently has a broad trigger; audit must detect it without mutating.
        result = audit_workflow_triggers(ROOT / ".github" / "workflows", contract=self.contract)
        self.assertIn("scanned", result)
        self.assertGreaterEqual(result["scanned"], 1)
        self.assertFalse(result.get("mayModify", True))


if __name__ == "__main__":
    unittest.main()
