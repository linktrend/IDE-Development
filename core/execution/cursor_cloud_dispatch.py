"""Fail-closed Cursor Cloud SDK/API dispatch contract.

The authenticated ``cursor-agent`` CLI is a local-workspace capability.  It is
not evidence that this process can create a Cursor Cloud agent.  Cloud
creation therefore requires ``CURSOR_API_KEY``.  The Python SDK is the
preferred orchestration client because it binds the repository URL and
starting ref explicitly; the HTTP port remains the verification/fallback
surface.
"""

from __future__ import annotations

import copy
import hashlib
import json
import os
import re
from dataclasses import dataclass, field, replace
from typing import Any, Mapping, Protocol, Sequence
from urllib.parse import urlsplit, urlunsplit


CONTROL_ID = "cursor-cloud-dispatch-v1"
ADAPTIVE_CAPACITY_POLICY = "adaptive_minimum_of_live_evidence"
API_BASE_URL = "https://api.cursor.com"
API_PATH = "/v1/agents"
ENV_TYPE = "cloud"
ENV_NAME = "IDE Development 2.5.1"
ENV_PUBLIC_ID = "1937ddb1-9d3e-11f1-a7d1-d6b4613131ce"
SAVED_REPOSITORY_ROOT = "/agent/repos"
MAX_API_ATTEMPTS = 2
_HEX = re.compile(r"^[0-9a-f]{40,64}$")


class CursorCloudDispatchError(RuntimeError):
    """A Cursor Cloud request was rejected before or after external I/O."""

    def __init__(self, code: str, detail: str, **diagnostics: Any) -> None:
        self.code = code
        self.detail = detail
        self.diagnostics = diagnostics
        super().__init__(f"{code}: {detail}")


@dataclass(frozen=True)
class CursorCloudDispatchRequest:
    repository: str
    target_path: str
    target_remote: str
    ref: str
    commit: str
    tree: str
    model: str
    expected_build_id: str
    toolchain: Mapping[str, str]
    setup_receipt_digest: str
    model_parameters: Mapping[str, str] = field(default_factory=dict)
    explicit_scope_repositories: tuple[str, ...] = ()
    explicit_scope_remotes: Mapping[str, str] = field(default_factory=dict)
    environment_name: str = ENV_NAME
    environment_public_id: str = ENV_PUBLIC_ID
    governed_setup: bool = False
    concurrency_policy: str = ADAPTIVE_CAPACITY_POLICY

    def validate(self) -> None:
        if not self.repository.strip() or not self.ref.strip():
            raise CursorCloudDispatchError(
                "cursor_cloud_identity_missing", "repository and ref are required"
            )
        repository_parts = self.repository.split("/")
        if (
            len(repository_parts) != 2
            or any(part in {"", ".", ".."} or "\\" in part for part in repository_parts)
        ):
            raise CursorCloudDispatchError(
                "cursor_cloud_repository_invalid",
                "repository must be an owner/name identity without traversal",
            )
        self.resolved_target_path
        normalize_repository_remote(self.target_remote)
        if not self.governed_setup:
            raise CursorCloudDispatchError(
                "cursor_cloud_governed_setup_required",
                "target checkout setup must be explicitly governed before dispatch",
            )
        if not re.fullmatch(r"sha256:[0-9a-f]{64}", self.setup_receipt_digest):
            raise CursorCloudDispatchError(
                "cursor_cloud_setup_receipt_invalid",
                "an exact governed setup receipt digest is required",
            )
        if not _HEX.fullmatch(self.commit) or not _HEX.fullmatch(self.tree):
            raise CursorCloudDispatchError(
                "cursor_cloud_identity_invalid",
                "commit and tree must be exact hexadecimal git identities",
            )
        model = self.model.strip()
        if not model:
            raise CursorCloudDispatchError(
                "cursor_cloud_model_missing", "an exact non-Fast model is required"
            )
        if model.casefold() == "fast" or model.casefold().startswith("fast-"):
            raise CursorCloudDispatchError(
                "cursor_cloud_fast_model_forbidden",
                "Fast is not an admitted Cursor Cloud model",
            )
        validate_grok_audit_model_parameters(self)
        if str(self.model_parameters.get("fast", "false")).casefold() != "false":
            raise CursorCloudDispatchError(
                "cursor_cloud_fast_model_forbidden",
                "SDK model parameters must explicitly keep Fast disabled",
            )
        if not self.expected_build_id.strip():
            raise CursorCloudDispatchError(
                "cursor_cloud_build_provenance_missing",
                "expected build ID is required as provenance",
            )
        if self.environment_name != ENV_NAME:
            raise CursorCloudDispatchError(
                "cursor_cloud_environment_mismatch",
                "dispatch must target the named IDE Development 2.5.1 cloud environment",
            )
        if self.environment_public_id != ENV_PUBLIC_ID:
            raise CursorCloudDispatchError(
                "cursor_cloud_environment_public_id_mismatch",
                "dispatch must target the saved IDE Development 2.5.1 public environment identity",
            )
        if not self.toolchain or any(
            not str(key).strip() or not str(value).strip()
            for key, value in self.toolchain.items()
        ):
            raise CursorCloudDispatchError(
                "cursor_cloud_toolchain_missing", "toolchain attestation data is required"
            )
        if self.concurrency_policy != ADAPTIVE_CAPACITY_POLICY:
            raise CursorCloudDispatchError(
                "cursor_cloud_capacity_policy_invalid",
                "dispatch must use the adaptive capacity policy",
            )

    @property
    def environment(self) -> dict[str, str]:
        return {"type": ENV_TYPE, "name": self.environment_name}

    @property
    def environment_identity(self) -> dict[str, str]:
        """The named environment plus provider identity, kept out of API selectors."""

        return {**self.environment, "publicId": self.environment_public_id}

    @property
    def resolved_target_path(self) -> str:
        return canonical_saved_repository_path(self.repository, self.target_path)


def canonical_saved_repository_path(repository: str, target_path: str) -> str:
    """Resolve only ``/agent/repos/<repo>``; reject primary/default ambiguity."""

    repo_name = repository.rstrip("/").split("/")[-1]
    raw = str(target_path or "")
    if not repo_name or not raw or "\\" in raw or "//" in raw:
        raise CursorCloudDispatchError(
            "cursor_cloud_target_path_invalid", "target repository path is missing or ambiguous"
        )
    if raw.startswith(SAVED_REPOSITORY_ROOT + "/"):
        relative = raw[len(SAVED_REPOSITORY_ROOT) + 1 :]
    elif raw.startswith("/"):
        raise CursorCloudDispatchError(
            "cursor_cloud_target_path_escape", "target path is outside the saved repository root"
        )
    else:
        relative = raw
    segments = relative.split("/")
    if len(segments) != 1 or segments[0] in {"", ".", ".."} or segments[0] != repo_name:
        raise CursorCloudDispatchError(
            "cursor_cloud_target_path_ambiguous",
            "target path must select the requested repository, not the environment primary repo",
        )
    return f"{SAVED_REPOSITORY_ROOT}/{repo_name}"


def normalize_repository_remote(remote: str) -> str:
    """Normalize local ``origin`` readback for exact repository comparison."""

    value = str(remote or "").strip()
    parsed = urlsplit(value)
    if (
        parsed.scheme not in {"http", "https"}
        or not parsed.hostname
        or parsed.username
        or parsed.password
        or parsed.query
        or parsed.fragment
    ):
        raise CursorCloudDispatchError(
            "cursor_cloud_remote_invalid",
            "remote must be an HTTP(S) URL without credentials",
        )
    path = parsed.path.rstrip("/")
    if path.endswith(".git"):
        path = path[:-4]
    if not path or "//" in path or ".." in path.split("/"):
        raise CursorCloudDispatchError(
            "cursor_cloud_remote_invalid", "remote path is not canonical"
        )
    return urlunsplit((parsed.scheme.casefold(), parsed.hostname.casefold(), path, "", ""))


@dataclass(frozen=True)
class CursorCloudDispatchResult:
    status: str
    idempotency_key: str
    client_agent_id: str
    agent_id: str
    run_id: str
    environment: Mapping[str, str]
    environment_public_id: str
    model: str
    expected_build_id: str
    revision: int
    attestation_prompt: str


class CursorCloudIntentStore(Protocol):
    def read(self, idempotency_key: str) -> Mapping[str, Any] | None: ...

    def compare_and_write(
        self,
        idempotency_key: str,
        expected_revision: int,
        expected_digest: str | None,
        payload: Mapping[str, Any],
    ) -> None: ...

    def list_intents(self) -> list[Mapping[str, Any]]: ...


class CursorCloudHTTPPort(Protocol):
    def post(
        self, path: str, *, headers: Mapping[str, str], body: Mapping[str, Any]
    ) -> Mapping[str, Any]: ...

    def get(self, path: str, *, headers: Mapping[str, str]) -> Mapping[str, Any]: ...


def is_grok_audit_model(model: str) -> bool:
    return "grok" in str(model or "").casefold()


def apply_configured_audit_model_parameters(
    request: CursorCloudDispatchRequest,
    config: Mapping[str, Any],
) -> CursorCloudDispatchRequest:
    """Bind configured Grok audit parameters before dispatch validation."""

    if not is_grok_audit_model(request.model):
        return request
    audit = dict(config["auditModelParameters"])
    merged = dict(audit)
    merged.update(dict(request.model_parameters))
    return replace(request, model_parameters=merged)


def validate_grok_audit_model_parameters(request: CursorCloudDispatchRequest) -> None:
    if not is_grok_audit_model(request.model):
        return
    required = {"effort": "medium", "fast": "false"}
    for key, expected in required.items():
        if key not in request.model_parameters:
            raise CursorCloudDispatchError(
                "cursor_cloud_audit_parameter_missing",
                f"Grok audit dispatch requires explicit model parameter {key}",
                parameter=key,
            )
        if str(request.model_parameters[key]) != expected:
            raise CursorCloudDispatchError(
                "cursor_cloud_audit_parameter_mismatch",
                f"Grok audit dispatch requires {key}={expected}",
                parameter=key,
            )


def validate_repository_scope(
    request: CursorCloudDispatchRequest, config: Mapping[str, Any]
) -> None:
    """Default to one repository per run; admit coordinated multi-repo only explicitly."""

    extras = tuple(request.explicit_scope_repositories)
    if not extras:
        if request.explicit_scope_remotes:
            raise CursorCloudDispatchError(
                "cursor_cloud_explicit_scope_remote_without_repositories",
                "explicit scope remotes require coordinated repository identities",
            )
        return
    if not config.get("multiRepositoryRequiresExplicitScope"):
        raise CursorCloudDispatchError(
            "cursor_cloud_multi_repository_forbidden",
            "multi-repository dispatch requires explicit scope admission",
        )
    seen = {request.repository}
    for repo in extras:
        parts = repo.split("/")
        if (
            len(parts) != 2
            or any(part in {"", ".", ".."} or "\\" in part for part in parts)
            or repo in seen
        ):
            raise CursorCloudDispatchError(
                "cursor_cloud_explicit_scope_repository_invalid",
                "explicit scope repository identity is invalid or duplicated",
            )
        seen.add(repo)
        remote = str(request.explicit_scope_remotes.get(repo) or "")
        if not remote:
            raise CursorCloudDispatchError(
                "cursor_cloud_explicit_scope_remote_missing",
                "each explicit-scope repository requires a governed remote",
                repository=repo,
            )
        normalize_repository_remote(remote)


def _sdk_repository_bindings(
    request: CursorCloudDispatchRequest,
) -> list[tuple[str, str]]:
    bindings = [(normalize_repository_remote(request.target_remote), request.ref)]
    for repo in request.explicit_scope_repositories:
        remote = normalize_repository_remote(str(request.explicit_scope_remotes[repo]))
        bindings.append((remote, request.ref))
    deduped: list[tuple[str, str]] = []
    seen: set[tuple[str, str]] = set()
    for item in bindings:
        if item in seen:
            continue
        seen.add(item)
        deduped.append(item)
    return deduped


class CursorCloudSDKPort(Protocol):
    def create_agent(
        self,
        *,
        api_key: str,
        model: str,
        model_parameters: Mapping[str, str],
        repository_url: str,
        starting_ref: str,
        repository_bindings: Sequence[tuple[str, str]] | None = None,
        prompt: str,
        name: str,
        agent_id: str,
        idempotency_key: str,
    ) -> Mapping[str, Any]: ...


class CursorPythonSDKPort:
    """Lazy real ``cursor-sdk`` adapter.

    Import is deferred so validation and consumers that use only REST do not
    acquire a mandatory runtime dependency.  Handles are retained because a
    cloud agent must outlive the create call.
    """

    def __init__(self) -> None:
        self._agents: dict[str, Any] = {}

    def create_agent(
        self,
        *,
        api_key: str,
        model: str,
        model_parameters: Mapping[str, str],
        repository_url: str,
        starting_ref: str,
        repository_bindings: Sequence[tuple[str, str]] | None = None,
        prompt: str,
        name: str,
        agent_id: str,
        idempotency_key: str,
    ) -> Mapping[str, Any]:
        try:
            from cursor_sdk import (
                Agent,
                CloudAgentOptions,
                CloudRepository,
                ModelParameterValue,
                ModelSelection,
            )
        except ImportError as exc:  # pragma: no cover - depends on host runtime
            raise CursorCloudDispatchError(
                "cursor_cloud_sdk_unavailable",
                "install cursor-sdk or use the explicit REST fallback",
            ) from exc
        bindings = list(repository_bindings or [(repository_url, starting_ref)])
        agent = Agent.create(
            model=ModelSelection(
                id=model,
                params=[
                    ModelParameterValue(id=key, value=value)
                    for key, value in sorted(model_parameters.items())
                ],
            ),
            api_key=api_key,
            name=name,
            agent_id=agent_id,
            idempotency_key=idempotency_key,
            cloud=CloudAgentOptions(
                repos=[
                    CloudRepository(url=url, starting_ref=ref)
                    for url, ref in bindings
                ],
                auto_create_pr=False,
            ),
        )
        run = agent.send(prompt)
        agent_id = str(getattr(agent, "agent_id", "") or "")
        run_id = str(getattr(run, "run_id", None) or getattr(run, "id", "") or "")
        if not agent_id or not run_id:
            raise CursorCloudDispatchError(
                "cursor_cloud_sdk_identity_missing",
                "SDK create/send did not return durable agent and run identities",
            )
        self._agents[agent_id] = agent
        return {
            "statusCode": 201,
            "agentId": agent_id,
            "runId": run_id,
            "model": model,
            "repository": repository_url,
            "startingRef": starting_ref,
        }


class _SDKAsHTTPPort:
    """Normalize the SDK create/send result into the existing commit path."""

    def __init__(self, request: CursorCloudDispatchRequest, sdk: CursorCloudSDKPort) -> None:
        self.request = request
        self.sdk = sdk

    def post(
        self, path: str, *, headers: Mapping[str, str], body: Mapping[str, Any]
    ) -> Mapping[str, Any]:
        if path != API_PATH:
            raise CursorCloudDispatchError("cursor_cloud_sdk_path_invalid", "unexpected SDK path")
        response = dict(
            self.sdk.create_agent(
                api_key=str(headers["Authorization"]).removeprefix("Bearer "),
                model=str(body["model"]),
                model_parameters=self.request.model_parameters,
                repository_url=normalize_repository_remote(self.request.target_remote),
                starting_ref=self.request.ref,
                repository_bindings=_sdk_repository_bindings(self.request),
                prompt=str(body["prompt"]),
                name=f"{self.request.repository}:{self.request.ref}",
                agent_id=str(body["agentId"]),
                idempotency_key=str(headers["Idempotency-Key"]),
            )
        )
        if response.get("repository") != normalize_repository_remote(self.request.target_remote):
            raise CursorCloudDispatchError(
                "cursor_cloud_sdk_repository_mismatch",
                "SDK response repository does not match the governed target",
            )
        if response.get("startingRef") != self.request.ref:
            raise CursorCloudDispatchError(
                "cursor_cloud_sdk_ref_mismatch",
                "SDK response starting ref does not match the governed target",
            )
        response["env"] = self.request.environment
        return response


class DurableCursorCloudIntentStore:
    """Minimal durable-store-shaped implementation for local runtimes/tests."""

    def __init__(self) -> None:
        self._records: dict[str, dict[str, Any]] = {}
        self.read_count = 0
        self.write_count = 0

    def read(self, idempotency_key: str) -> dict[str, Any] | None:
        self.read_count += 1
        value = self._records.get(idempotency_key)
        return copy.deepcopy(value) if value is not None else None

    def list_intents(self) -> list[dict[str, Any]]:
        return [copy.deepcopy(value) for value in self._records.values()]

    def compare_and_write(
        self,
        idempotency_key: str,
        expected_revision: int,
        expected_digest: str | None,
        payload: Mapping[str, Any],
    ) -> None:
        current = self._records.get(idempotency_key)
        current_revision = int(current["revision"]) if current else 0
        current_digest = str(current["digest"]) if current else None
        if (current_revision, current_digest) != (expected_revision, expected_digest):
            raise CursorCloudDispatchError(
                "cursor_cloud_intent_cas_collision", "dispatch intent changed concurrently"
            )
        stored = {"revision": expected_revision + 1, **copy.deepcopy(dict(payload))}
        stored["digest"] = _stored_digest(stored)
        self._records[idempotency_key] = stored
        self.write_count += 1


def _canonical(value: Mapping[str, Any]) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode()


def _digest(value: Mapping[str, Any]) -> str:
    return "sha256:" + hashlib.sha256(_canonical(value)).hexdigest()


def _stored_digest(value: Mapping[str, Any]) -> str:
    return _digest({key: item for key, item in value.items() if key != "digest"})


def cursor_cloud_idempotency_key(request: CursorCloudDispatchRequest) -> str:
    request.validate()
    identity = {
        "control": CONTROL_ID,
        "repository": request.repository,
        "targetPath": request.resolved_target_path,
        "targetRemote": normalize_repository_remote(request.target_remote),
        "ref": request.ref,
        "commit": request.commit,
        "tree": request.tree,
        "model": request.model,
        "modelParameters": dict(request.model_parameters),
        "explicitScopeRepositories": list(request.explicit_scope_repositories),
        "explicitScopeRemotes": {
            repo: normalize_repository_remote(remote)
            for repo, remote in sorted(request.explicit_scope_remotes.items())
        },
        "environment": request.environment,
        "environmentPublicId": request.environment_public_id,
        "expectedBuildId": request.expected_build_id,
        "toolchain": dict(request.toolchain),
        "governedSetup": request.governed_setup,
        "setupReceiptDigest": request.setup_receipt_digest,
        "concurrencyPolicy": request.concurrency_policy,
    }
    return CONTROL_ID + ":" + hashlib.sha256(_canonical(identity)).hexdigest()


def supersede_obsolete_prepared_intents(
    store: CursorCloudIntentStore,
    *,
    policy: str = ADAPTIVE_CAPACITY_POLICY,
) -> list[str]:
    """Invalidate every uncompleted intent bound to the retired fixed cap.

    Completed evidence is immutable.  A store that cannot enumerate intents is
    rejected rather than silently leaving an obsolete PREPARED record alive.
    """

    list_intents = getattr(store, "list_intents", None)
    if not callable(list_intents):
        raise CursorCloudDispatchError(
            "cursor_cloud_intent_supersession_unavailable",
            "intent store cannot enumerate PREPARED records",
        )
    superseded: list[str] = []
    for record in list_intents():
        if not isinstance(record, Mapping) or record.get("state") != "PREPARED":
            continue
        bound_policy = record.get("concurrencyPolicy")
        fixed = bound_policy in {"fixed_hosted_2", "fixed_hosted_worker_cap", "max_hosted_2"}
        if not fixed and "maxHostedWorkers" in record:
            fixed = record.get("maxHostedWorkers") == 2
        if not fixed:
            continue
        key = str(record.get("idempotencyKey") or "")
        if not key:
            raise CursorCloudDispatchError(
                "cursor_cloud_intent_supersession_invalid",
                "obsolete PREPARED intent has no idempotency key",
            )
        revision = int(record.get("revision", 0))
        expected_digest = str(record.get("digest") or "") or None
        payload = dict(record)
        payload.update({
            "state": "SUPERSEDED",
            "supersededByPolicy": policy,
            "supersessionReason": "obsolete_fixed_hosted_worker_cap",
        })
        payload.pop("digest", None)
        payload.pop("revision", None)
        store.compare_and_write(key, revision, expected_digest, payload)
        superseded.append(key)
    return superseded


def cursor_cloud_client_agent_id(request: CursorCloudDispatchRequest) -> str:
    """Return a deterministic client id; retries cannot create a second agent."""

    return "ide-" + hashlib.sha256(cursor_cloud_idempotency_key(request).encode()).hexdigest()[:32]


def build_attestation_prompt(request: CursorCloudDispatchRequest) -> str:
    request.validate()
    matrix = f"repository={request.repository}; path={request.resolved_target_path}; remote={normalize_repository_remote(request.target_remote)}; ref={request.ref}; commit={request.commit}; tree={request.tree}"
    toolchain = ", ".join(f"{key}={value}" for key, value in sorted(request.toolchain.items()))
    return (
        "ATTESTATION ONLY. Do not perform product mutation, commit, push, or run migrations. "
        f"First cd to and resolve the exact saved-environment target path {request.resolved_target_path}; "
        f"the environment primary repository is not the target. Verify a clean workspace and normalized remote. "
        f"During governed setup only, verify exact normalized origin and cleanliness, advertise the exact issue ref, "
        f"then perform one no-tags/no-prune single-ref fetch into refs/linktrend/attestation/PKT-01; "
        f"use a deterministic detached isolated worktree at the approved commit/tree ({request.commit}/{request.tree}) "
        f"and reuse it only if the registered worktree is exact and clean. Then "
        "report PASS/FAIL for the exact remote, repository/path/ref/commit/tree matrix "
        f"({matrix}), and toolchain ({toolchain}). "
        f"Environment={{type:{ENV_TYPE}, name:{request.environment_name}, publicId:{request.environment_public_id}}}. "
        f"Governed setup receipt {request.setup_receipt_digest} must remain provenance only. "
        f"Expected build ID {request.expected_build_id} is provenance only; it is not a selectable API parameter. "
        "A wrong remote, path, ref, commit, tree, environment, or toolchain is a hard stop and mutation remains unauthorized."
    )


def require_cursor_cloud_api_key(
    environment: Mapping[str, str] | None = None, *, cursor_cli_authenticated: bool = False
) -> str:
    """Resolve a Cloud API key without ever including its value in diagnostics."""

    env = os.environ if environment is None else environment
    value = str(env.get("CURSOR_API_KEY") or "")
    if not value.strip():
        detail = "CURSOR_API_KEY is required for Cursor Cloud API authority"
        if cursor_cli_authenticated:
            detail += "; cursor-agent CLI login/local workspace is not Cloud API authority"
        raise CursorCloudDispatchError("cursor_cloud_api_key_required", detail)
    if any(char.isspace() for char in value):
        raise CursorCloudDispatchError("cursor_cloud_api_key_invalid", "CURSOR_API_KEY is malformed")
    return value


def _readback_write(
    store: CursorCloudIntentStore,
    key: str,
    payload: Mapping[str, Any],
    *,
    expected_revision: int,
    expected_digest: str | None,
) -> Mapping[str, Any]:
    store.compare_and_write(key, expected_revision, expected_digest, payload)
    readback = store.read(key)
    if readback is None or readback.get("digest") != _stored_digest(readback):
        raise CursorCloudDispatchError(
            "cursor_cloud_intent_readback_failed", "PREPARED intent was not read back"
        )
    for field, value in payload.items():
        if readback.get(field) != value:
            raise CursorCloudDispatchError(
                "cursor_cloud_intent_readback_failed", "intent readback differs", field=field
            )
    return readback


def _response_value(response: Mapping[str, Any], *keys: str) -> Any:
    for key in keys:
        if response.get(key) is not None:
            return response[key]
    return None


def _normalize_rest_run_readback(
    response: Mapping[str, Any], request: CursorCloudDispatchRequest
) -> dict[str, Any]:
    observed_env = _response_value(response, "env", "environment") or request.environment
    if not isinstance(observed_env, Mapping):
        observed_env = request.environment
    fast_value = response.get("fast")
    if fast_value is None:
        params = _response_value(response, "modelParameters", "model_parameters")
        if isinstance(params, Mapping) and "fast" in params:
            fast_value = str(params["fast"]).casefold() == "true"
        else:
            fast_value = True
    elif isinstance(fast_value, str):
        fast_value = fast_value.casefold() == "true"
    return {
        "environment": dict(observed_env),
        "environmentPublicId": str(
            _response_value(response, "environmentPublicId", "environment_public_id")
            or request.environment_public_id
        ),
        "observedBuildId": str(
            _response_value(response, "observedBuildId", "observed_build_id", "buildId") or ""
        ),
        "expectedBuildId": str(
            _response_value(response, "expectedBuildId", "expected_build_id")
            or request.expected_build_id
        ),
        "effectiveModel": str(_response_value(response, "effectiveModel", "model") or request.model),
        "fast": bool(fast_value),
    }


def _rest_get_run_readback(
    http: CursorCloudHTTPPort,
    agent_id: str,
    headers: Mapping[str, str],
    request: CursorCloudDispatchRequest,
) -> Mapping[str, Any]:
    get = getattr(http, "get", None)
    if not callable(get):
        raise CursorCloudDispatchError(
            "cursor_cloud_rest_readback_unavailable",
            "HTTP port must implement GET for mandatory REST readback",
        )
    response = get(f"{API_PATH}/{agent_id}", headers=headers)
    status = int(response.get("statusCode", response.get("status", 0)) or 0)
    if status != 200:
        raise CursorCloudDispatchError(
            "cursor_cloud_rest_readback_rejected",
            "REST GET readback did not return HTTP 200",
            statusCode=status,
        )
    readback = _normalize_rest_run_readback(response, request)
    validate_cursor_cloud_run_readback(request, readback)
    return readback


def dispatch_cursor_cloud(
    request: CursorCloudDispatchRequest,
    store: CursorCloudIntentStore,
    http: CursorCloudHTTPPort,
    *,
    environment: Mapping[str, str] | None = None,
    cursor_cli_authenticated: bool = False,
    rest_readback: CursorCloudHTTPPort | None = None,
    require_rest_readback: bool = False,
) -> CursorCloudDispatchResult:
    """Create one Cloud agent using mocked or real HTTP authority.

    No Cursor endpoint is contacted by this module itself; callers provide the
    HTTP port.  Tests must provide a fake port and never use a live key.
    When ``require_rest_readback`` is true, a REST GET on the created agent
    must succeed and match the governed request before durable COMMITTED state.
    """

    request.validate()
    api_key = require_cursor_cloud_api_key(
        environment, cursor_cli_authenticated=cursor_cli_authenticated
    )
    supersede_obsolete_prepared_intents(store)
    key = cursor_cloud_idempotency_key(request)
    client_agent_id = cursor_cloud_client_agent_id(request)
    prompt = build_attestation_prompt(request)
    current = store.read(key)
    if current is not None and current.get("state") == "COMMITTED":
        return CursorCloudDispatchResult(
            "duplicate",
            key,
            client_agent_id,
            str(current["agentId"]),
            str(current["runId"]),
            dict(current["environment"]),
            str(current["environmentPublicId"]),
            str(current["model"]),
            str(current["expectedBuildId"]),
            int(current["revision"]),
            prompt,
        )
    if current is None:
        intent = {
            "state": "PREPARED",
            "idempotencyKey": key,
            "clientAgentId": client_agent_id,
            "repository": request.repository,
            "targetPath": request.resolved_target_path,
            "targetRemote": normalize_repository_remote(request.target_remote),
            "ref": request.ref,
            "commit": request.commit,
            "tree": request.tree,
            "environment": request.environment,
            "environmentPublicId": request.environment_public_id,
            "model": request.model,
            "modelParameters": dict(request.model_parameters),
            "explicitScopeRepositories": list(request.explicit_scope_repositories),
            "explicitScopeRemotes": {
                repo: normalize_repository_remote(remote)
                for repo, remote in sorted(request.explicit_scope_remotes.items())
            },
            "expectedBuildId": request.expected_build_id,
            "toolchain": dict(request.toolchain),
            "governedSetup": request.governed_setup,
            "setupReceiptDigest": request.setup_receipt_digest,
            "concurrencyPolicy": request.concurrency_policy,
            "requestDigest": _digest({"key": key, "prompt": prompt}),
        }
        current = _readback_write(
            store, key, intent, expected_revision=0, expected_digest=None
        )
    if current.get("clientAgentId") != client_agent_id:
        raise CursorCloudDispatchError(
            "cursor_cloud_idempotency_collision", "existing intent has another client agent id"
        )
    headers = {
        "Authorization": "Bearer " + api_key,
        "Content-Type": "application/json",
        "Idempotency-Key": key,
    }
    body = {
        "agentId": client_agent_id,
        "env": request.environment,
        "model": request.model,
        "prompt": prompt,
    }
    response: Mapping[str, Any] | None = None
    for attempt in range(MAX_API_ATTEMPTS):
        try:
            response = http.post(API_PATH, headers=headers, body=body)
            break
        except CursorCloudDispatchError:
            raise
        except Exception as exc:  # keep PREPARED for one idempotent retry
            if attempt + 1 == MAX_API_ATTEMPTS:
                raise CursorCloudDispatchError(
                    "cursor_cloud_api_interrupted",
                    "Cloud API call did not produce an authoritative response after one retry",
                ) from exc
    if response is None:  # pragma: no cover - loop either returns or raises
        raise CursorCloudDispatchError(
            "cursor_cloud_api_interrupted", "Cloud API response was unavailable"
        )
    status = int(response.get("statusCode", response.get("status", 0)) or 0)
    if status != 201:
        raise CursorCloudDispatchError(
            "cursor_cloud_api_rejected", "Cursor Cloud API did not return HTTP 201", statusCode=status
        )
    agent_id = str(_response_value(response, "agentId", "id") or "")
    run = response.get("run")
    run_id = str(_response_value(response, "runId") or (run.get("id") if isinstance(run, Mapping) else "") or "")
    if not agent_id or not run_id:
        raise CursorCloudDispatchError(
            "cursor_cloud_response_identity_missing", "response must include agent and run identity"
        )
    if agent_id != client_agent_id:
        raise CursorCloudDispatchError(
            "cursor_cloud_agent_identity_mismatch",
            "Cloud response did not preserve the client-supplied agent identity",
        )
    observed_env = _response_value(response, "env", "environment")
    if observed_env is None:
        observed_env = request.environment
    if not isinstance(observed_env, Mapping) or dict(observed_env) != request.environment:
        raise CursorCloudDispatchError(
            "cursor_cloud_environment_mismatch", "Cloud response environment does not match the request"
        )
    observed_model = str(_response_value(response, "model") or request.model)
    if observed_model != request.model:
        raise CursorCloudDispatchError(
            "cursor_cloud_model_mismatch", "Cloud response model does not match the exact request"
        )
    if require_rest_readback:
        readback_http = rest_readback if rest_readback is not None else http
        _rest_get_run_readback(readback_http, agent_id, headers, request)
    payload = dict(current)
    payload.update(
        {
            "state": "COMMITTED",
            "agentId": agent_id,
            "runId": run_id,
            "environment": dict(observed_env),
            "environmentPublicId": request.environment_public_id,
            "model": observed_model,
            "expectedBuildId": request.expected_build_id,
        }
    )
    committed = _readback_write(
        store,
        key,
        {field: value for field, value in payload.items() if field not in {"revision", "digest"}},
        expected_revision=int(current["revision"]),
        expected_digest=str(current["digest"]),
    )
    return CursorCloudDispatchResult(
        "committed",
        key,
        client_agent_id,
        agent_id,
        run_id,
        dict(observed_env),
        request.environment_public_id,
        observed_model,
        request.expected_build_id,
        int(committed["revision"]),
        prompt,
    )


def dispatch_cursor_cloud_sdk(
    request: CursorCloudDispatchRequest,
    store: CursorCloudIntentStore,
    sdk: CursorCloudSDKPort,
    *,
    http: CursorCloudHTTPPort | None = None,
    environment: Mapping[str, str] | None = None,
    cursor_cli_authenticated: bool = False,
    require_rest_readback: bool = False,
) -> CursorCloudDispatchResult:
    """Preferred repository-bound SDK orchestration path.

    The durable intent, idempotency, model, attestation and post-create
    readback contract is shared with REST.  The difference is that the SDK
    receives the exact repository URL and starting ref as first-class fields.
    """

    return dispatch_cursor_cloud(
        request,
        store,
        _SDKAsHTTPPort(request, sdk),
        environment=environment,
        cursor_cli_authenticated=cursor_cli_authenticated,
        rest_readback=http,
        require_rest_readback=require_rest_readback,
    )


def orchestrate_cursor_cloud_dispatch(
    request: CursorCloudDispatchRequest,
    store: CursorCloudIntentStore,
    http: CursorCloudHTTPPort,
    *,
    sdk: CursorCloudSDKPort | None = None,
    config: Mapping[str, Any] | None = None,
    repo_root: str | None = None,
    environment: Mapping[str, str] | None = None,
    cursor_cli_authenticated: bool = False,
) -> CursorCloudDispatchResult:
    """SDK-preferred dispatch with mandatory REST readback and REST fallback."""

    if config is None:
        if repo_root is None:
            raise CursorCloudDispatchError(
                "cursor_cloud_config_missing",
                "orchestrator requires config or repo_root",
            )
        config = load_cursor_cloud_dispatch_config(repo_root)
    request = apply_configured_audit_model_parameters(request, config)
    validate_repository_scope(request, config)
    readback_required = bool(config.get("restReadbackRequired"))
    dispatch_kwargs = {
        "environment": environment,
        "cursor_cli_authenticated": cursor_cli_authenticated,
        "rest_readback": http,
        "require_rest_readback": readback_required,
    }
    preferred_sdk = config.get("preferredClient") == "cursor-python-sdk"
    if preferred_sdk and sdk is not None:
        try:
            return dispatch_cursor_cloud(
                request,
                store,
                _SDKAsHTTPPort(request, sdk),
                **dispatch_kwargs,
            )
        except CursorCloudDispatchError as exc:
            if exc.code != "cursor_cloud_sdk_unavailable":
                raise
    return dispatch_cursor_cloud(request, store, http, **dispatch_kwargs)


def validate_cursor_cloud_attestation(
    request: CursorCloudDispatchRequest, attestation: Mapping[str, Any]
) -> None:
    """Permit mutation only after an exact, explicit no-mutation attestation."""

    request.validate()
    if attestation.get("status") != "PASS" or attestation.get("noMutation") is not True:
        raise CursorCloudDispatchError(
            "cursor_cloud_attestation_required", "mutation requires a PASS no-mutation attestation"
        )
    if attestation.get("workspaceClean") is not True:
        raise CursorCloudDispatchError(
            "cursor_cloud_attestation_required",
            "mutation requires a clean target workspace attestation",
        )
    expected = {
        "environment": request.environment,
        "targetPath": request.resolved_target_path,
        "remote": normalize_repository_remote(request.target_remote),
        "repository": request.repository,
        "ref": request.ref,
        "commit": request.commit,
        "tree": request.tree,
        "toolchain": dict(request.toolchain),
        "workspaceClean": True,
    }
    for field, value in expected.items():
        observed = attestation.get(field)
        if field == "environment" and isinstance(observed, Mapping):
            observed = dict(observed)
        if field == "remote":
            observed = normalize_repository_remote(str(observed or ""))
        if field == "toolchain" and isinstance(observed, Mapping):
            observed = dict(observed)
        if observed != value:
            raise CursorCloudDispatchError(
                "cursor_cloud_attestation_mismatch",
                "mutation blocked because Cloud attestation does not match",
                field=field,
            )


def validate_cursor_cloud_run_readback(
    request: CursorCloudDispatchRequest, readback: Mapping[str, Any]
) -> None:
    """Validate post-creation provider readback without treating build provenance as a selector."""

    request.validate()
    observed_environment = readback.get("environment")
    if not isinstance(observed_environment, Mapping) or dict(observed_environment) != request.environment:
        raise CursorCloudDispatchError(
            "cursor_cloud_run_environment_mismatch",
            "run readback environment name/type does not match",
        )
    if readback.get("environmentPublicId") != request.environment_public_id:
        raise CursorCloudDispatchError(
            "cursor_cloud_run_environment_public_id_mismatch",
            "run readback public environment identity does not match",
        )
    observed_build = str(readback.get("observedBuildId") or "").strip()
    if not observed_build:
        raise CursorCloudDispatchError(
            "cursor_cloud_run_build_readback_missing",
            "run readback must record observed build provenance",
        )
    if readback.get("expectedBuildId") != request.expected_build_id:
        raise CursorCloudDispatchError(
            "cursor_cloud_run_build_provenance_mismatch",
            "run readback expected build provenance differs from the request",
        )
    if readback.get("effectiveModel") != request.model:
        raise CursorCloudDispatchError(
            "cursor_cloud_run_effective_model_mismatch",
            "run readback effective model differs from the exact requested model",
        )
    if readback.get("fast") is not False:
        raise CursorCloudDispatchError(
            "cursor_cloud_run_fast_readback_mismatch",
            "run readback must explicitly prove Fast is false",
        )


def load_cursor_cloud_dispatch_config(repo_root: str) -> dict[str, Any]:
    from pathlib import Path

    import jsonschema

    root = Path(repo_root).resolve()
    config = json.loads(
        (root / "core/managed-core/content/config/cursor-cloud-dispatch.json").read_text()
    )
    schema = json.loads(
        (root / "core/managed-core/schemas/cursor-cloud-dispatch.schema.json").read_text()
    )
    errors = sorted(error.message for error in jsonschema.Draft202012Validator(schema).iter_errors(config))
    if errors:
        raise CursorCloudDispatchError("cursor_cloud_config_invalid", "; ".join(errors))
    return config
