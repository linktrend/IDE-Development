"""Fail-closed Cursor Cloud API dispatch contract.

The authenticated ``cursor-agent`` CLI is a local-workspace capability.  It is
not evidence that this process can create a Cursor Cloud agent.  Cloud
creation therefore requires ``CURSOR_API_KEY`` and uses only the HTTP API
authority represented by that key.
"""

from __future__ import annotations

import copy
import hashlib
import json
import os
import re
from dataclasses import dataclass
from typing import Any, Mapping, Protocol
from urllib.parse import urlsplit, urlunsplit


CONTROL_ID = "cursor-cloud-dispatch-v1"
API_BASE_URL = "https://api.cursor.com"
API_PATH = "/v1/agents"
ENV_TYPE = "cloud"
ENV_NAME = "IDE Development 2.5.1"
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
    environment_name: str = ENV_NAME
    governed_setup: bool = False
    advertised_refs: Mapping[str, str] | None = None
    supersedes_intent_key: str | None = None

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
        advertised = self.advertised_refs
        if not isinstance(advertised, Mapping) or str(advertised.get(self.ref) or "") != self.commit:
            raise CursorCloudDispatchError(
                "cursor_cloud_advertised_ref_invalid",
                "pre-dispatch advertised issue ref is missing or does not point to the requested commit",
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
        if not self.toolchain or any(
            not str(key).strip() or not str(value).strip()
            for key, value in self.toolchain.items()
        ):
            raise CursorCloudDispatchError(
                "cursor_cloud_toolchain_missing", "toolchain attestation data is required"
            )

    @property
    def environment(self) -> dict[str, str]:
        return {"type": ENV_TYPE, "name": self.environment_name}

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


class CursorCloudHTTPPort(Protocol):
    def post(
        self, path: str, *, headers: Mapping[str, str], body: Mapping[str, Any]
    ) -> Mapping[str, Any]: ...


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
        "environment": request.environment,
        "expectedBuildId": request.expected_build_id,
        "toolchain": dict(request.toolchain),
        "governedSetup": request.governed_setup,
        "setupReceiptDigest": request.setup_receipt_digest,
        "advertisedRefs": dict(request.advertised_refs or {}),
        "supersedesIntentKey": request.supersedes_intent_key,
    }
    return CONTROL_ID + ":" + hashlib.sha256(_canonical(identity)).hexdigest()


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
        f"Environment={{type:{ENV_TYPE}, name:{request.environment_name}}}. "
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


def supersede_prepared_intent(
    store: CursorCloudIntentStore, previous_key: str, replacement_key: str
) -> Mapping[str, Any] | None:
    """Immutably retire a stale PREPARED intent before a rebaseline dispatch.

    A missing/deleted issue ref must be rebaselined and receive a newly created
    issue branch/intent. The old intent is never edited into the replacement and
    no Cloud call is made by this helper.
    """

    current = store.read(previous_key)
    if current is None:
        return None
    if current.get("state") != "PREPARED":
        raise CursorCloudDispatchError(
            "cursor_cloud_intent_not_supersedable",
            "only a PREPARED intent may be superseded; committed history is immutable",
        )
    payload = dict(current)
    payload.update({"state": "SUPERSEDED", "supersededBy": replacement_key})
    return _readback_write(
        store,
        previous_key,
        {field: value for field, value in payload.items() if field not in {"revision", "digest"}},
        expected_revision=int(current["revision"]),
        expected_digest=str(current["digest"]),
    )


def dispatch_cursor_cloud(
    request: CursorCloudDispatchRequest,
    store: CursorCloudIntentStore,
    http: CursorCloudHTTPPort,
    *,
    environment: Mapping[str, str] | None = None,
    cursor_cli_authenticated: bool = False,
) -> CursorCloudDispatchResult:
    """Create one Cloud agent using mocked or real HTTP authority.

    No Cursor endpoint is contacted by this module itself; callers provide the
    HTTP port.  Tests must provide a fake port and never use a live key.
    """

    request.validate()
    api_key = require_cursor_cloud_api_key(
        environment, cursor_cli_authenticated=cursor_cli_authenticated
    )
    key = cursor_cloud_idempotency_key(request)
    if request.supersedes_intent_key:
        supersede_prepared_intent(store, request.supersedes_intent_key, key)
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
            "model": request.model,
            "expectedBuildId": request.expected_build_id,
            "toolchain": dict(request.toolchain),
            "governedSetup": request.governed_setup,
            "setupReceiptDigest": request.setup_receipt_digest,
            "advertisedRefs": dict(request.advertised_refs or {}),
            "supersedesIntentKey": request.supersedes_intent_key,
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
    payload = dict(current)
    payload.update(
        {
            "state": "COMMITTED",
            "agentId": agent_id,
            "runId": run_id,
            "environment": dict(observed_env),
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
        observed_model,
        request.expected_build_id,
        int(committed["revision"]),
        prompt,
    )


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
