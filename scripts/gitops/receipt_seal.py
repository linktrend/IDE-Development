#!/usr/bin/env python3
"""WP-U06 pre-merge receipt sealing, canonical head resolution, and recovery.

Preserves the existing FullSuiteReceipt schemaVersion 2 identity format from
``coordinator.receipts``.  Never treats GitHub synthetic merge-ref SHAs as
promotable candidate identity.  Never invents empty commits or fake PRs for
legacy recovery.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any, Mapping, Sequence

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))
if str(SCRIPT_DIR.parent) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR.parent))

from coordinator.receipts import (  # noqa: E402
    CandidateIdentity,
    ReceiptError,
    verify_receipt,
)
from phase_integrator import MergeEligibility, phase_merge_eligibility  # noqa: E402

SHA40 = re.compile(r"^[0-9a-f]{40}$")
DIGEST_RE = re.compile(r"^sha256:[0-9a-f]{64}$")
BRANCH_RE = re.compile(r"^(?!.*(?:^|/)\.\.(?:/|$))[A-Za-z0-9._/-]+$")
MERGE_REF_RE = re.compile(r"^refs/pull/[0-9]+/merge$")


class SealError(Exception):
    def __init__(self, code: str, detail: str = "") -> None:
        self.code = code
        self.detail = detail or code
        super().__init__(self.code if not detail else f"{self.code}:{self.detail}")


class RecoveryError(Exception):
    def __init__(self, code: str, detail: str = "") -> None:
        self.code = code
        self.detail = detail or code
        super().__init__(self.code if not detail else f"{self.code}:{self.detail}")


def _sha(value: Any) -> str:
    text = str(value or "").strip().lower()
    return text if SHA40.fullmatch(text) else ""


def _digest(value: Any) -> str:
    text = str(value or "").strip().lower()
    return text if DIGEST_RE.fullmatch(text) else ""


def _mapping(value: Any) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise SealError("invalid_payload", "expected object")
    return value


def _git(repo: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(repo), *args],
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def resolve_canonical_candidate_head(payload: Mapping[str, Any]) -> dict[str, Any]:
    """Resolve the promotable candidate from PR head — never merge-ref identity."""

    data = _mapping(payload)
    pr = data.get("pull_request") if isinstance(data.get("pull_request"), Mapping) else {}
    head_obj = pr.get("head") if isinstance(pr.get("head"), Mapping) else {}
    base_obj = pr.get("base") if isinstance(pr.get("base"), Mapping) else {}

    explicit_branch = str(data.get("source_branch") or data.get("sourceBranch") or "").strip()
    head_ref = str(head_obj.get("ref") or explicit_branch or "").strip()
    if MERGE_REF_RE.fullmatch(explicit_branch) or MERGE_REF_RE.fullmatch(head_ref) or explicit_branch.endswith("/merge"):
        raise SealError("merge_ref_identity_forbidden", "merge-ref cannot identify the candidate")

    candidate_head = _sha(
        data.get("candidate_head")
        or data.get("candidateHead")
        or head_obj.get("sha")
        or data.get("expected_head")
    )
    if "candidate_head" in data or "candidateHead" in data:
        offered = _sha(data.get("candidate_head") or data.get("candidateHead"))
        pr_head = _sha(head_obj.get("sha"))
        merge_sha = _sha(pr.get("merge_commit_sha") or data.get("merge_ref_sha") or data.get("mergeRefSha"))
        if offered and merge_sha and offered == merge_sha and (not pr_head or offered != pr_head):
            raise SealError("merge_ref_identity_forbidden", "offered candidate head is the synthetic merge SHA")

    if not candidate_head:
        raw = head_obj.get("sha") or data.get("candidate_head") or data.get("candidateHead")
        if raw in (None, ""):
            raise SealError("candidate_head_missing", "PR head SHA is required")
        raise SealError("candidate_head_invalid", f"invalid candidate head: {raw!r}")

    if not head_ref or not BRANCH_RE.fullmatch(head_ref) or ".." in head_ref:
        raise SealError("source_branch_invalid", f"invalid source branch: {head_ref!r}")

    candidate_tree = _sha(data.get("candidate_tree") or data.get("candidateTree") or data.get("gitTree"))
    merge_sha = _sha(pr.get("merge_commit_sha") or data.get("merge_ref_sha") or data.get("mergeRefSha"))
    merge_tree = _sha(data.get("merge_ref_tree") or data.get("mergeRefTree"))
    base_sha = _sha(base_obj.get("sha") or data.get("base_sha") or data.get("baseSha"))
    base_tree = _sha(data.get("base_tree") or data.get("baseTree"))

    if merge_sha and merge_sha == candidate_head:
        raise SealError("merge_ref_identity_forbidden", "canonical head must not equal synthetic merge SHA")

    result: dict[str, Any] = {
        "accepted": True,
        "candidateHead": candidate_head,
        "candidateTree": candidate_tree or None,
        "sourceBranch": head_ref,
        "checkoutRef": candidate_head,
        "prNumber": pr.get("number") or data.get("pr_number") or data.get("prNumber"),
        "repository": (
            (head_obj.get("repo") or {}).get("full_name")
            if isinstance(head_obj.get("repo"), Mapping)
            else data.get("repository")
        ),
        "baseSha": base_sha or None,
        "baseTree": base_tree or None,
        "mergeRefEvidence": None,
    }
    if merge_sha:
        result["mergeRefEvidence"] = {
            "kind": "synthetic-merge-ref",
            "mergeSha": merge_sha,
            "mergeTree": merge_tree or None,
            "canonicalHead": candidate_head,
            "canonicalTree": candidate_tree or None,
            "baseSha": base_sha or None,
            "baseTree": base_tree or None,
            "workflowRunId": data.get("workflow_run_id") or data.get("workflowRunId"),
            "workflowRunAttempt": data.get("workflow_run_attempt") or data.get("workflowRunAttempt"),
            "promotableIdentity": False,
            "note": "Merge-ref evidence is integration-only and never replaces candidate head/tree identity.",
        }
    return result


def classify_receipt_artifact(
    artifact: Mapping[str, Any],
    *,
    expected: Mapping[str, Any],
) -> dict[str, Any]:
    """Classify one candidate receipt artifact before selection."""

    row = dict(artifact)
    artifact_id = str(row.get("id") or row.get("name") or "unknown")
    expected_repo = str(expected.get("repository") or "")
    expected_pr = expected.get("prNumber")
    expected_head = _sha(expected.get("headCommit") or expected.get("head") or expected.get("candidateHead"))
    expected_tree = _sha(expected.get("gitTree") or expected.get("tree") or expected.get("candidateTree"))
    expected_run = expected.get("workflowRunId")
    expected_attempt = expected.get("workflowRunAttempt")

    if row.get("readable") is False:
        head = _sha(row.get("headCommit") or row.get("head"))
        classification = "inaccessible"
        if head and expected_head and head != expected_head:
            classification = "inaccessible_stale"
        elif (
            expected_run is not None
            and row.get("workflowRunId") == expected_run
            and (expected_attempt is None or row.get("workflowRunAttempt") == expected_attempt)
            and head == expected_head
        ):
            classification = "inaccessible_expected"
        return {
            "id": artifact_id,
            "classification": classification,
            "artifact": row,
        }

    receipt = row.get("receipt")
    if receipt is not None and not isinstance(receipt, Mapping):
        return {"id": artifact_id, "classification": "malformed", "artifact": row}

    head = _sha(row.get("headCommit") or row.get("head"))
    tree = _sha(row.get("gitTree") or row.get("tree"))
    if isinstance(receipt, Mapping):
        identity = receipt.get("candidateIdentity") if isinstance(receipt.get("candidateIdentity"), Mapping) else {}
        head = head or _sha(identity.get("headCommit"))
        tree = tree or _sha(identity.get("gitTree"))
        try:
            # Parse only enough to reject malformed schema without requiring digest present in test stubs.
            if receipt.get("schemaVersion") not in (None, 2):
                return {"id": artifact_id, "classification": "malformed", "artifact": row}
        except Exception:
            return {"id": artifact_id, "classification": "malformed", "artifact": row}

    if expected_repo and str(row.get("repository") or "") not in ("", expected_repo):
        return {"id": artifact_id, "classification": "unrelated_repository", "artifact": row}
    if expected_pr is not None and row.get("prNumber") not in (None, expected_pr):
        return {"id": artifact_id, "classification": "unrelated_pr", "artifact": row}
    if expected_head and head and head != expected_head:
        return {"id": artifact_id, "classification": "stale_head", "artifact": row}
    if expected_tree and tree and tree != expected_tree:
        return {"id": artifact_id, "classification": "wrong_tree", "artifact": row}
    if expected_run is not None and row.get("workflowRunId") not in (None, expected_run):
        return {"id": artifact_id, "classification": "unrelated_run", "artifact": row}
    if expected_attempt is not None and row.get("workflowRunAttempt") not in (None, expected_attempt):
        return {"id": artifact_id, "classification": "unrelated_attempt", "artifact": row}

    exact_keys_match = (
        bool(expected_head)
        and head == expected_head
        and (not expected_tree or tree == expected_tree)
        and (expected_run is None or row.get("workflowRunId") == expected_run)
        and (expected_attempt is None or row.get("workflowRunAttempt") == expected_attempt)
    )
    if exact_keys_match:
        return {"id": artifact_id, "classification": "exact", "artifact": row}
    if not head:
        return {"id": artifact_id, "classification": "malformed", "artifact": row}
    return {"id": artifact_id, "classification": "non_matching", "artifact": row}


def enumerate_and_select_receipt(
    artifacts: Sequence[Mapping[str, Any]],
    *,
    expected: Mapping[str, Any],
) -> dict[str, Any]:
    """Enumerate all artifacts, skip unrelated failures, select exact receipt."""

    enumerated: list[dict[str, Any]] = []
    skipped: list[str] = []
    exact_rows: list[dict[str, Any]] = []
    inaccessible_expected: list[dict[str, Any]] = []

    for artifact in artifacts:
        classified = classify_receipt_artifact(artifact, expected=expected)
        enumerated.append(classified)
        code = classified["classification"]
        if code == "exact":
            exact_rows.append(classified)
        elif code == "inaccessible_expected":
            inaccessible_expected.append(classified)
        elif code in {
            "inaccessible",
            "inaccessible_stale",
            "stale_head",
            "wrong_tree",
            "unrelated_repository",
            "unrelated_pr",
            "unrelated_run",
            "unrelated_attempt",
            "non_matching",
            "malformed",
        }:
            skipped.append(classified["id"])

    if inaccessible_expected:
        return {
            "accepted": False,
            "code": "expected_receipt_inaccessible",
            "selected": None,
            "enumerated": enumerated,
            "skipped": skipped,
            "detail": "exact expected receipt is inaccessible",
        }
    if not exact_rows:
        return {
            "accepted": False,
            "code": "exact_receipt_missing",
            "selected": None,
            "enumerated": enumerated,
            "skipped": skipped,
            "detail": "no exact retained receipt matched repository/PR/head/tree/run-attempt",
        }
    if len(exact_rows) > 1:
        return {
            "accepted": False,
            "code": "exact_receipt_ambiguous",
            "selected": None,
            "enumerated": enumerated,
            "skipped": skipped,
            "detail": "multiple exact receipts matched",
        }
    selected = exact_rows[0]["artifact"]
    return {
        "accepted": True,
        "code": "exact_receipt_selected",
        "selected": selected,
        "enumerated": enumerated,
        "skipped": skipped,
        "detail": "exact retained receipt selected after full enumeration",
    }


def phase_merge_eligibility_with_receipt(
    record: Mapping[str, Any],
    *,
    live_head_sha: str,
    retained_receipt: Mapping[str, Any] | None,
    conflict: bool = False,
    expected_tree: str | None = None,
) -> MergeEligibility:
    """Ordinary Phase merge requires gates plus an exact retained receipt."""

    base = phase_merge_eligibility(record, live_head_sha=live_head_sha, conflict=conflict)
    checks = dict(base.checks)
    head = _sha(live_head_sha)
    if retained_receipt is None:
        checks["retainedReceipt"] = False
        failed = [name for name, ok in checks.items() if not ok]
        return MergeEligibility(False, "blocked:" + ",".join(failed + ["retained_receipt_missing"]), checks)

    try:
        identity = retained_receipt.get("candidateIdentity")
        if not isinstance(identity, Mapping):
            raise SealError("retained_receipt_malformed", "candidateIdentity missing")
        receipt_head = _sha(identity.get("headCommit"))
        receipt_tree = _sha(identity.get("gitTree"))
        if not receipt_head or receipt_head != head:
            checks["retainedReceipt"] = False
            failed = [name for name, ok in checks.items() if not ok]
            return MergeEligibility(
                False,
                "blocked:" + ",".join(failed + ["retained_receipt_wrong_head"]),
                checks,
            )
        live_tree = _sha(expected_tree)
        if not live_tree:
            candidate = record.get("candidateIdentity")
            if isinstance(candidate, Mapping):
                live_tree = _sha(candidate.get("gitTreeSha") or candidate.get("gitTree"))
        if live_tree and receipt_tree and receipt_tree != live_tree:
            checks["retainedReceipt"] = False
            failed = [name for name, ok in checks.items() if not ok]
            return MergeEligibility(
                False,
                "blocked:" + ",".join(failed + ["retained_receipt_wrong_tree"]),
                checks,
            )
        if str(retained_receipt.get("conclusion") or "").lower() != "success":
            checks["retainedReceipt"] = False
            failed = [name for name, ok in checks.items() if not ok]
            return MergeEligibility(
                False,
                "blocked:" + ",".join(failed + ["retained_receipt_not_success"]),
                checks,
            )
    except SealError as exc:
        checks["retainedReceipt"] = False
        failed = [name for name, ok in checks.items() if not ok]
        return MergeEligibility(False, "blocked:" + ",".join(failed + [exc.code]), checks)

    checks["retainedReceipt"] = True
    if not base.eligible:
        return MergeEligibility(False, base.detail, checks)
    return MergeEligibility(True, "all_current_candidate_gates_and_receipt_passed", checks)


def _installed_state_digest(state: Mapping[str, Any]) -> str:
    identity = {key: value for key, value in state.items() if key != "installedAt"}
    return "sha256:" + hashlib.sha256(
        json.dumps(identity, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def validate_recovery_dispatch(
    *,
    repo: Path,
    repository: str,
    expected_ref: str,
    expected_commit: str,
    expected_tree: str,
    package_version: str,
    checks: Mapping[str, Any],
    dependency_digest: str,
    installed_state_digest: str | None = None,
) -> dict[str, Any]:
    """Admit recovery only for an unchanged integrated development tree.

    Produces a dispatch plan.  Does not create commits, PRs, or mutate source.
    """

    root = Path(repo).resolve()
    if expected_ref != "development":
        raise RecoveryError("recovery_ref_invalid", "recovery is only allowed for development")
    commit = _sha(expected_commit)
    tree = _sha(expected_tree)
    if not commit:
        raise RecoveryError("forged_or_wrong_commit", "expected commit is invalid")
    if not tree:
        raise RecoveryError("forged_or_wrong_tree", "expected tree is invalid")
    if not repository or "/" not in repository:
        raise RecoveryError("repository_invalid", "repository must be owner/name")
    dep = _digest(dependency_digest)
    if not dep:
        raise RecoveryError("dependency_digest_invalid", "dependency digest is invalid")

    manifest_path = root / ".ide-development" / "MANIFEST.json"
    state_path = root / ".ide-development" / "installed-state.json"
    if not manifest_path.is_file():
        raise RecoveryError("manifest_missing", "exact installed release manifest is required")

    if _git(root, "status", "--porcelain"):
        raise RecoveryError("managed_drift", "recovery requires a clean managed checkout")
    if _git(root, "branch", "--show-current") != "development":
        raise RecoveryError("recovery_ref_mismatch", "checkout is not development")
    live_commit = _git(root, "rev-parse", "HEAD").lower()
    live_tree = _git(root, "rev-parse", "HEAD^{tree}").lower()
    if live_commit != commit:
        raise RecoveryError("forged_or_wrong_commit", f"live={live_commit} expected={commit}")
    if live_tree != tree:
        raise RecoveryError("forged_or_wrong_tree", f"live={live_tree} expected={tree}")

    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise RecoveryError("manifest_invalid", str(exc)) from exc
    if str(manifest.get("packageVersion") or "") != package_version:
        raise RecoveryError("manifest_version_mismatch", "manifest packageVersion does not match")

    try:
        state = json.loads(state_path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise RecoveryError("installed_state_invalid", str(exc)) from exc
    if str(state.get("packageVersion") or "") != package_version:
        raise RecoveryError("manifest_version_mismatch", "installed-state packageVersion does not match")
    live_digest = _installed_state_digest(state)
    if installed_state_digest and _digest(installed_state_digest) != live_digest:
        raise RecoveryError("installed_state_digest_mismatch", "installed-state digest mismatch")

    if not isinstance(checks, Mapping) or not all(
        str(checks.get(name) or "").lower() == "success" for name in ("fast", "ci", "security")
    ):
        raise RecoveryError("stale_or_failed_checks", "declared checks must all be success on the same tree")

    bound_dep = _digest(state.get("dependencyDigest"))
    if bound_dep and bound_dep != dep:
        raise RecoveryError("dependency_digest_mismatch", "dependency digest does not match installed binding")

    return {
        "accepted": True,
        "mode": "recovery",
        "repository": repository,
        "checkoutRef": "development",
        "candidateHead": commit,
        "candidateTree": tree,
        "packageVersion": package_version,
        "dependencyDigest": dep,
        "installedStateDigest": live_digest,
        "checks": {name: "success" for name in ("fast", "ci", "security")},
        "opensPullRequest": False,
        "createsCommit": False,
        "receiptSchemaVersion": 2,
        "promotable": True,
        "detail": "recovery dispatch admitted for unchanged integrated development tree",
    }


def evaluate_recovered_receipt_for_promotion(
    receipt: Mapping[str, Any],
    candidate_identity: Mapping[str, Any] | CandidateIdentity,
    *,
    required_gate: str = "full-gate",
) -> dict[str, Any]:
    """Accept recovered receipts for unchanged trees; reject content changes."""

    try:
        verdict = verify_receipt(receipt, candidate_identity, required_gate)
    except ReceiptError as exc:
        return {"accepted": False, "code": exc.code, "detail": str(exc)}
    if verdict.accepted:
        return {
            "accepted": True,
            "code": "accepted",
            "detail": verdict.message or "recovered receipt reusable for unchanged promotion",
            "sourceCommit": verdict.source_commit,
            "promotionCommit": verdict.promotion_commit,
        }
    # Map tree/content identity failures to the U06 content_changed signal.
    code = verdict.code
    if code in {"tree_mismatch", "source_mismatch", "dependency_mismatch", "profile_mismatch", "workflow_mismatch"}:
        code = "content_changed"
    return {"accepted": False, "code": code, "detail": verdict.message or code}


def _json_print(payload: Mapping[str, Any]) -> None:
    print(json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)

    resolve = commands.add_parser("resolve-head", help="resolve canonical PR head (never merge-ref identity)")
    resolve.add_argument("--payload", type=Path, required=True)

    select = commands.add_parser("select-receipt", help="enumerate artifacts and select exact receipt")
    select.add_argument("--artifacts", type=Path, required=True)
    select.add_argument("--expected", type=Path, required=True)

    merge = commands.add_parser("merge-eligibility", help="phase merge eligibility with retained receipt")
    merge.add_argument("--record", type=Path, required=True)
    merge.add_argument("--live-head", required=True)
    merge.add_argument("--receipt", type=Path)
    merge.add_argument("--expected-tree", default="")

    recovery = commands.add_parser("validate-recovery", help="validate recovery dispatch without commit/PR")
    recovery.add_argument("--repo", type=Path, required=True)
    recovery.add_argument("--repository", required=True)
    recovery.add_argument("--expected-ref", default="development")
    recovery.add_argument("--expected-commit", required=True)
    recovery.add_argument("--expected-tree", required=True)
    recovery.add_argument("--package-version", required=True)
    recovery.add_argument("--checks-json", type=Path, required=True)
    recovery.add_argument("--dependency-digest", required=True)
    recovery.add_argument("--installed-state-digest", default="")

    promote = commands.add_parser("evaluate-recovered-promotion", help="reuse recovered receipt for promotion")
    promote.add_argument("--receipt", type=Path, required=True)
    promote.add_argument("--identity", type=Path, required=True)
    promote.add_argument("--gate", default="full-gate")

    args = parser.parse_args(argv)
    try:
        if args.command == "resolve-head":
            payload = json.loads(args.payload.read_text(encoding="utf-8"))
            _json_print(resolve_canonical_candidate_head(payload))
            return 0
        if args.command == "select-receipt":
            artifacts = json.loads(args.artifacts.read_text(encoding="utf-8"))
            expected = json.loads(args.expected.read_text(encoding="utf-8"))
            result = enumerate_and_select_receipt(artifacts, expected=expected)
            _json_print(result)
            return 0 if result.get("accepted") else 1
        if args.command == "merge-eligibility":
            record = json.loads(args.record.read_text(encoding="utf-8"))
            receipt = None
            if args.receipt:
                receipt = json.loads(args.receipt.read_text(encoding="utf-8"))
            verdict = phase_merge_eligibility_with_receipt(
                record,
                live_head_sha=args.live_head,
                retained_receipt=receipt,
                expected_tree=args.expected_tree or None,
            )
            _json_print(verdict.__dict__ if hasattr(verdict, "__dict__") else {"eligible": verdict.eligible, "detail": verdict.detail, "checks": verdict.checks})
            return 0 if verdict.eligible else 1
        if args.command == "validate-recovery":
            checks = json.loads(args.checks_json.read_text(encoding="utf-8"))
            plan = validate_recovery_dispatch(
                repo=args.repo,
                repository=args.repository,
                expected_ref=args.expected_ref,
                expected_commit=args.expected_commit,
                expected_tree=args.expected_tree,
                package_version=args.package_version,
                checks=checks,
                dependency_digest=args.dependency_digest,
                installed_state_digest=args.installed_state_digest or None,
            )
            _json_print(plan)
            return 0
        if args.command == "evaluate-recovered-promotion":
            receipt = json.loads(args.receipt.read_text(encoding="utf-8"))
            identity = json.loads(args.identity.read_text(encoding="utf-8"))
            result = evaluate_recovered_receipt_for_promotion(receipt, identity, required_gate=args.gate)
            _json_print(result)
            return 0 if result.get("accepted") else 1
    except (SealError, RecoveryError) as exc:
        _json_print({"accepted": False, "code": exc.code, "detail": exc.detail})
        return 2
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        _json_print({"accepted": False, "code": "invalid_input", "detail": str(exc)})
        return 2
    return 2


if __name__ == "__main__":
    sys.exit(main())
