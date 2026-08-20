"""Coding Execution Protocol 1.0.1 packet tests. None of these tests may skip."""

from __future__ import annotations

import json
import sys
import unittest
from copy import deepcopy
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.execution.protocol import (  # noqa: E402
    AMENDMENT_ID,
    CANONICAL_PUBLISHER,
    LEGACY_PUBLISHERS,
    PROTOCOL_ID,
    PROTOCOL_VERSION,
    WAIVED_LEGACY_GATE,
    DurableHeartbeatStore,
    acquire_orchestration_lease,
    administrator_recovery,
    admit_resources,
    autowork_discovery_decision,
    candidate_identity,
    classify_legacy_publisher_gate,
    diagnose_retry_exhaustion,
    discover_runtime,
    evaluate_exhaustion_recovery,
    evaluate_heartbeat_gate,
    evaluate_issue_checkpoint,
    evaluate_verification_receipt,
    git_authority_allows,
    invalidate_candidate,
    load_execution_schema,
    persist_heartbeat,
    protocol_document_version,
    publisher_is_canonical,
    required_approval,
    retry_decision,
    schedule_hosted_capacity,
    validate_execution_manifest,
    validate_lease,
)


COMMIT_A = "004bd5faa1e14ee100a018e16dcb049f0fb2d8eb"
TREE_A = "6c55220132cc7e9a1baef06f8c147ee9ac9431e7"
COMMIT_B = "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
TREE_B = "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb"


def example_manifest() -> dict:
    path = ROOT / "core/execution/examples/execution-manifest.example.json"
    return json.loads(path.read_text(encoding="utf-8"))


class DiscoveryTests(unittest.TestCase):
    def test_runtime_discovers_protocol_1_0_1_surfaces(self) -> None:
        discovered = discover_runtime(ROOT)
        self.assertEqual(discovered.protocol_id, PROTOCOL_ID)
        self.assertEqual(discovered.protocol_version, "1.0.1")
        self.assertTrue(discovered.protocol_document.is_file())
        self.assertTrue(discovered.control_contract.is_file())
        self.assertTrue(discovered.schema_path.is_file())
        self.assertTrue(discovered.doctrine_path.is_file())
        self.assertTrue(discovered.hosted_capacity_doctrine.is_file())
        self.assertTrue(discovered.continuous_utilization_config.is_file())
        self.assertTrue(discovered.continuous_utilization_schema.is_file())
        self.assertTrue(discovered.continuous_utilization_example.is_file())
        self.assertIsNotNone(discovered.example_manifest)

    def test_protocol_and_doctrine_share_version_1_0_1(self) -> None:
        discovered = discover_runtime(ROOT)
        protocol_text = discovered.protocol_document.read_text(encoding="utf-8")
        doctrine_text = discovered.doctrine_path.read_text(encoding="utf-8")
        self.assertEqual(protocol_document_version(protocol_text), "1.0.1")
        self.assertEqual(protocol_document_version(doctrine_text), "1.0.1")
        self.assertIn("V25_BOOTSTRAP_LEAN", protocol_text)
        self.assertEqual(protocol_text, doctrine_text)

    def test_missing_surface_fails_closed(self) -> None:
        with self.assertRaises(FileNotFoundError):
            discover_runtime(Path("/tmp"))


class ManifestSchemaTests(unittest.TestCase):
    def test_example_manifest_is_schema_valid(self) -> None:
        result = validate_execution_manifest(example_manifest(), repo_root=ROOT)
        self.assertTrue(result.ok)
        self.assertFalse(result.skipped)
        self.assertEqual(result.errors, ())

    def test_unknown_top_level_field_is_rejected(self) -> None:
        document = example_manifest()
        document["secretToken"] = "nope"
        result = validate_execution_manifest(document, repo_root=ROOT)
        self.assertFalse(result.ok)
        self.assertTrue(result.errors)

    def test_wrong_protocol_version_is_rejected(self) -> None:
        document = example_manifest()
        document["protocol"]["version"] = "1.0.0"
        result = validate_execution_manifest(document, repo_root=ROOT)
        self.assertFalse(result.ok)

    def test_short_commit_is_rejected(self) -> None:
        document = example_manifest()
        document["baseline"]["commit"] = "abc"
        result = validate_execution_manifest(document, repo_root=ROOT)
        self.assertFalse(result.ok)

    def test_schema_loader_matches_discovery(self) -> None:
        schema = load_execution_schema(ROOT)
        self.assertEqual(schema["properties"]["protocol"]["properties"]["version"]["const"], "1.0.1")
        self.assertEqual(
            schema["properties"]["protocol"]["properties"]["amendment"]["const"],
            "V25_BOOTSTRAP_LEAN",
        )

    def test_missing_amendment_is_rejected(self) -> None:
        document = example_manifest()
        del document["protocol"]["amendment"]
        result = validate_execution_manifest(document, repo_root=ROOT)
        self.assertFalse(result.ok)


class ExactCandidateTests(unittest.TestCase):
    def test_identical_identity_is_not_invalidated(self) -> None:
        previous = candidate_identity(
            repository="linktrend/IDE-Development",
            commit=COMMIT_A,
            tree=TREE_A,
        )
        current = deepcopy(previous)
        result = invalidate_candidate(previous, current)
        self.assertFalse(result.invalidated)

    def test_new_commit_or_tree_invalidates(self) -> None:
        previous = candidate_identity(
            repository="linktrend/IDE-Development",
            commit=COMMIT_A,
            tree=TREE_A,
        )
        changed_commit = candidate_identity(
            repository="linktrend/IDE-Development",
            commit=COMMIT_B,
            tree=TREE_A,
        )
        changed_tree = candidate_identity(
            repository="linktrend/IDE-Development",
            commit=COMMIT_A,
            tree=TREE_B,
        )
        self.assertTrue(invalidate_candidate(previous, changed_commit).invalidated)
        self.assertEqual(
            invalidate_candidate(previous, changed_commit).reason,
            "exact_candidate_changed",
        )
        self.assertTrue(invalidate_candidate(previous, changed_tree).invalidated)

    def test_digest_change_invalidates_when_bound(self) -> None:
        previous = candidate_identity(
            repository="linktrend/IDE-Development",
            commit=COMMIT_A,
            tree=TREE_A,
            workflow_digest="sha256:aa",
            profile_digest="sha256:bb",
        )
        changed = candidate_identity(
            repository="linktrend/IDE-Development",
            commit=COMMIT_A,
            tree=TREE_A,
            workflow_digest="sha256:cc",
            profile_digest="sha256:bb",
        )
        result = invalidate_candidate(previous, changed)
        self.assertTrue(result.invalidated)
        self.assertEqual(result.reason, "workflow_digest_changed")


class BoundedRetryTests(unittest.TestCase):
    def test_ordinary_source_allows_three_then_stops(self) -> None:
        self.assertTrue(retry_decision("ordinary_source", 3).retry)
        fourth = retry_decision("ordinary_source", 4)
        self.assertFalse(fourth.retry)
        self.assertTrue(fourth.stop)
        self.assertEqual(fourth.reason, "ordinary_source_exhausted")

    def test_infrastructure_retries_once_then_stops(self) -> None:
        first = retry_decision("infrastructure", 1)
        self.assertTrue(first.retry)
        second = retry_decision("infrastructure", 2)
        self.assertFalse(second.retry)
        self.assertTrue(second.stop)
        self.assertEqual(second.reason, "infrastructure_stopped")

    def test_code_failure_never_retries(self) -> None:
        decision = retry_decision("code_failure", 1)
        self.assertFalse(decision.retry)
        self.assertTrue(decision.stop)
        self.assertEqual(decision.reason, "code_failure_no_retry")


class OrchestrationLeaseTests(unittest.TestCase):
    def test_exclusive_live_lease_blocks_other_holder(self) -> None:
        now = datetime(2026, 8, 20, tzinfo=timezone.utc)
        existing = acquire_orchestration_lease(
            holder="agent-a",
            packet_id="PKT-01",
            repository="linktrend/IDE-Development",
            nonce="n1",
            expires_at=now + timedelta(hours=1),
            now=now,
        )
        with self.assertRaises(PermissionError):
            acquire_orchestration_lease(
                holder="agent-b",
                packet_id="PKT-01",
                repository="linktrend/IDE-Development",
                nonce="n2",
                expires_at=now + timedelta(hours=1),
                existing=existing,
                now=now,
            )

    def test_expired_lease_cannot_mutate(self) -> None:
        now = datetime(2026, 8, 20, tzinfo=timezone.utc)
        lease = acquire_orchestration_lease(
            holder="agent-a",
            packet_id="PKT-01",
            repository="linktrend/IDE-Development",
            nonce="n1",
            expires_at=now,
            now=now,
        )
        self.assertFalse(
            validate_lease(
                lease,
                holder="agent-a",
                packet_id="PKT-01",
                repository="linktrend/IDE-Development",
                now=now,
            )
        )

    def test_matching_live_lease_authorizes_holder(self) -> None:
        now = datetime(2026, 8, 20, tzinfo=timezone.utc)
        lease = acquire_orchestration_lease(
            holder="agent-a",
            packet_id="PKT-01",
            repository="linktrend/IDE-Development",
            nonce="n1",
            expires_at=now + timedelta(minutes=5),
            now=now,
        )
        self.assertTrue(
            validate_lease(
                lease,
                holder="agent-a",
                packet_id="PKT-01",
                repository="linktrend/IDE-Development",
                now=now,
            )
        )


class ResourceUncertaintyTests(unittest.TestCase):
    def test_missing_snapshot_is_uncertain_and_not_admitted(self) -> None:
        verdict = admit_resources(None)
        self.assertFalse(verdict.admitted)
        self.assertTrue(verdict.uncertain)
        self.assertEqual(verdict.reason, "resource_uncertain")

    def test_unknown_field_is_blocking(self) -> None:
        verdict = admit_resources(
            {
                "cpu_percent": 10,
                "memory_percent": 10,
                "free_disk_gib": None,
                "docker_available": True,
            }
        )
        self.assertFalse(verdict.admitted)
        self.assertTrue(verdict.uncertain)

    def test_complete_snapshot_admits(self) -> None:
        verdict = admit_resources(
            {
                "cpu_percent": 10,
                "memory_percent": 10,
                "free_disk_gib": 40,
                "docker_available": True,
            }
        )
        self.assertTrue(verdict.admitted)
        self.assertFalse(verdict.uncertain)


class AutomaticApprovalTests(unittest.TestCase):
    def test_checkpoint_is_automatic(self) -> None:
        decision = required_approval("checkpoint")
        self.assertTrue(decision.allowed)
        self.assertTrue(decision.automatic)
        self.assertFalse(decision.founder_required)

    def test_main_promote_requires_recorded_founder(self) -> None:
        blocked = required_approval("main_promote")
        self.assertFalse(blocked.allowed)
        self.assertTrue(blocked.founder_required)
        allowed = required_approval(
            "main_promote",
            recorded_approvals={"main_promote": "founder"},
        )
        self.assertTrue(allowed.allowed)

    def test_self_review_and_self_merge_are_forbidden(self) -> None:
        self.assertFalse(required_approval("self_review").allowed)
        self.assertFalse(required_approval("self_merge").allowed)
        self.assertFalse(required_approval("prefer_incoming").allowed)


class GitAuthorityTests(unittest.TestCase):
    def test_implementer_may_push_issue_branch_only(self) -> None:
        self.assertTrue(
            git_authority_allows(
                "push_work_branch",
                branch="issue/341-pkt-01-iss-01-canonical-coding-execution-protoco",
                actor="implementer",
            )
        )
        self.assertFalse(
            git_authority_allows(
                "push_work_branch",
                branch="development",
                actor="implementer",
            )
        )

    def test_implementer_cannot_open_or_merge(self) -> None:
        self.assertFalse(git_authority_allows("open_pr", branch="issue/1-x", actor="implementer"))
        self.assertTrue(git_authority_allows("open_pr", branch="issue/1-x", actor="packager"))
        self.assertTrue(
            git_authority_allows(
                "merge_to_development",
                branch="phase/v25",
                actor="delivery_controller",
            )
        )
        self.assertFalse(
            git_authority_allows("nested_self_install", branch="issue/1-x", actor="implementer")
        )


class PublisherAuthorityTests(unittest.TestCase):
    def test_no_singular_legacy_publisher_is_canonical_for_v25(self) -> None:
        self.assertIsNone(CANONICAL_PUBLISHER)
        self.assertEqual(AMENDMENT_ID, "V25_BOOTSTRAP_LEAN")
        self.assertIn("linktrend-review-ready-publisher", LEGACY_PUBLISHERS)
        for name in LEGACY_PUBLISHERS:
            self.assertFalse(publisher_is_canonical(name))
        doctrine = (
            ROOT / "core/managed-core/content/doctrine/0003-autonomous-ship-pull-promote.md"
        ).read_text(encoding="utf-8")
        self.assertIn("V25_BOOTSTRAP_LEAN", doctrine)
        self.assertIn("WAIVED_LEGACY_GATE", doctrine)

    def test_failed_or_missing_legacy_publisher_is_waived_not_pass(self) -> None:
        for state in ("missing", "failed"):
            result = classify_legacy_publisher_gate(
                publisher="linktrend-review-ready-publisher",
                state=state,
            )
            self.assertEqual(result.classification, WAIVED_LEGACY_GATE)
            self.assertFalse(result.is_pass)
            self.assertFalse(result.is_implementation_failure)
        success = classify_legacy_publisher_gate(
            publisher="linktrend-review-ready-publisher",
            state="success",
        )
        self.assertFalse(success.is_pass)
        self.assertNotEqual(success.classification, WAIVED_LEGACY_GATE)


class IssueCheckpointTests(unittest.TestCase):
    def test_complete_evidence_accepts_without_review_ready_or_token(self) -> None:
        decision = evaluate_issue_checkpoint(
            pushed=True,
            commit=COMMIT_A,
            tree=TREE_A,
            scoped_diff=True,
            focused_tests_passed=True,
            independent_terra_verified=True,
            manifest_evidence=True,
            review_ready=False,
            automation_token_present=False,
        )
        self.assertTrue(decision.accepted)
        self.assertFalse(decision.requires_review_ready)
        self.assertFalse(decision.requires_token)
        self.assertEqual(decision.reason, "v25_bootstrap_lean_issue_checkpoint")

    def test_missing_terra_verification_is_not_accepted(self) -> None:
        decision = evaluate_issue_checkpoint(
            pushed=True,
            commit=COMMIT_A,
            tree=TREE_A,
            scoped_diff=True,
            focused_tests_passed=True,
            independent_terra_verified=False,
            manifest_evidence=True,
        )
        self.assertFalse(decision.accepted)
        self.assertEqual(decision.reason, "independent_terra_verification_required")


class AdministratorRecoveryTests(unittest.TestCase):
    def test_named_exact_head_recovery_after_replacement_proof(self) -> None:
        decision = administrator_recovery(
            named_exception="v25-protection-readback",
            exact_head=COMMIT_A,
            replacement_proof=True,
            operations=("protection_snapshot", "restore", "readback"),
        )
        self.assertTrue(decision.allowed)

    def test_unnamed_or_extra_operations_are_denied(self) -> None:
        unnamed = administrator_recovery(
            named_exception=" ",
            exact_head=COMMIT_A,
            replacement_proof=True,
            operations=("readback",),
        )
        self.assertFalse(unnamed.allowed)
        extra = administrator_recovery(
            named_exception="v25-protection-readback",
            exact_head=COMMIT_A,
            replacement_proof=True,
            operations=("protection_snapshot", "workflow_edit"),
        )
        self.assertFalse(extra.allowed)
        no_proof = administrator_recovery(
            named_exception="v25-protection-readback",
            exact_head=COMMIT_A,
            replacement_proof=False,
            operations=("readback",),
        )
        self.assertFalse(no_proof.allowed)


class AutoworkDiscoveryTests(unittest.TestCase):
    def test_callable_discovery_is_required(self) -> None:
        skipped = autowork_discovery_decision(callable_now=True, performed=False)
        self.assertTrue(skipped.required)
        self.assertFalse(skipped.ok)
        self.assertEqual(skipped.reason, "autowork_discovery_required_when_callable")
        ran = autowork_discovery_decision(callable_now=True, performed=True)
        self.assertTrue(ran.ok)

    def test_uncallable_cannot_claim_live_pass(self) -> None:
        hold = autowork_discovery_decision(callable_now=False, performed=False)
        self.assertTrue(hold.ok)
        self.assertEqual(hold.proof_level, "hold")
        claimed = autowork_discovery_decision(
            callable_now=False,
            performed=False,
            claimed_live_pass=True,
        )
        self.assertFalse(claimed.ok)
        self.assertEqual(claimed.reason, "cannot_claim_live_pass_when_not_callable")


class DurableHeartbeatGateTests(unittest.TestCase):
    def _record(self) -> dict:
        return {
            "packet_id": "PKT-01",
            "attempt_id": "ATT-02",
            "sequence": 1,
            "repository": "linktrend/IDE-Development",
            "commit": COMMIT_A,
            "tree": TREE_A,
            "payload_digest": "sha256:hb-1",
        }

    def test_write_and_readback_admits(self) -> None:
        result = persist_heartbeat(DurableHeartbeatStore(), self._record())
        self.assertTrue(result.ok)
        self.assertEqual(result.reason, "heartbeat_durable")

    def test_missing_readback_is_rejected(self) -> None:
        checkout = candidate_identity(
            repository="linktrend/IDE-Development",
            commit=COMMIT_A,
            tree=TREE_A,
        )
        result = evaluate_heartbeat_gate(
            written=self._record(),
            readback=None,
            checkout=checkout,
        )
        self.assertFalse(result.ok)
        self.assertEqual(result.reason, "heartbeat_readback_missing")

    def test_mutated_readback_is_rejected(self) -> None:
        written = self._record()
        readback = dict(written)
        readback["payload_digest"] = "sha256:tampered"
        result = evaluate_heartbeat_gate(
            written=written,
            readback=readback,
            checkout=candidate_identity(
                repository="linktrend/IDE-Development",
                commit=COMMIT_A,
                tree=TREE_A,
            ),
        )
        self.assertFalse(result.ok)
        self.assertEqual(result.reason, "heartbeat_readback_mismatch")


class CheckoutBoundReceiptTests(unittest.TestCase):
    def test_exact_checkout_receipt_is_promotable(self) -> None:
        decision = evaluate_verification_receipt(
            {
                "checkoutRef": "issue/349-pkt-01",
                "commit": COMMIT_A,
                "tree": TREE_A,
                "promotableIdentity": True,
            },
            checkout=candidate_identity(
                repository="linktrend/IDE-Development",
                commit=COMMIT_A,
                tree=TREE_A,
            ),
        )
        self.assertTrue(decision.accepted)
        self.assertTrue(decision.promotable)

    def test_merge_ref_identity_is_forbidden(self) -> None:
        decision = evaluate_verification_receipt(
            {
                "checkoutRef": "refs/pull/343/merge",
                "commit": COMMIT_A,
                "tree": TREE_A,
                "promotableIdentity": True,
            },
            checkout=candidate_identity(
                repository="linktrend/IDE-Development",
                commit=COMMIT_A,
                tree=TREE_A,
            ),
        )
        self.assertFalse(decision.accepted)
        self.assertEqual(decision.reason, "merge_ref_identity_forbidden")


class RetryExhaustionRecoveryTests(unittest.TestCase):
    def test_ordinary_exhaustion_requires_new_identity(self) -> None:
        diagnosis = diagnose_retry_exhaustion("ordinary_source", 4)
        self.assertTrue(diagnosis.exhausted)
        self.assertEqual(diagnosis.recovery, "new_identity")
        previous = candidate_identity(
            repository="linktrend/IDE-Development",
            commit=COMMIT_A,
            tree=TREE_A,
        )
        silent = evaluate_exhaustion_recovery(
            diagnosis, previous=previous, current=previous
        )
        self.assertFalse(silent.allowed)
        self.assertEqual(silent.reason, "silent_retry_after_exhaustion")
        recovered = evaluate_exhaustion_recovery(
            diagnosis,
            previous=previous,
            current=candidate_identity(
                repository="linktrend/IDE-Development",
                commit=COMMIT_B,
                tree=TREE_B,
            ),
        )
        self.assertTrue(recovered.allowed)

    def test_infrastructure_hold_allows_named_exception(self) -> None:
        diagnosis = diagnose_retry_exhaustion("infrastructure", 2)
        self.assertEqual(diagnosis.recovery, "hold")
        identity = candidate_identity(
            repository="linktrend/IDE-Development",
            commit=COMMIT_A,
            tree=TREE_A,
        )
        self.assertFalse(
            evaluate_exhaustion_recovery(
                diagnosis, previous=identity, current=identity
            ).allowed
        )
        named = evaluate_exhaustion_recovery(
            diagnosis,
            previous=identity,
            current=identity,
            named_exception=True,
        )
        self.assertTrue(named.allowed)
        self.assertEqual(named.reason, "named_exception_recovery")


class HostedCapacitySchedulerTests(unittest.TestCase):
    def test_busy_allocator_without_snapshot_is_uncertain(self) -> None:
        verdict = schedule_hosted_capacity(
            None, allocator_status="exhausted", available_slots=0
        )
        self.assertFalse(verdict.scheduled)
        self.assertTrue(verdict.uncertain)
        self.assertEqual(verdict.reason, "resource_uncertain")
        self.assertNotEqual(verdict.diagnosis, "capacity_exhausted")

    def test_complete_snapshot_with_no_slots_is_exhausted(self) -> None:
        verdict = schedule_hosted_capacity(
            {
                "cpu_percent": 10,
                "memory_percent": 10,
                "free_disk_gib": 40,
                "docker_available": True,
            },
            allocator_status="exhausted",
            available_slots=0,
        )
        self.assertFalse(verdict.scheduled)
        self.assertEqual(verdict.diagnosis, "capacity_exhausted")

    def test_complete_snapshot_with_slots_schedules(self) -> None:
        verdict = schedule_hosted_capacity(
            {
                "cpu_percent": 10,
                "memory_percent": 10,
                "free_disk_gib": 40,
                "docker_available": True,
            },
            available_slots=1,
        )
        self.assertTrue(verdict.scheduled)
        self.assertEqual(verdict.reason, "scheduled")


if __name__ == "__main__":
    unittest.main()
