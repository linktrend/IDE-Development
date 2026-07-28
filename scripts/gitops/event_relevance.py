#!/usr/bin/env python3
"""Concurrency group keys and privileged-event relevance (testable mirrors of workflow YAML).

GitHub Actions concurrency expressions cannot be executed here; these helpers mirror the
intended mapping so tests can prove pull_request_target / workflow_run / check_run for the
same PR/head share one group, and that unrelated events mint zero App tokens.
"""

from __future__ import annotations

from typing import Any


OUTCOME_CHECKS = frozenset(
    {
        "Linktrend Packager Result",
        "Linktrend Integrator Result",
        "Linktrend Staging Outcome",
        "Linktrend Main Outcome",
        "evaluate",
        "enable-auto-merge",
        "merge-when-ready",
    }
)


def _pr_number_from_list(prs: list | None) -> str:
    if not prs:
        return ""
    return str((prs[0] or {}).get("number") or "")


def _head_ref_from_list(prs: list | None) -> str:
    if not prs:
        return ""
    head = (prs[0] or {}).get("head") or {}
    return str(head.get("ref") or "")


def _base_ref_from_list(prs: list | None) -> str:
    if not prs:
        return ""
    base = (prs[0] or {}).get("base") or {}
    return str(base.get("ref") or "")


def candidate_pr_or_head(event_name: str, event: dict[str, Any]) -> tuple[str, str]:
    """Return (pr_number, head_sha) from trusted event fields only (no API)."""
    if event_name in {"pull_request", "pull_request_target"}:
        pr = event.get("pull_request") or {}
        return str(pr.get("number") or ""), str((pr.get("head") or {}).get("sha") or "")

    if event_name == "workflow_dispatch":
        inputs = event.get("inputs") or {}
        return (
            str(inputs.get("pr_number") or inputs.get("promote_pr_number") or ""),
            str(inputs.get("expected_head_sha") or inputs.get("expected_promote_head") or ""),
        )

    if event_name == "workflow_run":
        wr = event.get("workflow_run") or {}
        return _pr_number_from_list(wr.get("pull_requests")), str(wr.get("head_sha") or "")

    if event_name == "check_run":
        cr = event.get("check_run") or {}
        return _pr_number_from_list(cr.get("pull_requests")), str(cr.get("head_sha") or "")

    return "", ""


def packager_concurrency_group(event_name: str, event: dict[str, Any], *, run_id: str = "0") -> str:
    """Mirror Packager evaluate concurrency: PR number, else head SHA — never event/run/check ids."""
    if event_name in {"schedule", "workflow_dispatch"} and not (
        event.get("inputs") or {}
    ).get("pr_number"):
        # Discover path — unique per run (not shared with evaluate)
        return f"linktrend-packager-discover-{run_id}"

    pr, head = candidate_pr_or_head(event_name, event)
    key = pr or head
    if not key:
        return f"linktrend-packager-eval-skip-{run_id}"
    return f"linktrend-packager-eval-{key}"


def integrator_concurrency_group(event_name: str, event: dict[str, Any], *, run_id: str = "0") -> str:
    """Mirror Integrator concurrency: PR number, else head SHA; cancel-in-progress must be false."""
    if event_name == "workflow_dispatch":
        pr = str((event.get("inputs") or {}).get("pr_number") or "")
        if pr:
            return f"linktrend-integrator-eval-{pr}"
        return f"linktrend-integrator-eval-dispatch-{run_id}"

    pr, head = candidate_pr_or_head(event_name, event)
    key = pr or head
    if not key:
        return f"linktrend-integrator-eval-skip-{run_id}"
    return f"linktrend-integrator-eval-{key}"


def _is_external_check(event: dict[str, Any]) -> bool:
    cr = event.get("check_run") or {}
    slug = str((cr.get("app") or {}).get("slug") or "")
    name = str(cr.get("name") or "")
    if slug == "github-actions":
        return False
    if name in OUTCOME_CHECKS:
        return False
    return True


def _wr_success(event: dict[str, Any]) -> bool:
    wr = event.get("workflow_run") or {}
    return str(wr.get("conclusion") or "") == "success"


def may_run_packager_evaluate(event_name: str, event: dict[str, Any]) -> bool:
    if event_name == "pull_request_target":
        pr = event.get("pull_request") or {}
        base = str((pr.get("base") or {}).get("ref") or "")
        head_ref = str((pr.get("head") or {}).get("ref") or "")
        return base == "development" and not head_ref.startswith("promote/")

    if event_name == "workflow_run":
        if not _wr_success(event):
            return False
        wr = event.get("workflow_run") or {}
        # Push CI with no PR must not wake Packager
        if str(wr.get("event") or "") not in {"pull_request", "pull_request_target"}:
            return False
        head_branch = str(wr.get("head_branch") or "")
        if head_branch.startswith("promote/"):
            return False
        prs = wr.get("pull_requests") or []
        if prs and _base_ref_from_list(prs) != "development":
            return False
        return True

    if event_name == "check_run":
        if not _is_external_check(event):
            return False
        cr = event.get("check_run") or {}
        prs = cr.get("pull_requests") or []
        if not prs:
            return False
        if _base_ref_from_list(prs) != "development":
            return False
        if _head_ref_from_list(prs).startswith("promote/"):
            return False
        return True

    return False


def may_run_packager_discover(event_name: str, event: dict[str, Any]) -> bool:
    return event_name in {"schedule", "workflow_dispatch"}


def may_run_integrator(event_name: str, event: dict[str, Any]) -> bool:
    if event_name == "workflow_dispatch":
        return True
    if event_name == "pull_request_target":
        pr = event.get("pull_request") or {}
        if bool(pr.get("draft")):
            return False
        base = str((pr.get("base") or {}).get("ref") or "")
        head_ref = str((pr.get("head") or {}).get("ref") or "")
        return base == "development" and not head_ref.startswith("promote/")

    if event_name == "workflow_run":
        if not _wr_success(event):
            return False
        wr = event.get("workflow_run") or {}
        if str(wr.get("event") or "") not in {"pull_request", "pull_request_target"}:
            return False
        if str(wr.get("head_branch") or "").startswith("promote/"):
            return False
        prs = wr.get("pull_requests") or []
        if prs and _base_ref_from_list(prs) != "development":
            return False
        return True

    if event_name == "check_run":
        if not _is_external_check(event):
            return False
        cr = event.get("check_run") or {}
        prs = cr.get("pull_requests") or []
        if not prs:
            return False
        if _base_ref_from_list(prs) != "development":
            return False
        if _head_ref_from_list(prs).startswith("promote/"):
            return False
        return True

    return False


def may_run_staging_promote(event_name: str, event: dict[str, Any]) -> bool:
    if event_name in {"schedule", "workflow_dispatch"}:
        return True
    if event_name == "pull_request_target":
        pr = event.get("pull_request") or {}
        base = str((pr.get("base") or {}).get("ref") or "")
        head_ref = str((pr.get("head") or {}).get("ref") or "")
        return base == "staging" and head_ref.startswith("promote/staging/")

    if event_name == "workflow_run":
        if not _wr_success(event):
            return False
        wr = event.get("workflow_run") or {}
        return str(wr.get("head_branch") or "").startswith("promote/staging/")

    if event_name == "check_run":
        if not _is_external_check(event):
            return False
        cr = event.get("check_run") or {}
        prs = cr.get("pull_requests") or []
        if not prs:
            return False
        return (
            _base_ref_from_list(prs) == "staging"
            and _head_ref_from_list(prs).startswith("promote/staging/")
        )

    return False


def may_run_main_promote(event_name: str, event: dict[str, Any]) -> bool:
    if event_name in {"schedule", "workflow_dispatch"}:
        return True
    if event_name == "pull_request_target":
        pr = event.get("pull_request") or {}
        base = str((pr.get("base") or {}).get("ref") or "")
        head_ref = str((pr.get("head") or {}).get("ref") or "")
        return base == "main" and head_ref.startswith("promote/main/")

    if event_name == "workflow_run":
        if not _wr_success(event):
            return False
        wr = event.get("workflow_run") or {}
        return str(wr.get("head_branch") or "").startswith("promote/main/")

    if event_name == "check_run":
        if not _is_external_check(event):
            return False
        cr = event.get("check_run") or {}
        prs = cr.get("pull_requests") or []
        if not prs:
            return False
        return (
            _base_ref_from_list(prs) == "main"
            and _head_ref_from_list(prs).startswith("promote/main/")
        )

    return False


def privileged_workflows_for(event_name: str, event: dict[str, Any]) -> list[str]:
    """Which privileged workflows may start (and thus mint App tokens) for this event."""
    out: list[str] = []
    if may_run_packager_discover(event_name, event):
        out.append("packager-discover")
    if may_run_packager_evaluate(event_name, event):
        out.append("packager-evaluate")
    if may_run_integrator(event_name, event):
        out.append("integrator")
    if may_run_staging_promote(event_name, event):
        out.append("staging-promote")
    if may_run_main_promote(event_name, event):
        out.append("main-promote")
    return out
