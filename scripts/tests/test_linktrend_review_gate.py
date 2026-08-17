"""Focused tests for WP-U01 Linktrend Review Gate."""

from __future__ import annotations

import json
import unittest
from pathlib import Path

from jsonschema import Draft202012Validator

from scripts.gitops.linktrend_review_gate import (
    MAX_INFRASTRUCTURE_ATTEMPTS,
    OUTCOME_ADVISORY,
    OUTCOME_FAILED,
    OUTCOME_FINDINGS,
    OUTCOME_PASSED,
    OUTCOME_UNKNOWN,
    RAW_BUGBOT_CONTEXT,
    REVIEW_GATE_CONTEXT,
    ReviewGateError,
    assert_full_suite_allows_bugbot,
    classify_bugbot_result,
    evaluate_fallback_review,
    evaluate_github_approval,
    gate_commit_status,
    invalidate_if_head_changed,
    migrated_required_contexts,
    reject_third_infrastructure_attempt,
    reject_undocumented_task_hold,
    require_no_raw_bugbot_required,
    require_review_gate_on_development,
)

ROOT = Path(__file__).resolve().parents[2]
SCHEMA = ROOT / "core" / "managed-core" / "schemas" / "linktrend-review-gate.schema.json"
MODULE = ROOT / "scripts" / "gitops" / "linktrend_review_gate.py"
DOCTRINE = ROOT / "docs" / "contracts" / "LINKTREND-REVIEW-GATE.md"
WORKFLOW = ROOT / ".github" / "workflows" / "linktrend-review-gate.yml"
HEAD = "a" * 40
TREE = "b" * 40
REPO = "linktrend/IDE-Development"


class LinktrendReviewGateTests(unittest.TestCase):
    def test_packaged_surfaces_exist(self) -> None:
        self.assertTrue(MODULE.is_file())
        self.assertTrue(SCHEMA.is_file())
        self.assertTrue(DOCTRINE.is_file())
        self.assertTrue(WORKFLOW.is_file())
        self.assertIn("needs: full", (ROOT / ".github/workflows/linktrend-integrator-merge.yml").read_text())

    def _classify(self, **kwargs):
        base = dict(
            repository=REPO,
            head_sha=HEAD,
            git_tree=TREE,
            pull_request=322,
            bugbot_state="completed",
            bugbot_conclusion="success",
            infrastructure_attempts=1,
            result_head_sha=HEAD,
        )
        base.update(kwargs)
        return classify_bugbot_result(**base)

    def test_all_classified_outcomes(self) -> None:
        passed = self._classify()
        self.assertEqual(passed.outcome, OUTCOME_PASSED)
        self.assertTrue(passed.gateSuccess)
        self.assertTrue(passed.bugbotPassedClaim)

        findings = self._classify(findings_present=True)
        self.assertEqual(findings.outcome, OUTCOME_FINDINGS)
        self.assertFalse(findings.gateSuccess)

        failed = self._classify(bugbot_state="failure", bugbot_conclusion="failure")
        self.assertEqual(failed.outcome, OUTCOME_FAILED)
        self.assertFalse(failed.gateSuccess)

        advisory = self._classify(
            bugbot_state="completed",
            bugbot_conclusion="neutral",
            provider_error={"class": "quota"},
        )
        self.assertEqual(advisory.outcome, OUTCOME_ADVISORY)
        self.assertTrue(advisory.gateSuccess)
        self.assertFalse(advisory.bugbotPassedClaim)
        self.assertTrue(advisory.alertFounder)
        self.assertFalse(advisory.bugbotPassedClaim)
        self.assertIn("advisory-unavailable", advisory.sanitizedAlert or "")
        status = gate_commit_status(advisory)
        self.assertEqual(status["state"], "success")
        self.assertIn("not a Bugbot pass", status["description"])

        unknown = self._classify(bugbot_conclusion="neutral")
        self.assertEqual(unknown.outcome, OUTCOME_UNKNOWN)
        self.assertFalse(unknown.gateSuccess)

        Draft202012Validator(json.loads(SCHEMA.read_text(encoding="utf-8"))).validate(passed.to_dict())
        Draft202012Validator(json.loads(SCHEMA.read_text(encoding="utf-8"))).validate(advisory.to_dict())

    def test_fail_closed_missing_malformed_forged_wrong_head(self) -> None:
        for kwargs in (
            {"missing": True},
            {"malformed": True},
            {"forged": True},
            {"result_head_sha": "c" * 40},
        ):
            result = self._classify(**kwargs)
            self.assertEqual(result.outcome, OUTCOME_UNKNOWN)
            self.assertFalse(result.gateSuccess)

    def test_full_failure_blocks_bugbot_request(self) -> None:
        with self.assertRaises(ReviewGateError) as ctx:
            assert_full_suite_allows_bugbot("failure")
        self.assertEqual(ctx.exception.code, "bugbot_before_full_forbidden")
        assert_full_suite_allows_bugbot("success")

    def test_third_infrastructure_attempt_rejected(self) -> None:
        reject_third_infrastructure_attempt(MAX_INFRASTRUCTURE_ATTEMPTS)
        with self.assertRaises(ReviewGateError) as ctx:
            reject_third_infrastructure_attempt(MAX_INFRASTRUCTURE_ATTEMPTS + 1)
        self.assertEqual(ctx.exception.code, "infrastructure_attempt_limit")
        with self.assertRaises(ReviewGateError):
            self._classify(infrastructure_attempts=3)

    def test_new_commit_invalidates_prior_outcome(self) -> None:
        with self.assertRaises(ReviewGateError) as ctx:
            invalidate_if_head_changed(bound_head=HEAD, live_head="d" * 40)
        self.assertEqual(ctx.exception.code, "stale_head")

    def test_raw_bugbot_required_contexts_rejected(self) -> None:
        migrated = migrated_required_contexts([RAW_BUGBOT_CONTEXT, "Linktrend Fast Gate"])
        self.assertEqual(migrated[0], REVIEW_GATE_CONTEXT)
        require_review_gate_on_development(migrated)
        with self.assertRaises(ReviewGateError) as ctx:
            require_no_raw_bugbot_required([RAW_BUGBOT_CONTEXT])
        self.assertEqual(ctx.exception.code, "raw_bugbot_required")
        with self.assertRaises(ReviewGateError):
            require_review_gate_on_development(["Linktrend Fast Gate"])

    def test_protection_and_consumer_defaults_migrated(self) -> None:
        from scripts.gitops import repository_protection as rp
        from scripts.gitops import ruleset_plan as plan

        self.assertEqual(rp.BUGBOT_CHECK, REVIEW_GATE_CONTEXT)
        self.assertNotIn(RAW_BUGBOT_CONTEXT, rp.managed_baseline("development"))
        self.assertIn(REVIEW_GATE_CONTEXT, rp.managed_baseline("development"))
        self.assertIn(REVIEW_GATE_CONTEXT, plan.CONTEXTS["development"])
        self.assertNotIn(RAW_BUGBOT_CONTEXT, plan.CONTEXTS["development"])
        consumer = json.loads((ROOT / ".github/linktrend-gitops-consumer.json").read_text())
        self.assertEqual(consumer["bugbotCheckName"], REVIEW_GATE_CONTEXT)
        self.assertEqual(consumer["reviewGateCheckName"], REVIEW_GATE_CONTEXT)
        self.assertEqual(consumer["bugbotProviderCheckName"], RAW_BUGBOT_CONTEXT)

    def test_undocumented_task_hold_rejected(self) -> None:
        reject_undocumented_task_hold(configured_gates_passed=True, task_hold=None)
        with self.assertRaises(ReviewGateError) as ctx:
            reject_undocumented_task_hold(configured_gates_passed=True, task_hold="extra review")
        self.assertEqual(ctx.exception.code, "undocumented_task_hold")

    def test_fallback_reviewer_rules(self) -> None:
        ok = evaluate_fallback_review(
            outcome=OUTCOME_ADVISORY,
            independent_review_configured=True,
            reviewer_actor="reviewer-bot",
            implementer_actor="implementer-bot",
            evidence_head=HEAD,
            live_head=HEAD,
        )
        self.assertTrue(ok["requested"])
        with self.assertRaises(ReviewGateError) as ctx:
            evaluate_fallback_review(
                outcome=OUTCOME_ADVISORY,
                independent_review_configured=True,
                reviewer_actor="same",
                implementer_actor="same",
                evidence_head=HEAD,
                live_head=HEAD,
            )
        self.assertEqual(ctx.exception.code, "fallback_implementer_rejected")
        with self.assertRaises(ReviewGateError):
            evaluate_fallback_review(
                outcome=OUTCOME_ADVISORY,
                independent_review_configured=True,
                reviewer_actor="reviewer-bot",
                implementer_actor="implementer-bot",
                evidence_head=HEAD,
                live_head="e" * 40,
            )

    def test_same_account_comment_not_github_approval(self) -> None:
        with self.assertRaises(ReviewGateError) as ctx:
            evaluate_github_approval(
                approving_review_required=True,
                reviewer_login="",
                comment_author_login="carlos",
                technical_review_clean=True,
                evidence_head=HEAD,
                live_head=HEAD,
                approval_source="comment",
            )
        self.assertEqual(ctx.exception.code, "same_account_approval_rejected")
        technical = evaluate_github_approval(
            approving_review_required=False,
            reviewer_login="reviewer",
            comment_author_login="reviewer",
            technical_review_clean=True,
            evidence_head=HEAD,
            live_head=HEAD,
        )
        self.assertEqual(technical["mode"], "technical_review_only")
        self.assertFalse(technical["rerunFastFull"])

    def test_observer_rejects_raw_bugbot_as_managed_gate(self) -> None:
        import subprocess
        import sys

        script = r"""
import os, sys
sys.path.insert(0, "scripts/gitops")
os.chdir(%r)
import repair_observer
cfg = repair_observer.load_config({
    "LINKTREND_BUGBOT_PROVIDER_CHECK_NAME": "Cursor Bugbot",
    "LINKTREND_REVIEW_GATE_CHECK_NAME": "Linktrend Review Gate",
})
assert cfg.bugbot_check_name == "Cursor Bugbot"
assert cfg.review_gate_check_name == "Linktrend Review Gate"
try:
    repair_observer.load_config({"LINKTREND_REVIEW_GATE_CHECK_NAME": "Cursor Bugbot"})
except RuntimeError as exc:
    assert "raw_bugbot_required" in str(exc)
else:
    raise SystemExit("expected raw_bugbot_required")
print("ok")
""" % str(ROOT)
        completed = subprocess.run(
            [sys.executable, "-c", script],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertIn("ok", completed.stdout)


if __name__ == "__main__":
    unittest.main()
