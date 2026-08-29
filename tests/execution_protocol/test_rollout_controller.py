"""Deterministic staged consumer rollout tests."""

from __future__ import annotations

import json
import unittest
from pathlib import Path

from jsonschema import Draft202012Validator

from core.execution.rollout import (
    RolloutConfig,
    build_provider_consumer_handoff,
    consume_provider_consumer_handoff,
    evaluate_provider_consumer_handoff,
    plan_rollout,
)


PACKAGE = "sha256:" + "a" * 64
ENVIRONMENT = "sha256:" + "b" * 64
PROVIDER = {"repository": "linktrend/provider", "commit": "a" * 40, "tree": "b" * 40}
CONSUMER = {"repository": "linktrend/consumer", "commit": "c" * 40, "tree": "d" * 40}
RECEIPT = {
    "status": "accepted",
    "protected": True,
    "receiptDigest": "sha256:" + "e" * 64,
    "provider": PROVIDER,
    "owner": "provider-owner",
}


def typed_handoff(**changes):
    values = {
        "provider": PROVIDER,
        "consumer": CONSUMER,
        "artifact_digest": "sha256:" + "f" * 64,
        "contract_digest": "sha256:" + "1" * 64,
        "verdict": "accepted",
        "lifecycle_state": "accepted",
        "accepted_receipt": RECEIPT,
    }
    values.update(changes)
    return build_provider_consumer_handoff(**values)


def target(name: str, status: str = "PENDING", **extra):
    return {"name": name, "status": status, **extra}


def verified(name: str, **extra):
    after_tree = extra.pop("afterTree", "2" * 40)
    return target(
        name,
        "VERIFIED",
        afterTree=after_tree,
        receipt={
            "status": "PASSED",
            "packageDigest": PACKAGE,
            "environmentDigest": ENVIRONMENT,
            "afterTree": after_tree,
        },
        **extra,
    )


class RolloutControllerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.config = RolloutConfig.from_mapping(
            {
                "canaryTargets": ["canary-a"],
                "downstreamTargets": ["repo-b", "repo-c", "repo-d"],
                "maxParallel": 3,
            }
        )

    def test_downstream_is_read_only_until_canary_passes(self) -> None:
        result = plan_rollout(
            self.config,
            [target("canary-a"), target("repo-b"), target("repo-c"), target("repo-d")],
            package_digest=PACKAGE,
            environment_digest=ENVIRONMENT,
        )
        mutations = [row for row in result["actions"] if row["mutating"]]
        self.assertEqual([(row["kind"], row["target"]) for row in mutations], [("UPDATE", "canary-a")])
        self.assertEqual(
            {row["target"] for row in result["actions"] if row["kind"] == "PRESTAGE"},
            {"repo-b", "repo-c", "repo-d"},
        )

    def test_canary_pass_fills_all_safe_slots_in_same_turn(self) -> None:
        result = plan_rollout(
            self.config,
            [verified("canary-a"), target("repo-b"), target("repo-c"), target("repo-d")],
            package_digest=PACKAGE,
            environment_digest=ENVIRONMENT,
        )
        updates = [row["target"] for row in result["actions"] if row["kind"] == "UPDATE"]
        self.assertEqual(updates, ["repo-b", "repo-c", "repo-d"])
        self.assertEqual(result["availableMutationSlots"], 3)

    def test_repository_failure_isolated_but_systemic_failure_rolls_back(self) -> None:
        isolated = plan_rollout(
            self.config,
            [
                verified("canary-a"),
                target("repo-b", "FAILED", failureScope="REPOSITORY"),
                target("repo-c"),
                target("repo-d"),
            ],
            package_digest=PACKAGE,
            environment_digest=ENVIRONMENT,
        )
        self.assertFalse(isolated["halted"])
        self.assertEqual(isolated["isolatedTargets"], ["repo-b"])
        self.assertEqual(
            [row["target"] for row in isolated["actions"] if row["kind"] == "UPDATE"],
            ["repo-c", "repo-d"],
        )

        stopped = plan_rollout(
            self.config,
            [
                verified("canary-a", beforeTree="1" * 40),
                target("repo-b", "FAILED", failureScope="SYSTEMIC"),
                target("repo-c", "MUTATING", beforeTree="3" * 40, afterTree="4" * 40),
                target("repo-d"),
            ],
            package_digest=PACKAGE,
            environment_digest=ENVIRONMENT,
        )
        self.assertTrue(stopped["halted"])
        self.assertEqual(stopped["status"], "SYSTEMIC_STOP")
        self.assertEqual(
            {row["target"] for row in stopped["actions"] if row["kind"] == "ROLLBACK"},
            {"canary-a", "repo-c"},
        )

    def test_exact_receipt_reused_and_changed_package_invalidates_it(self) -> None:
        receipt = {
            "status": "PASSED",
            "packageDigest": PACKAGE,
            "environmentDigest": ENVIRONMENT,
            "afterTree": "2" * 40,
        }
        unchanged = target("canary-a", "VERIFIED", afterTree="2" * 40, receipt=receipt)
        result = plan_rollout(
            self.config,
            [unchanged, target("repo-b"), target("repo-c"), target("repo-d")],
            package_digest=PACKAGE,
            environment_digest=ENVIRONMENT,
        )
        self.assertEqual(result["reusedEvidence"], ["canary-a"])
        self.assertNotIn("canary-a", [row["target"] for row in result["actions"]])

        changed = plan_rollout(
            self.config,
            [unchanged, target("repo-b"), target("repo-c"), target("repo-d")],
            package_digest="sha256:" + "c" * 64,
            environment_digest=ENVIRONMENT,
        )
        self.assertEqual(changed["reusedEvidence"], [])
        self.assertIn("canary-a", [row["target"] for row in changed["actions"] if row["kind"] == "UPDATE"])

    def test_topology_is_configuration_not_product_constant(self) -> None:
        config = RolloutConfig.from_mapping(
            {"canaryTargets": [], "downstreamTargets": ["one", "two"], "maxParallel": 1}
        )
        result = plan_rollout(
            config,
            [target("one"), target("two")],
            package_digest=PACKAGE,
            environment_digest=ENVIRONMENT,
        )
        self.assertEqual([row["target"] for row in result["actions"] if row["kind"] == "UPDATE"], ["one"])

    def test_program_run_may_contain_one_repository(self) -> None:
        config = RolloutConfig.from_mapping(
            {"canaryTargets": ["only-repository"], "downstreamTargets": [], "maxParallel": 1}
        )
        result = plan_rollout(
            config,
            [target("only-repository")],
            package_digest=PACKAGE,
            environment_digest=ENVIRONMENT,
        )
        self.assertEqual(
            [row["target"] for row in result["actions"] if row["kind"] == "UPDATE"],
            ["only-repository"],
        )

    def test_typed_handoff_schema_and_exact_protected_admission(self) -> None:
        handoff = typed_handoff()
        schema = json.loads(
            (Path(__file__).resolve().parents[2] / "core/managed-core/schemas/provider-consumer-handoff.schema.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual(list(Draft202012Validator(schema).iter_errors(handoff)), [])
        admitted = evaluate_provider_consumer_handoff(
            handoff,
            protected_provider_identity=PROVIDER,
            accepted_receipt=RECEIPT,
        )
        self.assertTrue(admitted["admitted"])
        self.assertEqual(admitted["reason"], "accepted_protected_provider_receipt")
        self.assertFalse(admitted["integrationClaimed"])
        self.assertEqual(
            consume_provider_consumer_handoff(
                handoff,
                protected_provider_identity=PROVIDER,
                accepted_receipt=RECEIPT,
            ),
            (True, "accepted_protected_provider_receipt"),
        )

    def test_stale_provider_pin_and_missing_receipt_fail_closed(self) -> None:
        stale = evaluate_provider_consumer_handoff(
            typed_handoff(),
            protected_provider_identity={**PROVIDER, "commit": "9" * 40},
            accepted_receipt=RECEIPT,
        )
        self.assertFalse(stale["admitted"])
        self.assertEqual(stale["reason"], "stale_provider_pin")
        self.assertFalse(stale["integrationClaimed"])
        self.assertEqual(stale["blocker"]["blockingRepository"], PROVIDER["repository"])

        missing = evaluate_provider_consumer_handoff(
            typed_handoff(), protected_provider_identity=PROVIDER
        )
        self.assertFalse(missing["admitted"])
        self.assertEqual(missing["reason"], "accepted_receipt_missing")

    def test_rollout_allows_only_read_only_independent_preparation_while_blocked(self) -> None:
        blocked_handoff = typed_handoff(
            verdict="blocked",
            lifecycle_state="prepared",
            accepted_receipt=None,
            blocker={
                "blockingRepository": PROVIDER["repository"],
                "handoffClass": "provider-consumer",
                "owner": "provider-owner",
                "nextAction": "accept the current protected provider receipt",
            },
        )
        result = plan_rollout(
            self.config,
            [
                target("canary-a"),
                target("repo-b", independentPreparation=True),
                target("repo-c"),
                target("repo-d"),
            ],
            package_digest=PACKAGE,
            environment_digest=ENVIRONMENT,
            handoff=blocked_handoff,
            protected_provider_identity=PROVIDER,
        )
        self.assertEqual(result["status"], "BLOCKED")
        self.assertFalse(result["integrationAdmitted"])
        self.assertEqual(
            [(row["kind"], row["target"], row["mutating"]) for row in result["actions"]],
            [("PREPARE", "repo-b", False)],
        )
        self.assertEqual(result["blocker"]["blockingRepository"], PROVIDER["repository"])
        self.assertEqual(result["blocker"]["owner"], "provider-owner")
        self.assertNotIn("UPDATE", [row["kind"] for row in result["actions"]])

    def test_rollout_admits_integration_after_exact_handoff_and_receipt(self) -> None:
        result = plan_rollout(
            self.config,
            [target("canary-a"), target("repo-b"), target("repo-c"), target("repo-d")],
            package_digest=PACKAGE,
            environment_digest=ENVIRONMENT,
            handoff=typed_handoff(),
            protected_provider_identity=PROVIDER,
            accepted_receipt=RECEIPT,
        )
        self.assertTrue(result["integrationAdmitted"])
        self.assertEqual(result["providerHandoff"]["status"], "ADMITTED")
        self.assertEqual(
            [row["target"] for row in result["actions"] if row["kind"] == "UPDATE"],
            ["canary-a"],
        )


if __name__ == "__main__":
    unittest.main()
