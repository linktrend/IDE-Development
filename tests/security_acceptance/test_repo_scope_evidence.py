"""Repository-scope confusion in GitHub/cleanup evidence (fixture-level only)."""

from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

from harness import REPO_ROOT, SCRIPTS_DIR, SECURITY_FIXTURES

if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from gitops.review_ready_dispatch import (  # noqa: E402
    DispatchValidationError,
    validate_evidence_json,
    validate_evidence_path,
    validate_repository,
)


class RepoScopeEvidenceTests(unittest.TestCase):
    def test_repository_mismatch_refused(self) -> None:
        with self.assertRaises(DispatchValidationError) as ctx:
            validate_repository(
                github_repository="linktrend/IDE-Development",
                requested_repository="linktrend/Some-Other-Repo",
            )
        self.assertEqual(ctx.exception.code, "repository_mismatch")

    def test_repository_format_invalid(self) -> None:
        with self.assertRaises(DispatchValidationError) as ctx:
            validate_repository(
                github_repository="linktrend/IDE-Development",
                requested_repository="not-a-slug",
            )
        self.assertEqual(ctx.exception.code, "repository_format_invalid")

    def test_missing_github_repository_context(self) -> None:
        with self.assertRaises(DispatchValidationError) as ctx:
            validate_repository(github_repository="", requested_repository=None)
        self.assertEqual(ctx.exception.code, "repository_context_invalid")

    def test_evidence_path_absolute_refused(self) -> None:
        with self.assertRaises(DispatchValidationError) as ctx:
            validate_evidence_path("/Users/someone/.linktrend/completion-evidence.json")
        self.assertEqual(ctx.exception.code, "evidence_path_absolute")

    def test_evidence_path_traversal_refused(self) -> None:
        with self.assertRaises(DispatchValidationError) as ctx:
            validate_evidence_path("../secrets/evidence.json")
        self.assertEqual(ctx.exception.code, "evidence_path_illegal")

    def test_cleanup_evidence_fixture_wrong_repo_marked(self) -> None:
        """Fixture-level proof: cleanup evidence must carry matching repo identity.

        No live cleanup apply — only fixture inspection + mismatch detection.
        """
        path = SECURITY_FIXTURES / "cleanup" / "wrong-repo-evidence.json"
        self.assertTrue(path.is_file(), path)
        payload = json.loads(path.read_text(encoding="utf-8"))
        context_repo = "linktrend/IDE-Development"
        evidence_repo = payload.get("repository") or payload.get("repo")
        self.assertIsInstance(evidence_repo, str)
        self.assertNotEqual(evidence_repo.lower(), context_repo.lower())
        # Same fail-closed rule as dispatch validate_repository
        with self.assertRaises(DispatchValidationError) as ctx:
            validate_repository(
                github_repository=context_repo,
                requested_repository=evidence_repo,
            )
        self.assertEqual(ctx.exception.code, "repository_mismatch")

    def test_external_state_audit_fixture_repo_binding(self) -> None:
        """Import-only audit: fixture client binds to declared --repo, no live calls."""
        from gitops.external_state_audit import FixtureClient, EXIT_REFUSED, AuditError

        fx = SECURITY_FIXTURES / "evidence" / "external-state-ok"
        self.assertTrue((fx / "state.json").is_file())
        client = FixtureClient("linktrend/IDE-Development", fx)
        self.assertEqual(client.repo, "linktrend/IDE-Development")
        # Scope confusion: evidence claiming another repo must not be treated as live apply.
        confused = SECURITY_FIXTURES / "cleanup" / "wrong-repo-evidence.json"
        data = json.loads(confused.read_text(encoding="utf-8"))
        self.assertEqual(data.get("mode"), "dry-run-only")
        self.assertTrue(data.get("applyForbidden", True))

    def test_evidence_json_missing_fields_refused(self) -> None:
        with self.assertRaises(DispatchValidationError) as ctx:
            validate_evidence_json(json.dumps({"schemaVersion": 1}))
        self.assertEqual(ctx.exception.code, "evidence_json_missing_fields")


if __name__ == "__main__":
    unittest.main()
