#!/usr/bin/env python3
"""Unit tests for App-backed managed-core release publisher helpers (WP-01B).

Does not mint tokens, create tags, or mutate GitHub.
"""

from __future__ import annotations

import hashlib
import os
import tempfile
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
    def _binding(self, *, dual_archives: bool = False) -> pub.Binding:
        archives = [
            {
                "format": "tar.gz",
                "name": "ide-development-managed-core-2.1.0.tar.gz",
                "path": "build/release-candidate/ide-development-managed-core-2.1.0.tar.gz",
                "sha256": "sha256:" + ("11" * 32),
                "bytes": 10,
            }
        ]
        if dual_archives:
            archives.append(
                {
                    "format": "zip",
                    "name": "ide-development-managed-core-2.1.0.zip",
                    "path": "build/release-candidate/ide-development-managed-core-2.1.0.zip",
                    "sha256": "sha256:" + ("22" * 32),
                    "bytes": 11,
                }
            )
        return pub.Binding(
            source_sha="aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
            version="2.1.0",
            tag="v2.1.0",
            manifest_hash="sha256:" + ("ab" * 32),
            archives=archives,
        )

    def _release_body(self, binding: pub.Binding) -> str:
        return (
            f"Immutable managed-core release `{binding.version}`.\n\n"
            f"- sourceCommit: `{binding.source_sha}`\n"
            f"- manifestHash: `{binding.manifest_hash}`\n"
            f"- publisher: `{pub.PUBLISHER_ID}`\n"
        )

    def _release(
        self,
        binding: pub.Binding,
        *,
        assets: list[dict[str, str]] | None = None,
        target_commitish: str | None = None,
        body: str | None = None,
        name: str | None = None,
    ) -> dict[str, Any]:
        return {
            "id": 42,
            "tag_name": binding.tag,
            "name": name if name is not None else f"managed-core {binding.version}",
            "target_commitish": target_commitish or binding.source_sha,
            "html_url": "https://github.com/linktrend/IDE-Development/releases/tag/v2.1.0",
            "upload_url": "https://uploads.github.com/repos/linktrend/IDE-Development/releases/42/assets{?name,label}",
            "body": body if body is not None else self._release_body(binding),
            "assets": assets or [],
        }

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

    def test_tag_only_partial_allows_retry(self) -> None:
        """Tag created before release/assets must not report tag_replay."""
        binding = self._binding()

        def api(method: str, url: str, body: dict[str, Any] | None = None, raw: bytes | None = None) -> Any:
            if "/git/ref/" in url:
                return {"object": {"sha": binding.source_sha, "type": "commit"}}
            if "/releases/tags/" in url:
                raise pub.ReleasePublishError("github_api_error", "API GET x -> 404: missing")
            raise AssertionError(f"unexpected {method} {url}")

        state = pub.assert_no_conflict_or_replay(
            binding=binding,
            repository="linktrend/IDE-Development",
            token="ghs_x",
            api=api,
        )
        self.assertEqual(state.tag_sha, binding.source_sha)
        self.assertIsNone(state.release)
        self.assertFalse(state.complete)
        self.assertEqual(state.missing_assets, frozenset(a["name"] for a in binding.archives))

    def test_release_only_partial_assets_allows_retry(self) -> None:
        """Release exists without tag / with missing assets may continue when consistent."""
        binding = self._binding(dual_archives=True)
        tar_name = binding.archives[0]["name"]

        def api(method: str, url: str, body: dict[str, Any] | None = None, raw: bytes | None = None) -> Any:
            if "/git/ref/" in url:
                raise pub.ReleasePublishError("github_api_error", "API GET x -> 404: missing")
            if "/releases/tags/" in url:
                return self._release(
                    binding,
                    assets=[{"name": tar_name, "digest": binding.archives[0]["sha256"]}],
                )
            raise AssertionError(f"unexpected {method} {url}")

        state = pub.assert_no_conflict_or_replay(
            binding=binding,
            repository="linktrend/IDE-Development",
            token="ghs_x",
            api=api,
        )
        self.assertIsNone(state.tag_sha)
        self.assertIsNotNone(state.release)
        self.assertEqual(state.matched_assets, frozenset({tar_name}))
        self.assertEqual(state.missing_assets, frozenset({binding.archives[1]["name"]}))
        self.assertFalse(state.complete)

    def test_replay_success_complete_match_allows_continue(self) -> None:
        binding = self._binding(dual_archives=True)

        def api(method: str, url: str, body: dict[str, Any] | None = None, raw: bytes | None = None) -> Any:
            if "/git/ref/" in url:
                return {"object": {"sha": binding.source_sha, "type": "commit"}}
            if "/releases/tags/" in url:
                return self._release(
                    binding,
                    assets=[
                        {"name": binding.archives[0]["name"], "digest": binding.archives[0]["sha256"]},
                        {"name": binding.archives[1]["name"], "digest": binding.archives[1]["sha256"]},
                    ],
                )
            raise AssertionError(f"unexpected {method} {url}")

        state = pub.assert_no_conflict_or_replay(
            binding=binding,
            repository="linktrend/IDE-Development",
            token="ghs_x",
            api=api,
        )
        self.assertTrue(state.complete)
        self.assertEqual(state.matched_assets, frozenset(a["name"] for a in binding.archives))
        self.assertEqual(state.missing_assets, frozenset())

    def test_checksum_conflict(self) -> None:
        binding = self._binding()

        def api(method: str, url: str, body: dict[str, Any] | None = None, raw: bytes | None = None) -> Any:
            if "/git/ref/" in url:
                raise pub.ReleasePublishError("github_api_error", "API GET x -> 404: missing")
            if "/releases/tags/" in url:
                return self._release(
                    binding,
                    assets=[
                        {
                            "name": binding.archives[0]["name"],
                            "digest": "sha256:" + ("ff" * 32),
                        }
                    ],
                )
            raise AssertionError(f"unexpected {method} {url}")

        with self.assertRaises(pub.ReleasePublishError) as ctx:
            pub.assert_no_conflict_or_replay(
                binding=binding,
                repository="linktrend/IDE-Development",
                token="ghs_x",
                api=api,
            )
        self.assertEqual(ctx.exception.code, "checksum_conflict")

    def test_release_source_conflict_blocks(self) -> None:
        binding = self._binding()
        other = "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb"

        def api(method: str, url: str, body: dict[str, Any] | None = None, raw: bytes | None = None) -> Any:
            if "/git/ref/" in url:
                return {"object": {"sha": binding.source_sha, "type": "commit"}}
            if "/releases/tags/" in url:
                bad_body = (
                    f"Immutable managed-core release `{binding.version}`.\n\n"
                    f"- sourceCommit: `{other}`\n"
                    f"- manifestHash: `{binding.manifest_hash}`\n"
                )
                return self._release(binding, body=bad_body, target_commitish=other)
            raise AssertionError(f"unexpected {method} {url}")

        with self.assertRaises(pub.ReleasePublishError) as ctx:
            pub.assert_no_conflict_or_replay(
                binding=binding,
                repository="linktrend/IDE-Development",
                token="ghs_x",
                api=api,
            )
        self.assertEqual(ctx.exception.code, "release_source_conflict")

    def test_clean_when_absent(self) -> None:
        binding = self._binding()

        def api(method: str, url: str, body: dict[str, Any] | None = None, raw: bytes | None = None) -> Any:
            raise pub.ReleasePublishError("github_api_error", f"API GET {url} -> 404: missing")

        state = pub.assert_no_conflict_or_replay(
            binding=binding,
            repository="linktrend/IDE-Development",
            token="ghs_x",
            api=api,
        )
        self.assertIsNone(state.tag_sha)
        self.assertIsNone(state.release)
        self.assertFalse(state.complete)


class IdempotentPublishTests(unittest.TestCase):
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
                    "path": "build/x.tar.gz",
                    "sha256": "sha256:" + ("11" * 32),
                    "bytes": 10,
                },
                {
                    "format": "zip",
                    "name": "ide-development-managed-core-2.1.0.zip",
                    "path": "build/x.zip",
                    "sha256": "sha256:" + ("22" * 32),
                    "bytes": 11,
                },
            ],
        )

    def _release_body(self, binding: pub.Binding) -> str:
        return (
            f"Immutable managed-core release `{binding.version}`.\n\n"
            f"- sourceCommit: `{binding.source_sha}`\n"
            f"- manifestHash: `{binding.manifest_hash}`\n"
            f"- publisher: `{pub.PUBLISHER_ID}`\n"
        )

    def test_create_continues_from_tag_only_partial(self) -> None:
        binding = self._binding()
        calls: list[tuple[str, str]] = []
        release_created = {"yes": False}

        def api(method: str, url: str, body: dict[str, Any] | None = None, raw: bytes | None = None) -> Any:
            calls.append((method, url))
            if method == "GET" and "/git/ref/" in url:
                return {"object": {"sha": binding.source_sha, "type": "commit"}}
            if method == "GET" and "/releases/tags/" in url:
                if release_created["yes"]:
                    return {
                        "id": 7,
                        "tag_name": binding.tag,
                        "name": f"managed-core {binding.version}",
                        "target_commitish": binding.source_sha,
                        "html_url": "https://example.test/release/7",
                        "upload_url": "https://uploads.example.test/assets{?name,label}",
                        "body": self._release_body(binding),
                        "assets": [],
                    }
                raise pub.ReleasePublishError("github_api_error", "API GET x -> 404: missing")
            if method == "POST" and url.endswith("/git/tags"):
                raise AssertionError("must not recreate annotated tag when already bound")
            if method == "POST" and url.endswith("/git/refs"):
                raise AssertionError("must not recreate tag ref when already bound")
            if method == "POST" and url.endswith("/releases"):
                release_created["yes"] = True
                return {
                    "id": 7,
                    "tag_name": binding.tag,
                    "name": f"managed-core {binding.version}",
                    "html_url": "https://example.test/release/7",
                    "upload_url": "https://uploads.example.test/assets{?name,label}",
                    "body": body.get("body") if isinstance(body, dict) else "",
                    "assets": [],
                }
            if method == "POST" and "uploads.example.test/assets" in url:
                return {"ok": True}
            raise AssertionError(f"unexpected {method} {url}")

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            # Build archives whose sha256 matches binding by writing known content
            # then updating binding digests to the real file digests.
            real_archives = []
            real_paths: dict[str, Path] = {}
            for idx, row in enumerate(binding.archives):
                raw = f"archive-{idx}".encode()
                path = root / row["name"]
                path.write_bytes(raw)
                digest = "sha256:" + hashlib.sha256(raw).hexdigest()
                real_archives.append({**row, "sha256": digest, "bytes": len(raw)})
                real_paths[row["name"]] = path
            real_binding = pub.Binding(
                source_sha=binding.source_sha,
                version=binding.version,
                tag=binding.tag,
                manifest_hash=binding.manifest_hash,
                archives=real_archives,
            )

            result = pub.create_tag_and_release(
                binding=real_binding,
                repository="linktrend/IDE-Development",
                token="ghs_x",
                archive_paths=real_paths,
                api=api,
            )

        self.assertEqual(result["releaseUrl"], "https://example.test/release/7")
        self.assertFalse(any(u.endswith("/git/tags") for _, u in calls if _ == "POST"))
        self.assertTrue(any(u.endswith("/releases") for m, u in calls if m == "POST"))
        upload_posts = [u for m, u in calls if m == "POST" and "uploads.example.test/assets" in u]
        self.assertEqual(len(upload_posts), 2)

    def test_create_uploads_only_missing_asset(self) -> None:
        binding = self._binding()
        tar = binding.archives[0]
        zip_row = binding.archives[1]
        uploaded: list[str] = []

        def api(method: str, url: str, body: dict[str, Any] | None = None, raw: bytes | None = None) -> Any:
            if method == "GET" and "/git/ref/" in url:
                return {"object": {"sha": binding.source_sha, "type": "commit"}}
            if method == "GET" and "/releases/tags/" in url:
                return {
                    "id": 9,
                    "tag_name": binding.tag,
                    "name": f"managed-core {binding.version}",
                    "target_commitish": binding.source_sha,
                    "html_url": "https://example.test/release/9",
                    "upload_url": "https://uploads.example.test/assets{?name,label}",
                    "body": self._release_body(binding),
                    "assets": [{"name": tar["name"], "digest": tar["sha256"]}],
                }
            if method == "POST" and (url.endswith("/git/tags") or url.endswith("/releases")):
                raise AssertionError(f"must not recreate tag/release on partial-assets retry: {url}")
            if method == "POST" and "uploads.example.test/assets" in url:
                uploaded.append(url)
                return {"ok": True}
            raise AssertionError(f"unexpected {method} {url}")

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            # Only the missing zip must be readable; tar is skipped via remote digest.
            zip_path = root / zip_row["name"]
            zip_path.write_bytes(b"zip-bytes")
            digest = "sha256:" + hashlib.sha256(b"zip-bytes").hexdigest()
            real_binding = pub.Binding(
                source_sha=binding.source_sha,
                version=binding.version,
                tag=binding.tag,
                manifest_hash=binding.manifest_hash,
                archives=[
                    tar,
                    {**zip_row, "sha256": digest, "bytes": len(b"zip-bytes")},
                ],
            )
            result = pub.create_tag_and_release(
                binding=real_binding,
                repository="linktrend/IDE-Development",
                token="ghs_x",
                archive_paths={zip_row["name"]: zip_path},
                api=api,
            )

        self.assertEqual(result["releaseId"], 9)
        self.assertEqual(len(uploaded), 1)
        self.assertIn(zip_row["name"], uploaded[0])

    def test_create_replay_success_skips_mutations(self) -> None:
        binding = self._binding()

        def api(method: str, url: str, body: dict[str, Any] | None = None, raw: bytes | None = None) -> Any:
            if method == "GET" and "/git/ref/" in url:
                return {"object": {"sha": binding.source_sha, "type": "commit"}}
            if method == "GET" and "/releases/tags/" in url:
                return {
                    "id": 11,
                    "tag_name": binding.tag,
                    "name": f"managed-core {binding.version}",
                    "target_commitish": binding.source_sha,
                    "html_url": "https://example.test/release/11",
                    "upload_url": "https://uploads.example.test/assets{?name,label}",
                    "body": self._release_body(binding),
                    "assets": [
                        {"name": binding.archives[0]["name"], "digest": binding.archives[0]["sha256"]},
                        {"name": binding.archives[1]["name"], "digest": binding.archives[1]["sha256"]},
                    ],
                }
            raise AssertionError(f"complete replay must not mutate: {method} {url}")

        result = pub.create_tag_and_release(
            binding=binding,
            repository="linktrend/IDE-Development",
            token="ghs_x",
            archive_paths={},
            api=api,
        )
        self.assertEqual(result["releaseId"], 11)
        self.assertEqual(result["releaseUrl"], "https://example.test/release/11")


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
