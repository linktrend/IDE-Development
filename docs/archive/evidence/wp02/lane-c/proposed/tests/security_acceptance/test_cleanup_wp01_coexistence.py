"""WP02 Lane C — coexistence: WP01 repo-scope security + cleanup wrong-repo fixture.

Assumes lead merged WP01 then cleanup tip. Fixture-level only — no live cleanup apply.
"""

from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPTS_DIR = REPO_ROOT / "scripts"
SECURITY_FIXTURES = SCRIPTS_DIR / "ide_development_tests" / "fixtures" / "security"

if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))
if str(SCRIPTS_DIR / "gitops") not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR / "gitops"))

from gitops.review_ready_dispatch import (  # noqa: E402
    DispatchValidationError,
    validate_repository,
)


class CleanupWp01CoexistenceTests(unittest.TestCase):
    def test_wrong_repo_fixture_still_refuses(self) -> None:
        path = SECURITY_FIXTURES / "cleanup" / "wrong-repo-evidence.json"
        self.assertTrue(path.is_file(), path)
        payload = json.loads(path.read_text(encoding="utf-8"))
        self.assertTrue(payload.get("applyForbidden", True))
        self.assertEqual(payload.get("mode"), "dry-run-only")
        with self.assertRaises(DispatchValidationError) as ctx:
            validate_repository(
                github_repository="linktrend/IDE-Development",
                requested_repository=payload.get("repository"),
            )
        self.assertEqual(ctx.exception.code, "repository_mismatch")

    def test_cleanup_controls_normalize_caller_repo_fail_closed(self) -> None:
        import cleanup_controls

        slug, reason = cleanup_controls.normalize_caller_repo("")
        self.assertIsNone(slug)
        self.assertTrue(reason)

        slug, reason = cleanup_controls.normalize_caller_repo("not-a-slug")
        self.assertIsNone(slug)

        slug, reason = cleanup_controls.normalize_caller_repo("linktrend/IDE-Development")
        self.assertEqual(slug, "linktrend/IDE-Development")

    def test_issue_branch_matching_bare_and_slug(self) -> None:
        import cleanup_controls

        self.assertEqual(cleanup_controls.issue_number_from_branch("issue/43"), 43)
        self.assertEqual(
            cleanup_controls.issue_number_from_branch(
                "issue/43-build-portable-ide-development-v2-managed-core-i"
            ),
            43,
        )
        self.assertIsNone(cleanup_controls.issue_number_from_branch("feature/43-x"))


if __name__ == "__main__":
    unittest.main()
