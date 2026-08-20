"""Named administrator-recovery contract for exact Phase heads."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.execution.protocol import WAIVED_LEGACY_GATE
from scripts.gitops import delivery_controller as controller
from scripts.gitops.administrator_recovery import (
    MemoryProtection,
    RecoveryError,
    recover_phase_merge,
)
from scripts.tests.test_delivery_controller import _handoff, _sha


class AdministratorRecoveryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.head = _sha(1)
        self.tree = _sha(2)
        self.github = controller.MemoryGitHub(repository="owner/name")
        self.github.require_admin_bypass = True
        self.github.prs[11] = {
            "number": 11,
            "isDraft": False,
            "state": "open",
            "head": "phase/next",
            "base": "development",
            "headSha": self.head,
            "mergeableState": "MERGEABLE",
        }
        self.github.refs["development"] = _sha(8)
        self.protections = MemoryProtection(repository="owner/name")
        self.protections.current = {"development": {"required": True}}

    def test_prefers_admin_match_head_commit_then_restores(self) -> None:
        result = recover_phase_merge(
            github=self.github,
            protections=self.protections,
            repository="owner/name",
            pr_number=11,
            phase_branch="phase/next",
            expected_head=self.head,
            expected_tree=self.tree,
            live_head=self.head,
            live_tree=self.tree,
            named_exception="phase-v25-exact-head-recovery",
            replacement_proof=True,
            obsolete_status_state="success",
        )
        self.assertEqual(result["mergePath"], "admin_match_head_commit")
        self.assertFalse(result["temporaryExceptionApplied"])
        self.assertFalse(result["directPush"])
        self.assertEqual(result["legacyClassification"], WAIVED_LEGACY_GATE)
        self.assertFalse(result["obsoleteStatusIsPass"])
        self.assertEqual(len(self.protections.snapshots), 1)
        self.assertEqual(len(self.protections.restores), 1)
        self.assertEqual(len(self.protections.readbacks), 1)
        self.assertEqual(len(self.protections.exceptions), 0)
        self.assertTrue(self.github.merges[0]["admin"])
        self.assertTrue(self.github.merges[0]["matchHeadCommit"])

    def test_minimum_exception_only_when_admin_merge_blocked(self) -> None:
        self.github.merge_rejections[11] = "protected"
        with self.assertRaises(RecoveryError):
            recover_phase_merge(
                github=self.github,
                protections=self.protections,
                repository="owner/name",
                pr_number=11,
                phase_branch="phase/next",
                expected_head=self.head,
                expected_tree=self.tree,
                live_head=self.head,
                live_tree=self.tree,
                named_exception="phase-v25-exact-head-recovery",
                replacement_proof=True,
                allow_temporary_exception=False,
            )

        failing = controller.MemoryGitHub(repository="owner/name")
        failing.require_admin_bypass = True
        failing.prs[11] = dict(self.github.prs[11])
        failing.refs["development"] = _sha(8)

        class RetryGitHub:
            def __init__(self) -> None:
                self.inner = failing
                self.calls = 0

            def merge_pull_request(self, **kwargs):
                self.calls += 1
                if self.calls == 1:
                    raise controller.ControllerError("protected_merge_rejected", "blocked")
                return self.inner.merge_pull_request(**kwargs)

            def push_protected(self, **kwargs):
                return self.inner.push_protected(**kwargs)

        protections = MemoryProtection(repository="owner/name")
        protections.current = {"development": {"required": True}}
        result = recover_phase_merge(
            github=RetryGitHub(),
            protections=protections,
            repository="owner/name",
            pr_number=11,
            phase_branch="phase/next",
            expected_head=self.head,
            expected_tree=self.tree,
            live_head=self.head,
            live_tree=self.tree,
            named_exception="phase-v25-exact-head-recovery",
            replacement_proof=True,
            allow_temporary_exception=True,
            obsolete_status_state="failed",
        )
        self.assertEqual(result["mergePath"], "minimum_temporary_exception")
        self.assertTrue(result["temporaryExceptionApplied"])
        self.assertEqual(len(protections.exceptions), 1)
        self.assertEqual(len(protections.restores), 1)
        self.assertEqual(len(protections.readbacks), 1)
        self.assertFalse(result["obsoleteStatus"]["isPass"])

    def test_changed_head_and_missing_proof_are_rejected(self) -> None:
        with self.assertRaises(RecoveryError) as unnamed:
            recover_phase_merge(
                github=self.github,
                protections=self.protections,
                repository="owner/name",
                pr_number=11,
                phase_branch="phase/next",
                expected_head=self.head,
                expected_tree=self.tree,
                live_head=self.head,
                live_tree=self.tree,
                named_exception="",
                replacement_proof=True,
            )
        self.assertEqual(unnamed.exception.code, "named_exception_required")
        with self.assertRaises(RecoveryError) as proof:
            recover_phase_merge(
                github=self.github,
                protections=self.protections,
                repository="owner/name",
                pr_number=11,
                phase_branch="phase/next",
                expected_head=self.head,
                expected_tree=self.tree,
                live_head=self.head,
                live_tree=self.tree,
                named_exception="phase-v25-exact-head-recovery",
                replacement_proof=False,
            )
        self.assertEqual(proof.exception.code, "replacement_proof_required")
        with self.assertRaises(RecoveryError) as changed:
            recover_phase_merge(
                github=self.github,
                protections=self.protections,
                repository="owner/name",
                pr_number=11,
                phase_branch="phase/next",
                expected_head=self.head,
                expected_tree=self.tree,
                live_head=_sha(9),
                live_tree=self.tree,
                named_exception="phase-v25-exact-head-recovery",
                replacement_proof=True,
            )
        self.assertEqual(changed.exception.code, "phase_head_changed")

    def test_controller_recovery_wrapper_preserves_one_phase_pr(self) -> None:
        result = controller.recover_phase_to_development(
            github=self.github,
            protections=self.protections,
            repository="owner/name",
            handoff=_handoff(head=self.head, tree=self.tree),
            pr=self.github.prs[11],
            live_head=self.head,
            live_tree=self.tree,
            named_exception="phase-v25-exact-head-recovery",
            replacement_proof=True,
            role="operator",
        )
        self.assertEqual(result["pr"], 11)
        self.assertEqual(result["testedHead"], self.head)
        self.assertFalse(result["directPush"])

    def test_live_admin_merge_uses_gh_pr_merge_admin_match_head(self) -> None:
        payload = {
            "number": 11,
            "html_url": "https://github.com/owner/name/pull/11",
            "draft": False,
            "state": "open",
            "head": {"ref": "phase/next", "sha": self.head, "repo": {"full_name": "owner/name"}},
            "base": {"ref": "development"},
            "mergeable_state": "MERGEABLE",
        }

        def transport(method, url, token, body):
            del token, body
            self.assertEqual(method, "GET")
            self.assertIn("/pulls/11", url)
            return payload

        github = controller.LiveGitHub(
            repository="owner/name",
            automation_token="ltfx.phase_api.v1",
            transport=transport,
        )
        completed = mock.Mock(returncode=0, stdout="merged", stderr="")
        with mock.patch("scripts.gitops.delivery_controller.subprocess.run", return_value=completed) as run:
            result = github.merge_pull_request(
                repository="owner/name",
                number=11,
                expected_head=self.head,
                admin=True,
                match_head_commit=True,
            )
        cmd = run.call_args.args[0]
        self.assertEqual(cmd[:3], ["gh", "pr", "merge"])
        self.assertIn("--admin", cmd)
        self.assertIn("--match-head-commit", cmd)
        self.assertIn(self.head, cmd)
        self.assertIn("--merge", cmd)
        self.assertTrue(result["admin"])
        self.assertFalse(result["directPush"])
