"""Mock-only tests for the Cursor Cloud API authority boundary."""

from __future__ import annotations

import unittest
from pathlib import Path

from core.execution.cursor_cloud_dispatch import (
    CursorCloudDispatchError,
    CursorCloudDispatchRequest,
    DurableCursorCloudIntentStore,
    ENV_PUBLIC_ID,
    apply_configured_audit_model_parameters,
    cursor_cloud_client_agent_id,
    cursor_cloud_idempotency_key,
    dispatch_cursor_cloud,
    dispatch_cursor_cloud_sdk,
    orchestrate_cursor_cloud_dispatch,
    supersede_obsolete_prepared_intents,
    load_cursor_cloud_dispatch_config,
    require_cursor_cloud_api_key,
    validate_cursor_cloud_run_readback,
    validate_cursor_cloud_attestation,
    validate_repository_scope,
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
    model_parameters={"effort": "medium", "fast": "false"},
)
KEY_NAME = "CURSOR_" + "API_KEY"


class FakeCursorCloudHTTP:
    def __init__(self, store: DurableCursorCloudIntentStore, *, fail_once: bool = False) -> None:
        self.store = store
        self.fail_once = fail_once
        self.calls: list[tuple[str, dict, dict]] = []
        self.get_calls: list[tuple[str, dict]] = []

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

    def get(self, path, *, headers):
        self.get_calls.append((path, dict(headers)))
        agent_id = path.rsplit("/", 1)[-1]
        return {
            "statusCode": 200,
            "agentId": agent_id,
            "runId": "run-379",
            "repository": REQUEST.target_remote,
            "startingRef": REQUEST.ref,
            "environment": {"type": "cloud", "name": "IDE Development 2.5.1"},
            "environmentPublicId": ENV_PUBLIC_ID,
            "observedBuildId": "bld-observed-379",
            "expectedBuildId": REQUEST.expected_build_id,
            "effectiveModel": REQUEST.model,
            "modelParameters": {"effort": "medium", "fast": "false"},
            "fast": False,
        }


class ConfigurableCursorCloudHTTP(FakeCursorCloudHTTP):
    """Fake HTTP port with adversarial GET readback overrides."""

    def __init__(
        self,
        store: DurableCursorCloudIntentStore,
        *,
        get_overrides: dict | None = None,
        omit_get_fields: tuple[str, ...] = (),
        fail_once: bool = False,
    ) -> None:
        super().__init__(store, fail_once=fail_once)
        self.get_overrides = dict(get_overrides or {})
        self.omit_get_fields = omit_get_fields

    def get(self, path, *, headers):
        response = super().get(path, headers=headers)
        for field in self.omit_get_fields:
            response.pop(field, None)
        if self.get_overrides:
            response.update(self.get_overrides)
        return response


class FakeCursorCloudSDK:
    def __init__(self) -> None:
        self.calls = []

    def create_agent(self, **kwargs):
        self.calls.append(dict(kwargs))
        return {
            "statusCode": 201,
            "agentId": kwargs["agent_id"],
            "runId": "run-379",
            "model": kwargs["model"],
            "repository": kwargs["repository_url"],
            "startingRef": kwargs["starting_ref"],
        }


class CursorCloudDispatchTests(unittest.TestCase):
    def test_obsolete_prepared_fixed_cap_is_superseded_but_committed_is_preserved(self) -> None:
        store = DurableCursorCloudIntentStore()
        store.compare_and_write(
            "old-fixed",
            0,
            None,
            {
                "state": "PREPARED",
                "idempotencyKey": "old-fixed",
                "concurrencyPolicy": "fixed_hosted_2",
            },
        )
        store.compare_and_write(
            "completed",
            0,
            None,
            {
                "state": "COMMITTED",
                "idempotencyKey": "completed",
                "concurrencyPolicy": "fixed_hosted_2",
            },
        )
        self.assertEqual(supersede_obsolete_prepared_intents(store), ["old-fixed"])
        self.assertEqual(store.read("old-fixed")["state"], "SUPERSEDED")
        self.assertEqual(store.read("completed")["state"], "COMMITTED")

    def test_dispatch_requires_enumerable_intent_store_for_supersession(self) -> None:
        class ReadOnlyStore:
            def read(self, key):
                return None

            def compare_and_write(self, *args, **kwargs):
                raise AssertionError("must fail before write")

        http = FakeCursorCloudHTTP(DurableCursorCloudIntentStore())
        with self.assertRaisesRegex(CursorCloudDispatchError, "enumerate"):
            dispatch_cursor_cloud(
                REQUEST,
                ReadOnlyStore(),
                http,
                environment={KEY_NAME: "test-only-key"},
            )

    def test_config_is_exact_and_cli_login_is_not_authority(self) -> None:
        config = load_cursor_cloud_dispatch_config(str(Path(__file__).resolve().parents[2]))
        self.assertEqual(config["apiBaseUrl"], "https://api.cursor.com")
        self.assertEqual(config["apiPath"], "/v1/agents")
        self.assertEqual(config["preferredClient"], "cursor-python-sdk")
        self.assertEqual(config["sdkPackage"], "cursor-sdk")
        self.assertEqual(config["sdkRepositoryBinding"], "repository-url-and-starting-ref")
        self.assertEqual(config["auditModelParameters"], {"effort": "medium", "fast": "false"})
        self.assertTrue(config["restReadbackRequired"])
        self.assertTrue(config["singleRepositoryPerRun"])
        self.assertTrue(config["multiRepositoryRequiresExplicitScope"])
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

    def test_sdk_path_binds_exact_repository_and_starting_ref(self) -> None:
        store = DurableCursorCloudIntentStore()
        sdk = FakeCursorCloudSDK()
        expected_client_id = cursor_cloud_client_agent_id(REQUEST)
        # The fake must echo the deterministic caller-owned agent identity.
        sdk.create_agent = lambda **kwargs: (
            sdk.calls.append(dict(kwargs))
            or {
                "statusCode": 201,
                "agentId": expected_client_id,
                "runId": "run-379",
                "model": kwargs["model"],
                "repository": kwargs["repository_url"],
                "startingRef": kwargs["starting_ref"],
            }
        )
        result = dispatch_cursor_cloud_sdk(
            REQUEST, store, sdk, environment={KEY_NAME: "test-only-key"}
        )
        self.assertEqual(result.status, "committed")
        self.assertEqual(sdk.calls[0]["repository_url"], REQUEST.target_remote)
        self.assertEqual(sdk.calls[0]["starting_ref"], REQUEST.ref)
        self.assertEqual(sdk.calls[0]["model"], REQUEST.model)
        self.assertEqual(
            sdk.calls[0]["model_parameters"],
            {"effort": "medium", "fast": "false"},
        )

    def test_grok_audit_rejects_missing_configured_model_parameters(self) -> None:
        request = CursorCloudDispatchRequest(
            **{**REQUEST.__dict__, "model_parameters": {}}
        )
        with self.assertRaisesRegex(CursorCloudDispatchError, "audit_parameter"):
            request.validate()

    def test_orchestrator_applies_configured_audit_model_parameters(self) -> None:
        config = load_cursor_cloud_dispatch_config(str(Path(__file__).resolve().parents[2]))
        bare = CursorCloudDispatchRequest(
            **{**REQUEST.__dict__, "model_parameters": {}}
        )
        bound = apply_configured_audit_model_parameters(bare, config)
        self.assertEqual(
            dict(bound.model_parameters),
            {"effort": "medium", "fast": "false"},
        )

    def test_orchestrator_requires_rest_get_readback_before_commit(self) -> None:
        store = DurableCursorCloudIntentStore()
        http = FakeCursorCloudHTTP(store)
        result = orchestrate_cursor_cloud_dispatch(
            REQUEST,
            store,
            http,
            sdk=FakeCursorCloudSDK(),
            repo_root=str(Path(__file__).resolve().parents[2]),
            environment={KEY_NAME: "test-only-key"},
        )
        self.assertEqual(result.status, "committed")
        self.assertEqual(len(http.get_calls), 1)
        self.assertTrue(http.get_calls[0][0].endswith(result.agent_id))
        self.assertEqual(store.read(result.idempotency_key)["state"], "COMMITTED")

    def test_orchestrator_falls_back_to_rest_when_sdk_unavailable(self) -> None:
        class UnavailableSDK:
            def create_agent(self, **kwargs):
                raise CursorCloudDispatchError(
                    "cursor_cloud_sdk_unavailable",
                    "install cursor-sdk or use the explicit REST fallback",
                )

        store = DurableCursorCloudIntentStore()
        http = FakeCursorCloudHTTP(store)
        result = orchestrate_cursor_cloud_dispatch(
            REQUEST,
            store,
            http,
            sdk=UnavailableSDK(),
            repo_root=str(Path(__file__).resolve().parents[2]),
            environment={KEY_NAME: "test-only-key"},
        )
        self.assertEqual(result.status, "committed")
        self.assertEqual(len(http.calls), 1)
        self.assertEqual(len(http.get_calls), 1)

    def test_multi_repository_requires_explicit_scope(self) -> None:
        config = load_cursor_cloud_dispatch_config(str(Path(__file__).resolve().parents[2]))
        implicit = CursorCloudDispatchRequest(
            **{
                **REQUEST.__dict__,
                "repository": "linktrend/LiNKbrain",
                "target_path": "/agent/repos/LiNKbrain",
                "target_remote": "https://github.com/linktrend/LiNKbrain",
                "explicit_scope_repositories": ("linktrend/IDE-Development",),
                "explicit_scope_remotes": {},
            }
        )
        with self.assertRaisesRegex(CursorCloudDispatchError, "remote"):
            validate_repository_scope(implicit, config)

    def test_multi_repository_explicit_scope_is_admitted(self) -> None:
        config = load_cursor_cloud_dispatch_config(str(Path(__file__).resolve().parents[2]))
        scoped = CursorCloudDispatchRequest(
            **{
                **REQUEST.__dict__,
                "explicit_scope_repositories": ("linktrend/LiNKbrain",),
                "explicit_scope_remotes": {
                    "linktrend/LiNKbrain": "https://github.com/linktrend/LiNKbrain",
                },
            }
        )
        validate_repository_scope(scoped, config)
        store = DurableCursorCloudIntentStore()
        sdk = FakeCursorCloudSDK()
        expected_client_id = cursor_cloud_client_agent_id(scoped)
        sdk.create_agent = lambda **kwargs: (
            sdk.calls.append(dict(kwargs))
            or {
                "statusCode": 201,
                "agentId": expected_client_id,
                "runId": "run-379",
                "model": kwargs["model"],
                "repository": kwargs["repository_url"],
                "startingRef": kwargs["starting_ref"],
            }
        )
        http = FakeCursorCloudHTTP(store)
        result = orchestrate_cursor_cloud_dispatch(
            scoped,
            store,
            http,
            sdk=sdk,
            config=config,
            environment={KEY_NAME: "test-only-key"},
        )
        self.assertEqual(result.status, "committed")
        self.assertEqual(
            sdk.calls[0]["repository_bindings"],
            [
                (scoped.target_remote, scoped.ref),
                ("https://github.com/linktrend/LiNKbrain", scoped.ref),
            ],
        )

    def test_sdk_fast_parameter_is_rejected_before_dispatch(self) -> None:
        request = CursorCloudDispatchRequest(
            **{**REQUEST.__dict__, "model_parameters": {"effort": "medium", "fast": "true"}}
        )
        with self.assertRaisesRegex(CursorCloudDispatchError, "fast=false"):
            request.validate()

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
        client_agent_id = cursor_cloud_client_agent_id(request)
        good = {
            "environment": request.environment,
            "environmentPublicId": ENV_PUBLIC_ID,
            "observedBuildId": "bld-observed-379",
            "expectedBuildId": request.expected_build_id,
            "effectiveModel": request.model,
            "fast": False,
            "agentId": client_agent_id,
            "runId": "run-379",
            "repositoryUrl": request.target_remote,
            "startingRef": request.ref,
        }
        validate_cursor_cloud_run_readback(
            request, good, expected_agent_id=client_agent_id, expected_run_id="run-379"
        )
        with self.assertRaisesRegex(CursorCloudDispatchError, "public environment"):
            validate_cursor_cloud_run_readback(
                request,
                {**good, "environmentPublicId": "wrong"},
                expected_agent_id=client_agent_id,
                expected_run_id="run-379",
            )
        with self.assertRaisesRegex(CursorCloudDispatchError, "effective model"):
            validate_cursor_cloud_run_readback(
                request,
                {**good, "effectiveModel": "Fast"},
                expected_agent_id=client_agent_id,
                expected_run_id="run-379",
            )
        with self.assertRaisesRegex(CursorCloudDispatchError, "Fast"):
            validate_cursor_cloud_run_readback(
                request,
                {**good, "fast": True},
                expected_agent_id=client_agent_id,
                expected_run_id="run-379",
            )
        with self.assertRaisesRegex(CursorCloudDispatchError, "repository"):
            validate_cursor_cloud_run_readback(
                request,
                {**good, "repositoryUrl": "https://github.com/linktrend/LiNKharness"},
                expected_agent_id=client_agent_id,
                expected_run_id="run-379",
            )
        with self.assertRaisesRegex(CursorCloudDispatchError, "starting ref"):
            validate_cursor_cloud_run_readback(
                request,
                {**good, "startingRef": "development"},
                expected_agent_id=client_agent_id,
                expected_run_id="run-379",
            )
        with self.assertRaisesRegex(CursorCloudDispatchError, "run identity"):
            validate_cursor_cloud_run_readback(
                request,
                {**good, "runId": "run-wrong"},
                expected_agent_id=client_agent_id,
                expected_run_id="run-379",
            )

    def test_adversarial_rest_readback_blocks_commit_before_committed(self) -> None:
        config = load_cursor_cloud_dispatch_config(str(Path(__file__).resolve().parents[2]))
        key = cursor_cloud_client_agent_id(REQUEST)
        scenarios = (
            ("wrong_repository", {"repository": "https://github.com/linktrend/LiNKharness"}, (), "repository"),
            ("wrong_ref", {"startingRef": "development"}, (), "starting ref"),
            ("wrong_run_id", {"runId": "run-adversarial"}, (), "run identity"),
            ("omit_environment_public_id", {}, ("environmentPublicId",), "public environment"),
            ("omit_expected_build_id", {}, ("expectedBuildId",), "expected build"),
            ("omit_effective_model", {}, ("effectiveModel",), "effective model"),
            ("omit_agent_id", {}, ("agentId",), "agent identity"),
            ("omit_run_id", {}, ("runId",), "run identity"),
        )
        for label, overrides, omit, err_pattern in scenarios:
            with self.subTest(scenario=label):
                store = DurableCursorCloudIntentStore()
                http = ConfigurableCursorCloudHTTP(
                    store, get_overrides=overrides, omit_get_fields=omit
                )
                with self.assertRaisesRegex(CursorCloudDispatchError, err_pattern):
                    orchestrate_cursor_cloud_dispatch(
                        REQUEST,
                        store,
                        http,
                        sdk=FakeCursorCloudSDK(),
                        config=config,
                        environment={KEY_NAME: "test-only-key"},
                    )
                prepared = store.read(cursor_cloud_idempotency_key(REQUEST))
                self.assertIsNotNone(prepared)
                self.assertEqual(prepared["state"], "PREPARED", label)
                self.assertEqual(len(http.get_calls), 1, label)

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
