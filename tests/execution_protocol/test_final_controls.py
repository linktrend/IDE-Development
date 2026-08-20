"""Adversarial tests for the PKT-08 revision-60 final controls."""

from __future__ import annotations

import copy
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

from core.execution.protocol import LeaseState
from core.execution.transactional_dispatch import (
    CONTROL_IDEMPOTENCY_KEY,
    DispatchBudget,
    DispatchInterrupted,
    DispatchRequest,
    DurableDispatchIntentStore,
    DurableDesignResumeStore,
    dispatch_transactionally,
    deterministic_dispatch_key,
    design_approval_decision,
    load_transactional_dispatch_config,
    resume_unsolicited_design_result,
)


IDENTITY = {
    "repository": "linktrend/IDE-Development",
    "commit": "a" * 40,
    "tree": "b" * 40,
}
NOW = datetime(2026, 8, 20, tzinfo=timezone.utc)


def request() -> DispatchRequest:
    return DispatchRequest(
        packet_id="PKT-08",
        repository=IDENTITY["repository"],
        commit=IDENTITY["commit"],
        tree=IDENTITY["tree"],
        action="run-focused-checks",
        payload={"command": "python3 -m unittest"},
    )


def lease(*, expires_at: datetime) -> LeaseState:
    return LeaseState(
        holder="executor-1",
        packet_id="PKT-08",
        repository=IDENTITY["repository"],
        nonce="nonce-1",
        expires_at=expires_at,
    )


class FakeExternalDispatch:
    def __init__(
        self,
        *,
        interrupt_after_201: bool = False,
        inject_wrong_authority_key: bool = False,
    ) -> None:
        self.calls = 0
        self.interrupt_after_201 = interrupt_after_201
        self.inject_wrong_authority_key = inject_wrong_authority_key
        self.authoritative: dict[str, dict[str, str]] = {}

    def dispatch(self, dispatch_request, idempotency_key):
        self.calls += 1
        response = {"statusCode": 201, "dispatchId": "dispatch-1"}
        self.authoritative[idempotency_key] = {
            "dispatchId": "dispatch-1",
            "idempotencyKey": (
                "attacker-key"
                if self.inject_wrong_authority_key
                else idempotency_key
            ),
        }
        if self.interrupt_after_201:
            self.interrupt_after_201 = False
            raise DispatchInterrupted(201, idempotency_key)
        return response

    def read_by_idempotency_key(self, idempotency_key):
        return copy.deepcopy(self.authoritative.get(idempotency_key))


class FinalControlTests(unittest.TestCase):
    def test_revision_60_config_is_schema_valid_and_exactly_bound(self) -> None:
        config = load_transactional_dispatch_config(
            Path(__file__).resolve().parents[2]
        )
        self.assertEqual(config["apiAcceptedStatusCode"], 201)
        self.assertFalse(config["conversationIsAuthority"])

    def test_dispatch_key_is_deterministic_and_request_bound(self) -> None:
        first = deterministic_dispatch_key(request())
        second = deterministic_dispatch_key(request())
        changed = deterministic_dispatch_key(
            DispatchRequest(
                **{**request().__dict__, "action": "different-action"}
            )
        )
        self.assertEqual(first, second)
        self.assertNotEqual(first, changed)
        self.assertTrue(first.startswith(CONTROL_IDEMPOTENCY_KEY + ":"))

    def test_write_ahead_dispatch_commits_once_with_same_turn_readback(self) -> None:
        store = DurableDispatchIntentStore()
        external = FakeExternalDispatch()
        result = dispatch_transactionally(
            request(),
            store,
            external,
            lease=lease(expires_at=NOW + timedelta(minutes=5)),
            holder="executor-1",
            now=NOW,
            budget=DispatchBudget(remaining_seconds=30, required_seconds=4),
        )
        self.assertEqual(result.status, "committed")
        self.assertEqual(external.calls, 1)
        self.assertGreaterEqual(store.read_count, store.write_count * 2)
        self.assertEqual(store.read_by_key(result.idempotency_key)["state"], "COMMITTED")

    def test_api_201_interruption_recovers_without_second_external_dispatch(self) -> None:
        store = DurableDispatchIntentStore()
        external = FakeExternalDispatch(interrupt_after_201=True)
        result = dispatch_transactionally(
            request(),
            store,
            external,
            lease=lease(expires_at=NOW + timedelta(minutes=5)),
            holder="executor-1",
            now=NOW,
            budget=DispatchBudget(remaining_seconds=30, required_seconds=4),
        )
        self.assertEqual(result.status, "recovered")
        self.assertEqual(result.dispatch_id, "dispatch-1")
        self.assertEqual(external.calls, 1)

    def test_injected_authority_after_201_is_rejected(self) -> None:
        store = DurableDispatchIntentStore()
        external = FakeExternalDispatch(
            interrupt_after_201=True, inject_wrong_authority_key=True
        )
        with self.assertRaisesRegex(RuntimeError, "external_authority_identity_mismatch"):
            dispatch_transactionally(
                request(),
                store,
                external,
                lease=lease(expires_at=NOW + timedelta(minutes=5)),
                holder="executor-1",
                now=NOW,
                budget=DispatchBudget(remaining_seconds=30, required_seconds=4),
            )
        self.assertEqual(external.calls, 1)
    def test_cas_collision_retries_commit_without_redispatch(self) -> None:
        store = DurableDispatchIntentStore()
        store.collide_next_commit = True
        external = FakeExternalDispatch()
        result = dispatch_transactionally(
            request(),
            store,
            external,
            lease=lease(expires_at=NOW + timedelta(minutes=5)),
            holder="executor-1",
            now=NOW,
            budget=DispatchBudget(remaining_seconds=30, required_seconds=4),
        )
        self.assertEqual(result.status, "committed")
        self.assertEqual(external.calls, 1)
        self.assertGreaterEqual(store.cas_attempt_count, 3)

    def test_stale_lease_fails_closed_before_write_ahead_or_dispatch(self) -> None:
        store = DurableDispatchIntentStore()
        external = FakeExternalDispatch()
        with self.assertRaisesRegex(RuntimeError, "stale_or_invalid_lease"):
            dispatch_transactionally(
                request(),
                store,
                external,
                lease=lease(expires_at=NOW - timedelta(seconds=1)),
                holder="executor-1",
                now=NOW,
                budget=DispatchBudget(remaining_seconds=30, required_seconds=4),
            )
        self.assertEqual(store.write_count, 0)
        self.assertEqual(external.calls, 0)

    def test_insufficient_deadline_budget_fails_before_any_side_effect(self) -> None:
        store = DurableDispatchIntentStore()
        external = FakeExternalDispatch()
        with self.assertRaisesRegex(RuntimeError, "deadline_budget_insufficient"):
            dispatch_transactionally(
                request(),
                store,
                external,
                lease=lease(expires_at=NOW + timedelta(minutes=5)),
                holder="executor-1",
                now=NOW,
                budget=DispatchBudget(remaining_seconds=3, required_seconds=4),
            )
        self.assertEqual(store.write_count, 0)
        self.assertEqual(external.calls, 0)

    def test_duplicate_wake_returns_committed_record_without_redispatch(self) -> None:
        store = DurableDispatchIntentStore()
        external = FakeExternalDispatch()
        first = dispatch_transactionally(
            request(),
            store,
            external,
            lease=lease(expires_at=NOW + timedelta(minutes=5)),
            holder="executor-1",
            now=NOW,
            budget=DispatchBudget(remaining_seconds=30, required_seconds=4),
        )
        repeated = dispatch_transactionally(
            request(),
            store,
            external,
            lease=lease(expires_at=NOW + timedelta(minutes=5)),
            holder="executor-1",
            now=NOW,
            budget=DispatchBudget(remaining_seconds=30, required_seconds=4),
        )
        self.assertEqual(first.idempotency_key, repeated.idempotency_key)
        self.assertEqual(repeated.status, "duplicate")
        self.assertEqual(external.calls, 1)

    def test_conversation_cannot_authorize_design_approval(self) -> None:
        decision = design_approval_decision(
            {"designAuthority": {"status": "PENDING"}},
            conversation={"status": "APPROVED"},
        )
        self.assertFalse(decision.approved)
        self.assertTrue(decision.executor_approval_required)
        self.assertEqual(decision.reason, "approved_manifest_required")

    def test_approved_manifest_suppresses_executor_approval(self) -> None:
        decision = design_approval_decision(
            {
                "designAuthority": {
                    "status": "APPROVED",
                    "manifestDigest": "sha256:" + "c" * 64,
                }
            },
            conversation={"status": "PENDING"},
        )
        self.assertTrue(decision.approved)
        self.assertTrue(decision.suppress_executor_approval)

    def test_unsolicited_design_only_terminal_result_resumes_once(self) -> None:
        manifest = {
            "designAuthority": {
                "status": "APPROVED",
                "manifestDigest": "sha256:" + "c" * 64,
            }
        }
        result = {
            "resultId": "design-result-1",
            "kind": "design-only",
            "terminal": True,
            "solicited": False,
        }
        store = DurableDesignResumeStore()
        first = resume_unsolicited_design_result(manifest, result, store)
        repeated = resume_unsolicited_design_result(manifest, result, store)
        self.assertTrue(first.resumed)
        self.assertFalse(repeated.resumed)
        self.assertEqual(repeated.reason, "duplicate_resume_suppressed")
        self.assertEqual(store.write_count, 1)


if __name__ == "__main__":
    unittest.main()
