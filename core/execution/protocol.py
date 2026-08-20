"""Coding Execution Protocol 1.0.1 validation and runtime discovery."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

from jsonschema import Draft202012Validator

PROTOCOL_ID = "coding-execution-protocol"
PROTOCOL_VERSION = "1.0.1"
CANONICAL_PUBLISHER = "linktrend-review-ready-publisher"
LEGACY_PUBLISHERS = frozenset(
    {
        "mark-review-ready.sh-as-publisher",
        "review-ready.json",
        "user-pat-publisher",
    }
)

PROTOCOL_DOCUMENT_RELATIVE_PATH = "core/execution/CODING-EXECUTION-PROTOCOL.md"
CONTROL_CONTRACT_RELATIVE_PATH = "core/contracts/EXECUTION-CONTROL-CONTRACT.md"
SCHEMA_RELATIVE_PATH = "core/contracts/EXECUTION-MANIFEST.schema.json"
DOCTRINE_RELATIVE_PATH = (
    "core/managed-core/content/doctrine/CODING-EXECUTION-PROTOCOL.md"
)
EXAMPLE_MANIFEST_RELATIVE_PATH = (
    "core/execution/examples/execution-manifest.example.json"
)

ORDINARY_SOURCE_REPAIR_LIMIT = 3
INFRASTRUCTURE_ATTEMPT_LIMIT = 2
CODE_FAILURE_RETRY_LIMIT = 0

PROTECTED_REFS = frozenset({"development", "staging", "main"})
RESERVED_APPROVAL_ACTIONS = frozenset(
    {
        "main_promote",
        "publish_release",
        "deploy_production",
        "github_protection_change",
        "provider_live_mutation",
    }
)
AUTOMATIC_ACTIONS = frozenset({"checkpoint", "issue_commit"})
FORBIDDEN_ACTOR_ACTIONS = frozenset({"self_review", "self_merge", "prefer_incoming"})

REQUIRED_DISCOVERY_PATHS = (
    PROTOCOL_DOCUMENT_RELATIVE_PATH,
    CONTROL_CONTRACT_RELATIVE_PATH,
    SCHEMA_RELATIVE_PATH,
    DOCTRINE_RELATIVE_PATH,
)


@dataclass(frozen=True)
class ProtocolDiscovery:
    protocol_id: str
    protocol_version: str
    repo_root: Path
    protocol_document: Path
    control_contract: Path
    schema_path: Path
    doctrine_path: Path
    example_manifest: Path | None


@dataclass(frozen=True)
class ValidationResult:
    ok: bool
    errors: tuple[str, ...] = ()

    @property
    def skipped(self) -> bool:
        return False


@dataclass(frozen=True)
class CandidateIdentity:
    repository: str
    commit: str
    tree: str
    workflow_digest: str | None = None
    profile_digest: str | None = None


@dataclass(frozen=True)
class InvalidationResult:
    invalidated: bool
    reason: str | None = None


@dataclass(frozen=True)
class RetryDecision:
    retry: bool
    stop: bool
    reason: str


@dataclass(frozen=True)
class LeaseState:
    holder: str
    packet_id: str
    repository: str
    nonce: str
    expires_at: datetime


@dataclass(frozen=True)
class ResourceVerdict:
    admitted: bool
    reason: str
    uncertain: bool = False


@dataclass(frozen=True)
class ApprovalDecision:
    allowed: bool
    automatic: bool
    founder_required: bool
    reason: str


@dataclass(frozen=True)
class AutoworkDiscoveryDecision:
    required: bool
    ok: bool
    proof_level: str
    reason: str


def _as_root(repo_root: Path | str) -> Path:
    return Path(repo_root).resolve()


def discover_runtime(repo_root: Path | str) -> ProtocolDiscovery:
    root = _as_root(repo_root)
    missing = [rel for rel in REQUIRED_DISCOVERY_PATHS if not (root / rel).is_file()]
    if missing:
        raise FileNotFoundError(
            "coding execution protocol surfaces missing: " + ", ".join(missing)
        )
    example = root / EXAMPLE_MANIFEST_RELATIVE_PATH
    return ProtocolDiscovery(
        protocol_id=PROTOCOL_ID,
        protocol_version=PROTOCOL_VERSION,
        repo_root=root,
        protocol_document=root / PROTOCOL_DOCUMENT_RELATIVE_PATH,
        control_contract=root / CONTROL_CONTRACT_RELATIVE_PATH,
        schema_path=root / SCHEMA_RELATIVE_PATH,
        doctrine_path=root / DOCTRINE_RELATIVE_PATH,
        example_manifest=example if example.is_file() else None,
    )


def load_execution_schema(repo_root: Path | str | None = None) -> dict[str, Any]:
    if repo_root is None:
        schema_path = Path(__file__).resolve().parents[1] / "contracts" / (
            "EXECUTION-MANIFEST.schema.json"
        )
    else:
        schema_path = discover_runtime(repo_root).schema_path
    return json.loads(schema_path.read_text(encoding="utf-8"))


def validate_execution_manifest(
    document: Mapping[str, Any],
    *,
    schema: Mapping[str, Any] | None = None,
    repo_root: Path | str | None = None,
) -> ValidationResult:
    loaded = dict(schema) if schema is not None else load_execution_schema(repo_root)
    validator = Draft202012Validator(loaded)
    errors = sorted(
        error.message for error in validator.iter_errors(document)
    )
    if errors:
        return ValidationResult(ok=False, errors=tuple(errors))
    protocol = document.get("protocol") or {}
    if protocol.get("id") != PROTOCOL_ID or protocol.get("version") != PROTOCOL_VERSION:
        return ValidationResult(
            ok=False,
            errors=("protocol identity must be coding-execution-protocol 1.0.1",),
        )
    return ValidationResult(ok=True)


def candidate_identity(
    *,
    repository: str,
    commit: str,
    tree: str,
    workflow_digest: str | None = None,
    profile_digest: str | None = None,
) -> CandidateIdentity:
    return CandidateIdentity(
        repository=repository,
        commit=commit,
        tree=tree,
        workflow_digest=workflow_digest,
        profile_digest=profile_digest,
    )


def invalidate_candidate(
    previous: CandidateIdentity,
    current: CandidateIdentity,
) -> InvalidationResult:
    if previous.repository != current.repository:
        return InvalidationResult(True, "repository_changed")
    if previous.commit != current.commit or previous.tree != current.tree:
        return InvalidationResult(True, "exact_candidate_changed")
    if (
        previous.workflow_digest is not None
        and previous.workflow_digest != current.workflow_digest
    ):
        return InvalidationResult(True, "workflow_digest_changed")
    if (
        previous.profile_digest is not None
        and previous.profile_digest != current.profile_digest
    ):
        return InvalidationResult(True, "profile_digest_changed")
    return InvalidationResult(False, None)


def retry_decision(
    kind: str,
    attempt: int,
    *,
    ordinary_limit: int = ORDINARY_SOURCE_REPAIR_LIMIT,
    infrastructure_limit: int = INFRASTRUCTURE_ATTEMPT_LIMIT,
    code_failure_limit: int = CODE_FAILURE_RETRY_LIMIT,
) -> RetryDecision:
    if attempt < 1:
        return RetryDecision(False, True, "invalid_attempt")
    if kind == "ordinary_source":
        if attempt <= ordinary_limit:
            return RetryDecision(True, False, "ordinary_source_repair")
        return RetryDecision(False, True, "ordinary_source_exhausted")
    if kind == "infrastructure":
        if attempt < infrastructure_limit:
            return RetryDecision(True, False, "infrastructure_retry")
        return RetryDecision(False, True, "infrastructure_stopped")
    if kind == "code_failure":
        if attempt <= code_failure_limit:
            return RetryDecision(True, False, "code_failure_retry")
        return RetryDecision(False, True, "code_failure_no_retry")
    return RetryDecision(False, True, "unknown_failure_kind")


def acquire_orchestration_lease(
    *,
    holder: str,
    packet_id: str,
    repository: str,
    nonce: str,
    expires_at: datetime,
    existing: LeaseState | None = None,
    now: datetime | None = None,
) -> LeaseState:
    clock = now or datetime.now(timezone.utc)
    if existing is not None and existing.expires_at > clock:
        if (
            existing.packet_id == packet_id
            and existing.repository == repository
            and existing.holder != holder
        ):
            raise PermissionError("orchestration_lease_held")
        if existing.nonce != nonce and existing.holder != holder:
            raise PermissionError("orchestration_lease_conflict")
    return LeaseState(
        holder=holder,
        packet_id=packet_id,
        repository=repository,
        nonce=nonce,
        expires_at=expires_at,
    )


def validate_lease(
    lease: LeaseState,
    *,
    holder: str,
    packet_id: str,
    repository: str,
    now: datetime | None = None,
) -> bool:
    clock = now or datetime.now(timezone.utc)
    if lease.expires_at <= clock:
        return False
    return (
        lease.holder == holder
        and lease.packet_id == packet_id
        and lease.repository == repository
    )


def admit_resources(snapshot: Mapping[str, Any] | None) -> ResourceVerdict:
    if snapshot is None:
        return ResourceVerdict(False, "resource_uncertain", True)
    required = ("cpu_percent", "memory_percent", "free_disk_gib", "docker_available")
    for key in required:
        if key not in snapshot or snapshot[key] is None:
            return ResourceVerdict(False, "resource_uncertain", True)
    if snapshot.get("interactive_use"):
        return ResourceVerdict(False, "interactive_use", False)
    return ResourceVerdict(True, "admitted", False)


def required_approval(
    action: str,
    *,
    recorded_approvals: Mapping[str, str] | None = None,
) -> ApprovalDecision:
    if action in FORBIDDEN_ACTOR_ACTIONS:
        return ApprovalDecision(False, False, False, "actor_forbidden")
    if action in AUTOMATIC_ACTIONS:
        return ApprovalDecision(True, True, False, "automatic")
    if action == "staging_promote":
        return ApprovalDecision(True, True, False, "automatic_on_receipt_identity")
    if action in RESERVED_APPROVAL_ACTIONS:
        approvals = recorded_approvals or {}
        if approvals.get(action) == "founder":
            return ApprovalDecision(True, False, True, "founder_recorded")
        return ApprovalDecision(False, False, True, "founder_required")
    return ApprovalDecision(False, False, True, "unknown_action")


def git_authority_allows(
    action: str,
    *,
    branch: str,
    actor: str,
) -> bool:
    if action in {"push_protected", "merge_own_pr", "prefer_incoming", "nested_self_install"}:
        return False
    if action == "push_work_branch":
        if branch in PROTECTED_REFS:
            return False
        return branch.startswith("issue/") and actor == "implementer"
    if action == "open_pr":
        return actor in {"packager", "packager_coordinator"}
    if action == "merge_to_development":
        return actor == "delivery_controller"
    return False


def publisher_is_canonical(name: str) -> bool:
    if name in LEGACY_PUBLISHERS:
        return False
    return name == CANONICAL_PUBLISHER


def autowork_discovery_decision(
    *,
    callable_now: bool,
    performed: bool,
    claimed_live_pass: bool = False,
) -> AutoworkDiscoveryDecision:
    if callable_now:
        if not performed:
            return AutoworkDiscoveryDecision(
                True,
                False,
                "none",
                "autowork_discovery_required_when_callable",
            )
        return AutoworkDiscoveryDecision(True, True, "discovery", "performed")
    if claimed_live_pass:
        return AutoworkDiscoveryDecision(
            False,
            False,
            "none",
            "cannot_claim_live_pass_when_not_callable",
        )
    return AutoworkDiscoveryDecision(False, True, "hold", "unavailable_hold")


def protocol_document_version(text: str) -> str | None:
    for line in text.splitlines():
        lowered = line.lower().lstrip("* ").strip()
        if lowered.startswith("protocol version:"):
            return line.split(":", 1)[1].replace("*", "").strip()
    return None
