"""Deterministic staged consumer rollout tests."""

from __future__ import annotations

import unittest

from core.execution.rollout import RolloutConfig, plan_rollout


PACKAGE = "sha256:" + "a" * 64
ENVIRONMENT = "sha256:" + "b" * 64


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


if __name__ == "__main__":
    unittest.main()
