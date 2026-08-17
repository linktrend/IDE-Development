#!/usr/bin/env python3
"""Linktrend Review Gate (WP-U01 / Update 1).

Classifies exact-head Bugbot provider results into managed outcomes and decides
the required ``Linktrend Review Gate`` context. Raw ``Cursor Bugbot`` remains an
observed provider signal only and must not stay required after migration.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import asdict, dataclass
from typing import Any, Mapping, Sequence

SCHEMA_VERSION = 1
KIND = "linktrend-review-gate"

REVIEW_GATE_CONTEXT = "Linktrend Review Gate"
RAW_BUGBOT_CONTEXT = "Cursor Bugbot"

OUTCOME_PASSED = "review-passed"
OUTCOME_FINDINGS = "review-findings"
OUTCOME_FAILED = "review-failed"
OUTCOME_ADVISORY = "advisory-unavailable"
OUTCOME_UNKNOWN = "review-unknown"

OUTCOMES = frozenset(
    {
        OUTCOME_PASSED,
        OUTCOME_FINDINGS,
        OUTCOME_FAILED,
        OUTCOME_ADVISORY,
        OUTCOME_UNKNOWN,
    }
)

MAX_INFRASTRUCTURE_ATTEMPTS = 2

PROVIDER_UNAVAILABLE_CLASSES = frozenset(
    {
        "quota",
        "spending_limit",
        "service_outage",
        "provider_error",
    }
)

FULL_SUITE_CONTEXT = "Linktrend Full Suite"
FOUNDER_ALERT_MARKER_PREFIX = "<!-- linktrend-review-gate-alert:"
INFRA_ATTEMPT_MARKER_PREFIX = "<!-- linktrend-review-gate-infra-attempt:"
FALLBACK_REQUEST_MARKER_PREFIX = "<!-- linktrend-review-gate-fallback:"
TRUSTED_PROVIDER_SOURCES = frozenset(
    {
        "repair_observer.usage_limit",
        "operator_verified_provider_error",
        "provider_status_api",
    }
)

_SHA40 = re.compile(r"^[0-9a-f]{40}$")


class ReviewGateError(Exception):
    """Fail-closed review-gate failure with a stable machine code."""

    def __init__(self, code: str, detail: str = "") -> None:
        self.code = code
        self.detail = detail
        super().__init__(f"{code}:{detail}" if detail else code)


def require_sha40(value: str, label: str = "sha") -> str:
    text = (value or "").strip().lower()
    if not _SHA40.fullmatch(text):
        raise ReviewGateError("invalid_sha", f"{label} must be 40 lowercase hex")
    return text


def _norm(value: Any) -> str:
    return str(value or "").strip()


def _lower(value: Any) -> str:
    return _norm(value).lower()


@dataclass(frozen=True)
class Classification:
    """One exact-candidate managed review classification."""

    outcome: str
    gateSuccess: bool
    bugbotPassedClaim: bool
    alertFounder: bool
    detail: str
    headSha: str
    gitTree: str
    repository: str
    pullRequest: int | None
    infrastructureAttempts: int
    providerClass: str | None
    sanitizedAlert: str | None

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["schemaVersion"] = SCHEMA_VERSION
        payload["kind"] = KIND
        payload["context"] = REVIEW_GATE_CONTEXT
        return payload


def assert_full_suite_allows_bugbot(full_suite_status: str) -> None:
    """Final-candidate Bugbot may run only after exact Full Suite success."""
    if _lower(full_suite_status) != "success":
        raise ReviewGateError(
            "bugbot_before_full_forbidden",
            f"full_suite_status={full_suite_status!r}",
        )


def reject_third_infrastructure_attempt(attempts: int) -> None:
    if attempts < 0:
        raise ReviewGateError("invalid_attempts", "attempts must be >= 0")
    if attempts > MAX_INFRASTRUCTURE_ATTEMPTS:
        raise ReviewGateError(
            "infrastructure_attempt_limit",
            f"attempts={attempts} max={MAX_INFRASTRUCTURE_ATTEMPTS}",
        )


def invalidate_if_head_changed(*, bound_head: str, live_head: str) -> None:
    bound = require_sha40(bound_head, "bound_head")
    live = require_sha40(live_head, "live_head")
    if bound != live:
        raise ReviewGateError("stale_head", f"bound={bound} live={live}")


def require_no_raw_bugbot_required(contexts: Sequence[str]) -> None:
    """Managed required contexts must not retain raw Cursor Bugbot after migration."""
    retained = [c for c in contexts if _norm(c) == RAW_BUGBOT_CONTEXT]
    if retained:
        raise ReviewGateError(
            "raw_bugbot_required",
            f"replace {RAW_BUGBOT_CONTEXT!r} with {REVIEW_GATE_CONTEXT!r}",
        )
    if REVIEW_GATE_CONTEXT not in {_norm(c) for c in contexts}:
        # Callers that pass development required-check lists must include the gate.
        # Empty lists are allowed for non-development surfaces.
        return


def require_review_gate_on_development(contexts: Sequence[str]) -> None:
    names = {_norm(c) for c in contexts}
    require_no_raw_bugbot_required(list(names))
    if REVIEW_GATE_CONTEXT not in names:
        raise ReviewGateError(
            "review_gate_missing",
            f"development required checks must include {REVIEW_GATE_CONTEXT!r}",
        )


def reject_undocumented_task_hold(
    *,
    configured_gates_passed: bool,
    task_hold: str | None,
) -> None:
    if configured_gates_passed and _norm(task_hold):
        raise ReviewGateError(
            "undocumented_task_hold",
            "task-level review HOLD is forbidden after configured gates pass",
        )


def evaluate_fallback_review(
    *,
    outcome: str,
    independent_review_configured: bool,
    reviewer_actor: str,
    implementer_actor: str,
    evidence_head: str,
    live_head: str,
) -> dict[str, Any]:
    """Route advisory-unavailable candidates to a non-implementer fallback reviewer."""
    if outcome != OUTCOME_ADVISORY:
        return {"requested": False, "reason": "fallback_not_applicable"}
    if not independent_review_configured:
        return {"requested": False, "reason": "independent_review_not_configured"}
    reviewer = _norm(reviewer_actor)
    implementer = _norm(implementer_actor)
    if not reviewer:
        raise ReviewGateError("fallback_reviewer_missing", "reviewer_actor required")
    if not implementer:
        raise ReviewGateError("implementer_missing", "implementer_actor required")
    if reviewer == implementer:
        raise ReviewGateError(
            "fallback_implementer_rejected",
            "fallback reviewer must not be the implementer",
        )
    invalidate_if_head_changed(bound_head=evidence_head, live_head=live_head)
    return {
        "requested": True,
        "reviewerActor": reviewer,
        "implementerActor": implementer,
        "headSha": require_sha40(live_head, "live_head"),
        "reason": "advisory_unavailable_fallback",
    }


def evaluate_github_approval(
    *,
    approving_review_required: bool,
    reviewer_login: str,
    comment_author_login: str,
    technical_review_clean: bool,
    evidence_head: str,
    live_head: str,
    approval_source: str = "review",
) -> dict[str, Any]:
    """Distinguish technical review evidence from GitHub approval."""
    invalidate_if_head_changed(bound_head=evidence_head, live_head=live_head)
    reviewer = _norm(reviewer_login)
    commenter = _norm(comment_author_login)
    source = _lower(approval_source) or "review"
    if approving_review_required:
        if source == "comment" or (commenter and not reviewer):
            raise ReviewGateError(
                "same_account_approval_rejected",
                "same-account review comment cannot satisfy required GitHub approval",
            )
        if not reviewer:
            raise ReviewGateError("approval_missing", "approving review required")
        return {
            "approvalSatisfied": True,
            "mode": "github_approval",
            "reviewerLogin": reviewer,
        }
    if not technical_review_clean:
        raise ReviewGateError("technical_review_incomplete", "exact-head technical review required")
    return {
        "approvalSatisfied": True,
        "mode": "technical_review_only",
        "rerunFastFull": False,
        "reviewerLogin": reviewer or commenter,
    }


def _provider_class(raw: Mapping[str, Any] | None) -> str | None:
    if not raw:
        return None
    value = _lower(raw.get("class") or raw.get("providerClass") or raw.get("errorClass"))
    if value in PROVIDER_UNAVAILABLE_CLASSES:
        return value
    return None


def verified_provider_unavailability(raw: Mapping[str, Any] | None) -> str | None:
    """Return an approved unavailable class only for trusted verified evidence.

    Free-text heuristics and unverified payloads must not produce
    ``advisory-unavailable`` or gate success.
    """
    if not raw:
        return None
    if raw.get("verified") is not True:
        return None
    source = _norm(raw.get("source") or raw.get("evidenceSource"))
    if source and source not in TRUSTED_PROVIDER_SOURCES:
        return None
    if not source:
        # verified:true without an explicit trusted source is not enough.
        return None
    return _provider_class(raw)


def count_infrastructure_attempts(markers: Sequence[str] | None, *, head_sha: str) -> int:
    """Count only infrastructure-retry markers for the exact candidate head."""
    head = require_sha40(head_sha, "head_sha")
    needle = f"{INFRA_ATTEMPT_MARKER_PREFIX} {head}"
    count = 0
    for raw in markers or []:
        text = _norm(raw)
        if needle in text:
            count += 1
    return count


def founder_alert_marker(head_sha: str) -> str:
    return f"{FOUNDER_ALERT_MARKER_PREFIX} {require_sha40(head_sha)} -->"


def infrastructure_attempt_marker(head_sha: str, attempt: int) -> str:
    return f"{INFRA_ATTEMPT_MARKER_PREFIX} {require_sha40(head_sha)}:{int(attempt)} -->"


def fallback_request_marker(head_sha: str) -> str:
    return f"{FALLBACK_REQUEST_MARKER_PREFIX} {require_sha40(head_sha)} -->"


def build_durable_founder_alert(classification: Classification) -> dict[str, Any]:
    """Build a durable, sanitized founder-alert payload with dedupe marker."""
    if not classification.alertFounder or not classification.sanitizedAlert:
        raise ReviewGateError("founder_alert_not_required", classification.outcome)
    marker = founder_alert_marker(classification.headSha)
    title = (
        f"[Linktrend Review Gate] Bugbot unavailable "
        f"{classification.repository}@{classification.headSha[:12]}"
    )
    body = (
        f"{marker}\n"
        f"{classification.sanitizedAlert}\n\n"
        f"outcome={classification.outcome}\n"
        f"providerClass={classification.providerClass or 'none'}\n"
        f"headSha={classification.headSha}\n"
        f"gitTree={classification.gitTree}\n"
        "This is not a Bugbot pass.\n"
    )
    return {
        "required": True,
        "marker": marker,
        "title": title,
        "body": body,
        "headSha": classification.headSha,
        "dedupeKey": marker,
    }


def founder_alert_already_recorded(existing_bodies: Sequence[str], *, head_sha: str) -> bool:
    marker = founder_alert_marker(head_sha)
    return any(marker in _norm(body) for body in existing_bodies or [])


def require_full_receipt_for_gate_success(
    *,
    gate_success: bool,
    full_receipt: Mapping[str, Any] | None,
    head_sha: str,
    git_tree: str,
) -> None:
    """Successful managed gate publish requires an exact-head Full receipt/check."""
    if not gate_success:
        return
    head = require_sha40(head_sha, "head_sha")
    tree = require_sha40(git_tree, "git_tree")
    if not full_receipt:
        raise ReviewGateError("full_receipt_missing", "successful gate requires Full receipt")
    receipt_head = require_sha40(str(full_receipt.get("headSha") or ""), "full_receipt.headSha")
    receipt_tree = require_sha40(str(full_receipt.get("gitTree") or full_receipt.get("tree") or ""), "full_receipt.gitTree")
    status = _lower(full_receipt.get("status") or full_receipt.get("conclusion") or "")
    context = _norm(full_receipt.get("context") or full_receipt.get("name") or FULL_SUITE_CONTEXT)
    if context not in {FULL_SUITE_CONTEXT, "full", "full-gate", "Linktrend Full Suite"}:
        raise ReviewGateError("full_receipt_wrong_context", context)
    if receipt_head != head:
        raise ReviewGateError("full_receipt_wrong_head", f"receipt={receipt_head} live={head}")
    if receipt_tree != tree:
        raise ReviewGateError("full_receipt_wrong_tree", f"receipt={receipt_tree} live={tree}")
    if status not in {"success", "passed"}:
        raise ReviewGateError("full_receipt_not_success", status or "missing")


def build_fallback_request_comment(
    *,
    fallback: Mapping[str, Any],
    head_sha: str,
) -> dict[str, Any]:
    if not fallback.get("requested"):
        return {"posted": False, "reason": fallback.get("reason") or "not_requested"}
    marker = fallback_request_marker(head_sha)
    reviewer = _norm(fallback.get("reviewerActor"))
    body = (
        f"{marker}\n"
        f"Linktrend Review Gate advisory-unavailable: requesting independent fallback review "
        f"from `{reviewer}` for exact head `{require_sha40(head_sha)}`.\n"
        "Implementer self-review is rejected.\n"
    )
    return {"posted": True, "marker": marker, "body": body, "reviewerActor": reviewer}


def classify_bugbot_result(
    *,
    repository: str,
    head_sha: str,
    git_tree: str,
    pull_request: int | None,
    bugbot_state: str,
    bugbot_conclusion: str | None = None,
    findings_present: bool = False,
    provider_error: Mapping[str, Any] | None = None,
    infrastructure_attempts: int = 1,
    result_head_sha: str | None = None,
    malformed: bool = False,
    forged: bool = False,
    missing: bool = False,
) -> Classification:
    """Classify one Bugbot provider observation into a managed outcome."""
    repo = _norm(repository)
    if not repo or "/" not in repo:
        raise ReviewGateError("invalid_repository", repository)
    head = require_sha40(head_sha, "head_sha")
    tree = require_sha40(git_tree, "git_tree")
    if infrastructure_attempts < 0:
        raise ReviewGateError("invalid_attempts", "attempts must be >= 0")

    if missing or malformed or forged:
        return Classification(
            outcome=OUTCOME_UNKNOWN,
            gateSuccess=False,
            bugbotPassedClaim=False,
            alertFounder=False,
            detail="missing_malformed_or_forged_result",
            headSha=head,
            gitTree=tree,
            repository=repo,
            pullRequest=pull_request,
            infrastructureAttempts=infrastructure_attempts,
            providerClass=None,
            sanitizedAlert=None,
        )

    if result_head_sha is not None:
        result_head = require_sha40(result_head_sha, "result_head_sha")
        if result_head != head:
            return Classification(
                outcome=OUTCOME_UNKNOWN,
                gateSuccess=False,
                bugbotPassedClaim=False,
                alertFounder=False,
                detail="wrong_head_result",
                headSha=head,
                gitTree=tree,
                repository=repo,
                pullRequest=pull_request,
                infrastructureAttempts=infrastructure_attempts,
                providerClass=None,
                sanitizedAlert=None,
            )

    state = _lower(bugbot_state)
    conclusion = _lower(bugbot_conclusion) if bugbot_conclusion is not None else ""
    # Unverified / heuristic provider payloads never authorize advisory success.
    provider = verified_provider_unavailability(provider_error)
    if provider_error and provider is None and provider_error.get("verified") is not True:
        # Explicitly ignore free-text/untrusted hints; continue fail-closed on conclusion.
        provider = None
    elif provider_error and provider is None:
        # verified claimed but source/class untrusted → fail closed as unknown.
        return Classification(
            outcome=OUTCOME_UNKNOWN,
            gateSuccess=False,
            bugbotPassedClaim=False,
            alertFounder=False,
            detail="untrusted_or_incomplete_provider_unavailability_evidence",
            headSha=head,
            gitTree=tree,
            repository=repo,
            pullRequest=pull_request,
            infrastructureAttempts=infrastructure_attempts,
            providerClass=None,
            sanitizedAlert=None,
        )

    if state in {"pending", "queued", "in_progress"}:
        return Classification(
            outcome=OUTCOME_UNKNOWN,
            gateSuccess=False,
            bugbotPassedClaim=False,
            alertFounder=False,
            detail="provider_still_running",
            headSha=head,
            gitTree=tree,
            repository=repo,
            pullRequest=pull_request,
            infrastructureAttempts=infrastructure_attempts,
            providerClass=None,
            sanitizedAlert=None,
        )

    if findings_present:
        return Classification(
            outcome=OUTCOME_FINDINGS,
            gateSuccess=False,
            bugbotPassedClaim=False,
            alertFounder=False,
            detail="genuine_unresolved_findings",
            headSha=head,
            gitTree=tree,
            repository=repo,
            pullRequest=pull_request,
            infrastructureAttempts=infrastructure_attempts,
            providerClass=None,
            sanitizedAlert=None,
        )

    if provider is not None:
        # Infrastructure retries are counted only on verified-unavailability attempts.
        reject_third_infrastructure_attempt(infrastructure_attempts)
        alert = (
            f"Bugbot provider unavailable ({provider}) for {repo}"
            f"@{head[:12]}; Linktrend Review Gate advisory-unavailable"
        )
        return Classification(
            outcome=OUTCOME_ADVISORY,
            gateSuccess=True,
            bugbotPassedClaim=False,
            alertFounder=True,
            detail=f"verified_provider_unavailable:{provider}",
            headSha=head,
            gitTree=tree,
            repository=repo,
            pullRequest=pull_request,
            infrastructureAttempts=infrastructure_attempts,
            providerClass=provider,
            sanitizedAlert=alert,
        )

    # Neutral alone is never advisory-unavailable.
    if conclusion == "neutral" or state == "neutral":
        return Classification(
            outcome=OUTCOME_UNKNOWN,
            gateSuccess=False,
            bugbotPassedClaim=False,
            alertFounder=False,
            detail="neutral_without_verified_provider_error",
            headSha=head,
            gitTree=tree,
            repository=repo,
            pullRequest=pull_request,
            infrastructureAttempts=infrastructure_attempts,
            providerClass=None,
            sanitizedAlert=None,
        )

    if state in {"success", "completed"} and conclusion in {"", "success"}:
        return Classification(
            outcome=OUTCOME_PASSED,
            gateSuccess=True,
            bugbotPassedClaim=True,
            alertFounder=False,
            detail="exact_head_bugbot_clean",
            headSha=head,
            gitTree=tree,
            repository=repo,
            pullRequest=pull_request,
            infrastructureAttempts=infrastructure_attempts,
            providerClass=None,
            sanitizedAlert=None,
        )

    if state in {"failure", "failed", "error", "cancelled", "timed_out"} or conclusion in {
        "failure",
        "cancelled",
        "timed_out",
        "action_required",
    }:
        # conclusion=failure never becomes gate success without verified unavailability above.
        return Classification(
            outcome=OUTCOME_FAILED,
            gateSuccess=False,
            bugbotPassedClaim=False,
            alertFounder=False,
            detail=f"provider_review_or_policy_failure:{state or conclusion}",
            headSha=head,
            gitTree=tree,
            repository=repo,
            pullRequest=pull_request,
            infrastructureAttempts=infrastructure_attempts,
            providerClass=None,
            sanitizedAlert=None,
        )

    return Classification(
        outcome=OUTCOME_UNKNOWN,
        gateSuccess=False,
        bugbotPassedClaim=False,
        alertFounder=False,
        detail=f"ambiguous_provider_result:{state}:{conclusion}",
        headSha=head,
        gitTree=tree,
        repository=repo,
        pullRequest=pull_request,
        infrastructureAttempts=infrastructure_attempts,
        providerClass=None,
        sanitizedAlert=None,
    )


def gate_commit_status(classification: Classification) -> dict[str, str]:
    """Map classification to an honest named commit-status payload."""
    if classification.outcome == OUTCOME_ADVISORY:
        description = "advisory-unavailable (not a Bugbot pass)"
    elif classification.outcome == OUTCOME_PASSED:
        description = "review-passed"
    else:
        description = classification.outcome
    return {
        "context": REVIEW_GATE_CONTEXT,
        "state": "success" if classification.gateSuccess else "failure",
        "description": description[:140],
    }


def migrated_required_contexts(contexts: Sequence[str]) -> list[str]:
    """Replace raw Bugbot required contexts with the managed review gate."""
    out: list[str] = []
    seen: set[str] = set()
    for raw in contexts:
        name = REVIEW_GATE_CONTEXT if _norm(raw) == RAW_BUGBOT_CONTEXT else _norm(raw)
        if not name or name in seen:
            continue
        seen.add(name)
        out.append(name)
    return out


def _load_json_arg(raw: str) -> Any:
    if raw == "-":
        return json.load(sys.stdin)
    return json.loads(raw)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    c = sub.add_parser("classify", help="Classify one Bugbot provider result")
    c.add_argument("--repository", required=True)
    c.add_argument("--head-sha", required=True)
    c.add_argument("--git-tree", required=True)
    c.add_argument("--pull-request", type=int)
    c.add_argument("--bugbot-state", required=True)
    c.add_argument("--bugbot-conclusion", default="")
    c.add_argument("--findings-present", action="store_true")
    c.add_argument("--provider-error-json", default="")
    c.add_argument("--infrastructure-attempts", type=int, default=1)
    c.add_argument("--result-head-sha", default="")
    c.add_argument("--missing", action="store_true")
    c.add_argument("--malformed", action="store_true")
    c.add_argument("--forged", action="store_true")

    r = sub.add_parser("require-contexts", help="Validate migrated required contexts")
    r.add_argument("--contexts-json", required=True)
    r.add_argument("--development", action="store_true")

    f = sub.add_parser("fallback", help="Evaluate advisory fallback review routing")
    f.add_argument("--outcome", required=True)
    f.add_argument("--independent-review-configured", action="store_true")
    f.add_argument("--reviewer-actor", required=True)
    f.add_argument("--implementer-actor", required=True)
    f.add_argument("--evidence-head", required=True)
    f.add_argument("--live-head", required=True)

    a = sub.add_parser("approval", help="Evaluate GitHub approval vs technical review")
    a.add_argument("--approving-review-required", action="store_true")
    a.add_argument("--reviewer-login", default="")
    a.add_argument("--comment-author-login", default="")
    a.add_argument("--technical-review-clean", action="store_true")
    a.add_argument("--evidence-head", required=True)
    a.add_argument("--live-head", required=True)
    a.add_argument("--approval-source", default="review", choices=["review", "comment"])

    b = sub.add_parser("assert-full", help="Fail closed when Bugbot precedes Full")
    b.add_argument("--full-suite-status", required=True)

    t = sub.add_parser("assert-attempts", help="Reject a third infrastructure attempt")
    t.add_argument("--attempts", type=int, required=True)

    fr = sub.add_parser("require-full-receipt", help="Require exact Full receipt before gate success")
    fr.add_argument("--gate-success", action="store_true")
    fr.add_argument("--full-receipt-json", required=True)
    fr.add_argument("--head-sha", required=True)
    fr.add_argument("--git-tree", required=True)

    fa = sub.add_parser("founder-alert", help="Build durable founder-alert payload")
    fa.add_argument("--classification-json", required=True)

    ci = sub.add_parser("count-infra-attempts", help="Count infrastructure retry markers")
    ci.add_argument("--head-sha", required=True)
    ci.add_argument("--markers-json", required=True)

    fb = sub.add_parser("fallback-comment", help="Build fallback request comment body")
    fb.add_argument("--fallback-json", required=True)
    fb.add_argument("--head-sha", required=True)

    args = parser.parse_args(argv)
    try:
        if args.command == "classify":
            provider = json.loads(args.provider_error_json) if args.provider_error_json else None
            result = classify_bugbot_result(
                repository=args.repository,
                head_sha=args.head_sha,
                git_tree=args.git_tree,
                pull_request=args.pull_request,
                bugbot_state=args.bugbot_state,
                bugbot_conclusion=args.bugbot_conclusion or None,
                findings_present=args.findings_present,
                provider_error=provider,
                infrastructure_attempts=args.infrastructure_attempts,
                result_head_sha=args.result_head_sha or None,
                malformed=args.malformed,
                forged=args.forged,
                missing=args.missing,
            )
            payload = {
                "classification": result.to_dict(),
                "commitStatus": gate_commit_status(result),
                "infraAttemptMarker": (
                    infrastructure_attempt_marker(result.headSha, result.infrastructureAttempts)
                    if result.outcome == OUTCOME_ADVISORY
                    else None
                ),
            }
            print(json.dumps(payload, indent=2, sort_keys=True))
            return 0
        if args.command == "require-contexts":
            contexts = _load_json_arg(args.contexts_json)
            if not isinstance(contexts, list):
                raise ReviewGateError("invalid_contexts", "contexts-json must be a list")
            migrated = migrated_required_contexts([str(x) for x in contexts])
            if args.development:
                require_review_gate_on_development(migrated)
            else:
                require_no_raw_bugbot_required(migrated)
            print(json.dumps({"contexts": migrated}, indent=2, sort_keys=True))
            return 0
        if args.command == "fallback":
            payload = evaluate_fallback_review(
                outcome=args.outcome,
                independent_review_configured=args.independent_review_configured,
                reviewer_actor=args.reviewer_actor,
                implementer_actor=args.implementer_actor,
                evidence_head=args.evidence_head,
                live_head=args.live_head,
            )
            print(json.dumps(payload, indent=2, sort_keys=True))
            return 0
        if args.command == "approval":
            payload = evaluate_github_approval(
                approving_review_required=args.approving_review_required,
                reviewer_login=args.reviewer_login,
                comment_author_login=args.comment_author_login,
                technical_review_clean=args.technical_review_clean,
                evidence_head=args.evidence_head,
                live_head=args.live_head,
                approval_source=args.approval_source,
            )
            print(json.dumps(payload, indent=2, sort_keys=True))
            return 0
        if args.command == "assert-full":
            assert_full_suite_allows_bugbot(args.full_suite_status)
            print(json.dumps({"ok": True}, indent=2))
            return 0
        if args.command == "assert-attempts":
            reject_third_infrastructure_attempt(args.attempts)
            print(json.dumps({"ok": True, "attempts": args.attempts}, indent=2))
            return 0
        if args.command == "require-full-receipt":
            receipt = _load_json_arg(args.full_receipt_json)
            if receipt is not None and not isinstance(receipt, dict):
                raise ReviewGateError("invalid_full_receipt", "full-receipt-json must be object or null")
            require_full_receipt_for_gate_success(
                gate_success=args.gate_success,
                full_receipt=receipt,
                head_sha=args.head_sha,
                git_tree=args.git_tree,
            )
            print(json.dumps({"ok": True}, indent=2, sort_keys=True))
            return 0
        if args.command == "founder-alert":
            raw = _load_json_arg(args.classification_json)
            classification = Classification(
                outcome=str(raw["outcome"]),
                gateSuccess=bool(raw["gateSuccess"]),
                bugbotPassedClaim=bool(raw["bugbotPassedClaim"]),
                alertFounder=bool(raw["alertFounder"]),
                detail=str(raw["detail"]),
                headSha=str(raw["headSha"]),
                gitTree=str(raw["gitTree"]),
                repository=str(raw["repository"]),
                pullRequest=raw.get("pullRequest"),
                infrastructureAttempts=int(raw.get("infrastructureAttempts") or 0),
                providerClass=raw.get("providerClass"),
                sanitizedAlert=raw.get("sanitizedAlert"),
            )
            print(json.dumps(build_durable_founder_alert(classification), indent=2, sort_keys=True))
            return 0
        if args.command == "count-infra-attempts":
            markers = _load_json_arg(args.markers_json)
            if not isinstance(markers, list):
                raise ReviewGateError("invalid_markers", "markers-json must be a list")
            count = count_infrastructure_attempts([str(x) for x in markers], head_sha=args.head_sha)
            print(json.dumps({"attempts": count}, indent=2, sort_keys=True))
            return 0
        if args.command == "fallback-comment":
            fallback = _load_json_arg(args.fallback_json)
            if not isinstance(fallback, dict):
                raise ReviewGateError("invalid_fallback", "fallback-json must be object")
            print(json.dumps(build_fallback_request_comment(fallback=fallback, head_sha=args.head_sha), indent=2, sort_keys=True))
            return 0
        raise ReviewGateError("unknown_command", args.command)
    except ReviewGateError as exc:
        print(json.dumps({"error": exc.code, "detail": exc.detail}, indent=2, sort_keys=True))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
