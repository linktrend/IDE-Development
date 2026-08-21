"""Focused reliability tests for issue-branch setup."""

from __future__ import annotations

import subprocess
import unittest
from unittest import mock

from scripts.gitops import create_issue_branch


def result(code: int = 0, stdout: str = "", stderr: str = "") -> subprocess.CompletedProcess[str]:
    return subprocess.CompletedProcess([], code, stdout, stderr)


class CreateIssueBranchTests(unittest.TestCase):
    @mock.patch.object(create_issue_branch.subprocess, "run")
    def test_missing_label_permission_falls_back_to_exact_title_and_unlabelled_create(self, run: mock.Mock) -> None:
        run.side_effect = [
            result(stdout='[]'),
            result(1, stderr="permission denied"),
            result(stdout='[]'),
            result(stdout="https://github.com/acme/repo/issues/42\n"),
        ]
        self.assertEqual(create_issue_branch.create_issue("acme/repo", "Roll out v2.5"), 42)
        create_command = run.call_args_list[-1].args[0]
        self.assertNotIn("--label", create_command)

    @mock.patch.object(create_issue_branch.subprocess, "run")
    def test_label_disappearing_mid_create_retries_without_label(self, run: mock.Mock) -> None:
        run.side_effect = [
            result(stdout='[{"name":"linktrend-agentsetup"}]'),
            result(stdout='[]'),
            result(1, stderr="label not found"),
            result(stdout="https://github.com/acme/repo/issues/43\n"),
        ]
        self.assertEqual(create_issue_branch.create_issue("acme/repo", "Roll out v2.5"), 43)
        self.assertIn("--label", run.call_args_list[-2].args[0])
        self.assertNotIn("--label", run.call_args_list[-1].args[0])


if __name__ == "__main__":
    unittest.main()
