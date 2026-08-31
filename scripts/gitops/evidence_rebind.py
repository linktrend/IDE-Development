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
import os
import re
import subprocess
import tempfile
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any, Mapping, MutableMapping, Sequence

try:
    from scripts.gitops.generated_output_closure import load_graph
except ModuleNotFoundError:  # pragma: no cover - gitops-on-path execution
    from generated_output_closure import load_graph

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
    "generatedPolicyDigest",
    "receiptDigest",
)
REBIND_STATE_FIELD = "evidenceRebinds"
REBIND_COUNT_FIELD = "evidenceRebindCount"
VERIFIED_STATE_FIELD = "verifiedEvidenceRebinds"
STATE_SCHEMA_VERSION = 1
STATE_KIND = "evidence-rebind-state"
MAX_REBINDS = 1


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


def _check_success(value: Any, *, exact_head: str, exact_tree: str, label: str) -> bool:
    if not isinstance(value, Mapping):
        return False
    conclusion = str(value.get("conclusion") or value.get("status") or value.get("result") or "").strip().lower()
    if conclusion not in {"success", "passed", "pass"}:
        return False
    head = _sha(value.get("headCommit") or value.get("headSha"))
    tree = _sha(value.get("gitTree") or value.get("gitTreeSha") or value.get("tree"))
    if not head or not tree:
        return False
    return head == exact_head and tree == exact_tree


def new_rebind_state() -> dict[str, Any]:
    return {
        "schemaVersion": STATE_SCHEMA_VERSION,
        "kind": STATE_KIND,
        REBIND_STATE_FIELD: [],
        REBIND_COUNT_FIELD: 0,
        VERIFIED_STATE_FIELD: [],
    }


def _policy_generated_paths(repo_root: Path | str) -> frozenset[str]:
    try:
        graph = load_graph(Path(repo_root).resolve())
        return generated_binding_paths(graph)
    except Exception as exc:
        raise EvidenceRebindError("generated_policy_invalid", "repository generated-output policy is unavailable") from exc


def _validated_generated_paths(
    repo_root: Path | str,
    supplied: Sequence[str] | None,
) -> tuple[str, ...]:
    expected = _policy_generated_paths(repo_root)
    if not expected:
        raise EvidenceRebindError("generated_policy_invalid", "repository generated-output policy declares no outputs")
    if supplied is not None and set(_paths(supplied)) != expected:
        raise EvidenceRebindError(
            "generated_policy_mismatch",
            "generated paths must equal the repository generated-output policy",
        )
    return tuple(sorted(expected))


def _durable_rebind_state(state: Mapping[str, Any]) -> tuple[int, list[Mapping[str, Any]]]:
    if not isinstance(state, Mapping):
        raise EvidenceRebindError("transaction_state_missing", "durable transaction/session state is required")
    raw_records = state.get(REBIND_STATE_FIELD)
    count = state.get(REBIND_COUNT_FIELD)
    if not isinstance(raw_records, list) or not isinstance(count, int) or isinstance(count, bool):
        raise EvidenceRebindError("transaction_state_missing", "durable evidence-rebind state is incomplete")
    records: list[Mapping[str, Any]] = []
    for record in raw_records:
        if not isinstance(record, Mapping):
            raise EvidenceRebindError("transaction_state_invalid", "durable evidence-rebind records must be objects")
        if not _digest(record.get("receiptDigest")):
            raise EvidenceRebindError("transaction_state_invalid", "durable evidence-rebind records require a receipt digest")
        records.append(record)
    if count != len(records) or count < 0:
        raise EvidenceRebindError("transaction_state_invalid", "durable evidence-rebind count is inconsistent")
    return count, records


def _validate_rebind_state(state: Mapping[str, Any]) -> tuple[int, list[Mapping[str, Any]], list[str]]:
    count, records = _durable_rebind_state(state)
    if state.get("schemaVersion") != STATE_SCHEMA_VERSION or state.get("kind") != STATE_KIND:
        raise EvidenceRebindError("transaction_state_invalid", "durable evidence-rebind state identity is invalid")
    verified = state.get(VERIFIED_STATE_FIELD)
    if not isinstance(verified, list) or any(not _digest(item) for item in verified):
        raise EvidenceRebindError("transaction_state_invalid", "verified evidence-rebind digests are invalid")
    if len(set(verified)) != len(verified):
        raise EvidenceRebindError("transaction_state_invalid", "verified evidence-rebind digests must be unique")
    return count, records, list(verified)


def _record_rebind_state(state: MutableMapping[str, Any], receipt: Mapping[str, Any]) -> None:
    count, records, verified = _validate_rebind_state(state)
    if count >= MAX_REBINDS:
        raise EvidenceRebindError("receipt_loop_detected", "only one evidence-rebind is permitted by durable transaction/session state")
    updated = [dict(item) for item in records]
    updated.append(
        {
            "receiptDigest": receipt["receiptDigest"],
            "sourceCommit": receipt["sourceCommit"],
            "exactHeadCommit": receipt["exactHeadCommit"],
            "exactHeadTree": receipt["exactHeadTree"],
        }
    )
    state[REBIND_STATE_FIELD] = updated
    state[REBIND_COUNT_FIELD] = len(updated)
    state[VERIFIED_STATE_FIELD] = verified


def _record_rebind_verification(state: MutableMapping[str, Any], receipt_digest: str) -> None:
    count, records, verified = _validate_rebind_state(state)
    del count, records
    digest = _digest(receipt_digest)
    if not digest:
        raise EvidenceRebindError("transaction_state_invalid", "verified receipt digest is invalid")
    if digest in verified:
        raise EvidenceRebindError("receipt_replay", "the same signed evidence-rebind receipt cannot verify twice")
    state[VERIFIED_STATE_FIELD] = [*verified, digest]


def load_rebind_state(path: str | Path) -> dict[str, Any]:
    destination = Path(path)
    try:
        payload = json.loads(destination.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise EvidenceRebindError("transaction_state_missing", "durable evidence-rebind transaction/session state cannot be loaded") from exc
    if not isinstance(payload, Mapping):
        raise EvidenceRebindError("transaction_state_invalid", "durable evidence-rebind state must be an object")
    state = dict(payload)
    _validate_rebind_state(state)
    return state


def persist_rebind_state(path: str | Path, state: Mapping[str, Any]) -> Path:
    destination = Path(path)
    if destination.is_symlink():
        raise EvidenceRebindError("transaction_state_invalid", "durable evidence-rebind state path must not be a symlink")
    state_copy = dict(state)
    _validate_rebind_state(state_copy)
    destination.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=f".{destination.name}.", suffix=".tmp", dir=str(destination.parent))
    temporary_path = Path(temporary)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(canonical_json_bytes(state_copy).decode("utf-8"))
            handle.flush()
            os.fsync(handle.fileno())
        if destination.is_symlink():
            raise EvidenceRebindError("transaction_state_invalid", "durable evidence-rebind state path became a symlink")
        os.replace(temporary_path, destination)
    except Exception:
        try:
            temporary_path.unlink(missing_ok=True)
        except OSError:
            pass
        raise
    return destination


@contextmanager
def rebind_state_lock(path: str | Path):
    """Serialize durable state read, verification, and persistence."""

    import fcntl

    lock_path = Path(path).with_name(f".{Path(path).name}.lock")
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    descriptor = os.open(lock_path, os.O_CREAT | os.O_RDWR, 0o600)
    try:
        fcntl.flock(descriptor, fcntl.LOCK_EX)
        yield
    finally:
        fcntl.flock(descriptor, fcntl.LOCK_UN)
        os.close(descriptor)


def _evidence_mapping(
    value: Any,
    *,
    exact_head: str,
    exact_tree: str,
    label: str,
    require_success: bool = True,
) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        raise EvidenceRebindError("evidence_missing", f"{label} must be an exact-head evidence mapping")
    evidence = dict(value)
    if require_success:
        valid = _check_success(evidence, exact_head=exact_head, exact_tree=exact_tree, label=label)
    else:
        valid = evidence.get("valid") is True and _sha(
            evidence.get("headCommit") or evidence.get("headSha")
        ) == exact_head and _sha(
            evidence.get("gitTree") or evidence.get("gitTreeSha") or evidence.get("tree")
        ) == exact_tree
    if not valid:
        raise EvidenceRebindError("evidence_stale", f"{label} must be accepted and bind exact head commit/tree")
    return evidence


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


def git_commit_tree(repo: Path | str, commit: str) -> tuple[str, str]:
    """Resolve a commit and its tree strictly from the local Git object database."""

    root = Path(repo).resolve()
    resolved_commit = git_rev_parse(root, f"{commit}^{{commit}}")
    resolved_tree = git_rev_parse(root, f"{resolved_commit}^{{tree}}")
    return resolved_commit, resolved_tree


def git_changed_paths(repo: Path, source_commit: str, head_commit: str) -> tuple[str, ...]:
    result = subprocess.run(
        [
            "git",
            "-C",
            str(repo),
            "diff-tree",
            "--no-commit-id",
            "-r",
            "--name-only",
            "--no-renames",
            f"{source_commit}^{{tree}}",
            f"{head_commit}^{{tree}}",
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise EvidenceRebindError("stale_identity", "cannot diff source to exact head")
    rows = [line.strip() for line in (result.stdout or "").splitlines() if line.strip()]
    if not rows:
        raise EvidenceRebindError("stale_identity", "evidence-rebind requires a non-empty generated delta")
    return _paths(sorted(set(rows)))


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
    repo_root: Path | str,
    source_commit: str,
    source_tree: str,
    exact_head_commit: str,
    exact_head_tree: str,
    changed_paths: Sequence[str] | None,
    generated_paths: Sequence[str] | None,
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
    durable_state: Mapping[str, Any],
    required_narrow_checks: Sequence[str] = DEFAULT_NARROW_CHECKS,
    receipt_digest: str | None = None,
) -> RebindDecision:
    """Fail closed unless the exact delta is generated-only and independently accepted."""

    source = _sha(source_commit)
    source_tree_sha = _sha(source_tree)
    head = _sha(exact_head_commit)
    head_tree = _sha(exact_head_tree)
    if not source or not source_tree_sha or not head or not head_tree:
        return RebindDecision(False, "stale_identity", "source or exact-head identity is incomplete")
    try:
        trusted_source, trusted_source_tree = git_commit_tree(repo_root, source)
        trusted_head, trusted_head_tree = git_commit_tree(repo_root, head)
    except EvidenceRebindError as error:
        return RebindDecision(False, error.code, error.detail)
    if source != trusted_source or source_tree_sha != trusted_source_tree:
        return RebindDecision(False, "stale_identity", "source identity does not match trusted Git commit/tree objects")
    if head != trusted_head or head_tree != trusted_head_tree:
        return RebindDecision(False, "stale_identity", "exact-head identity does not match trusted Git commit/tree objects")
    if source == head:
        return RebindDecision(False, "stale_identity", "evidence-rebind requires a distinct exact head")
    if source_tree_sha == head_tree:
        return RebindDecision(False, "stale_identity", "generated-only rebind requires a changed Git tree")

    try:
        rebind_count, records, _verified = _validate_rebind_state(durable_state)
        existing_digest = _digest(receipt_digest)
        issued_digests = {
            _digest(record.get("receiptDigest"))
            for record in records
            if isinstance(record, Mapping)
        }
        if rebind_count >= MAX_REBINDS and existing_digest not in issued_digests:
            return RebindDecision(
                False,
                "receipt_loop_detected",
                "only one evidence-rebind is permitted by durable transaction/session state",
            )
        policy_generated = _validated_generated_paths(repo_root, generated_paths)
    except EvidenceRebindError as error:
        return RebindDecision(False, error.code, error.detail)

    receipt = _mapping(source_full_receipt)
    receipt_head = _sha(_receipt_field(receipt, "headCommit", "sourceCommit", "commit"))
    receipt_tree = _sha(_receipt_field(receipt, "gitTree", "gitTreeSha", "tree"))
    receipt_digest = _digest(_receipt_field(receipt, "receiptDigest", "sourceReceiptDigest"))
    if receipt_head != source or receipt_tree != source_tree_sha or not receipt_digest:
        return RebindDecision(False, "stale_identity", "Full evidence is not bound to the independently accepted source")

    try:
        # The caller's path list is intentionally ignored.  The complete set
        # comes from the trusted source/head tree objects above.
        changed = git_changed_paths(Path(repo_root).resolve(), source, head)
        generated = set(policy_generated)
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
    if review_head != head or review_tree != head_tree:
        return RebindDecision(False, "delta_review_missing", "independent delta review is not bound to the exact head commit/tree", changed_paths=changed)
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
        if not _check_success(value, exact_head=head, exact_tree=head_tree, label=f"hosted check {name}"):
            return RebindDecision(False, "narrow_checks_failed", f"narrow hosted check is not exact-head evidence: {name}", changed_paths=changed)

    if not isinstance(scanner, Mapping) or not _check_success(scanner, exact_head=head, exact_tree=head_tree, label="scanner"):
        return RebindDecision(False, "scanner_failure", "secret scanner did not succeed on the exact head commit/tree", changed_paths=changed)

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
    repo_root: Path | str,
    exact_head_commit: str,
    exact_head_tree: str,
    underlying_source_digest: str,
    changed_paths: Sequence[str],
    generated_paths: Sequence[str] | None,
    delta_review: Mapping[str, Any],
    narrow_hosted_checks: Mapping[str, Any],
    scanner: Mapping[str, Any],
    durable_state: Mapping[str, Any],
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
    exact_head = _sha(exact_head_commit)
    exact_tree = _sha(exact_head_tree)
    trusted_source, trusted_source_tree = git_commit_tree(repo_root, source_commit)
    if source_commit != trusted_source or source_tree != trusted_source_tree:
        raise EvidenceRebindError("stale_identity", "source identity does not match trusted Git commit/tree objects")
    trusted_head, trusted_tree = git_commit_tree(repo_root, exact_head)
    if exact_head != trusted_head or exact_tree != trusted_tree:
        raise EvidenceRebindError("stale_identity", "exact-head identity does not match trusted Git commit/tree objects")
    derived_changed = git_changed_paths(Path(repo_root).resolve(), source_commit, exact_head)
    policy_generated = _validated_generated_paths(repo_root, generated_paths)
    count, _records, _verified = _validate_rebind_state(durable_state)
    if count >= MAX_REBINDS:
        raise EvidenceRebindError("receipt_loop_detected", "only one evidence-rebind is permitted by durable transaction/session state")
    _evidence_mapping(
        delta_review,
        exact_head=exact_head,
        exact_tree=exact_tree,
        label="independent delta review",
        require_success=False,
    )
    if not isinstance(narrow_hosted_checks, Mapping) or not narrow_hosted_checks:
        raise EvidenceRebindError("evidence_missing", "hosted checks are required")
    for name, value in narrow_hosted_checks.items():
        _evidence_mapping(value, exact_head=exact_head, exact_tree=exact_tree, label=f"hosted check {name}")
    _evidence_mapping(scanner, exact_head=exact_head, exact_tree=exact_tree, label="scanner")
    payload = {
        "schemaVersion": SCHEMA_VERSION,
        "kind": KIND,
        "repository": repository,
        "sourceCommit": source_commit,
        "sourceTree": source_tree,
        "sourceReceiptDigest": source_digest,
        "sourceWorkflowRunId": run_id,
        "sourceWorkflowRunAttempt": attempt,
        "exactHeadCommit": exact_head,
        "exactHeadTree": exact_tree,
        "underlyingSourceDigest": _digest(underlying_source_digest),
        "dependencyDigest": _digest(identity.get("dependencyDigest")),
        "profileDigest": _digest(identity.get("profileDigest")),
        "workflowDigest": _digest(identity.get("workflowDigest")),
        "changedPaths": list(derived_changed),
        "generatedPaths": list(policy_generated),
        "authenticatedBy": authenticated_by,
        "deltaReviewDigest": canonical_digest(_mapping(delta_review)),
        "narrowChecksDigest": canonical_digest(_mapping(narrow_hosted_checks)),
        "scannerDigest": canonical_digest(_mapping(scanner)),
        "generatedPolicyDigest": canonical_digest({"generatedPaths": list(policy_generated)}),
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
    repo_root: Path | str,
    delta_review: Mapping[str, Any] | None,
    narrow_hosted_checks: Mapping[str, Any] | None,
    scanner: Mapping[str, Any] | None,
    durable_state: MutableMapping[str, Any],
    owned_paths: Sequence[str] = (),
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
        _count, records, verified = _validate_rebind_state(durable_state)
        issued_digests = {
            _digest(record.get("receiptDigest"))
            for record in records
            if isinstance(record, Mapping)
        }
        if supplied not in issued_digests:
            return RebindDecision(False, "transaction_state_missing", "signed evidence-rebind receipt is not recorded in durable transaction/session state")
        if supplied in verified:
            return RebindDecision(False, "receipt_replay", "the same signed evidence-rebind receipt cannot verify twice")
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
        if delta_review is None or narrow_hosted_checks is None or scanner is None:
            return RebindDecision(False, "evidence_missing", "exact-head review, hosted checks, and scanner evidence are required")
        if not isinstance(narrow_hosted_checks, Mapping) or not narrow_hosted_checks:
            return RebindDecision(False, "evidence_missing", "exact-head hosted check mappings are required")
        policy_generated = _validated_generated_paths(repo_root, payload.get("generatedPaths"))
        if payload.get("generatedPolicyDigest") != canonical_digest({"generatedPaths": list(policy_generated)}):
            return RebindDecision(False, "generated_policy_mismatch", "receipt generated paths are not bound to repository policy")
        if payload.get("deltaReviewDigest") != canonical_digest(_mapping(delta_review)):
            return RebindDecision(False, "evidence_mismatch", "independent review evidence does not match receipt digest")
        if payload.get("narrowChecksDigest") != canonical_digest(_mapping(narrow_hosted_checks)):
            return RebindDecision(False, "evidence_mismatch", "hosted check evidence does not match receipt digest")
        if payload.get("scannerDigest") != canonical_digest(_mapping(scanner)):
            return RebindDecision(False, "evidence_mismatch", "scanner evidence does not match receipt digest")
        _evidence_mapping(
            delta_review,
            exact_head=payload["exactHeadCommit"],
            exact_tree=payload["exactHeadTree"],
            label="independent delta review",
            require_success=False,
        )
        for name, value in narrow_hosted_checks.items():
            _evidence_mapping(
                value,
                exact_head=payload["exactHeadCommit"],
                exact_tree=payload["exactHeadTree"],
                label=f"hosted check {name}",
            )
        _evidence_mapping(
            scanner,
            exact_head=payload["exactHeadCommit"],
            exact_tree=payload["exactHeadTree"],
            label="scanner",
        )
        declared_generated = policy_generated
        decision = admit_evidence_rebind(
            repo_root=repo_root,
            source_commit=str(payload["sourceCommit"]),
            source_tree=str(payload["sourceTree"]),
            exact_head_commit=str(payload["exactHeadCommit"]),
            exact_head_tree=str(payload["exactHeadTree"]),
            # changedPaths is receipt output, never an authority for admission.
            changed_paths=None,
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
            delta_review=delta_review,
            narrow_hosted_checks=narrow_hosted_checks,
            scanner=scanner,
            source_full_receipt=source,
            durable_state=durable_state,
            receipt_digest=str(payload["receiptDigest"]),
        )
        if not decision.allowed:
            return decision
        _record_rebind_verification(durable_state, str(payload["receiptDigest"]))
        return decision
    except EvidenceRebindError as error:
        return RebindDecision(False, error.code, error.detail)


def issue_evidence_rebind_receipt(
    source_full_receipt: Mapping[str, Any],
    *,
    repo_root: Path | str,
    exact_head_commit: str,
    exact_head_tree: str,
    changed_paths: Sequence[str],
    generated_paths: Sequence[str] | None,
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
    durable_state: MutableMapping[str, Any],
    store_path: str | Path | None = None,
    state_path: str | Path | None = None,
) -> dict[str, Any]:
    """Admit, sign, and optionally persist an exact-head evidence-rebind receipt."""

    decision = admit_evidence_rebind(
        repo_root=repo_root,
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
        durable_state=durable_state,
    )
    if not decision.allowed:
        raise EvidenceRebindError(decision.code, decision.detail)
    signed = create_evidence_rebind_receipt(
        source_full_receipt,
        repo_root=repo_root,
        exact_head_commit=exact_head_commit,
        exact_head_tree=exact_head_tree,
        underlying_source_digest=decision.underlying_source_digest or underlying_source_digest_source,
        changed_paths=decision.changed_paths or changed_paths,
        generated_paths=generated_paths,
        delta_review=delta_review,
        narrow_hosted_checks=narrow_hosted_checks,
        scanner=scanner,
        durable_state=durable_state,
    )
    _record_rebind_state(durable_state, signed)
    if state_path is not None:
        persist_rebind_state(state_path, durable_state)
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
    "git_commit_tree",
    "git_rev_parse",
    "issue_evidence_rebind_receipt",
    "load_rebind_state",
    "new_rebind_state",
    "underlying_source_digest",
    "persist_rebind_state",
    "rebind_state_lock",
    "verify_evidence_rebind_receipt",
]
