"""Protected Phase delivery remains one PR/gate with exact review and founder main."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.gitops import delivery_controller as controller
from scripts.tests.test_delivery_controller import (
    _gates,
    _handoff,
    _identity,
    _named_checks,
    _receipt,
    _repository_ci,
    _sha,
)


class PhaseDeliveryContractTests(unittest.TestCase):
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

    def test_normal_protected_merge_does_not_use_admin_recovery(self) -> None:
        result = controller.deliver_phase_to_development(
            github=self.github,
            repository="owner/name",
            handoff=self.handoff,
            pr=self.pr,
            live_head=self.head,
            live_tree=self.tree,
            gate_payload=_gates(self.head),
            named_checks=_named_checks(self.head),
            repository_ci=_repository_ci(self.head),
            receipt=self.receipt,
            candidate_identity=self.identity,
            role="operator",
        )
        self.assertEqual(result["status"], "merged")
        self.assertFalse(result["directPush"])
        self.assertEqual(self.github.merges[0]["method"], "merge")
        self.assertFalse(self.github.merges[0].get("admin", False))
        self.assertNotIn("recovery", result)

    def test_missing_full_or_review_gate_still_blocks_development(self) -> None:
        checks = _named_checks(self.head)
        checks.pop("Linktrend Full Suite")
        with self.assertRaisesRegex(controller.ControllerError, "required_gate_missing"):
            controller.verify_development_eligibility(
                handoff=self.handoff,
                pr=self.pr,
                repository="owner/name",
                live_head=self.head,
                live_tree=self.tree,
                gate_payload=_gates(self.head),
                named_checks=checks,
                repository_ci=_repository_ci(self.head),
                receipt=self.receipt,
                candidate_identity=self.identity,
            )

    def test_main_still_requires_founder_approval(self) -> None:
        with self.assertRaisesRegex(controller.ControllerError, "founder_approval_missing"):
            controller.complete_main_promotion(
                github=self.github,
                repository="owner/name",
                pr_number=11,
                expected_head=self.head,
                source_sha=self.head,
                base_sha=_sha(6),
                approval={},
                receipt=self.receipt,
                role="operator",
            )
