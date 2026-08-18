"""Trusted Review Gate bootstrap tests (WP-U01 classifier + AC-U05-06/14 scope).

Runtime package blobs are exact copies from sealed product candidate
2f204781e093acad694b084e7c4ba0652fd17721. Surface-migration assertions that
require unrelated v2.4.0 product changes are skipped here; they remain on the
sealed candidate and must not be copied onto that candidate to make this gate
understand receipts.
"""

from __future__ import annotations

import json
import os
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
    comment_bodies_from_slurp,
    count_infrastructure_attempts,
    decide_founder_alert_publish,
    evaluate_fallback_review,
    evaluate_github_approval,
    flatten_gh_slurp_pages,
    founder_alert_already_recorded,
    founder_alert_marker,
    gate_commit_status,
    infrastructure_attempt_marker,
    invalidate_if_head_changed,
    issue_bodies_from_slurp,
    migrated_required_contexts,
    normalize_full_receipt_payload,
    reject_third_infrastructure_attempt,
    reject_undocumented_task_hold,
    require_full_receipt_for_gate_success,
    require_no_raw_bugbot_required,
    require_review_gate_on_development,
    simulate_repeated_founder_alert_events,
    structured_bugbot_findings_present,
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


# Bootstrap omits live ruleset/evaluator/observer product migrations (AC-U05-14).
_BOOTSTRAP_SKIP_SURFACES = (
    "bootstrap scope: deferred to sealed product candidate / later ruleset migration; "
    "do not copy verifier repair onto PR #326"
)


class LinktrendReviewGateTests(unittest.TestCase):
    def test_packaged_surfaces_exist(self) -> None:
        self.assertTrue(MODULE.is_file())
        self.assertTrue(SCHEMA.is_file())
        self.assertTrue(DOCTRINE.is_file())
        self.assertTrue(WORKFLOW.is_file())
        self.assertTrue(MANAGED_WORKFLOW.is_file())
        self.assertIn("needs: full", (ROOT / ".github/workflows/linktrend-integrator-merge.yml").read_text())
        # Default-branch trust boundary: live workflow == managed template bytes.
        live = WORKFLOW.read_text(encoding="utf-8")
        self.assertEqual(live, MANAGED_WORKFLOW.read_text(encoding="utf-8"))
        self.assertIn("on:\n  check_run:", live)
        self.assertIn("Linktrend Review Gate", live)
        self.assertIn("advisory_must_not_claim_bugbot_pass", live)
        self.assertIn("require-full-receipt", live)
        self.assertNotIn(".gitTree=$t", live)

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

        annotated = self._classify(annotations_count=2, bugbot_conclusion="success")
        self.assertEqual(annotated.outcome, OUTCOME_FINDINGS)
        self.assertFalse(annotated.gateSuccess)
        self.assertFalse(annotated.bugbotPassedClaim)

        action_required = self._classify(
            bugbot_state="completed",
            bugbot_conclusion="action_required",
        )
        self.assertEqual(action_required.outcome, OUTCOME_FINDINGS)
        self.assertFalse(action_required.gateSuccess)

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
        with self.assertRaises(ReviewGateError) as missing_tree:
            require_full_receipt_for_gate_success(
                gate_success=True,
                full_receipt={"name": FULL_SUITE_CONTEXT, "headSha": HEAD, "status": "success"},
                head_sha=HEAD,
                git_tree=TREE,
            )
        self.assertEqual(missing_tree.exception.code, "full_receipt_missing_tree")
        # FullSuiteReceipt v2 candidateIdentity.gitTreeSha is preserved.
        v2 = {
            "name": FULL_SUITE_CONTEXT,
            "candidateIdentity": {"sourceSha": HEAD, "gitTreeSha": TREE},
            "conclusion": "success",
        }
        require_full_receipt_for_gate_success(
            gate_success=True, full_receipt=v2, head_sha=HEAD, git_tree=TREE
        )

    def test_normalize_full_receipt_never_injects_live_tree(self) -> None:
        raw = {
            "name": FULL_SUITE_CONTEXT,
            "headSha": HEAD,
            "status": "success",
            "outputSummary": f"head={HEAD}\ngitTreeSha={'d' * 40}\n",
        }
        normalized = normalize_full_receipt_payload(raw)
        assert normalized is not None
        self.assertEqual(normalized["gitTree"], "d" * 40)
        self.assertNotEqual(normalized["gitTree"], TREE)
        # Empty receipt stays empty — callers must not fill from live TREE.
        empty = normalize_full_receipt_payload(
            {"name": FULL_SUITE_CONTEXT, "headSha": HEAD, "status": "success"}
        )
        assert empty is not None
        self.assertEqual(empty["gitTree"], "")

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

    @unittest.skip(_BOOTSTRAP_SKIP_SURFACES)
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

    @unittest.skip(_BOOTSTRAP_SKIP_SURFACES)
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
        self.assertNotIn("named gates + Cursor Bugbot", bootstrap)
        cursor_bootstrap = (ROOT / ".cursor/rules/cursor-gitops-bootstrap.mdc").read_text()
        self.assertIn("named gates + Linktrend Review Gate", cursor_bootstrap)
        self.assertNotIn("named gates + Cursor Bugbot", cursor_bootstrap)
        external = (ROOT / "docs/contracts/EXTERNAL-STATE-AUDIT.md").read_text()
        self.assertIn("Linktrend Review Gate", external)
        self.assertNotIn("`Cursor Bugbot`", external)
        for rel in (
            "scripts/tests/test-consumer-profile-matrix.sh",
            "scripts/tests/test_local_coordinator_workflow_profile.sh",
            "scripts/tests/test-managed-runner-routing.sh",
        ):
            text = (ROOT / rel).read_text()
            self.assertIn("bugbotProviderCheckName", text)
            self.assertRegex(
                text,
                r'"bugbotProviderCheckName"\s*:\s*"Cursor Bugbot"',
            )
            self.assertNotRegex(
                text,
                r'"bugbotProviderCheckName"\s*:\s*"Linktrend Review Gate"',
            )

    def test_workflow_forbids_heuristic_and_wires_alert_fallback_full(self) -> None:
        for path in (WORKFLOW, MANAGED_WORKFLOW):
            text = path.read_text()
            self.assertIn("Free-text provider heuristics are forbidden", text)
            self.assertNotIn("grep -Eq 'quota|rate limit", text)
            self.assertIn("founder-alert", text)
            self.assertIn("founder-alert-dedupe", text)
            self.assertIn("fallback", text)
            self.assertIn("require-full-receipt", text)
            self.assertIn("normalize-full-receipt", text)
            self.assertIn("count-infra-attempts", text)
            self.assertIn("issues: write", text)
            self.assertIn("review-gate-provider-error.json", text)
            # U01-R3: never overwrite receipt tree with live TREE.
            self.assertNotIn(".gitTree=$t", text)
            self.assertNotIn("gitTree:$t", text)
            self.assertIn("never overwrite with live TREE", text)
            # U01-R2: dedupe from issue bodies with fail-closed read.
            self.assertIn("flatten-issue-bodies", text)
            self.assertIn("founder_alert_dedupe_unreadable", text)
            self.assertIn("--paginate --slurp", text)
            # Slurp payloads must enter via stdin, never argv interpolation.
            self.assertIn("--slurp-json -", text)
            self.assertIn("--issue-bodies-json -", text)
            self.assertIn("--markers-json -", text)
            self.assertNotIn('--slurp-json "${', text)
            self.assertNotIn("--slurp-json \"${", text)
            self.assertNotIn("MARKERS_SLURP", text)
            self.assertNotIn("ALERT_SLURP", text)
            # Marker reads must not fail-open to empty arrays.
            self.assertNotIn("2>/dev/null || echo '[]'", text)
            self.assertNotIn("|| echo '[]'", text)
            self.assertIn("flatten-comment-bodies", text)
            self.assertIn("HOLD: infra_marker_read_failed", text)
            self.assertIn("set -euo pipefail", text)
            # Trust boundary: default-branch scripts; candidate is data only.
            self.assertIn("github.event.repository.default_branch", text)
            self.assertIn("Checkout trusted default branch (scripts only)", text)
            self.assertNotIn("ref: ${{ github.event.check_run.head_sha }}", text)
            self.assertNotIn("CHECK_DETAILS", text)
            self.assertIn("CHECK_ANNOTATIONS_COUNT", text)
            self.assertIn("--annotations-count", text)
            self.assertIn("python3 scripts/gitops/linktrend_review_gate.py", text)
            self.assertIn("contents/.linktrend/review-gate-provider-error.json?ref=", text)
            self.assertIn("statuses: write", text)
            # U01-R4: infra marker publication is fail-closed.
            self.assertIn("infra_attempt_marker_persist_failed", text)
            self.assertNotIn('-f body="${INFRA_MARKER}" >/dev/null || true', text)

    def test_pr_cannot_rewrite_classifier_or_self_approve(self) -> None:
        """Negative: PR head must not supply executable classifier scripts."""
        live = WORKFLOW.read_text(encoding="utf-8")
        managed = MANAGED_WORKFLOW.read_text(encoding="utf-8")
        self.assertEqual(live, managed)
        for text in (live, managed):
            self.assertIn("ref: ${{ github.event.repository.default_branch }}", text)
            self.assertNotIn("ref: ${{ github.event.check_run.head_sha }}", text)
            self.assertNotIn("ref: ${{ github.event.pull_request.head.sha }}", text)
            self.assertNotIn("untrusted-source-data/scripts", text)
            # Scripts execute from trusted checkout root only.
            self.assertIn("python3 scripts/gitops/linktrend_review_gate.py classify", text)
            # Free-text Bugbot check summaries must not drive classification.
            self.assertNotIn("CHECK_DETAILS", text)
            self.assertNotIn("github.event.check_run.output.summary", text)
            self.assertNotIn("check_run.output.summary", text)

        # Missing / neutral / free-text provider hints never become pass.
        self.assertEqual(self._classify(missing=True).outcome, OUTCOME_UNKNOWN)
        self.assertFalse(self._classify(missing=True).gateSuccess)
        neutral = self._classify(bugbot_conclusion="neutral")
        self.assertEqual(neutral.outcome, OUTCOME_UNKNOWN)
        self.assertFalse(neutral.gateSuccess)
        heuristic = self._classify(
            bugbot_state="completed",
            bugbot_conclusion="success",
            provider_error={
                "verified": False,
                "class": "quota",
                "source": "candidate-free-text-says-clean",
            },
        )
        # Unverified provider error is ignored; clean success remains success.
        self.assertEqual(heuristic.outcome, OUTCOME_PASSED)
        # Candidate prose / untrusted source cannot force advisory success:
        forged_advisory = self._classify(
            bugbot_state="completed",
            bugbot_conclusion="neutral",
            provider_error={
                "verified": True,
                "class": "quota",
                "source": "grep-heuristic",
            },
        )
        self.assertEqual(forged_advisory.outcome, OUTCOME_UNKNOWN)
        self.assertFalse(forged_advisory.gateSuccess)

        # Structured annotations force review-findings even if conclusion looks clean.
        self.assertTrue(structured_bugbot_findings_present(annotations_count=1))
        self.assertFalse(structured_bugbot_findings_present(annotations_count=0))
        self.assertFalse(structured_bugbot_findings_present(annotations_count=None))
        blocked = self._classify(annotations_count=1, bugbot_conclusion="success")
        self.assertEqual(blocked.outcome, OUTCOME_FINDINGS)
        self.assertFalse(blocked.gateSuccess)
        self.assertFalse(blocked.bugbotPassedClaim)

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
        # Issue-body dedupe decision path.
        first = decide_founder_alert_publish(
            alert_required=True,
            issue_bodies=[],
            bodies_readable=True,
            head_sha=HEAD,
        )
        self.assertTrue(first["publish"])
        second = decide_founder_alert_publish(
            alert_required=True,
            issue_bodies=[alert["body"]],
            bodies_readable=True,
            head_sha=HEAD,
        )
        self.assertFalse(second["publish"])
        self.assertEqual(second["reason"], "already_recorded")
        with self.assertRaises(ReviewGateError) as unreadable:
            decide_founder_alert_publish(
                alert_required=True,
                issue_bodies=None,
                bodies_readable=False,
                head_sha=HEAD,
            )
        self.assertEqual(unreadable.exception.code, "founder_alert_dedupe_unreadable")
        # Repeated workflow events create exactly one durable alert.
        repeated = simulate_repeated_founder_alert_events(alert_required=True, head_sha=HEAD)
        self.assertEqual(repeated["created"], 1)
        passed = self._classify()
        with self.assertRaises(ReviewGateError):
            build_durable_founder_alert(passed)

    def test_workflow_path_wrong_tree_receipt_negative(self) -> None:
        """Adversarial: receipt tree differs from live TREE and must fail closed."""
        receipt = {
            "name": FULL_SUITE_CONTEXT,
            "headSha": HEAD,
            "gitTree": "d" * 40,
            "status": "success",
        }
        # Simulate the fixed workflow: normalize without injecting live TREE.
        normalized = normalize_full_receipt_payload(receipt)
        assert normalized is not None
        self.assertEqual(normalized["gitTree"], "d" * 40)
        with self.assertRaises(ReviewGateError) as ctx:
            require_full_receipt_for_gate_success(
                gate_success=True,
                full_receipt=normalized,
                head_sha=HEAD,
                git_tree=TREE,
            )
        self.assertEqual(ctx.exception.code, "full_receipt_wrong_tree")
        # Old buggy overwrite path would have masked this — prove inject is absent.
        self.assertNotIn('.gitTree=$t', WORKFLOW.read_text())

    def test_paginated_slurp_flatten_multi_page_bodies_and_dedupe(self) -> None:
        """Two+ pages must flatten to one JSON list; alert/marker counts stay exact."""
        marker = founder_alert_marker(HEAD)
        infra1 = infrastructure_attempt_marker(HEAD, 1)
        infra2 = infrastructure_attempt_marker(HEAD, 2)
        # Empty / single / multi-page deterministic flatten.
        self.assertEqual(flatten_gh_slurp_pages([]), [])
        self.assertEqual(
            comment_bodies_from_slurp([[{"body": infra1}]]),
            [infra1],
        )
        two_pages = [
            [{"body": infra1}, {"body": "noise"}],
            [{"body": infra2}, {"body": marker + "\nalert body"}],
        ]
        bodies = comment_bodies_from_slurp(two_pages)
        self.assertEqual(len(bodies), 4)
        self.assertEqual(count_infrastructure_attempts(bodies, head_sha=HEAD), 2)
        # Issue pages skip pull_request entries and flatten across pages.
        issue_pages = [
            [
                {"body": "pr body", "pull_request": {"url": "https://example/pr/1"}},
                {"body": "other issue"},
            ],
            [{"body": f"{marker}\nfounder alert page 2"}],
        ]
        issue_bodies = issue_bodies_from_slurp(issue_pages)
        self.assertEqual(issue_bodies, ["other issue", f"{marker}\nfounder alert page 2"])
        decision = decide_founder_alert_publish(
            alert_required=True,
            issue_bodies=issue_bodies,
            bodies_readable=True,
            head_sha=HEAD,
        )
        self.assertFalse(decision["publish"])
        self.assertEqual(decision["reason"], "already_recorded")
        # Malformed slurp / fail-open equivalent must fail closed (not become []).
        with self.assertRaises(ReviewGateError) as bad:
            flatten_gh_slurp_pages("not-json")
        self.assertEqual(bad.exception.code, "paginated_response_invalid")
        with self.assertRaises(ReviewGateError):
            flatten_gh_slurp_pages([{"not": "a page list"}])
        # Simulate two workflow events after multi-page prior bodies → one alert.
        repeated = simulate_repeated_founder_alert_events(
            alert_required=True,
            head_sha=HEAD,
            prior_issue_bodies=["unrelated"],
        )
        self.assertEqual(repeated["created"], 1)

    def test_slurp_json_stdin_handles_arg_max_and_pipefail_hold(self) -> None:
        """Workflow path: stdin --slurp-json - survives ARG_MAX; upstream fail stays HOLD."""
        marker = founder_alert_marker(HEAD)
        infra1 = infrastructure_attempt_marker(HEAD, 1)
        # Empty / one / multi-page via stdin CLI.
        for pages, expected_len in (
            ([], 0),
            ([[{"body": infra1}]], 1),
            ([[{"body": infra1}], [{"body": infrastructure_attempt_marker(HEAD, 2)}]], 2),
        ):
            proc = subprocess.run(
                [sys.executable, str(MODULE), "flatten-comment-bodies", "--slurp-json", "-"],
                input=json.dumps(pages),
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(proc.returncode, 0, proc.stderr)
            bodies = json.loads(proc.stdout)
            self.assertEqual(len(bodies), expected_len)
            if expected_len:
                self.assertEqual(
                    count_infrastructure_attempts(bodies, head_sha=HEAD),
                    expected_len,
                )

        # Payload larger than ARG_MAX must succeed via stdin and fail via argv.
        try:
            arg_max = int(os.sysconf("SC_ARG_MAX"))
        except (AttributeError, ValueError, OSError):
            arg_max = 131072
        # Keep well above ARG_MAX while staying tractable for unit runtime.
        target = max(arg_max + 4096, 300_000)
        chunk = "x" * 4000
        page: list[dict[str, str]] = []
        size = 2  # rough JSON overhead
        while size < target:
            page.append({"body": chunk})
            size += len(chunk) + 20
        pages = [page, [{"body": marker + "\npage2"}]]
        payload = json.dumps(pages)
        self.assertGreater(len(payload), arg_max)

        stdin_proc = subprocess.run(
            [sys.executable, str(MODULE), "flatten-issue-bodies", "--slurp-json", "-"],
            input=payload,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(stdin_proc.returncode, 0, stdin_proc.stderr)
        issue_bodies = json.loads(stdin_proc.stdout)
        self.assertTrue(any(marker in body for body in issue_bodies))
        decision = decide_founder_alert_publish(
            alert_required=True,
            issue_bodies=issue_bodies,
            bodies_readable=True,
            head_sha=HEAD,
        )
        self.assertFalse(decision["publish"])

        argv_failed = False
        try:
            argv_proc = subprocess.run(
                [sys.executable, str(MODULE), "flatten-issue-bodies", "--slurp-json", payload],
                text=True,
                capture_output=True,
                check=False,
            )
            argv_failed = argv_proc.returncode != 0
        except OSError:
            argv_failed = True
        self.assertTrue(argv_failed)

        # Upstream read failure must not be masked when pipefail is set.
        hold_script = r"""
set -euo pipefail
if ! (
  false \
    | python3 scripts/gitops/linktrend_review_gate.py flatten-comment-bodies --slurp-json -
); then
  echo "HOLD: infra_marker_read_failed"
  exit 1
fi
"""
        hold = subprocess.run(
            ["bash", "-lc", hold_script],
            cwd=str(ROOT),
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(hold.returncode, 1)
        self.assertIn("HOLD: infra_marker_read_failed", hold.stdout + hold.stderr)

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

    @unittest.skip(_BOOTSTRAP_SKIP_SURFACES)
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
        # Observer template is present on development but not migrated in this
        # bootstrap; still enforce no trailing whitespace on gate surfaces.
        for path in (WORKFLOW, MANAGED_WORKFLOW, MODULE):
            for index, line in enumerate(path.read_text().splitlines(), 1):
                self.assertFalse(
                    line.endswith(" ") or line.endswith("\t"),
                    f"{path}:{index} has trailing whitespace",
                )


if __name__ == "__main__":
    unittest.main()
