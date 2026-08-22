"""Mock-only tests for the Cursor Cloud API authority boundary."""

from __future__ import annotations

import unittest
from pathlib import Path

from core.execution.cursor_cloud_dispatch import (
    CursorCloudDispatchError,
    CursorCloudDispatchRequest,
    DurableCursorCloudIntentStore,
    ENV_PUBLIC_ID,
    dispatch_cursor_cloud,
    load_cursor_cloud_dispatch_config,
    require_cursor_cloud_api_key,
    validate_cursor_cloud_run_readback,
    validate_cursor_cloud_attestation,
)


REQUEST = CursorCloudDispatchRequest(
    repository="linktrend/IDE-Development",
    target_path="/agent/repos/IDE-Development",
    target_remote="https://github.com/linktrend/IDE-Development",
    ref="issue/379-cursor-cloud",
    commit="a" * 40,
    tree="b" * 40,
    model="cursor-grok-4.5-high",
    expected_build_id="ide-development-2.5.1-build-379",
    toolchain={"python": "3.12", "node": "22"},
    setup_receipt_digest="sha256:c27e25298bc82faafcbac97c11c3da84f872f1ea998e28e757736a4c66dfe5f2",
    governed_setup=True,
)
KEY_NAME = "CURSOR_" + "API_KEY"


class FakeCursorCloudHTTP:
    def __init__(self, store: DurableCursorCloudIntentStore, *, fail_once: bool = False) -> None:
        self.store = store
        self.fail_once = fail_once
        self.calls: list[tuple[str, dict, dict]] = []

    def post(self, path, *, headers, body):
        self.calls.append((path, dict(headers), dict(body)))
        key = headers["Idempotency-Key"]
        self.assert_prepared = self.store.read(key)
        if self.fail_once:
            self.fail_once = False
            raise TimeoutError("fake timeout after unknown acceptance")
        return {
            "statusCode": 201,
            "agentId": body["agentId"],
            "runId": "run-379",
            "env": body["env"],
            "model": body["model"],
        }


class CursorCloudDispatchTests(unittest.TestCase):
    def test_config_is_exact_and_cli_login_is_not_authority(self) -> None:
        config = load_cursor_cloud_dispatch_config(str(Path(__file__).resolve().parents[2]))
        self.assertEqual(config["apiBaseUrl"], "https://api.cursor.com")
        self.assertEqual(config["apiPath"], "/v1/agents")
        self.assertEqual(config["savedRepositoryLayout"], "/agent/repos/<repo>")
        self.assertEqual(config["maxApiAttempts"], 2)
        self.assertEqual(config["environment"]["publicId"], ENV_PUBLIC_ID)
        self.assertTrue(config["runReadbackRequired"])
        self.assertEqual(config["apiBinding"], "prompt-and-governed-setup-only")
        self.assertTrue(config["setupReceiptRequired"])
        self.assertFalse(config["cliLoginIsCloudAuthority"])
        with self.assertRaisesRegex(CursorCloudDispatchError, "CLI login"):
            require_cursor_cloud_api_key({}, cursor_cli_authenticated=True)

    def test_requires_api_key_without_exposing_value(self) -> None:
        value_to_hide = "cursor-secret-value"
        with self.assertRaises(CursorCloudDispatchError) as raised:
            require_cursor_cloud_api_key({KEY_NAME: " bad key"})
        self.assertNotIn(value_to_hide, str(raised.exception))
        with self.assertRaises(CursorCloudDispatchError):
            require_cursor_cloud_api_key({})

    def test_governed_setup_receipt_is_required_and_prompt_bound(self) -> None:
        request = CursorCloudDispatchRequest(
            **{**REQUEST.__dict__, "setup_receipt_digest": "sha256:bad"}
        )
        with self.assertRaisesRegex(CursorCloudDispatchError, "setup receipt"):
            request.validate()
        store = DurableCursorCloudIntentStore()
        http = FakeCursorCloudHTTP(store)
        dispatch_cursor_cloud(REQUEST, store, http, environment={KEY_NAME: "test-only-key"})
        self.assertIn(REQUEST.setup_receipt_digest, http.calls[0][2]["prompt"])

    def test_prepared_intent_precedes_mock_api_and_duplicate_is_suppressed(self) -> None:
        store = DurableCursorCloudIntentStore()
        http = FakeCursorCloudHTTP(store)
        first = dispatch_cursor_cloud(
            REQUEST, store, http, environment={KEY_NAME: "test-only-key"}
        )
        self.assertEqual(first.status, "committed")
        self.assertEqual(len(http.calls), 1)
        path, headers, body = http.calls[0]
        self.assertEqual(path, "/v1/agents")
        self.assertTrue(http.assert_prepared and http.assert_prepared["state"] == "PREPARED")
        self.assertEqual(body["env"], {"type": "cloud", "name": "IDE Development 2.5.1"})
        self.assertEqual(body["model"], REQUEST.model)
        self.assertNotIn("buildId", body)
        self.assertEqual(first.expected_build_id, REQUEST.expected_build_id)
        self.assertEqual(headers["Authorization"], "Bearer test-only-key")
        repeated = dispatch_cursor_cloud(
            REQUEST, store, http, environment={KEY_NAME: "test-only-key"}
        )
        self.assertEqual(repeated.status, "duplicate")
        self.assertEqual(len(http.calls), 1)

    def test_exact_linkbrain_selection_is_prompt_bound_not_unsupported_api_binding(self) -> None:
        request = CursorCloudDispatchRequest(
            **{
                **REQUEST.__dict__,
                "repository": "linktrend/LiNKbrain",
                "target_path": "/agent/repos/LiNKbrain",
                "target_remote": "https://github.com/linktrend/LiNKbrain",
            }
        )
        store = DurableCursorCloudIntentStore()
        http = FakeCursorCloudHTTP(store)
        result = dispatch_cursor_cloud(
            request, store, http, environment={KEY_NAME: "test-only-key"}
        )
        self.assertEqual(result.status, "committed")
        body = http.calls[0][2]
        self.assertEqual(body["env"], {"type": "cloud", "name": "IDE Development 2.5.1"})
        self.assertNotIn("repository", body)
        self.assertNotIn("ref", body)
        self.assertNotIn("commit", body)
        self.assertNotIn("tree", body)
        self.assertIn("cd to and resolve the exact saved-environment target path /agent/repos/LiNKbrain", body["prompt"])
        self.assertIn("https://github.com/linktrend/LiNKbrain", body["prompt"])

    def test_repo_relative_target_is_canonicalized_to_saved_environment_root(self) -> None:
        request = CursorCloudDispatchRequest(
            **{**REQUEST.__dict__, "repository": "linktrend/LiNKbrain", "target_path": "LiNKbrain"}
        )
        self.assertEqual(request.resolved_target_path, "/agent/repos/LiNKbrain")

    def test_default_primary_repo_is_rejected_before_http(self) -> None:
        request = CursorCloudDispatchRequest(
            **{**REQUEST.__dict__, "repository": "linktrend/LiNKbrain", "target_path": "/agent/repos/LiNKharness"}
        )
        http = FakeCursorCloudHTTP(DurableCursorCloudIntentStore())
        with self.assertRaisesRegex(CursorCloudDispatchError, "target path"):
            dispatch_cursor_cloud(
                request,
                http.store,
                http,
                environment={KEY_NAME: "test-only-key"},
            )
        self.assertEqual(http.calls, [])

    def test_missing_ambiguous_and_traversing_target_paths_fail_closed(self) -> None:
        for target_path in ("", "/agent/repos/LiNKbrain/child", "../LiNKbrain", "/tmp/LiNKbrain"):
            request = CursorCloudDispatchRequest(
                **{**REQUEST.__dict__, "target_path": target_path}
            )
            http = FakeCursorCloudHTTP(DurableCursorCloudIntentStore())
            with self.assertRaises(CursorCloudDispatchError):
                dispatch_cursor_cloud(
                    request,
                    http.store,
                    http,
                    environment={KEY_NAME: "test-only-key"},
                )
            self.assertEqual(http.calls, [], target_path)

    def test_remote_path_ref_commit_tree_mismatch_blocks_mutation(self) -> None:
        good = {
            "status": "PASS",
            "noMutation": True,
            "environment": REQUEST.environment,
            "targetPath": REQUEST.target_path,
            "remote": REQUEST.target_remote + ".git",
            "repository": REQUEST.repository,
            "ref": REQUEST.ref,
            "commit": REQUEST.commit,
            "tree": REQUEST.tree,
            "toolchain": dict(REQUEST.toolchain),
            "workspaceClean": True,
        }
        for field, value in (
            ("targetPath", "/agent/repos/LiNKharness"),
            ("remote", "https://github.com/linktrend/LiNKharness"),
            ("ref", "development"),
            ("commit", "c" * 40),
            ("tree", "d" * 40),
        ):
            with self.assertRaisesRegex(CursorCloudDispatchError, "mismatch"):
                validate_cursor_cloud_attestation(REQUEST, {**good, field: value})

    def test_unknown_timeout_gets_one_idempotent_retry(self) -> None:
        store = DurableCursorCloudIntentStore()
        http = FakeCursorCloudHTTP(store, fail_once=True)
        result = dispatch_cursor_cloud(
            REQUEST, store, http, environment={KEY_NAME: "test-only-key"}
        )
        self.assertEqual(result.status, "committed")
        self.assertEqual(len(http.calls), 2)
        self.assertEqual(http.calls[0][1]["Idempotency-Key"], http.calls[1][1]["Idempotency-Key"])

    def test_fast_and_wrong_environment_fail_before_http(self) -> None:
        store = DurableCursorCloudIntentStore()
        http = FakeCursorCloudHTTP(store)
        with self.assertRaisesRegex(CursorCloudDispatchError, "Fast"):
            dispatch_cursor_cloud(
                CursorCloudDispatchRequest(**{**REQUEST.__dict__, "model": "Fast"}),
                store,
                http,
                environment={KEY_NAME: "test-only-key"},
            )
        with self.assertRaisesRegex(CursorCloudDispatchError, "environment"):
            dispatch_cursor_cloud(
                CursorCloudDispatchRequest(**{**REQUEST.__dict__, "environment_name": "local"}),
                store,
                http,
                environment={KEY_NAME: "test-only-key"},
            )
        self.assertEqual(http.calls, [])

    def test_public_environment_identity_and_run_readback_are_required(self) -> None:
        request = REQUEST
        good = {
            "environment": request.environment,
            "environmentPublicId": ENV_PUBLIC_ID,
            "observedBuildId": "bld-observed-379",
            "expectedBuildId": request.expected_build_id,
            "effectiveModel": request.model,
            "fast": False,
        }
        validate_cursor_cloud_run_readback(request, good)
        with self.assertRaisesRegex(CursorCloudDispatchError, "public environment"):
            validate_cursor_cloud_run_readback(request, {**good, "environmentPublicId": "wrong"})
        with self.assertRaisesRegex(CursorCloudDispatchError, "effective model"):
            validate_cursor_cloud_run_readback(request, {**good, "effectiveModel": "Fast"})
        with self.assertRaisesRegex(CursorCloudDispatchError, "Fast"):
            validate_cursor_cloud_run_readback(request, {**good, "fast": True})

    def test_attestation_mismatch_blocks_mutation(self) -> None:
        good = {
            "status": "PASS",
            "noMutation": True,
            "environment": REQUEST.environment,
            "targetPath": REQUEST.target_path,
            "remote": REQUEST.target_remote + ".git",
            "repository": REQUEST.repository,
            "ref": REQUEST.ref,
            "commit": REQUEST.commit,
            "tree": REQUEST.tree,
            "toolchain": dict(REQUEST.toolchain),
            "workspaceClean": True,
        }
        validate_cursor_cloud_attestation(REQUEST, good)
        with self.assertRaisesRegex(CursorCloudDispatchError, "mismatch"):
            validate_cursor_cloud_attestation(REQUEST, {**good, "commit": "c" * 40})
        with self.assertRaisesRegex(CursorCloudDispatchError, "no-mutation"):
            validate_cursor_cloud_attestation(REQUEST, {**good, "noMutation": False})


if __name__ == "__main__":
    unittest.main()
