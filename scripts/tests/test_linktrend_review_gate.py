"""Focused tests for WP-U01 Linktrend Review Gate (including repair findings)."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from jsonschema import Draft202012Validator

from scripts.gitops.linktrend_review_gate import (
    FULL_SUITE_CONTEXT,
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
    build_durable_founder_alert,
    build_fallback_request_comment,
    classify_bugbot_result,
    count_infrastructure_attempts,
    evaluate_fallback_review,
    evaluate_github_approval,
    founder_alert_already_recorded,
    founder_alert_marker,
    gate_commit_status,
    infrastructure_attempt_marker,
    invalidate_if_head_changed,
    migrated_required_contexts,
    reject_third_infrastructure_attempt,
    reject_undocumented_task_hold,
    require_full_receipt_for_gate_success,
    require_no_raw_bugbot_required,
    require_review_gate_on_development,
    verified_provider_unavailability,
)

ROOT = Path(__file__).resolve().parents[2]
SCHEMA = ROOT / "core" / "managed-core" / "schemas" / "linktrend-review-gate.schema.json"
MODULE = ROOT / "scripts" / "gitops" / "linktrend_review_gate.py"
DOCTRINE = ROOT / "docs" / "contracts" / "LINKTREND-REVIEW-GATE.md"
WORKFLOW = ROOT / ".github" / "workflows" / "linktrend-review-gate.yml"
MANAGED_WORKFLOW = ROOT / "core" / "github" / "managed-workflows" / "linktrend-review-gate.yml"
OBSERVER_TEMPLATE = ROOT / "core" / "github" / "managed-workflows" / "linktrend-repair-observer.yml"
HEAD = "a" * 40
TREE = "b" * 40
REPO = "linktrend/IDE-Development"


def _verified_quota() -> dict:
    return {
        "verified": True,
        "class": "quota",
        "source": "repair_observer.usage_limit",
    }


class LinktrendReviewGateTests(unittest.TestCase):
    def test_packaged_surfaces_exist(self) -> None:
        self.assertTrue(MODULE.is_file())
        self.assertTrue(SCHEMA.is_file())
        self.assertTrue(DOCTRINE.is_file())
        self.assertTrue(WORKFLOW.is_file())
        self.assertTrue(MANAGED_WORKFLOW.is_file())
        self.assertIn("needs: full", (ROOT / ".github/workflows/linktrend-integrator-merge.yml").read_text())

    def _classify(self, **kwargs):
        base = dict(
            repository=REPO,
            head_sha=HEAD,
            git_tree=TREE,
            pull_request=322,
            bugbot_state="completed",
            bugbot_conclusion="success",
            infrastructure_attempts=0,
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
            provider_error=_verified_quota(),
            infrastructure_attempts=1,
        )
        self.assertEqual(advisory.outcome, OUTCOME_ADVISORY)
        self.assertTrue(advisory.gateSuccess)
        self.assertFalse(advisory.bugbotPassedClaim)
        self.assertTrue(advisory.alertFounder)
        self.assertIn("advisory-unavailable", advisory.sanitizedAlert or "")
        status = gate_commit_status(advisory)
        self.assertEqual(status["state"], "success")
        self.assertIn("not a Bugbot pass", status["description"])

        unknown = self._classify(bugbot_conclusion="neutral")
        self.assertEqual(unknown.outcome, OUTCOME_UNKNOWN)
        self.assertFalse(unknown.gateSuccess)

        Draft202012Validator(json.loads(SCHEMA.read_text(encoding="utf-8"))).validate(passed.to_dict())
        Draft202012Validator(json.loads(SCHEMA.read_text(encoding="utf-8"))).validate(advisory.to_dict())

    def test_failure_never_becomes_advisory_via_heuristic(self) -> None:
        # Free-text / unverified payload must not convert failure into gate success.
        heuristic = {"class": "quota", "verified": False, "source": "repair_observer.usage_limit"}
        result = self._classify(
            bugbot_state="failure",
            bugbot_conclusion="failure",
            provider_error=heuristic,
        )
        self.assertEqual(result.outcome, OUTCOME_FAILED)
        self.assertFalse(result.gateSuccess)
        self.assertIsNone(verified_provider_unavailability({"class": "quota"}))
        self.assertIsNone(
            verified_provider_unavailability(
                {"verified": True, "class": "quota", "source": "grep-heuristic"}
            )
        )

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

    def test_full_receipt_required_before_successful_gate_publish(self) -> None:
        good = {
            "name": FULL_SUITE_CONTEXT,
            "headSha": HEAD,
            "gitTree": TREE,
            "status": "success",
        }
        require_full_receipt_for_gate_success(
            gate_success=True, full_receipt=good, head_sha=HEAD, git_tree=TREE
        )
        require_full_receipt_for_gate_success(
            gate_success=False, full_receipt=None, head_sha=HEAD, git_tree=TREE
        )
        with self.assertRaises(ReviewGateError) as missing:
            require_full_receipt_for_gate_success(
                gate_success=True, full_receipt=None, head_sha=HEAD, git_tree=TREE
            )
        self.assertEqual(missing.exception.code, "full_receipt_missing")
        with self.assertRaises(ReviewGateError) as wrong_head:
            require_full_receipt_for_gate_success(
                gate_success=True,
                full_receipt={**good, "headSha": "c" * 40},
                head_sha=HEAD,
                git_tree=TREE,
            )
        self.assertEqual(wrong_head.exception.code, "full_receipt_wrong_head")
        with self.assertRaises(ReviewGateError) as wrong_tree:
            require_full_receipt_for_gate_success(
                gate_success=True,
                full_receipt={**good, "gitTree": "d" * 40},
                head_sha=HEAD,
                git_tree=TREE,
            )
        self.assertEqual(wrong_tree.exception.code, "full_receipt_wrong_tree")
        with self.assertRaises(ReviewGateError) as stale:
            require_full_receipt_for_gate_success(
                gate_success=True,
                full_receipt={**good, "status": "failure"},
                head_sha=HEAD,
                git_tree=TREE,
            )
        self.assertEqual(stale.exception.code, "full_receipt_not_success")

    def test_infrastructure_attempts_count_only_infra_markers(self) -> None:
        markers = [
            infrastructure_attempt_marker(HEAD, 1),
            "ordinary classification note",
            founder_alert_marker(HEAD),
            infrastructure_attempt_marker(HEAD, 2),
            infrastructure_attempt_marker("c" * 40, 1),
        ]
        self.assertEqual(count_infrastructure_attempts(markers, head_sha=HEAD), 2)
        reject_third_infrastructure_attempt(MAX_INFRASTRUCTURE_ATTEMPTS)
        with self.assertRaises(ReviewGateError) as ctx:
            reject_third_infrastructure_attempt(MAX_INFRASTRUCTURE_ATTEMPTS + 1)
        self.assertEqual(ctx.exception.code, "infrastructure_attempt_limit")
        # Ordinary classifications with attempts=0 do not hit the infra limit.
        self.assertEqual(self._classify(infrastructure_attempts=0).outcome, OUTCOME_PASSED)
        with self.assertRaises(ReviewGateError):
            self._classify(
                provider_error=_verified_quota(),
                bugbot_conclusion="neutral",
                infrastructure_attempts=3,
            )

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

    def test_managed_surfaces_reject_raw_bugbot_required_defaults(self) -> None:
        wire = (ROOT / "scripts/wire-repo.sh").read_text()
        self.assertIn('BUGBOT_NAME="${BUGBOT_NAME:-Linktrend Review Gate}"', wire)
        self.assertIn('"bugbotProviderCheckName": "Cursor Bugbot"', wire)
        verify = (ROOT / "scripts/verify-ide-development.sh").read_text()
        self.assertIn('__LINKTREND_BUGBOT_PROVIDER_CHECK_NAME__", "Cursor Bugbot"', verify)
        self.assertIn('__LINKTREND_REVIEW_GATE_CHECK_NAME__", "Linktrend Review Gate"', verify)
        apply = (ROOT / "scripts/apply-development-merge-ruleset.sh").read_text()
        self.assertIn("Linktrend Review Gate", apply)
        self.assertNotIn('"Cursor Bugbot"', apply)
        self.assertNotIn("\n  \"Cursor Bugbot\"\n", apply)
        coord = (ROOT / "scripts/tests/test_local_coordinator_workflow_profile.sh").read_text()
        self.assertIn("Linktrend Review Gate", coord)
        self.assertNotIn('"bugbotCheckName": "Cursor Bugbot"', coord)
        observer = OBSERVER_TEMPLATE.read_text()
        self.assertIn("__LINKTREND_BUGBOT_PROVIDER_CHECK_NAME__", observer)
        self.assertIn("__LINKTREND_REVIEW_GATE_CHECK_NAME__", observer)
        self.assertIn(
            "github.event.check_run.name == '__LINKTREND_BUGBOT_PROVIDER_CHECK_NAME__'",
            observer,
        )
        bootstrap = (ROOT / "core/github/managed-runtime/cursor-gitops-bootstrap.mdc").read_text()
        self.assertIn("Linktrend Review Gate", bootstrap)
        external = (ROOT / "docs/contracts/EXTERNAL-STATE-AUDIT.md").read_text()
        self.assertIn("Linktrend Review Gate", external)
        self.assertNotIn("`Cursor Bugbot`", external)

    def test_workflow_forbids_heuristic_and_wires_alert_fallback_full(self) -> None:
        text = WORKFLOW.read_text()
        self.assertIn("Free-text provider heuristics are forbidden", text)
        self.assertNotIn("grep -Eq 'quota|rate limit", text)
        self.assertIn("founder-alert", text)
        self.assertIn("fallback", text)
        self.assertIn("require-full-receipt", text)
        self.assertIn("count-infra-attempts", text)
        self.assertIn("issues: write", text)
        self.assertIn("review-gate-provider-error.json", text)

    def test_durable_founder_alert_dedupe_and_fail_closed(self) -> None:
        advisory = self._classify(
            bugbot_conclusion="neutral",
            provider_error=_verified_quota(),
            infrastructure_attempts=1,
        )
        alert = build_durable_founder_alert(advisory)
        self.assertTrue(alert["required"])
        self.assertIn(founder_alert_marker(HEAD), alert["body"])
        self.assertTrue(
            founder_alert_already_recorded([alert["body"]], head_sha=HEAD)
        )
        self.assertFalse(founder_alert_already_recorded(["other"], head_sha=HEAD))
        passed = self._classify()
        with self.assertRaises(ReviewGateError):
            build_durable_founder_alert(passed)

    def test_undocumented_task_hold_rejected(self) -> None:
        reject_undocumented_task_hold(configured_gates_passed=True, task_hold=None)
        with self.assertRaises(ReviewGateError) as ctx:
            reject_undocumented_task_hold(configured_gates_passed=True, task_hold="extra review")
        self.assertEqual(ctx.exception.code, "undocumented_task_hold")

    def test_fallback_reviewer_rules_and_comment(self) -> None:
        ok = evaluate_fallback_review(
            outcome=OUTCOME_ADVISORY,
            independent_review_configured=True,
            reviewer_actor="reviewer-bot",
            implementer_actor="implementer-bot",
            evidence_head=HEAD,
            live_head=HEAD,
        )
        self.assertTrue(ok["requested"])
        comment = build_fallback_request_comment(fallback=ok, head_sha=HEAD)
        self.assertTrue(comment["posted"])
        self.assertIn("advisory-unavailable", comment["body"])
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

    def test_workflow_static_no_trailing_whitespace(self) -> None:
        for path in (WORKFLOW, MANAGED_WORKFLOW, MODULE, OBSERVER_TEMPLATE):
            for index, line in enumerate(path.read_text().splitlines(), 1):
                self.assertFalse(
                    line.endswith(" ") or line.endswith("\t"),
                    f"{path}:{index} has trailing whitespace",
                )


if __name__ == "__main__":
    unittest.main()
