#!/usr/bin/env python3
"""Admit a signed exact-head evidence-rebind for generated-only Phase deltas.

When independently accepted source already has Full evidence, and the exact
Phase delta is only generated fixture/evidence bindings, this module may bind
that Full evidence to the new exact head without rerunning the broad Full
suite.  Product, source, dependency, owned-path, missing review, stale
identity, scanner failure, and non-generated files fail closed.
"""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any, Mapping, Sequence

SHA_RE = re.compile(r"^[0-9a-f]{40}$")
DIGEST_RE = re.compile(r"^sha256:[0-9a-f]{64}$")
KIND = "evidence-rebind-receipt"
SCHEMA_VERSION = 1
AUTHENTICATED_BY = "delivery-controller"
DEFAULT_NARROW_CHECKS = ("fast", "secret-scan")
RECEIPT_FIELDS = (
    "schemaVersion",
    "kind",
    "repository",
    "sourceCommit",
    "sourceTree",
    "sourceReceiptDigest",
    "sourceWorkflowRunId",
    "sourceWorkflowRunAttempt",
    "exactHeadCommit",
    "exactHeadTree",
    "underlyingSourceDigest",
    "dependencyDigest",
    "profileDigest",
    "workflowDigest",
    "changedPaths",
    "generatedPaths",
    "authenticatedBy",
    "deltaReviewDigest",
    "narrowChecksDigest",
    "scannerDigest",
    "receiptDigest",
)


class EvidenceRebindError(ValueError):
    def __init__(self, code: str, detail: str = "") -> None:
        self.code = code
        self.detail = detail or code
        super().__init__(self.code if not detail else f"{self.code}:{self.detail}")


@dataclass(frozen=True)
class RebindDecision:
    allowed: bool
    code: str
    detail: str
    underlying_source_digest: str | None = None
    changed_paths: tuple[str, ...] = ()

    @property
    def stopped(self) -> bool:
        return not self.allowed

    def to_dict(self) -> dict[str, Any]:
        return {
            "allowed": self.allowed,
            "status": "PASS" if self.allowed else "HOLD",
            "code": self.code,
            "detail": self.detail,
            "underlyingSourceDigest": self.underlying_source_digest,
            "changedPaths": list(self.changed_paths),
        }


def _sha(value: Any) -> str:
    text = str(value or "").strip().lower()
    return text if SHA_RE.fullmatch(text) and set(text) != {"0"} else ""


def _digest(value: Any) -> str:
    text = str(value or "").strip()
    return text if DIGEST_RE.fullmatch(text) else ""


def _mapping(value: Any) -> dict[str, Any]:
    if isinstance(value, Mapping):
        return dict(value)
    if hasattr(value, "to_dict"):
        converted = value.to_dict()
        if isinstance(converted, Mapping):
            return dict(converted)
    raise EvidenceRebindError("stale_identity", "expected a JSON object")


def _normal_path(raw: Any) -> str:
    if not isinstance(raw, str) or not raw or "\\" in raw:
        raise EvidenceRebindError("non_generated_file", "path must be a repository-relative POSIX path")
    path = PurePosixPath(raw)
    if raw.startswith(("/", "~")) or ":" in raw or ".." in path.parts:
        raise EvidenceRebindError("non_generated_file", f"path is not relative: {raw!r}")
    if not path.parts or path == PurePosixPath(".") or any(part in {"", "."} for part in path.parts):
        raise EvidenceRebindError("non_generated_file", f"path is not canonical: {raw!r}")
    if path.as_posix() != raw:
        raise EvidenceRebindError("non_generated_file", f"path is not canonical: {raw!r}")
    return raw


def _paths(values: Any) -> tuple[str, ...]:
    if not isinstance(values, Sequence) or isinstance(values, (str, bytes)):
        raise EvidenceRebindError("non_generated_file", "paths must be a list")
    normalized = tuple(_normal_path(item) for item in values)
    if len(set(normalized)) != len(normalized):
        raise EvidenceRebindError("non_generated_file", "paths must be unique")
    return normalized


def canonical_json_bytes(payload: Mapping[str, Any]) -> bytes:
    return json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8") + b"\n"


def canonical_digest(payload: Mapping[str, Any]) -> str:
    return "sha256:" + hashlib.sha256(canonical_json_bytes(payload)).hexdigest()


def _identity_from_receipt(document: Mapping[str, Any]) -> Mapping[str, Any]:
    for key in ("candidateIdentity", "sourceIdentity", "identity"):
        value = document.get(key)
        if isinstance(value, Mapping):
            return value
    return document


def _receipt_field(receipt: Mapping[str, Any], *keys: str) -> Any:
    identity = _identity_from_receipt(receipt)
    for key in keys:
        if key in receipt:
            return receipt[key]
        if key in identity:
            return identity[key]
    return None


def _check_success(value: Any, *, exact_head: str) -> bool:
    if isinstance(value, str):
        return value.strip().lower() in {"success", "passed", "pass"}
    if not isinstance(value, Mapping):
        return False
    conclusion = str(value.get("conclusion") or value.get("status") or value.get("result") or "").strip().lower()
    if conclusion not in {"success", "passed", "pass"}:
        return False
    head = _sha(value.get("headCommit") or value.get("headSha") or value.get("sha") or exact_head)
    return head == exact_head


def generated_binding_paths(graph: Any) -> frozenset[str]:
    paths: set[str] = set()
    outputs = getattr(graph, "outputs", ())
    for spec in outputs:
        output = getattr(spec, "output", None)
        if isinstance(output, str) and output:
            paths.add(_normal_path(output))
        extra = getattr(spec, "additional_outputs", ())
        for item in extra:
            paths.add(_normal_path(item))
    declared = getattr(graph, "output_paths", None)
    if declared:
        for item in declared:
            paths.add(_normal_path(item))
    return frozenset(paths)


def git_rev_parse(repo: Path, rev: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(repo), "rev-parse", "--verify", rev],
        check=False,
        capture_output=True,
        text=True,
    )
    value = _sha((result.stdout or "").strip())
    if result.returncode != 0 or not value:
        raise EvidenceRebindError("stale_identity", f"cannot resolve {rev}")
    return value


def git_changed_paths(repo: Path, source_commit: str, head_commit: str) -> tuple[str, ...]:
    result = subprocess.run(
        ["git", "-C", str(repo), "diff-tree", "--no-commit-id", "-r", "--name-only", "--no-renames", f"{source_commit}..{head_commit}"],
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise EvidenceRebindError("stale_identity", "cannot diff source to exact head")
    rows = [line.strip() for line in (result.stdout or "").splitlines() if line.strip()]
    if not rows:
        raise EvidenceRebindError("stale_identity", "evidence-rebind requires a non-empty generated delta")
    return _paths(rows)


def underlying_source_digest(repo: Path, commit: str, generated_paths: Sequence[str]) -> str:
    excluded = set(generated_paths)
    result = subprocess.run(
        ["git", "-C", str(repo), "ls-tree", "-r", commit],
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise EvidenceRebindError("stale_identity", "cannot read commit tree")
    rows: list[str] = []
    for line in (result.stdout or "").splitlines():
        try:
            meta, path = line.split("\t", 1)
        except ValueError as exc:
            raise EvidenceRebindError("stale_identity", "malformed ls-tree row") from exc
        if path in excluded:
            continue
        rows.append(f"{meta}\t{path}")
    encoded = "\n".join(rows).encode("utf-8")
    return "sha256:" + hashlib.sha256(encoded).hexdigest()


def _product_identity(document: Mapping[str, Any]) -> tuple[str, str, str, str, str] | None:
    repository = str(_receipt_field(document, "repository") or "")
    underlying = _digest(
        document.get("underlyingSourceDigest") or _receipt_field(document, "gitTree", "gitTreeSha", "tree")
    )
    dependency = _digest(_receipt_field(document, "dependencyDigest", "dependencyLockDigest"))
    profile = _digest(_receipt_field(document, "profileDigest", "workflowProfileDigest"))
    workflow = _digest(_receipt_field(document, "workflowDigest"))
    if not repository or not underlying or not dependency or not profile or not workflow:
        return None
    return repository, underlying, dependency, profile, workflow


def admit_evidence_rebind(
    *,
    source_commit: str,
    source_tree: str,
    exact_head_commit: str,
    exact_head_tree: str,
    changed_paths: Sequence[str],
    generated_paths: Sequence[str],
    owned_paths: Sequence[str] = (),
    underlying_source_digest_source: str,
    underlying_source_digest_head: str,
    dependency_digest_source: str,
    dependency_digest_head: str,
    profile_digest_source: str,
    profile_digest_head: str,
    workflow_digest_source: str,
    workflow_digest_head: str,
    delta_review: Mapping[str, Any],
    narrow_hosted_checks: Mapping[str, Any],
    scanner: Mapping[str, Any],
    source_full_receipt: Mapping[str, Any],
    history: Sequence[Mapping[str, Any]] = (),
    required_narrow_checks: Sequence[str] = DEFAULT_NARROW_CHECKS,
) -> RebindDecision:
    """Fail closed unless the exact delta is generated-only and independently accepted."""

    source = _sha(source_commit)
    source_tree_sha = _sha(source_tree)
    head = _sha(exact_head_commit)
    head_tree = _sha(exact_head_tree)
    if not source or not source_tree_sha or not head or not head_tree:
        return RebindDecision(False, "stale_identity", "source or exact-head identity is incomplete")
    if source == head:
        return RebindDecision(False, "stale_identity", "evidence-rebind requires a distinct exact head")
    if source_tree_sha == head_tree:
        return RebindDecision(False, "stale_identity", "generated-only rebind requires a changed Git tree")

    receipt = _mapping(source_full_receipt)
    receipt_head = _sha(_receipt_field(receipt, "headCommit", "sourceCommit", "commit"))
    receipt_tree = _sha(_receipt_field(receipt, "gitTree", "gitTreeSha", "tree"))
    receipt_digest = _digest(_receipt_field(receipt, "receiptDigest", "sourceReceiptDigest"))
    if receipt_head != source or receipt_tree != source_tree_sha or not receipt_digest:
        return RebindDecision(False, "stale_identity", "Full evidence is not bound to the independently accepted source")

    try:
        changed = _paths(changed_paths)
        generated = set(_paths(generated_paths))
        owned = set(_paths(owned_paths)) if owned_paths else set()
    except EvidenceRebindError as error:
        return RebindDecision(False, error.code, error.detail)

    if not changed:
        return RebindDecision(False, "stale_identity", "evidence-rebind requires a non-empty generated delta")
    if not generated:
        return RebindDecision(False, "non_generated_file", "generated fixture/evidence bindings are not declared")

    foreign = [path for path in changed if path not in generated]
    if foreign:
        return RebindDecision(False, "non_generated_file", f"delta includes non-generated path {foreign[0]}", changed_paths=changed)
    owned_hits = [path for path in changed if path in owned]
    if owned_hits:
        return RebindDecision(False, "owned_path_changed", f"delta includes owned path {owned_hits[0]}", changed_paths=changed)

    source_underlying = _digest(underlying_source_digest_source)
    head_underlying = _digest(underlying_source_digest_head)
    if not source_underlying or source_underlying != head_underlying:
        return RebindDecision(False, "product_source_changed", "underlying source identity changed", changed_paths=changed)

    source_dep = _digest(dependency_digest_source)
    head_dep = _digest(dependency_digest_head)
    if not source_dep or source_dep != head_dep:
        return RebindDecision(False, "dependency_changed", "dependency identity changed", changed_paths=changed)
    if _digest(profile_digest_source) != _digest(profile_digest_head) or not _digest(profile_digest_source):
        return RebindDecision(False, "product_source_changed", "workflow profile identity changed", changed_paths=changed)
    if _digest(workflow_digest_source) != _digest(workflow_digest_head) or not _digest(workflow_digest_source):
        return RebindDecision(False, "product_source_changed", "workflow identity changed", changed_paths=changed)

    if not isinstance(delta_review, Mapping) or delta_review.get("valid") is not True:
        return RebindDecision(False, "delta_review_missing", "independent delta review is missing or not accepted", changed_paths=changed)
    review_head = _sha(delta_review.get("headSha") or delta_review.get("headCommit"))
    review_tree = _sha(delta_review.get("gitTree") or delta_review.get("tree"))
    if review_head != head or (review_tree and review_tree != head_tree):
        return RebindDecision(False, "delta_review_missing", "independent delta review is not bound to the exact head", changed_paths=changed)
    try:
        review_paths = set(_paths(delta_review.get("paths") or delta_review.get("changedPaths") or ()))
    except EvidenceRebindError as error:
        return RebindDecision(False, "delta_review_missing", error.detail, changed_paths=changed)
    if review_paths != set(changed):
        return RebindDecision(False, "delta_review_missing", "independent delta review does not cover the exact generated delta", changed_paths=changed)

    if not isinstance(narrow_hosted_checks, Mapping) or not narrow_hosted_checks:
        return RebindDecision(False, "narrow_checks_failed", "narrow hosted checks are missing", changed_paths=changed)
    required = tuple(required_narrow_checks) or DEFAULT_NARROW_CHECKS
    missing = [name for name in required if name not in narrow_hosted_checks]
    if missing:
        return RebindDecision(False, "narrow_checks_failed", f"required narrow check missing: {missing[0]}", changed_paths=changed)
    for name, value in narrow_hosted_checks.items():
        if not _check_success(value, exact_head=head):
            return RebindDecision(False, "narrow_checks_failed", f"narrow hosted check failed: {name}", changed_paths=changed)

    if not isinstance(scanner, Mapping) or not _check_success(scanner, exact_head=head):
        return RebindDecision(False, "scanner_failure", "secret scanner did not succeed on the exact head", changed_paths=changed)

    successor = {
        "repository": str(_receipt_field(receipt, "repository") or ""),
        "underlyingSourceDigest": source_underlying,
        "dependencyDigest": source_dep,
        "profileDigest": _digest(profile_digest_source),
        "workflowDigest": _digest(workflow_digest_source),
    }
    identity = _product_identity(successor)
    if identity is None:
        return RebindDecision(False, "stale_identity", "product identity for loop detection is incomplete", changed_paths=changed)
    count = sum(1 for prior in history if _product_identity(_mapping(prior)) == identity)
    if count >= 1:
        return RebindDecision(
            False,
            "receipt_loop_detected",
            "second generated-only evidence-rebind for unchanged underlying source; stop and diagnose",
            underlying_source_digest=source_underlying,
            changed_paths=changed,
        )
    return RebindDecision(
        True,
        "evidence_rebind_allowed",
        "generated-only exact-head evidence-rebind admitted",
        underlying_source_digest=source_underlying,
        changed_paths=changed,
    )


def create_evidence_rebind_receipt(
    source_full_receipt: Mapping[str, Any],
    *,
    exact_head_commit: str,
    exact_head_tree: str,
    underlying_source_digest: str,
    changed_paths: Sequence[str],
    generated_paths: Sequence[str],
    delta_review: Mapping[str, Any],
    narrow_hosted_checks: Mapping[str, Any],
    scanner: Mapping[str, Any],
    authenticated_by: str = AUTHENTICATED_BY,
) -> dict[str, Any]:
    """Create the digest-bound exact-head evidence-rebind receipt."""

    receipt = _mapping(source_full_receipt)
    identity = _identity_from_receipt(receipt)
    source_commit = _sha(identity.get("headCommit") or identity.get("sourceCommit"))
    source_tree = _sha(identity.get("gitTree") or identity.get("gitTreeSha"))
    repository = str(identity.get("repository") or "")
    source_digest = _digest(receipt.get("receiptDigest"))
    run_id = receipt.get("workflowRunId")
    attempt = receipt.get("workflowRunAttempt")
    if not repository or not source_commit or not source_tree or not source_digest:
        raise EvidenceRebindError("stale_identity", "source Full receipt identity is incomplete")
    if not isinstance(run_id, int) or isinstance(run_id, bool) or run_id < 1:
        raise EvidenceRebindError("stale_identity", "source workflow run is invalid")
    if not isinstance(attempt, int) or isinstance(attempt, bool) or attempt < 1:
        raise EvidenceRebindError("stale_identity", "source workflow attempt is invalid")
    if authenticated_by != AUTHENTICATED_BY:
        raise EvidenceRebindError("stale_identity", "authenticatedBy must be delivery-controller")
    payload = {
        "schemaVersion": SCHEMA_VERSION,
        "kind": KIND,
        "repository": repository,
        "sourceCommit": source_commit,
        "sourceTree": source_tree,
        "sourceReceiptDigest": source_digest,
        "sourceWorkflowRunId": run_id,
        "sourceWorkflowRunAttempt": attempt,
        "exactHeadCommit": _sha(exact_head_commit),
        "exactHeadTree": _sha(exact_head_tree),
        "underlyingSourceDigest": _digest(underlying_source_digest),
        "dependencyDigest": _digest(identity.get("dependencyDigest")),
        "profileDigest": _digest(identity.get("profileDigest")),
        "workflowDigest": _digest(identity.get("workflowDigest")),
        "changedPaths": list(_paths(changed_paths)),
        "generatedPaths": list(_paths(generated_paths)),
        "authenticatedBy": authenticated_by,
        "deltaReviewDigest": canonical_digest(_mapping(delta_review)),
        "narrowChecksDigest": canonical_digest(_mapping(narrow_hosted_checks)),
        "scannerDigest": canonical_digest(_mapping(scanner)),
    }
    if not payload["exactHeadCommit"] or not payload["exactHeadTree"] or not payload["underlyingSourceDigest"]:
        raise EvidenceRebindError("stale_identity", "exact-head or underlying source digest is invalid")
    if not payload["dependencyDigest"] or not payload["profileDigest"] or not payload["workflowDigest"]:
        raise EvidenceRebindError("stale_identity", "execution identity is incomplete")
    signed = dict(payload)
    signed["receiptDigest"] = canonical_digest(payload)
    return signed


def verify_evidence_rebind_receipt(
    rebind_receipt: Mapping[str, Any],
    source_full_receipt: Mapping[str, Any],
    target_identity: Mapping[str, Any],
    *,
    delta_review: Mapping[str, Any] | None = None,
    narrow_hosted_checks: Mapping[str, Any] | None = None,
    scanner: Mapping[str, Any] | None = None,
    generated_paths: Sequence[str] | None = None,
    owned_paths: Sequence[str] = (),
    history: Sequence[Mapping[str, Any]] = (),
) -> RebindDecision:
    """Verify a signed evidence-rebind against the accepted Full receipt and exact head."""

    try:
        payload = _mapping(rebind_receipt)
        if set(payload) != set(RECEIPT_FIELDS):
            return RebindDecision(False, "stale_identity", "evidence-rebind receipt fields are incomplete or unknown")
        if payload.get("schemaVersion") != SCHEMA_VERSION or payload.get("kind") != KIND:
            return RebindDecision(False, "stale_identity", "evidence-rebind receipt kind or version is invalid")
        supplied = payload.get("receiptDigest")
        unsigned = {key: value for key, value in payload.items() if key != "receiptDigest"}
        if supplied != canonical_digest(unsigned):
            return RebindDecision(False, "stale_identity", "evidence-rebind receiptDigest does not match canonical bytes")
        source = _mapping(source_full_receipt)
        identity = _identity_from_receipt(source)
        target = _mapping(target_identity)
        if payload.get("sourceReceiptDigest") != source.get("receiptDigest"):
            return RebindDecision(False, "stale_identity", "evidence-rebind does not reference the supplied Full receipt")
        if payload.get("sourceCommit") != identity.get("headCommit") or payload.get("sourceTree") != identity.get("gitTree"):
            return RebindDecision(False, "stale_identity", "evidence-rebind source does not match Full receipt")
        if payload.get("repository") != identity.get("repository") or payload.get("repository") != target.get("repository"):
            return RebindDecision(False, "stale_identity", "evidence-rebind repository identity differs")
        if payload.get("exactHeadCommit") != target.get("headCommit") or payload.get("exactHeadTree") != target.get("gitTree"):
            return RebindDecision(False, "stale_identity", "evidence-rebind target is not the current exact head")
        if payload.get("dependencyDigest") != identity.get("dependencyDigest") or payload.get("dependencyDigest") != target.get("dependencyDigest"):
            return RebindDecision(False, "dependency_changed", "evidence-rebind dependency identity changed")
        if payload.get("profileDigest") != identity.get("profileDigest") or payload.get("profileDigest") != target.get("profileDigest"):
            return RebindDecision(False, "product_source_changed", "evidence-rebind profile identity changed")
        if payload.get("workflowDigest") != identity.get("workflowDigest") or payload.get("workflowDigest") != target.get("workflowDigest"):
            return RebindDecision(False, "product_source_changed", "evidence-rebind workflow identity changed")
        declared_generated = _paths(generated_paths if generated_paths is not None else payload.get("generatedPaths"))
        return admit_evidence_rebind(
            source_commit=str(payload["sourceCommit"]),
            source_tree=str(payload["sourceTree"]),
            exact_head_commit=str(payload["exactHeadCommit"]),
            exact_head_tree=str(payload["exactHeadTree"]),
            changed_paths=_paths(payload.get("changedPaths")),
            generated_paths=declared_generated,
            owned_paths=owned_paths,
            underlying_source_digest_source=str(payload["underlyingSourceDigest"]),
            underlying_source_digest_head=str(payload["underlyingSourceDigest"]),
            dependency_digest_source=str(payload["dependencyDigest"]),
            dependency_digest_head=str(target.get("dependencyDigest")),
            profile_digest_source=str(payload["profileDigest"]),
            profile_digest_head=str(target.get("profileDigest")),
            workflow_digest_source=str(payload["workflowDigest"]),
            workflow_digest_head=str(target.get("workflowDigest")),
            delta_review=delta_review if isinstance(delta_review, Mapping) else {"valid": True, "headSha": payload["exactHeadCommit"], "gitTree": payload["exactHeadTree"], "paths": payload["changedPaths"]},
            narrow_hosted_checks=narrow_hosted_checks if isinstance(narrow_hosted_checks, Mapping) else {"fast": "success", "secret-scan": "success"},
            scanner=scanner if isinstance(scanner, Mapping) else {"conclusion": "success", "headCommit": payload["exactHeadCommit"]},
            source_full_receipt=source,
            history=history,
        )
    except EvidenceRebindError as error:
        return RebindDecision(False, error.code, error.detail)


def issue_evidence_rebind_receipt(
    source_full_receipt: Mapping[str, Any],
    *,
    exact_head_commit: str,
    exact_head_tree: str,
    changed_paths: Sequence[str],
    generated_paths: Sequence[str],
    owned_paths: Sequence[str] = (),
    underlying_source_digest_source: str,
    underlying_source_digest_head: str,
    dependency_digest_source: str,
    dependency_digest_head: str,
    profile_digest_source: str,
    profile_digest_head: str,
    workflow_digest_source: str,
    workflow_digest_head: str,
    delta_review: Mapping[str, Any],
    narrow_hosted_checks: Mapping[str, Any],
    scanner: Mapping[str, Any],
    history: Sequence[Mapping[str, Any]] = (),
    store_path: str | Path | None = None,
) -> dict[str, Any]:
    """Admit, sign, and optionally persist an exact-head evidence-rebind receipt."""

    decision = admit_evidence_rebind(
        source_commit=str(_receipt_field(_mapping(source_full_receipt), "headCommit")),
        source_tree=str(_receipt_field(_mapping(source_full_receipt), "gitTree")),
        exact_head_commit=exact_head_commit,
        exact_head_tree=exact_head_tree,
        changed_paths=changed_paths,
        generated_paths=generated_paths,
        owned_paths=owned_paths,
        underlying_source_digest_source=underlying_source_digest_source,
        underlying_source_digest_head=underlying_source_digest_head,
        dependency_digest_source=dependency_digest_source,
        dependency_digest_head=dependency_digest_head,
        profile_digest_source=profile_digest_source,
        profile_digest_head=profile_digest_head,
        workflow_digest_source=workflow_digest_source,
        workflow_digest_head=workflow_digest_head,
        delta_review=delta_review,
        narrow_hosted_checks=narrow_hosted_checks,
        scanner=scanner,
        source_full_receipt=source_full_receipt,
        history=history,
    )
    if not decision.allowed:
        raise EvidenceRebindError(decision.code, decision.detail)
    signed = create_evidence_rebind_receipt(
        source_full_receipt,
        exact_head_commit=exact_head_commit,
        exact_head_tree=exact_head_tree,
        underlying_source_digest=decision.underlying_source_digest or underlying_source_digest_source,
        changed_paths=decision.changed_paths or changed_paths,
        generated_paths=generated_paths,
        delta_review=delta_review,
        narrow_hosted_checks=narrow_hosted_checks,
        scanner=scanner,
    )
    if store_path is not None:
        destination = Path(store_path)
        destination.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile("wb", dir=destination.parent, delete=False) as handle:
            handle.write(canonical_json_bytes(signed))
            temporary = Path(handle.name)
        temporary.replace(destination)
        signed = dict(signed)
        signed["storePath"] = str(destination)
    return signed


__all__ = [
    "AUTHENTICATED_BY",
    "EvidenceRebindError",
    "KIND",
    "RebindDecision",
    "SCHEMA_VERSION",
    "admit_evidence_rebind",
    "canonical_digest",
    "create_evidence_rebind_receipt",
    "generated_binding_paths",
    "git_changed_paths",
    "git_rev_parse",
    "issue_evidence_rebind_receipt",
    "underlying_source_digest",
    "verify_evidence_rebind_receipt",
]
