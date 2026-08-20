"""v2.5 GitHub auth: Issue checkpoints are token-independent."""

from __future__ import annotations

import os
import sys
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.execution.protocol import WAIVED_LEGACY_GATE
from scripts.gitops import github_auth
from scripts.gitops.delivery_controller import ControllerError, resolve_production_github
from scripts.gitops.packager_coordinator import CoordinatorError, resolve_production_adapters


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
            {"AUTOMATION_TOKEN": "ghs_not_canonical", "AUTOMATION_TOKEN_SOURCE": "github_token"}
        )
        missing = github_auth.classify_legacy_publisher_token({})
        for row in (present, missing):
            self.assertEqual(row["classification"], WAIVED_LEGACY_GATE)
            self.assertFalse(row["isPass"])
            self.assertFalse(row["isImplementationFailure"])
            self.assertEqual(row["canonicalForV25"], "none")

    def test_phase_api_uses_gh_token_not_automation_token(self) -> None:
        token, source = github_auth.resolve_phase_api_token({"GH_TOKEN": "ghs_phase", "GITHUB_TOKEN": "ghs_other"})
        self.assertEqual(token, "ghs_phase")
        self.assertEqual(source, "GH_TOKEN")
        with self.assertRaises(github_auth.GitHubAuthError) as raised:
            github_auth.resolve_phase_api_token({"AUTOMATION_TOKEN": "ghs_publisher"})
        self.assertEqual(raised.exception.code, "legacy_publisher_token_not_canonical")
        with self.assertRaises(github_auth.GitHubAuthError) as missing:
            github_auth.resolve_phase_api_token({})
        self.assertEqual(missing.exception.code, "missing_github_credentials")

    def test_packager_and_controller_do_not_require_automation_token_source(self) -> None:
        env_keys = (
            "AUTOMATION_TOKEN",
            "AUTOMATION_TOKEN_SOURCE",
            "GH_TOKEN",
            "GITHUB_TOKEN",
            "LINKTREND_BUGBOT_USER_TOKEN",
            "BUGBOT_USER_TOKEN",
        )
        saved = {key: os.environ.pop(key, None) for key in env_keys}
        try:
            with self.assertRaises(CoordinatorError) as packager:
                resolve_production_adapters("owner/name")
            self.assertEqual(packager.exception.code, "missing_github_credentials")
            with self.assertRaises(ControllerError) as controller:
                resolve_production_github("owner/name")
            self.assertEqual(controller.exception.code, "missing_github_credentials")
            os.environ["GH_TOKEN"] = "ghs_phase_api"
            with mock.patch(
                "scripts.gitops.packager_coordinator.require_bugbot_user_token",
                return_value="user-token",
            ):
                github, _pusher = resolve_production_adapters("owner/name")
            self.assertEqual(github.automation_token, "ghs_phase_api")
            live = resolve_production_github("owner/name")
            self.assertEqual(live.automation_token, "ghs_phase_api")
        finally:
            for key, value in saved.items():
                if value is None:
                    os.environ.pop(key, None)
                else:
                    os.environ[key] = value
