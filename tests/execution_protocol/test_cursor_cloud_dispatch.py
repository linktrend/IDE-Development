"""Mock-only tests for the Cursor Cloud API authority boundary."""

from __future__ import annotations

import unittest
from pathlib import Path

from core.execution.cursor_cloud_dispatch import (
    CursorCloudDispatchError,
    CursorCloudDispatchRequest,
    DurableCursorCloudIntentStore,
    dispatch_cursor_cloud,
    load_cursor_cloud_dispatch_config,
    require_cursor_cloud_api_key,
    validate_cursor_cloud_attestation,
)


REQUEST = CursorCloudDispatchRequest(
    repository="linktrend/IDE-Development",
    ref="issue/379-cursor-cloud",
    commit="a" * 40,
    tree="b" * 40,
    model="cursor-grok-4.5-high",
    expected_build_id="ide-development-2.5.1-build-379",
    toolchain={"python": "3.12", "node": "22"},
)
KEY_NAME = "CURSOR_" + "API_KEY"


class FakeCursorCloudHTTP:
    def __init__(self, store: DurableCursorCloudIntentStore) -> None:
        self.store = store
        self.calls: list[tuple[str, dict, dict]] = []

    def post(self, path, *, headers, body):
        self.calls.append((path, dict(headers), dict(body)))
        key = headers["Idempotency-Key"]
        self.assert_prepared = self.store.read(key)
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

    def test_attestation_mismatch_blocks_mutation(self) -> None:
        good = {
            "status": "PASS",
            "noMutation": True,
            "environment": REQUEST.environment,
            "repository": REQUEST.repository,
            "ref": REQUEST.ref,
            "commit": REQUEST.commit,
            "tree": REQUEST.tree,
            "toolchain": dict(REQUEST.toolchain),
        }
        validate_cursor_cloud_attestation(REQUEST, good)
        with self.assertRaisesRegex(CursorCloudDispatchError, "mismatch"):
            validate_cursor_cloud_attestation(REQUEST, {**good, "commit": "c" * 40})
        with self.assertRaisesRegex(CursorCloudDispatchError, "no-mutation"):
            validate_cursor_cloud_attestation(REQUEST, {**good, "noMutation": False})


if __name__ == "__main__":
    unittest.main()
