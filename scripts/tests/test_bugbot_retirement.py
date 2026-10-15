"""No-Bugbot policy and owned-native-review trust-boundary regressions.

Native execution is mocked here. Passing tests do not claim provider execution
or effective model attestation; a real independent smoke remains separate.
"""
from __future__ import annotations

import copy
import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts.gitops import independent_review_convergence as native
from scripts.gitops import delivery_controller as controller
from scripts.gitops import packager_evaluate, packager_logic, phase_integrator, write_outcome
from scripts.gitops.bugbot_user_credentials import BugbotUserCredentialsError, require_bugbot_user_token
from scripts.gitops.coordinator.config import load_delivery_config
from scripts.gitops.promotion_receipt_gate import evaluate_development_gates
from scripts.gitops.repair_observer import ObserverConfig, _check_event

ROOT = Path(__file__).resolve().parents[2]
HEAD = "a" * 40
TREE = "b" * 40


def trusted_fixture(head=HEAD, tree=TREE, repository="owner/name"):
    # Independently held fixture bytes, never a callback taken from JSON.
    report = {"accepted": True, "headSha": head, "gitTree": tree, "repository": repository,
              "paths": ["app.py"], "findings": [], "reportText": "Independent exact-candidate inspection is clean.",
              "reviewerActor": "fresh-native-thread", "implementerActor": "caller-thread",
              "provenance": {"receiptId": "fresh-native-thread", "producer": "owned-native-codex-process"}}
    encoded = native.canonical_review_bytes(report)
    expected = native.review_binding(report, repository=repository, head_sha=head, git_tree=tree)
    def verifier(*, report_bytes, binding):
        return report_bytes == encoded and binding == expected
    return report, verifier


class BugbotRetirementTests(unittest.TestCase):
    def test_canonical_disabled_and_legacy_migration_cannot_enable_bot(self):
        payload = json.loads((ROOT / ".github/linktrend-delivery-mode.json").read_text())
        self.assertEqual(load_delivery_config(payload).review.bugbot, "disabled")
        payload["review"]["bugbot"] = "final-candidate-only"
        migrated = load_delivery_config(payload)
        self.assertEqual(migrated.to_dict()["review"], {"bugbot": "disabled"})
        self.assertEqual(migrated.profiles["full"].commands, load_delivery_config(ROOT).profiles["full"].commands)
        for value in ("always", "enabled", True, None):
            payload["review"]["bugbot"] = value
            with self.assertRaises(ValueError):
                load_delivery_config(payload)

    def test_canonical_schema_preserves_complete_receipt_identity(self):
        from jsonschema import Draft202012Validator
        schema = json.loads((ROOT / "core/managed-core/schemas/delivery-modes.schema.json").read_text())
        payload = json.loads((ROOT / ".github/linktrend-delivery-mode.json").read_text())
        validator = Draft202012Validator(schema)
        self.assertEqual(list(validator.iter_errors(payload)), [])
        payload["promotion"]["identity"].remove("headCommit")
        self.assertTrue(list(validator.iter_errors(payload)))

    def test_all_legacy_request_routes_fail_closed_without_io(self):
        for green in (False, True):
            self.assertEqual(packager_logic.should_request_bugbot(comments=[], head_sha=HEAD, fast_gate_ok=green), (False, "bugbot_disabled"))
        with self.assertRaisesRegex(ValueError, "bugbot_disabled"):
            packager_logic.build_bugbot_comment("@cursor review", HEAD)
        with self.assertRaises(BugbotUserCredentialsError):
            require_bugbot_user_token("bugbot_comment")
        self.assertEqual(phase_integrator.phase_bugbot_request_allowed({}, live_head_sha=HEAD), (False, "bugbot_disabled"))
        with patch("subprocess.run", side_effect=AssertionError("unexpected external call")), patch("subprocess.check_output", side_effect=AssertionError("unexpected external call")):
            self.assertEqual(packager_evaluate.evaluate_pr(7, "unused")["status"], "blocked")
            self.assertEqual(_check_event({"check_run": {"name": "Cursor Bugbot", "conclusion": "success"}}, "owner/name", ObserverConfig())["reason"], "bugbot_disabled")
        self.assertIsNone(write_outcome.commit_status_state("bugbot_requested"))

    def test_workflows_never_request_or_publish_bot_success(self):
        for folder in (ROOT / ".github/workflows", ROOT / "core/github/managed-workflows"):
            for path in folder.glob("*.yml"):
                text = path.read_text()
                self.assertNotIn("@cursor review", text, path)
                self.assertNotIn("bugbot run", text.lower(), path)
            retired = (folder / "linktrend-review-gate.yml").read_text()
            self.assertNotIn("check_run:", retired)
            self.assertNotIn("statuses: write", retired)
            self.assertNotIn("pull-requests: write", retired)
            self.assertIn("exit 1", retired)
            observer = (folder / "linktrend-repair-observer.yml").read_text()
            self.assertNotIn("check_run:", observer)

    def test_disabled_bot_cannot_replace_real_gates_or_independent_review(self):
        report, verifier = trusted_fixture()
        good = {"status": "passed", "sha": HEAD}
        gates = {"seal": good, "fast": good, "full": good, "independentNarrowReview": report}
        def check(value, producer=verifier):
            return evaluate_development_gates(value, HEAD, expected_git_tree=TREE, repository="owner/name", trusted_review_verifier=producer)
        self.assertTrue(check(gates).accepted)
        for gate in ("seal", "fast", "full"):
            for mutation in ({"status": "failed", "sha": HEAD}, {"status": "passed", "sha": "c" * 40}, None):
                changed = dict(gates)
                if mutation is None: changed.pop(gate)
                else: changed[gate] = mutation
                self.assertFalse(check(changed).accepted, (gate, mutation))
        no_review = {k:v for k,v in gates.items() if k != "independentNarrowReview"}
        no_review["bugbot"] = {"status": "passed", "sha": HEAD}
        self.assertFalse(check(no_review).accepted)
        self.assertFalse(check(gates, None).accepted)
        for key, value in (("headSha", "c" * 40), ("gitTree", "c" * 40), ("reviewerActor", "caller-thread"), ("reportText", "changed"), ("findings", [{"severity": "P1"}])):
            changed = copy.deepcopy(gates); changed["independentNarrowReview"][key] = value
            self.assertFalse(check(changed).accepted, key)


class OwnedNativeReviewerTests(unittest.TestCase):
    def setUp(self):
        self.api_before = self._metadata()
        self.api_after = None
        self.pr_reads = 0
        transport = patch.object(controller, "_github_api", side_effect=self._transport)
        auth = patch.object(controller, "resolve_phase_api_token", return_value=("fixture-phase-api", "GH_TOKEN"))
        transport.start(); auth.start()
        self.addCleanup(transport.stop); self.addCleanup(auth.stop)

    def _metadata(self, **changes):
        value = {"headSha": HEAD, "gitTree": TREE, "baseCommit": "c"*40,
                 "branchCommit": "c"*40, "protected": True,
                 "headRepository": "owner/name", "baseRepository": "owner/name",
                 "headBranch": "phase/demo", "baseBranch": "development"}
        value.update(changes)
        return value

    def _transport(self, method, url, token, body=None):
        self.assertEqual(method, "GET")
        self.assertIsNone(body)
        if url.endswith("/pulls/7"):
            self.pr_reads += 1
        current = self.api_after if self.pr_reads > 1 and self.api_after is not None else self.api_before
        if url.endswith("/pulls/7"):
            return {"number":7, "state":"open", "merged":False,
                    "head":{"sha":current["headSha"], "ref":current["headBranch"], "repo":{"full_name":current["headRepository"]}},
                    "base":{"sha":current["baseCommit"], "ref":current["baseBranch"], "repo":{"full_name":current["baseRepository"]}}}
        if url.endswith("/branches/development"):
            return {"name":"development", "protected":current["protected"], "commit":{"sha":current["branchCommit"]}}
        if "/git/commits/" in url:
            return {"sha":current["headSha"], "tree":{"sha":current["gitTree"]}}
        raise AssertionError("unexpected metadata endpoint: " + url)

    def _execute(self, *, stdout=None, returncode=0, dirty_after=False, adapter=None,
                 baseline_sha="c"*40, api_before=None, api_after=None, ancestor=True, report_paths=None):
        adapter = adapter or native.NativeReviewerAdapter()
        self.api_before = api_before or self._metadata()
        self.api_after = api_after
        self.pr_reads = 0
        report = {"accepted": True, "headSha": HEAD, "gitTree": TREE,
                  "paths": report_paths if report_paths is not None else ["first.txt", "second.txt"],
                  "findings": [], "reportText": "Reviewed the exact diff and its proof."}
        events = [{"type":"thread.started", "thread_id":"fresh-thread"}, {"type":"turn.started"},
                  {"type":"item.completed", "item":{"type":"agent_message", "text":json.dumps(report)}}, {"type":"turn.completed"}]
        stdout = stdout if stdout is not None else "\n".join(json.dumps(e) for e in events)
        status_reads = 0
        self.git_calls = []
        def git(argv, **kwargs):
            nonlocal status_reads
            self.git_calls.append(argv)
            operation=argv[1:]
            if operation == ["rev-parse","HEAD"]: return HEAD
            if operation == ["rev-parse","HEAD^{tree}"]: return TREE
            if operation == ["status","--porcelain"]:
                status_reads += 1
                return " M app.py" if dirty_after and status_reads > 1 else ""
            if operation[:2] == ["merge-base","--is-ancestor"]:
                if not ancestor: raise subprocess.CalledProcessError(1, argv)
                return ""
            if operation[:1] == ["diff"]:
                self.assertEqual(operation[-2:], [self.api_before["baseCommit"],HEAD])
                return "first.txt\nsecond.txt"
            raise AssertionError(argv)
        with patch.dict(os.environ, {"CODEX_THREAD_ID":"actual-caller"}), patch.object(Path, "is_file", return_value=True), patch.object(native.subprocess, "check_output", side_effect=git), patch.object(native.subprocess, "run", return_value=subprocess.CompletedProcess([],returncode,stdout,"")) as runner:
            try:
                result = adapter.review(workdir=ROOT, repository="owner/name", head_sha=HEAD, git_tree=TREE,
                                        baseline_sha=baseline_sha, pr_number=7, implementer_run_id="actual-caller")
            finally:
                self.last_native_calls = runner.call_count
            argv = runner.call_args.args[0]
            self.assertEqual(argv[0], native.EXPECTED_NATIVE_CODEX)
            self.assertIn('approval_policy="never"', argv)
            self.assertIn('sandbox_mode="read-only"', argv)
            self.assertNotIn("resume", argv)
        return adapter, result

    def test_fresh_owned_runtime_output_can_verify_only_in_original_adapter(self):
        adapter, result = self._execute()
        with self.assertRaisesRegex(ValueError, "not_independent"):
            self._execute(adapter=adapter)
        args=dict(repository="owner/name",head_sha=HEAD,git_tree=TREE)
        self.assertTrue(native.validate_candidate_review(result,verifier=adapter.verify_report,**args)[0])
        self.assertFalse(native.validate_candidate_review(result,verifier=native.NativeReviewerAdapter().verify_report,**args)[0])
        changed=dict(result,reportText="replayed altered report")
        self.assertFalse(native.validate_candidate_review(changed,verifier=adapter.verify_report,**args)[0])

    def test_owned_base_scope_cannot_be_truncated_or_replaced_by_caller(self):
        for supplied_base in ("d"*40, "e"*40, HEAD):
            with self.subTest(base=supplied_base), self.assertRaisesRegex(ValueError, "claimed_base_mismatch"):
                self._execute(baseline_sha=supplied_base)
            self.assertEqual(self.last_native_calls, 0)
            self.assertFalse(any(call[1] == "diff" for call in self.git_calls))
        with self.assertRaisesRegex(ValueError, "output_not_candidate_bound"):
            self._execute(report_paths=["second.txt"])
        with self.assertRaisesRegex(ValueError, "base_ancestry_unproven"):
            self._execute(ancestor=False)
        self.assertEqual(self.last_native_calls, 0)

    def test_stale_unprotected_wrong_repository_and_wrong_target_metadata_fail(self):
        for mutation, reason in (
            ({"branchCommit":"d"*40}, "base_stale"), ({"protected":False}, "base_unprotected"),
            ({"headRepository":"fork/name"}, "repository_mismatch"),
            ({"baseRepository":"fork/name"}, "repository_mismatch"),
            ({"baseBranch":"staging"}, "target_invalid"),
            ({"headSha":"d"*40}, "remote_candidate_mismatch"),
            ({"gitTree":"e"*40}, "remote_candidate_mismatch"),
        ):
            with self.subTest(mutation=mutation), self.assertRaisesRegex((ValueError,controller.ControllerError), reason):
                self._execute(api_before=self._metadata(**mutation))
            self.assertEqual(self.last_native_calls, 0)

    def test_base_head_tree_or_branch_changes_during_review_invalidate_report(self):
        for mutation in (
            {"baseCommit":"d"*40,"branchCommit":"d"*40}, {"headSha":"e"*40},
            {"gitTree":"e"*40}, {"headBranch":"phase/moved"},
        ):
            with self.subTest(mutation=mutation), self.assertRaisesRegex(ValueError, "remote_scope_changed"):
                self._execute(api_after=self._metadata(**mutation))
        adapter, report = self._execute()
        self.api_after = self._metadata(baseCommit="d"*40, branchCommit="d"*40)
        self.assertFalse(native.validate_candidate_review(report,repository="owner/name",head_sha=HEAD,git_tree=TREE,verifier=adapter.verify_report)[0])

    def test_failed_turn_missing_protocol_wrong_head_replay_and_changed_checkout_fail(self):
        adapter, valid = self._execute()
        report = {k:v for k,v in valid.items() if k not in {"provenance","repository","reviewerActor","implementerActor"}}
        def events(thread="fresh", final="turn.completed", head=HEAD, start=True):
            raw=[{"type":"thread.started","thread_id":thread}]
            if start: raw.append({"type":"turn.started"})
            raw.extend([{"type":"item.completed","item":{"type":"agent_message","text":json.dumps(dict(report,headSha=head))}},{"type":final}])
            return "\n".join(json.dumps(e) for e in raw)
        for options in ({"returncode":1},{"dirty_after":True},{"stdout":events(thread="actual-caller")},{"stdout":events(final="turn.failed")},{"stdout":events(head="d"*40)},{"stdout":events(start=False)},{"stdout":"{}"}):
            with self.subTest(options=options), self.assertRaises((ValueError,TypeError,KeyError)):
                self._execute(**options)
        with patch.object(native,"NATIVE_CODEX",Path("/tmp/untrusted-reviewer")), self.assertRaisesRegex(ValueError,"runtime_unavailable"):
            self._execute()


if __name__ == "__main__":
    unittest.main()
