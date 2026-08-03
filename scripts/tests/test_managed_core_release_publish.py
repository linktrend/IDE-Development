#!/usr/bin/env python3
"""Unit tests for App-backed managed-core release publisher helpers (WP-01B).

Does not mint tokens, create tags, or mutate GitHub.
"""

from __future__ import annotations

import os
import unittest
from pathlib import Path
from typing import Any
from unittest import mock

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parents[1]
import sys

sys.path.insert(0, str(REPO_ROOT / "scripts"))

from gitops import managed_core_release_publish as pub  # noqa: E402


class RequireAppTokenTests(unittest.TestCase):
    def test_requires_github_app_source(self) -> None:
        with mock.patch.dict(os.environ, {"AUTOMATION_TOKEN_SOURCE": "pat", "AUTOMATION_TOKEN": "x"}, clear=False):
            with self.assertRaises(pub.ReleasePublishError) as ctx:
                pub.require_app_token(token="x", token_source="pat")
            self.assertEqual(ctx.exception.code, "automation_credentials_blocked")

    def test_refuses_missing_token(self) -> None:
        with self.assertRaises(pub.ReleasePublishError) as ctx:
            pub.require_app_token(token="", token_source="github_app")
        self.assertEqual(ctx.exception.code, "automation_credentials_blocked")

    def test_refuses_personal_token_prefix(self) -> None:
        with self.assertRaises(pub.ReleasePublishError) as ctx:
            pub.require_app_token(token="ghp_not_a_real_token", token_source="github_app")
        self.assertEqual(ctx.exception.code, "personal_token_forbidden")

    def test_refuses_banned_env(self) -> None:
        env = {
            "AUTOMATION_TOKEN_SOURCE": "github_app",
            "AUTOMATION_TOKEN": "ghs_app_installation_token_shape",
            "LINKTREND_BUGBOT_USER_TOKEN": "should-not-be-present",
        }
        with mock.patch.dict(os.environ, env, clear=False):
            with self.assertRaises(pub.ReleasePublishError) as ctx:
                pub.require_app_token()
            self.assertEqual(ctx.exception.code, "personal_token_forbidden")

    def test_accepts_app_token(self) -> None:
        token = pub.require_app_token(
            token="ghs_app_installation_token_shape",
            token_source="github_app",
        )
        self.assertEqual(token, "ghs_app_installation_token_shape")


class ConflictReplayTests(unittest.TestCase):
    def _binding(self) -> pub.Binding:
        return pub.Binding(
            source_sha="aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
            version="2.1.0",
            tag="v2.1.0",
            manifest_hash="sha256:" + ("ab" * 32),
            archives=[
                {
                    "format": "tar.gz",
                    "name": "ide-development-managed-core-2.1.0.tar.gz",
                    "path": "build/release-candidate/ide-development-managed-core-2.1.0.tar.gz",
                    "sha256": "sha256:" + ("11" * 32),
                    "bytes": 10,
                }
            ],
        )

    def test_tag_conflict_different_sha(self) -> None:
        binding = self._binding()

        def api(method: str, url: str, body: dict[str, Any] | None = None, raw: bytes | None = None) -> Any:
            if "/git/ref/" in url:
                return {"object": {"sha": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb", "type": "commit"}}
            raise AssertionError(f"unexpected {method} {url}")

        with self.assertRaises(pub.ReleasePublishError) as ctx:
            pub.assert_no_conflict_or_replay(
                binding=binding,
                repository="linktrend/IDE-Development",
                token="ghs_x",
                api=api,
            )
        self.assertEqual(ctx.exception.code, "tag_conflict")

    def test_tag_replay_same_sha(self) -> None:
        binding = self._binding()

        def api(method: str, url: str, body: dict[str, Any] | None = None, raw: bytes | None = None) -> Any:
            if "/git/ref/" in url:
                return {"object": {"sha": binding.source_sha, "type": "commit"}}
            raise AssertionError(f"unexpected {method} {url}")

        with self.assertRaises(pub.ReleasePublishError) as ctx:
            pub.assert_no_conflict_or_replay(
                binding=binding,
                repository="linktrend/IDE-Development",
                token="ghs_x",
                api=api,
            )
        self.assertEqual(ctx.exception.code, "tag_replay")

    def test_release_replay(self) -> None:
        binding = self._binding()

        def api(method: str, url: str, body: dict[str, Any] | None = None, raw: bytes | None = None) -> Any:
            if "/git/ref/" in url:
                raise pub.ReleasePublishError("github_api_error", "API GET x -> 404: missing")
            if "/releases/tags/" in url:
                return {
                    "id": 1,
                    "assets": [
                        {
                            "name": binding.archives[0]["name"],
                            "digest": binding.archives[0]["sha256"],
                        }
                    ],
                }
            raise AssertionError(f"unexpected {method} {url}")

        with self.assertRaises(pub.ReleasePublishError) as ctx:
            pub.assert_no_conflict_or_replay(
                binding=binding,
                repository="linktrend/IDE-Development",
                token="ghs_x",
                api=api,
            )
        self.assertEqual(ctx.exception.code, "release_replay")

    def test_checksum_conflict(self) -> None:
        binding = self._binding()

        def api(method: str, url: str, body: dict[str, Any] | None = None, raw: bytes | None = None) -> Any:
            if "/git/ref/" in url:
                raise pub.ReleasePublishError("github_api_error", "API GET x -> 404: missing")
            if "/releases/tags/" in url:
                return {
                    "id": 1,
                    "assets": [
                        {
                            "name": binding.archives[0]["name"],
                            "digest": "sha256:" + ("ff" * 32),
                        }
                    ],
                }
            raise AssertionError(f"unexpected {method} {url}")

        with self.assertRaises(pub.ReleasePublishError) as ctx:
            pub.assert_no_conflict_or_replay(
                binding=binding,
                repository="linktrend/IDE-Development",
                token="ghs_x",
                api=api,
            )
        self.assertEqual(ctx.exception.code, "checksum_conflict")

    def test_clean_when_absent(self) -> None:
        binding = self._binding()

        def api(method: str, url: str, body: dict[str, Any] | None = None, raw: bytes | None = None) -> Any:
            raise pub.ReleasePublishError("github_api_error", f"API GET {url} -> 404: missing")

        pub.assert_no_conflict_or_replay(
            binding=binding,
            repository="linktrend/IDE-Development",
            token="ghs_x",
            api=api,
        )


class EvidenceSchemaTests(unittest.TestCase):
    def test_evidence_locator_omits_path(self) -> None:
        binding = pub.Binding(
            source_sha="aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
            version="2.1.0",
            tag="v2.1.0",
            manifest_hash="sha256:" + ("cd" * 32),
            archives=[
                {
                    "format": "tar.gz",
                    "name": "ide-development-managed-core-2.1.0.tar.gz",
                    "path": "build/x.tar.gz",
                    "sha256": "sha256:" + ("22" * 32),
                    "bytes": 99,
                },
                {
                    "format": "zip",
                    "name": "ide-development-managed-core-2.1.0.zip",
                    "path": "build/x.zip",
                    "sha256": "sha256:" + ("33" * 32),
                    "bytes": 100,
                },
            ],
        )
        evidence = pub.build_release_evidence(
            binding=binding,
            repository="linktrend/IDE-Development",
            publication_status="pending_governed_publish",
            dry_run=True,
        )
        self.assertNotIn("path", evidence["locator"]["primaryArchive"])
        self.assertEqual(evidence["locator"]["primaryArchive"]["format"], "tar.gz")
        for row in evidence["archives"]:
            self.assertNotIn("path", row)


class SourceTipBindingTests(unittest.TestCase):
    def test_source_sha_mismatch(self) -> None:
        def api(method: str, url: str, body: dict[str, Any] | None = None, raw: bytes | None = None) -> Any:
            return {"commit": {"sha": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb"}}

        with self.assertRaises(pub.ReleasePublishError) as ctx:
            pub.bind_source_sha_to_default_tip(
                source_sha="aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
                repository="linktrend/IDE-Development",
                default_branch="main",
                token="ghs_x",
                api=api,
            )
        self.assertEqual(ctx.exception.code, "source_sha_mismatch")


if __name__ == "__main__":
    unittest.main()
