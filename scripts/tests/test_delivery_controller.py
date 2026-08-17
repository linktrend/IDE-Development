"""WP-U02 delivery controller unit, negative, and contract tests."""

from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from scripts.gitops import delivery_controller as controller
from scripts.gitops import packager_discover as discover
from scripts.gitops.coordinator import receipts
from scripts.ide_development.constants import RC_REQUIRED_SCHEMA_RELS


ROOT = Path(__file__).resolve().parents[2]
DIGEST = "sha256:" + ("b" * 64)
COMMAND_DIGEST = "sha256:" + ("c" * 64)
DEP_DIGEST = "sha256:" + ("d" * 64)
PROFILE_DIGEST = "sha256:" + ("e" * 64)
WORKFLOW_DIGEST = "sha256:" + ("f" * 64)


def _sha(n: int = 1) -> str:
    return f"{n:040x}"


def _identity(*, head: str, tree: str, repository: str = "owner/name", branch: str = "phase/next") -> dict[str, str]:
    return {
        "repository": repository,
        "sourceBranch": branch,
        "headCommit": head,
        "gitTree": tree,
        "dependencyDigest": DEP_DIGEST,
        "profileDigest": PROFILE_DIGEST,
        "workflowDigest": WORKFLOW_DIGEST,
    }


def _receipt(identity: dict[str, str]) -> dict[str, object]:
    raw = {
        "schemaVersion": 2,
        "candidateIdentity": identity,
        "workflowRunId": 501,
        "workflowRunAttempt": 1,
        "runnerLabel": "ubuntu-24.04-arm",
        "startedAt": "2026-08-18T01:00:00Z",
        "completedAt": "2026-08-18T01:01:00Z",
        "conclusion": "success",
        "commandDigest": COMMAND_DIGEST,
        "evidenceDigests": {"evidence/full.log": DIGEST},
    }
    return receipts.create_full_suite_receipt(raw).to_dict()


def _handoff(*, head: str, tree: str, base: str | None = None) -> dict[str, object]:
    return {
        "schemaVersion": 1,
        "kind": "phase-handoff",
        "repository": "owner/name",
        "phaseBranch": "phase/next",
        "phasePr": {"number": 11, "url": "https://github.com/owner/name/pull/11", "isDraft": True},
        "headCommit": head,
        "gitTree": tree,
        "baseCommit": base or _sha(9),
        "candidateRevision": "rev-1",
        "acceptedCommits": [{"branch": "issue/1-alpha", "sha": head, "order": 1}],
        "evidenceLocations": {
            "phaseRecord": ".linktrend/phase-delivery-record.json",
            "handoff": ".linktrend/phase-handoff.json",
        },
        "valid": True,
        "component": "phase_packager_coordinator",
    }


def _named_checks(head: str) -> dict[str, dict[str, str]]:
    return {
        name: {"status": "success", "sha": head}
        for name in controller.REQUIRED_CHECK_NAMES
    }


def _gates(head: str) -> dict[str, dict[str, str]]:
    return {
        "seal": {"status": "passed", "sha": head},
        "fast": {"status": "passed", "sha": head},
        "bugbot": {"status": "passed", "sha": head},
        "full": {"status": "passed", "sha": head},
    }


class DeliveryControllerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.head = _sha(1)
        self.tree = _sha(2)
        self.identity = _identity(head=self.head, tree=self.tree)
        self.receipt = _receipt(self.identity)
        self.handoff = _handoff(head=self.head, tree=self.tree)
        self.pr = {
            "number": 11,
            "isDraft": False,
            "state": "open",
            "head": "phase/next",
            "base": "development",
            "headSha": self.head,
            "mergeableState": "MERGEABLE",
        }
        self.github = controller.MemoryGitHub(repository="owner/name")
        self.github.prs[11] = dict(self.pr)
        self.github.refs["development"] = _sha(8)
        self.github.refs["staging"] = _sha(7)
        self.github.refs["main"] = _sha(6)

    def test_component_replaces_nonexistent_integrator_handoff(self) -> None:
        self.assertTrue(controller.IS_DELIVERY_CONTROLLER)
        self.assertEqual(controller.COMPONENT_KIND, "delivery_controller")
        self.assertIn("Replaces the nonexistent Integrator", controller.__doc__)
        self.assertFalse(getattr(discover, "IS_DELIVERY_CONTROLLER", False))

    def test_valid_phase_pr_reaches_development_without_external_integrator(self) -> None:
        result = controller.deliver_phase_to_development(
            github=self.github,
            repository="owner/name",
            handoff=self.handoff,
            pr=self.pr,
            live_head=self.head,
            live_tree=self.tree,
            gate_payload=_gates(self.head),
            named_checks=_named_checks(self.head),
            receipt=self.receipt,
            candidate_identity=self.identity,
            role="operator",
        )
        self.assertEqual(result["status"], "merged")
        self.assertEqual(result["stage"], "development")
        self.assertFalse(result["directPush"])
        self.assertEqual(result["component"], "delivery_controller")
        self.assertEqual(len(self.github.merges), 1)
        self.assertEqual(self.github.protected_push_attempts[0]["branch"], "development")

    def test_worker_cannot_invoke_self_merge_path(self) -> None:
        with self.assertRaisesRegex(controller.ControllerError, "worker_self_merge_forbidden"):
            controller.merge_to_development(
                github=self.github,
                repository="owner/name",
                pr_number=11,
                expected_head=self.head,
                role="worker",
            )
        with self.assertRaisesRegex(controller.ControllerError, "worker_self_merge_forbidden"):
            controller.require_controller_role("implementer")

    def test_stale_or_changed_pr_is_rejected(self) -> None:
        with self.assertRaisesRegex(controller.ControllerError, "stale_pr_head"):
            controller.accept_phase_pr(
                {**self.pr, "headSha": _sha(99)},
                self.handoff,
                repository="owner/name",
                live_head=self.head,
                live_tree=self.tree,
            )
        stale_handoff = dict(self.handoff, headCommit=_sha(3), valid=True)
        with self.assertRaisesRegex(controller.ControllerError, "handoff_stale_head"):
            controller.accept_phase_pr(
                self.pr,
                stale_handoff,
                repository="owner/name",
                live_head=self.head,
                live_tree=self.tree,
            )

    def test_failed_missing_or_skipped_gates_are_rejected(self) -> None:
        missing = dict(_named_checks(self.head))
        del missing["Linktrend Review Gate"]
        with self.assertRaisesRegex(controller.ControllerError, "required_gate_missing"):
            controller.verify_development_eligibility(
                handoff=self.handoff,
                pr=self.pr,
                repository="owner/name",
                live_head=self.head,
                live_tree=self.tree,
                gate_payload=_gates(self.head),
                named_checks=missing,
                receipt=self.receipt,
                candidate_identity=self.identity,
            )
        skipped = dict(_named_checks(self.head))
        skipped["Linktrend Fast Checks"] = {"status": "skipped", "sha": self.head}
        with self.assertRaisesRegex(controller.ControllerError, "required_gate_skipped"):
            controller.verify_development_eligibility(
                handoff=self.handoff,
                pr=self.pr,
                repository="owner/name",
                live_head=self.head,
                live_tree=self.tree,
                gate_payload=_gates(self.head),
                named_checks=skipped,
                receipt=self.receipt,
                candidate_identity=self.identity,
            )
        failed_gates = dict(_gates(self.head), fast={"status": "failed", "sha": self.head})
        with self.assertRaisesRegex(controller.ControllerError, "fast_not_passed"):
            controller.verify_development_eligibility(
                handoff=self.handoff,
                pr=self.pr,
                repository="owner/name",
                live_head=self.head,
                live_tree=self.tree,
                gate_payload=failed_gates,
                named_checks=_named_checks(self.head),
                receipt=self.receipt,
                candidate_identity=self.identity,
            )

    def test_receipt_mismatch_or_forgery_is_rejected(self) -> None:
        forged = dict(self.receipt, receiptDigest="sha256:" + ("a" * 64))
        with self.assertRaisesRegex(controller.ControllerError, "receipt_rejected"):
            controller.verify_development_eligibility(
                handoff=self.handoff,
                pr=self.pr,
                repository="owner/name",
                live_head=self.head,
                live_tree=self.tree,
                gate_payload=_gates(self.head),
                named_checks=_named_checks(self.head),
                receipt=forged,
                candidate_identity=self.identity,
            )

    def test_staging_reuses_exact_receipt_without_full_rerun(self) -> None:
        result = controller.promote_to_staging(
            github=self.github,
            repository="owner/name",
            development_sha=self.head,
            staging_sha=_sha(7),
            candidate_sha=self.head,
            candidate_tree=self.tree,
            receipt=self.receipt,
            candidate_identity=self.identity,
            release_gate={"status": "passed", "testProfile": "release", "fullSuiteInvoked": False},
            role="operator",
        )
        self.assertEqual(result["status"], "merged")
        self.assertEqual(result["stage"], "staging")
        self.assertTrue(result["receiptReused"])
        self.assertFalse(result["fullSuiteRerun"])
        with self.assertRaisesRegex(controller.ControllerError, "full_suite_reentered"):
            controller.promote_to_staging(
                github=self.github,
                repository="owner/name",
                development_sha=self.head,
                staging_sha=_sha(7),
                candidate_sha=self.head,
                candidate_tree=self.tree,
                receipt=self.receipt,
                candidate_identity=self.identity,
                release_gate={"status": "passed", "testProfile": "release"},
                role="operator",
                full_suite_invoked=True,
            )

    def test_changed_staging_content_is_rejected(self) -> None:
        with self.assertRaisesRegex(controller.ControllerError, "changed_staging_content"):
            controller.promote_to_staging(
                github=self.github,
                repository="owner/name",
                development_sha=self.head,
                staging_sha=_sha(7),
                candidate_sha=self.head,
                candidate_tree=_sha(99),
                receipt=self.receipt,
                candidate_identity=self.identity,
                release_gate={"status": "passed", "testProfile": "release"},
                role="operator",
            )

    def test_main_waits_for_explicit_founder_approval(self) -> None:
        prepared = controller.prepare_main_promotion(
            github=self.github,
            repository="owner/name",
            staging_sha=self.head,
            main_sha=_sha(6),
            candidate_sha=self.head,
            receipt=self.receipt,
            candidate_identity=self.identity,
            release_gate={"status": "passed", "testProfile": "release"},
            role="operator",
        )
        self.assertEqual(prepared["status"], "waiting_founder_approval")
        self.assertFalse(prepared["founderApprovalInferred"])
        with self.assertRaisesRegex(controller.ControllerError, "founder_approval_missing"):
            controller.complete_main_promotion(
                github=self.github,
                repository="owner/name",
                pr_number=int(prepared["pr"]),
                expected_head=self.head,
                source_sha=self.head,
                base_sha=_sha(6),
                approval={},
                receipt=self.receipt,
                role="operator",
            )

    def test_ambiguous_or_stale_main_approval_is_rejected(self) -> None:
        prepared = controller.prepare_main_promotion(
            github=self.github,
            repository="owner/name",
            staging_sha=self.head,
            main_sha=_sha(6),
            candidate_sha=self.head,
            receipt=self.receipt,
            candidate_identity=self.identity,
            release_gate={"status": "passed", "testProfile": "release"},
            role="operator",
        )
        with self.assertRaisesRegex(controller.ControllerError, "founder_approval_ambiguous"):
            controller.complete_main_promotion(
                github=self.github,
                repository="owner/name",
                pr_number=int(prepared["pr"]),
                expected_head=self.head,
                source_sha=self.head,
                base_sha=_sha(6),
                approval={
                    "decision": "approve",
                    "inferredFromGreenCi": True,
                    "sourceSha": self.head,
                    "baseSha": _sha(6),
                    "prHeadSha": self.head,
                    "receiptDigest": receipts.compute_receipt_digest(self.receipt),
                },
                receipt=self.receipt,
                role="operator",
            )
        with self.assertRaisesRegex(controller.ControllerError, "stale_"):
            controller.complete_main_promotion(
                github=self.github,
                repository="owner/name",
                pr_number=int(prepared["pr"]),
                expected_head=self.head,
                source_sha=self.head,
                base_sha=_sha(6),
                approval={
                    "decision": "approve",
                    "sourceSha": _sha(55),
                    "baseSha": _sha(6),
                    "prHeadSha": self.head,
                    "receiptDigest": receipts.compute_receipt_digest(self.receipt),
                },
                receipt=self.receipt,
                role="operator",
            )

    def test_protected_merge_rejection_stops_without_direct_push(self) -> None:
        self.github.merge_rejections[11] = "branch protection prevented merge"
        stopped = controller.deliver_phase_to_development(
            github=self.github,
            repository="owner/name",
            handoff=self.handoff,
            pr=self.pr,
            live_head=self.head,
            live_tree=self.tree,
            gate_payload=_gates(self.head),
            named_checks=_named_checks(self.head),
            receipt=self.receipt,
            candidate_identity=self.identity,
            role="operator",
        )
        self.assertEqual(stopped["status"], "stopped")
        self.assertEqual(stopped["code"], "protected_merge_rejected")
        self.assertFalse(stopped["directPushAttempted"])
        self.assertFalse(stopped["bypassAttempted"])

    def test_temporary_branches_deleted_only_after_successful_merges(self) -> None:
        with self.assertRaisesRegex(controller.ControllerError, "cleanup_before_success"):
            controller.cleanup_temporary_branches(
                github=self.github,
                repository="owner/name",
                branches=["promote/staging/aaaaaaaaaaaa"],
                merge_succeeded=False,
                controller_owned={"promote/staging/aaaaaaaaaaaa": True},
            )
        self.github.refs["promote/staging/aaaaaaaaaaaa"] = self.head
        self.github.refs["issue/1-unique"] = self.head
        cleaned = controller.cleanup_temporary_branches(
            github=self.github,
            repository="owner/name",
            branches=["promote/staging/aaaaaaaaaaaa", "issue/1-unique"],
            merge_succeeded=True,
            controller_owned={"promote/staging/aaaaaaaaaaaa": True},
        )
        self.assertEqual(cleaned["deleted"], ["promote/staging/aaaaaaaaaaaa"])
        self.assertEqual(cleaned["preserved"], ["issue/1-unique"])

    def test_controller_identical_across_supported_agents(self) -> None:
        result = controller.run_identical_under_agents(
            "merge-development",
            {"head": self.head, "tree": self.tree},
            [
                {},
                {"CURSOR_AGENT": "cursor"},
                {"CODEX_HOME": "/tmp/codex"},
                {"TERRA_AGENT": "terra"},
            ],
        )
        self.assertEqual(result["status"], "identical")
        self.assertEqual(len({row["payloadDigest"] for row in result["results"]}), 1)

    def test_draft_cross_repo_and_conflict_rejected(self) -> None:
        with self.assertRaisesRegex(controller.ControllerError, "draft_pr"):
            controller.accept_phase_pr(
                {**self.pr, "isDraft": True},
                self.handoff,
                repository="owner/name",
                live_head=self.head,
                live_tree=self.tree,
            )
        with self.assertRaisesRegex(controller.ControllerError, "cross_repository"):
            controller.accept_phase_pr(
                {**self.pr, "crossRepository": True},
                self.handoff,
                repository="owner/name",
                live_head=self.head,
                live_tree=self.tree,
            )
        with self.assertRaisesRegex(controller.ControllerError, "merge_conflict"):
            controller.verify_development_eligibility(
                handoff=self.handoff,
                pr=self.pr,
                repository="owner/name",
                live_head=self.head,
                live_tree=self.tree,
                gate_payload=_gates(self.head),
                named_checks=_named_checks(self.head),
                receipt=self.receipt,
                candidate_identity=self.identity,
                conflict=True,
            )

    def test_complete_main_success_path(self) -> None:
        prepared = controller.prepare_main_promotion(
            github=self.github,
            repository="owner/name",
            staging_sha=self.head,
            main_sha=_sha(6),
            candidate_sha=self.head,
            receipt=self.receipt,
            candidate_identity=self.identity,
            release_gate={"status": "passed", "testProfile": "release"},
            role="founder",
        )
        completed = controller.complete_main_promotion(
            github=self.github,
            repository="owner/name",
            pr_number=int(prepared["pr"]),
            expected_head=self.head,
            source_sha=self.head,
            base_sha=_sha(6),
            approval={
                "decision": "approve",
                "sourceSha": self.head,
                "baseSha": _sha(6),
                "prHeadSha": self.head,
                "receiptDigest": receipts.compute_receipt_digest(self.receipt),
            },
            receipt=self.receipt,
            role="founder",
        )
        self.assertEqual(completed["status"], "merged")
        self.assertTrue(completed["founderApproval"])

    def test_index_manifest_schema_and_hosted_fast_cover_controller(self) -> None:
        index = (ROOT / "core/managed-core/INDEX.yaml").read_text(encoding="utf-8")
        self.assertIn("schemas/delivery-operation.schema.json", index)
        self.assertIn("core/managed-core/schemas/delivery-operation.schema.json", RC_REQUIRED_SCHEMA_RELS)
        manifest = json.loads((ROOT / "core/managed-core/MANIFEST.json").read_text(encoding="utf-8"))
        sources = {row["source"] for row in manifest["files"]}
        self.assertIn("core/managed-core/schemas/delivery-operation.schema.json", sources)
        self.assertIn("scripts/gitops/delivery_controller.py", sources)
        self.assertIn("scripts/tests/test_delivery_controller.py", sources)
        runtime = json.loads((ROOT / "core/github/managed-runtime/MANIFEST.json").read_text(encoding="utf-8"))
        self.assertIn("scripts/gitops/delivery_controller.py", runtime["files"])
        fast = json.loads((ROOT / ".github/linktrend-delivery-mode.json").read_text(encoding="utf-8"))
        blob = json.dumps(fast["profiles"]["fast"]["commands"])
        self.assertIn("delivery_controller.py", blob)
        self.assertIn("test_delivery_controller", blob)
        doctrine = (ROOT / "docs/AUTONOMOUS-GIT-OPERATIONS.md").read_text(encoding="utf-8")
        self.assertIn("delivery controller", doctrine.lower())
        self.assertNotIn("waits indefinitely for an undefined merge actor", doctrine.lower())
        agents = (ROOT / "core/managed-core/platforms/codex/AGENTS.managed-section.md").read_text(encoding="utf-8")
        self.assertIn("delivery controller", agents.lower())
        self.assertNotIn("Integrator merges to `development`", agents)
        bootstrap = (ROOT / "core/managed-core/platforms/cursor/rules/cursor-gitops-bootstrap.mdc").read_text(
            encoding="utf-8"
        )
        self.assertIn("delivery controller", bootstrap.lower())
        self.assertNotIn("Integrator merges only when", bootstrap)
        schema = json.loads(
            (ROOT / "core/managed-core/schemas/delivery-operation.schema.json").read_text(encoding="utf-8")
        )
        record = controller.write_operation_record(
            Path(tempfile.mkdtemp()) / "delivery-operation.json",
            {
                "status": "merged",
                "stage": "development",
                "pr": 11,
                "testedHead": self.head,
                "mergeCommitSha": _sha(3),
                "directPush": False,
            },
        )
        for key in schema["required"]:
            self.assertIn(key, record)


if __name__ == "__main__":
    unittest.main()
