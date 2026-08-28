"""Focused local tests for explicit Cursor routing and model policy."""

from __future__ import annotations

import unittest
from pathlib import Path

from core.execution.cursor_cloud_dispatch import (
    CursorCloudDispatchError,
    CursorCloudDispatchRequest,
    DurableCursorCloudIntentStore,
    dispatch_cursor_cloud,
    dispatch_cursor_cloud_sdk,
    load_cursor_cloud_dispatch_config,
    load_routing_registry,
    supersede_obsolete_prepared_intents,
    validate_cursor_cloud_attestation,
    validate_cursor_cloud_run_readback,
)


REQUEST = CursorCloudDispatchRequest(
    repository="linktrend/example-app",
    target_remote="https://github.com/linktrend/example-app.git",
    ref="issue/123-example",
    commit="a" * 40,
    tree="b" * 40,
    model="grok-4.6",
    expected_build_id="example-build-123",
    toolchain={"python": "3.12", "node": "22"},
    setup_receipt_digest="sha256:" + "c" * 64,
    model_parameters={"effort": "medium", "fast": "false"},
    governed_setup=True,
)
KEY_ENV = {"CURSOR_API_KEY": "test-only-key"}


class FakeCursorHTTP:
    def __init__(self, store: DurableCursorCloudIntentStore, *, mismatch: str | None = None) -> None:
        self.store = store
        self.mismatch = mismatch
        self.calls: list[tuple[str, dict, dict]] = []
        self.get_calls: list[tuple[str, dict]] = []
        self.archive_calls: list[tuple[str, dict]] = []

    def post(self, path, *, headers, body):
        self.calls.append((path, dict(headers), dict(body)))
        if path.endswith("/archive"):
            return {"statusCode": 202}
        return {"statusCode": 201, "agentId": body["agentId"], "runId": "run-123"}

    def get(self, path, *, headers):
        self.get_calls.append((path, dict(headers)))
        values = {
            "statusCode": 200,
            "repository": REQUEST.normalized_remote,
            "ref": REQUEST.ref,
            "commit": REQUEST.commit,
            "tree": REQUEST.tree,
            "provider": REQUEST.provider,
            "model": REQUEST.model,
            "effort": "medium",
            "fast": False,
        }
        if self.mismatch:
            values[self.mismatch] = "wrong"
        return values

    def archive(self, agent_id, *, headers):
        self.archive_calls.append((agent_id, dict(headers)))
        return {"status": "archived"}


class FakeCursorSDK:
    def __init__(self) -> None:
        self.calls: list[dict] = []
        self.get_calls: list[str] = []
        self.archive_calls: list[str] = []

    def create_agent(self, **kwargs):
        self.calls.append(dict(kwargs))
        return {"statusCode": 201, "agentId": kwargs["agent_id"], "runId": "run-sdk-123"}

    def get_agent(self, agent_id):
        self.get_calls.append(agent_id)
        return {
            "statusCode": 200,
            "repository": REQUEST.normalized_remote,
            "ref": REQUEST.ref,
            "commit": REQUEST.commit,
            "tree": REQUEST.tree,
            "provider": REQUEST.provider,
            "model": REQUEST.model,
            "effort": "medium",
            "fast": False,
        }

    def archive_agent(self, agent_id):
        self.archive_calls.append(agent_id)
        return {"status": "archived"}


class CursorCloudDispatchTests(unittest.TestCase):
    def test_configs_are_versioned_and_do_not_invent_repositories(self) -> None:
        root = str(Path(__file__).resolve().parents[2])
        dispatch_config = load_cursor_cloud_dispatch_config(root)
        registry = load_routing_registry(root)
        self.assertEqual(dispatch_config["directApiRepositoryBinding"], "repos[]")
        self.assertEqual(dispatch_config["ordinaryDevelopment"]["model"], "grok-4.6")
        self.assertEqual(dispatch_config["ordinaryDevelopment"]["effort"], "medium")
        self.assertFalse(dispatch_config["ordinaryDevelopment"]["fast"])
        self.assertEqual(dispatch_config["lunaFallback"]["provider"], "codex-cli")
        self.assertEqual(registry["programs"], [])

    def test_direct_api_contains_explicit_repos_binding_and_no_environment_selector(self) -> None:
        store = DurableCursorCloudIntentStore()
        http = FakeCursorHTTP(store)
        result = dispatch_cursor_cloud(REQUEST, store, http, environment=KEY_ENV)
        self.assertEqual(result.status, "committed")
        body = http.calls[0][2]
        self.assertEqual(body["repos"], [{"url": REQUEST.normalized_remote, "startingRef": REQUEST.ref}])
        self.assertNotIn("env", body)
        self.assertNotIn("environment", body)
        self.assertEqual(http.get_calls[0][0].rsplit("/", 1)[-1], result.agent_id)

    def test_sdk_uses_equivalent_repository_bindings_and_same_readback_path(self) -> None:
        store = DurableCursorCloudIntentStore()
        sdk = FakeCursorSDK()
        result = dispatch_cursor_cloud_sdk(REQUEST, store, sdk, environment=KEY_ENV)
        self.assertEqual(result.status, "committed")
        self.assertEqual(sdk.calls[0]["repository_bindings"], REQUEST.repository_bindings)
        self.assertEqual(sdk.calls[0]["model"], "grok-4.6")
        self.assertEqual(sdk.calls[0]["model_parameters"], {"effort": "medium", "fast": "false"})
        self.assertEqual(sdk.get_calls, [result.agent_id])

    def test_readback_binds_exact_repository_ref_commit_and_tree(self) -> None:
        store = DurableCursorCloudIntentStore()
        http = FakeCursorHTTP(store, mismatch="commit")
        with self.assertRaisesRegex(CursorCloudDispatchError, "archived"):
            dispatch_cursor_cloud(REQUEST, store, http, environment=KEY_ENV)
        self.assertEqual(len(http.archive_calls), 1)
        key = next(iter(store.list_intents()))["idempotencyKey"]
        self.assertEqual(store.read(key)["state"], "REJECTED")

    def test_validate_readback_rejects_missing_or_wrong_identity(self) -> None:
        good = {
            "repository": REQUEST.normalized_remote,
            "ref": REQUEST.ref,
            "commit": REQUEST.commit,
            "tree": REQUEST.tree,
            "provider": "cursor",
            "model": "grok-4.6",
            "effort": "medium",
            "fast": False,
        }
        validate_cursor_cloud_run_readback(REQUEST, good)
        for field, value in (("repository", "https://github.com/other/repo"), ("ref", "development"), ("tree", "d" * 40), ("fast", True)):
            with self.assertRaises(CursorCloudDispatchError):
                validate_cursor_cloud_run_readback(REQUEST, {**good, field: value})
        with self.assertRaisesRegex(CursorCloudDispatchError, "setup"):
            validate_cursor_cloud_run_readback(REQUEST, {**good, "installStatus": "failed"})

    def test_unsupported_provider_model_effort_and_fast_fail_before_dispatch(self) -> None:
        cases = (
            {"provider": "codex-cli"},
            {"model": "grok-4.5"},
            {"model_parameters": {"effort": "high", "fast": "false"}},
            {"model_parameters": {"effort": "medium", "fast": "true"}},
        )
        for changes in cases:
            request = CursorCloudDispatchRequest(**{**REQUEST.__dict__, **changes})
            http = FakeCursorHTTP(DurableCursorCloudIntentStore())
            with self.assertRaises(CursorCloudDispatchError):
                dispatch_cursor_cloud(request, http.store, http, environment=KEY_ENV)
            self.assertEqual(http.calls, [])

    def test_old_saved_environment_fields_are_not_accepted_as_routing(self) -> None:
        with self.assertRaisesRegex(CursorCloudDispatchError, "saved environment"):
            from core.execution.cursor_cloud_dispatch import canonical_saved_repository_path

            canonical_saved_repository_path("linktrend/example-app", "/agent/repos/example-app")

    def test_exact_identity_and_repository_url_are_preflight_requirements(self) -> None:
        for changes in (
            {"commit": "a" * 39},
            {"tree": "b" * 41},
            {"target_remote": "https://github.com/linktrend/other"},
        ):
            with self.assertRaises(CursorCloudDispatchError):
                CursorCloudDispatchRequest(**{**REQUEST.__dict__, **changes}).validate()

    def test_missing_api_key_is_not_replaced_by_cli_login(self) -> None:
        http = FakeCursorHTTP(DurableCursorCloudIntentStore())
        with self.assertRaisesRegex(CursorCloudDispatchError, "CLI login"):
            dispatch_cursor_cloud(REQUEST, http.store, http, cursor_cli_authenticated=True)
        self.assertEqual(http.calls, [])

    def test_prepared_intent_precedes_api_and_duplicate_is_suppressed(self) -> None:
        store = DurableCursorCloudIntentStore()
        http = FakeCursorHTTP(store)
        first = dispatch_cursor_cloud(REQUEST, store, http, environment=KEY_ENV)
        repeated = dispatch_cursor_cloud(REQUEST, store, http, environment=KEY_ENV)
        self.assertEqual(first.status, "committed")
        self.assertEqual(repeated.status, "duplicate")
        self.assertEqual(len(http.calls), 1)
        self.assertEqual(store.read(first.idempotency_key)["state"], "COMMITTED")

    def test_obsolete_prepared_fixed_cap_is_superseded(self) -> None:
        store = DurableCursorCloudIntentStore()
        store.compare_and_write("old", 0, None, {"state": "PREPARED", "idempotencyKey": "old", "concurrencyPolicy": "fixed_hosted_2"})
        self.assertEqual(supersede_obsolete_prepared_intents(store), ["old"])
        self.assertEqual(store.read("old")["state"], "SUPERSEDED")

    def test_attestation_requires_exact_read_only_identity(self) -> None:
        good = {
            "status": "PASS", "noMutation": True, "repository": REQUEST.repository,
            "remote": REQUEST.target_remote, "ref": REQUEST.ref, "commit": REQUEST.commit,
            "tree": REQUEST.tree, "toolchain": dict(REQUEST.toolchain), "workspaceClean": True,
        }
        validate_cursor_cloud_attestation(REQUEST, good)
        with self.assertRaises(CursorCloudDispatchError):
            validate_cursor_cloud_attestation(REQUEST, {**good, "commit": "c" * 40})


if __name__ == "__main__":
    unittest.main()
