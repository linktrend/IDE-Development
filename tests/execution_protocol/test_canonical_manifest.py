"""Canonical execution-manifest adversarial and positive tests. None may skip."""

from __future__ import annotations

import json
import sys
import unittest
from copy import deepcopy
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.execution.lifecycle import (  # noqa: E402
    validate_execution_lifecycle,
    validate_plan_or_runtime,
)
from core.execution.protocol import (  # noqa: E402
    DurableHeartbeatStore,
    candidate_identity,
    diagnose_retry_exhaustion,
    evaluate_exhaustion_recovery,
    persist_heartbeat,
    schedule_hosted_capacity,
    validate_execution_manifest,
)

COMMIT = "004bd5faa1e14ee100a018e16dcb049f0fb2d8eb"
TREE = "6c55220132cc7e9a1baef06f8c147ee9ac9431e7"
COMMIT_B = "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
TREE_B = "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb"
FOLLOW_ON_CONTROLS = (
    "durableHeartbeat",
    "checkoutBoundVerification",
    "retryExhaustion",
    "hostedCapacityScheduler",
)


def canonical_manifest() -> dict:
    path = ROOT / "core/execution/examples/execution-manifest.example.json"
    return json.loads(path.read_text(encoding="utf-8"))


def canonical_running() -> dict:
    path = ROOT / "core/execution/examples/execution-runtime-repaired-terminal.example.json"
    return json.loads(path.read_text(encoding="utf-8"))


def _complete_from_canonical() -> dict:
    document = canonical_manifest()
    packet = document["packets"][0]
    packet["executionState"] = "COMPLETE"
    packet["acceptedCommit"] = COMMIT
    packet["acceptedTree"] = TREE
    packet["completionEvidence"] = {
        "kind": "packet_completion",
        "commit": COMMIT,
        "tree": TREE,
        "summary": "PKT-01 follow-on contracts accepted",
    }
    packet["verificationReceipt"] = {
        "checkoutRef": "issue/349-ide-development-v2-5-pkt-01-durable-heartbeat-pe",
        "commit": COMMIT,
        "tree": TREE,
        "kind": "checkout_bound",
        "promotableIdentity": True,
    }
    packet["attempts"] = [
        {
            "id": "ATT-01",
            "authoritative": False,
            "lifecycle": "TERMINAL",
            "rawStatus": "failed",
            "endedAt": "2026-08-20T07:00:00Z",
            "result": None,
            "reason": "ordinary_source_repair",
        },
        {
            "id": "ATT-03",
            "authoritative": True,
            "lifecycle": "TERMINAL",
            "rawStatus": "succeeded",
            "endedAt": "2026-08-20T08:00:00Z",
            "result": "accepted",
            "reason": None,
        },
    ]
    packet["writeLock"] = {"active": False, "attemptId": "ATT-03"}
    return document


class CanonicalManifestPositiveTests(unittest.TestCase):
    def test_canonical_plan_manifest_is_schema_and_semantically_valid(self) -> None:
        document = canonical_manifest()
        schema = validate_execution_manifest(document, repo_root=ROOT)
        semantic = validate_execution_lifecycle(document)
        combined = validate_plan_or_runtime(document, repo_root=ROOT)
        self.assertTrue(schema.ok, schema.errors)
        self.assertTrue(semantic.ok, semantic.errors)
        self.assertTrue(combined.ok, combined.errors)
        self.assertFalse(combined.skipped)
        for key in FOLLOW_ON_CONTROLS:
            self.assertIn(key, document["controls"])

    def test_canonical_running_manifest_requires_durable_heartbeat(self) -> None:
        document = canonical_running()
        result = validate_plan_or_runtime(document, repo_root=ROOT)
        self.assertTrue(result.ok, result.errors)
        self.assertTrue(document["packets"][0]["heartbeat"]["readback"])

    def test_canonical_complete_manifest_binds_checkout_receipt(self) -> None:
        result = validate_plan_or_runtime(_complete_from_canonical(), repo_root=ROOT)
        self.assertTrue(result.ok, result.errors)

    def test_canonical_heartbeat_persist_matches_checkout(self) -> None:
        packet = canonical_running()["packets"][0]
        heartbeat = packet["heartbeat"]
        record = {
            "packet_id": packet["id"],
            "attempt_id": heartbeat["attemptId"],
            "sequence": heartbeat["sequence"],
            "repository": packet["orchestrationLease"]["repository"],
            "commit": heartbeat["commit"],
            "tree": heartbeat["tree"],
            "payload_digest": heartbeat["payloadDigest"],
        }
        result = persist_heartbeat(DurableHeartbeatStore(), record)
        self.assertTrue(result.ok)
        self.assertEqual(result.reason, "heartbeat_durable")

    def test_canonical_capacity_control_schedules_only_with_complete_snapshot(self) -> None:
        self.assertTrue(
            canonical_manifest()["controls"]["hostedCapacityScheduler"]["busyIsNotDiagnosis"]
        )
        scheduled = schedule_hosted_capacity(
            {
                "cpu_percent": 4,
                "memory_percent": 8,
                "free_disk_gib": 50,
                "docker_available": True,
            },
            available_slots=2,
        )
        self.assertTrue(scheduled.scheduled)


class CanonicalManifestAdversarialTests(unittest.TestCase):
    def test_packet_routing_and_cursor_cloud_controls_are_required(self) -> None:
        document = canonical_manifest()
        del document["controls"]["packetRouting"]
        result = validate_execution_manifest(document, repo_root=ROOT)
        self.assertFalse(result.ok)
        self.assertTrue(any("packetRouting" in error for error in result.errors), result.errors)

        document = canonical_manifest()
        del document["controls"]["packetRouting"]["conformance"]
        result = validate_execution_manifest(document, repo_root=ROOT)
        self.assertFalse(result.ok)
        self.assertTrue(result.errors)

        document = canonical_manifest()
        document["controls"]["cursorCloudExecution"]["preDispatchAdvertisedRefValidation"] = False
        result = validate_execution_manifest(document, repo_root=ROOT)
        self.assertFalse(result.ok)
        self.assertTrue(any("True" in error or "const" in error for error in result.errors), result.errors)

    def test_prepared_supersession_is_immutable_and_never_reuses_cloud_attempt(self) -> None:
        document = canonical_manifest()
        document["controls"]["cursorCloudExecution"]["preparedSupersession"]["neverReuseCloudAttempt"] = False
        result = validate_execution_manifest(document, repo_root=ROOT)
        self.assertFalse(result.ok)
        self.assertTrue(result.errors)

    def test_missing_follow_on_control_is_rejected(self) -> None:
        for key in FOLLOW_ON_CONTROLS:
            document = canonical_manifest()
            del document["controls"][key]
            result = validate_execution_manifest(document, repo_root=ROOT)
            self.assertFalse(result.ok, key)
            self.assertTrue(result.errors, key)

    def test_unknown_trust_boundary_field_is_rejected(self) -> None:
        document = canonical_manifest()
        document["controls"]["reviewReadyPublisher"] = {"enabled": True}
        result = validate_execution_manifest(document, repo_root=ROOT)
        self.assertFalse(result.ok)

    def test_heartbeat_without_readback_is_rejected(self) -> None:
        document = canonical_running()
        document["packets"][0]["heartbeat"]["readback"] = False
        result = validate_plan_or_runtime(document, repo_root=ROOT)
        self.assertFalse(result.ok)
        self.assertTrue(
            any("heartbeat_readback_missing" in err for err in result.errors),
            result.errors,
        )

    def test_dropped_heartbeat_store_is_rejected(self) -> None:
        class DroppingStore(DurableHeartbeatStore):
            def read(self, record):  # type: ignore[no-untyped-def]
                del record
                return None

        packet = canonical_running()["packets"][0]
        heartbeat = packet["heartbeat"]
        result = persist_heartbeat(
            DroppingStore(),
            {
                "packet_id": packet["id"],
                "attempt_id": heartbeat["attemptId"],
                "sequence": heartbeat["sequence"],
                "repository": packet["orchestrationLease"]["repository"],
                "commit": heartbeat["commit"],
                "tree": heartbeat["tree"],
                "payload_digest": heartbeat["payloadDigest"],
            },
        )
        self.assertFalse(result.ok)
        self.assertEqual(result.reason, "heartbeat_readback_missing")

    def test_merge_ref_receipt_cannot_complete_canonical_packet(self) -> None:
        document = _complete_from_canonical()
        document["packets"][0]["verificationReceipt"]["checkoutRef"] = "refs/pull/343/merge"
        result = validate_plan_or_runtime(document, repo_root=ROOT)
        self.assertFalse(result.ok)
        self.assertTrue(
            any("merge_ref_identity_forbidden" in err for err in result.errors),
            result.errors,
        )

    def test_receipt_tree_mismatch_is_rejected(self) -> None:
        document = _complete_from_canonical()
        document["packets"][0]["verificationReceipt"]["tree"] = TREE_B
        result = validate_plan_or_runtime(document, repo_root=ROOT)
        self.assertFalse(result.ok)
        self.assertTrue(
            any("checkout_identity_mismatch" in err for err in result.errors),
            result.errors,
        )

    def test_silent_retry_after_exhaustion_on_canonical_identity_is_rejected(self) -> None:
        identity = candidate_identity(
            repository="linktrend/IDE-Development",
            commit=COMMIT,
            tree=TREE,
        )
        diagnosis = diagnose_retry_exhaustion("ordinary_source", 4)
        decision = evaluate_exhaustion_recovery(
            diagnosis, previous=identity, current=identity
        )
        self.assertFalse(decision.allowed)
        self.assertEqual(decision.reason, "silent_retry_after_exhaustion")
        document = canonical_running()
        before = deepcopy(document)
        document["packets"][0]["attempts"][0]["reason"] = "infrastructure_stopped"
        document["packets"][0]["retryExhaustion"] = {
            "kind": "infrastructure",
            "exhausted": True,
            "reason": "infrastructure_stopped",
            "recovery": "continue",
        }
        result = validate_plan_or_runtime(document, repo_root=ROOT)
        self.assertFalse(result.ok)
        self.assertTrue(
            any("silent_retry_after_exhaustion" in err for err in result.errors),
            result.errors,
        )
        self.assertEqual(before["packets"][0]["attempts"][0]["reason"], "ordinary_source_repair")

    def test_busy_allocator_cannot_be_diagnosed_from_incomplete_canonical_snapshot(self) -> None:
        verdict = schedule_hosted_capacity(
            {
                "cpu_percent": 10,
                "memory_percent": 10,
                "free_disk_gib": None,
                "docker_available": True,
            },
            allocator_status="busy",
            available_slots=0,
        )
        self.assertFalse(verdict.scheduled)
        self.assertEqual(verdict.reason, "resource_uncertain")
        self.assertNotEqual(verdict.diagnosis, "capacity_exhausted")

    def test_does_not_silently_normalize_adversarial_complete_receipt(self) -> None:
        document = _complete_from_canonical()
        document["packets"][0]["verificationReceipt"]["promotableIdentity"] = False
        before = deepcopy(document)
        result = validate_plan_or_runtime(document, repo_root=ROOT)
        self.assertFalse(result.ok)
        self.assertEqual(document, before)

    def test_new_identity_recovery_from_canonical_baseline_is_allowed(self) -> None:
        previous = candidate_identity(
            repository=canonical_manifest()["baseline"]["repository"],
            commit=canonical_manifest()["baseline"]["commit"],
            tree=canonical_manifest()["baseline"]["tree"],
        )
        current = candidate_identity(
            repository=previous.repository,
            commit=COMMIT_B,
            tree=TREE_B,
        )
        diagnosis = diagnose_retry_exhaustion("code_failure", 1)
        decision = evaluate_exhaustion_recovery(
            diagnosis, previous=previous, current=current
        )
        self.assertTrue(decision.allowed)
        self.assertEqual(decision.reason, "new_identity_recovery")


if __name__ == "__main__":
    unittest.main()
