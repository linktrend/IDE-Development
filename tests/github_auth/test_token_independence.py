"""v2.5 GitHub auth: Issue checkpoints are token-independent."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.execution.protocol import WAIVED_LEGACY_GATE
from scripts.gitops import github_auth


class TokenIndependenceTests(unittest.TestCase):
    def test_issue_checkpoint_does_not_require_token_or_review_ready(self) -> None:
        self.assertFalse(github_auth.checkpoint_requires_token())
        self.assertFalse(github_auth.checkpoint_requires_review_ready())
        self.assertFalse(github_auth.checkpoint_requires_automation_token())
        decision = github_auth.issue_checkpoint_auth_decision({})
        self.assertTrue(decision["acceptWithoutToken"])
        self.assertTrue(decision["acceptWithoutReviewReady"])
        self.assertTrue(decision["acceptWithoutIssuePr"])
        self.assertTrue(decision["acceptWithoutHostedCompletionStatus"])
        self.assertEqual(decision["legacyClassification"], WAIVED_LEGACY_GATE)
        self.assertFalse(decision["pass"])

    def test_automation_token_is_waived_legacy_and_never_pass(self) -> None:
        present = github_auth.classify_legacy_publisher_token(
            {"AUTOMATION_TOKEN": "ltfx.not_canonical.v1", "AUTOMATION_TOKEN_SOURCE": "github_token"}
        )
        missing = github_auth.classify_legacy_publisher_token({})
        for row in (present, missing):
            self.assertEqual(row["classification"], WAIVED_LEGACY_GATE)
            self.assertFalse(row["isPass"])
            self.assertFalse(row["isImplementationFailure"])
            self.assertEqual(row["canonicalForV25"], "none")

    def test_phase_api_uses_gh_token_not_automation_token(self) -> None:
        token, source = github_auth.resolve_phase_api_token({"GH_TOKEN": "ltfx.phase.v1", "GITHUB_TOKEN": "ltfx.other.v1"})
        self.assertEqual(token, "ltfx.phase.v1")
        self.assertEqual(source, "GH_TOKEN")
        with self.assertRaises(github_auth.GitHubAuthError) as raised:
            github_auth.resolve_phase_api_token({"AUTOMATION_TOKEN": "ltfx.publisher.v1"})
        self.assertEqual(raised.exception.code, "legacy_publisher_token_not_canonical")
        with self.assertRaises(github_auth.GitHubAuthError) as missing:
            github_auth.resolve_phase_api_token({})
        self.assertEqual(missing.exception.code, "missing_github_credentials")
