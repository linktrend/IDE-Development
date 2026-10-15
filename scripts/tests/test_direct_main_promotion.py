"""Direct Program promotion must preserve exact authority and receipt fences."""
from __future__ import annotations

import copy
import json
import re
import subprocess
import unittest
from pathlib import Path

from scripts.gitops import delivery_controller as controller
from scripts.gitops import main_approve_package_reuse as reuse
from scripts.tests.test_delivery_controller import _sha, _identity, _receipt
from scripts.gitops.coordinator.receipts import compute_receipt_digest

ROOT = Path(__file__).resolve().parents[2]


class DirectMainTests(unittest.TestCase):
    def setUp(self):
        self.head, self.tree, self.base = _sha(1), _sha(2), _sha(6)
        self.github = controller.MemoryGitHub(repository="owner/name")
        self.github.refs = {"development": self.head, "main": self.base, "staging": _sha(7)}
        self.github.commit_trees[self.head] = self.tree
        self.identity = _identity(head=self.head, tree=self.tree)
        self.receipt = _receipt(self.identity)
        self.prepare = dict(github=self.github, repository="owner/name", development_sha=self.head,
                            main_sha=self.base, candidate_sha=self.head, receipt=self.receipt,
                            candidate_identity=self.identity, role="program-lead",
                            release_gate={"status": "passed", "testProfile": "release"})

    def _package(self):
        result = controller.prepare_main_promotion(**self.prepare)
        self.complete = dict(github=self.github, repository="owner/name", pr_number=result["pr"],
                             expected_head=self.head, source_sha=self.head, base_sha=self.base,
                             approval={"decision": "approve", "sourceSha": self.head,
                                       "baseSha": self.base, "prHeadSha": self.head,
                                       "receiptDigest": compute_receipt_digest(self.receipt)},
                             receipt=self.receipt, role="program-lead")
        return result

    def test_roles_do_not_default_or_accept_unknown_or_worker(self):
        for role in ("", "unknown", "worker", "implementer", "operator", "coordinator"):
            with self.subTest(role=role), self.assertRaises(controller.ControllerError):
                controller.prepare_main_promotion(**{**self.prepare, "role": role})
        self.assertEqual(self.github.prs, {})
        self.assertEqual(self.github.merges, [])

    def test_packaging_rejects_stale_source_or_target_before_writes(self):
        for branch, code in (("development", "stale_development_source"), ("main", "stale_main_target")):
            original = self.github.refs[branch]
            self.github.refs[branch] = _sha(20)
            with self.subTest(branch=branch), self.assertRaisesRegex(controller.ControllerError, code):
                controller.prepare_main_promotion(**self.prepare)
            self.github.refs[branch] = original
        self.assertEqual(self.github.prs, {})

    def test_changed_receipt_tree_remains_rejected(self):
        other = _identity(head=self.head, tree=_sha(20))
        with self.assertRaisesRegex(controller.ControllerError, "candidate_identity_mismatch"):
            controller.prepare_main_promotion(**{**self.prepare, "candidate_identity": other})
        self.assertEqual(self.github.prs, {})

    def test_approval_cannot_reuse_advanced_source_or_target(self):
        self._package()
        for branch, code in (("development", "stale_development_source"), ("main", "stale_main_target")):
            original = self.github.refs[branch]
            self.github.refs[branch] = _sha(20)
            with self.subTest(branch=branch), self.assertRaisesRegex(controller.ControllerError, code):
                controller.complete_main_promotion(**self.complete)
            self.github.refs[branch] = original
        self.assertEqual(self.github.merges, [])

    def test_approval_cannot_change_source_marker_receipt_or_target(self):
        result = self._package()
        pr = self.github.prs[result["pr"]]
        original = copy.deepcopy(pr)
        for key, value in (("sourceBranch", "staging"), ("sourceSha", _sha(20)),
                           ("targetSha", _sha(20)), ("candidateHead", _sha(20)),
                           ("receiptDigest", "sha256:" + "0" * 64)):
            marker = json.loads(re.search(r"<!-- linktrend-promote:\s*(\{.*?\})\s*-->", original["body"]).group(1))
            marker[key] = value
            pr["body"] = "<!-- linktrend-promote: " + json.dumps(marker) + " -->"
            with self.subTest(key=key), self.assertRaisesRegex(controller.ControllerError, "main_promotion_marker_mismatch"):
                controller.complete_main_promotion(**self.complete)
        self.assertEqual(self.github.merges, [])

    def test_no_cross_repo_wrong_base_draft_or_closed_main_pr(self):
        result = self._package()
        original = copy.deepcopy(self.github.prs[result["pr"]])
        for key, value in (("crossRepository", True), ("base", "staging"),
                           ("head", "phase/foreign"), ("isDraft", True), ("state", "closed")):
            self.github.prs[result["pr"]] = {**original, key: value}
            with self.subTest(key=key), self.assertRaises(controller.ControllerError):
                controller.complete_main_promotion(**self.complete)
        self.assertEqual(self.github.merges, [])

    def test_exact_approval_normal_protected_merge_preserves_staging(self):
        self._package()
        staging = self.github.refs["staging"]
        result = controller.complete_main_promotion(**self.complete)
        self.assertEqual(result["status"], "merged")
        self.assertFalse(self.github.merges[-1]["admin"])
        self.assertEqual(self.github.refs["staging"], staging)
        self.assertEqual(self.github.deleted_refs, [])
        self.assertEqual(self.github.protected_push_attempts, [])

    def test_reuse_rejects_old_staging_marker(self):
        self._package()
        marker = json.loads(re.search(r"<!-- linktrend-promote:\s*(\{.*?\})\s*-->", self.github.prs[1]["body"]).group(1))
        self.assertIsNotNone(reuse.parse_marker("<!-- linktrend-promote: " + json.dumps(marker) + " -->")[0])
        marker["sourceBranch"] = "staging"
        self.assertEqual(reuse.parse_marker("<!-- linktrend-promote: " + json.dumps(marker) + " -->")[1], "marker_source_branch_not_development")

    def test_retained_shell_fails_before_any_tool_or_credential(self):
        completed = subprocess.run(["/bin/bash", str(ROOT / "scripts/gitops/promote_staging.sh")],
                                   cwd="/tmp", env={"PATH": "/nonexistent"}, capture_output=True, text=True)
        self.assertEqual(completed.returncode, 1)
        self.assertIn("staging promotion disabled", completed.stderr)

    def test_shell_main_requires_designated_lease_before_tools(self):
        result = subprocess.run(["/bin/bash", str(ROOT / "scripts/gitops/promote_main.sh")],
                                cwd="/tmp", env={"PATH": "/nonexistent"}, capture_output=True, text=True)
        self.assertEqual(result.returncode, 1)
        self.assertIn("designated Program lead role required", result.stderr)

    def test_branch_source_rejects_staging_without_deleting_refs(self):
        import textwrap
        workflow = (ROOT / "core/github/managed-workflows/branch-source-policy.yml").read_text()
        script = textwrap.dedent(workflow.split("        run: |\n", 1)[1])
        for base, head, expected in (("staging", "promote/staging/abc", 1),
                                     ("development", "phase/accepted", 0),
                                     ("main", "promote/main/abc", 0),
                                     ("main", "phase/wrong", 1)):
            result = subprocess.run(["/bin/bash", "-c", script],
                                    env={"BASE_BRANCH": base, "HEAD_BRANCH": head},
                                    capture_output=True, text=True)
            with self.subTest(base=base, head=head):
                self.assertEqual(result.returncode, expected)

    def test_main_receipt_coordinates_reject_wrong_live_source_and_head(self):
        import os
        import textwrap
        workflow = (ROOT / "core/github/managed-workflows/linktrend-staging-to-main.yml").read_text()
        script = workflow.split("coordinates=\"$(python3 - <<'PY'\n", 1)[1].split("          PY\n", 1)[0]
        script = textwrap.dedent(script)
        marker = {"stage": "main", "targetBranch": "main", "sourceBranch": "development",
                  "sourceSha": self.head, "candidateHead": self.head, "fullRunId": 501}
        for key, value, expected in ((None, None, 0), ("sourceBranch", "staging", 1),
                                     ("sourceSha", _sha(9), 1), ("candidateHead", _sha(9), 1)):
            changed = {**marker, **({key: value} if key else {})}
            env = {**os.environ, "PR_BODY": "<!-- linktrend-promote: " + json.dumps(changed) + " -->",
                   "DEVELOPMENT_SHA": self.head, "HEAD_SHA": self.head}
            result = subprocess.run([__import__("sys").executable, "-c", script],
                                    env=env, capture_output=True, text=True)
            with self.subTest(key=key):
                self.assertEqual(result.returncode, expected)

    def test_minimal_review_pair_cannot_reenable_paid_bot(self):
        from scripts.gitops.coordinator.config import load_delivery_config, ConfigError
        payload = json.loads((ROOT / ".github/linktrend-delivery-mode.json").read_text())
        profiles = copy.deepcopy(payload["profiles"])
        for policy in ("disabled", "final-candidate-only"):
            payload["review"]["bugbot"] = policy
            config = load_delivery_config(payload)
            self.assertEqual(config.review.bugbot, "disabled")
            self.assertEqual(config.to_dict()["profiles"], profiles)
            self.assertEqual(config.staging_promotion, "disabled")
        payload["review"]["bugbot"] = "enabled"
        with self.assertRaises(ConfigError):
            load_delivery_config(payload)

    def test_schema_requires_head_commit_and_disabled_policy(self):
        from jsonschema import Draft202012Validator
        schema = json.loads((ROOT / "core/managed-core/schemas/delivery-modes.schema.json").read_text())
        payload = json.loads((ROOT / ".github/linktrend-delivery-mode.json").read_text())
        validator = Draft202012Validator(schema)
        self.assertEqual(list(validator.iter_errors(payload)), [])
        payload["promotion"]["identity"].remove("headCommit")
        self.assertTrue(list(validator.iter_errors(payload)))
        payload["promotion"]["identity"].append("headCommit")
        payload["review"]["bugbot"] = "final-candidate-only"
        self.assertTrue(list(validator.iter_errors(payload)))

    def test_phase_to_protected_development_transition_preserves_full_receipt(self):
        from scripts.gitops.coordinator.receipts import create_transition_receipt
        phase_head = self.head
        dev_head = _sha(50)
        transition = create_transition_receipt(self.receipt, target_branch="development",
            target_commit=dev_head, target_tree=self.tree, protected_base_commit=_sha(8)).to_dict()
        self.github.refs["development"] = dev_head
        self.github.commit_trees[dev_head] = self.tree
        identity = {**self.identity, "headCommit": dev_head, "sourceBranch": "development"}
        prepared = controller.prepare_main_promotion(**{**self.prepare,
            "development_sha": dev_head, "candidate_sha": dev_head,
            "candidate_identity": identity, "transition_receipt": transition})
        marker = json.loads(re.search(r"<!-- linktrend-promote:\s*(\{.*?\})\s*-->", self.github.prs[prepared["pr"]]["body"]).group(1))
        self.assertEqual(marker["sourceSha"], dev_head)
        self.assertEqual(marker["transitionReceipt"], transition)
        self.assertEqual(self.receipt["candidateIdentity"]["headCommit"], phase_head)
        without_transition = {**self.prepare, "development_sha": dev_head,
            "candidate_sha": dev_head, "candidate_identity": identity}
        with self.assertRaisesRegex(controller.ControllerError, "receipt_rejected"):
            controller.prepare_main_promotion(**without_transition)

    def test_transition_cli_consumes_existing_receipt_and_rejects_missing_transition(self):
        import tempfile
        import sys
        from scripts.gitops.coordinator.receipts import create_transition_receipt
        dev = _sha(50)
        transition = create_transition_receipt(self.receipt, target_branch="development",
            target_commit=dev, target_tree=self.tree, protected_base_commit=_sha(8)).to_dict()
        identity = {**self.identity, "headCommit": dev, "sourceBranch": "development"}
        with tempfile.TemporaryDirectory(prefix="direct-main-receipts-") as td:
            root = Path(td)
            for name, value in (("full", self.receipt), ("identity", identity), ("transition", transition)):
                (root / (name + ".json")).write_text(json.dumps(value))
            cmd = [sys.executable, str(ROOT / "scripts/gitops/gate_receipt.py"), "verify",
                   "--receipt", str(root / "full.json"), "--identity", str(root / "identity.json"),
                   "--gate", "full-gate"]
            no_transition = subprocess.run(cmd, capture_output=True, text=True)
            self.assertEqual(no_transition.returncode, 1)
            valid = subprocess.run(cmd + ["--transition-receipt", str(root / "transition.json")],
                                   capture_output=True, text=True)
            self.assertEqual(valid.returncode, 0, valid.stderr + valid.stdout)
            self.assertTrue(json.loads(valid.stdout)["accepted"])


if __name__ == "__main__":
    unittest.main()
