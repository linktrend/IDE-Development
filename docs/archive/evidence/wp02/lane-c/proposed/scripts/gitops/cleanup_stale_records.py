#!/usr/bin/env python3
"""Dry-run inventory of stale IDE Development repair records (Issue #51).

Default posture is plan-only. Never closes GitHub Issues, PRs, or branches.
Live GitHub close remains deferred to Codex/Principal (or repair_task.resolve
for an exact repaired SHA). File-backend completed-record cleanup is delegated
to cleanup_controls.plan_completed_repair_cleanup / repair_task
plan-cleanup-completed.

Preserve always: Issues #43/#44/#51, PR #49, repairs tied to OPEN PRs.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

_GITOPS_DIR = Path(__file__).resolve().parent
if str(_GITOPS_DIR) not in sys.path:
    sys.path.insert(0, str(_GITOPS_DIR))
from cleanup_controls import (  # noqa: E402
    issue_number_from_branch,
    load_preserve_policy,
    plan_completed_repair_cleanup,
    preserve_reason,
)

MARKER_PREFIX = "<!-- linktrend-repair-task:"
LABEL_PRIMARY = "linktrend-repair"


def _caller_repo_for_pr_evidence(repo: str) -> tuple[str | None, str]:
    """Validate caller ``--repo`` for PR-evidence authorization.

    Empty or invalid explicit values must not fall through to implicit ``gh``
    (no ``--repo``) or per-row repository when authorizing file-backend deletes.
    Returns ``(slug, "explicit")`` or ``(None, reason)``.
    """
    slug = (repo or "").strip()
    if not slug:
        return None, "repo_missing"
    if "/" not in slug or " " in slug:
        return None, "repo_invalid"
    return slug, "explicit"


def parse_marker(body: str) -> dict[str, Any] | None:
    for line in (body or "").splitlines():
        if MARKER_PREFIX in line:
            try:
                raw = line.split(MARKER_PREFIX, 1)[1].strip()
                if raw.endswith("-->"):
                    raw = raw[: -len("-->")].strip()
                return json.loads(raw)
            except (json.JSONDecodeError, TypeError, ValueError):
                return None
    return None


def _gh_json(args: list[str]) -> Any:
    try:
        out = subprocess.check_output(["gh", *args], text=True, stderr=subprocess.DEVNULL)
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None
    try:
        return json.loads(out or "null")
    except json.JSONDecodeError:
        return None


def _pr_state(repo: str, pr: str) -> str:
    if not pr or str(pr) in ("", "0", "null", "None"):
        return "NONE"
    data = _gh_json(
        [
            "pr",
            "view",
            str(pr),
            "--repo",
            repo,
            "--json",
            "number,state,mergedAt",
        ]
    )
    if not isinstance(data, dict):
        return "UNKNOWN"
    if data.get("state") == "OPEN":
        return "OPEN"
    if data.get("state") == "MERGED" or data.get("mergedAt"):
        return "MERGED"
    if data.get("state") == "CLOSED":
        return "CLOSED"
    return "UNKNOWN"


def classify_repair(
    task: dict[str, Any],
    *,
    repo: str,
    policy: dict[str, Any],
    pr_state: str | None = None,
) -> dict[str, Any]:
    """Classify one repair marker into keep | candidate | deferred."""
    issue_n = task.get("issueNumber")
    branch = str(task.get("branch") or "")
    pr = str(task.get("prNumber") or task.get("pr") or "")
    failure_type = str(task.get("failureType") or "")
    row: dict[str, Any] = {
        "issueNumber": issue_n,
        "failureId": task.get("failureId") or task.get("id"),
        "failureType": failure_type,
        "branch": branch,
        "pr": pr,
        "resolutionState": task.get("resolutionState") or task.get("status") or "",
        "repairStatus": task.get("repairStatus") or "",
    }

    # Never touch preserve-listed issue numbers themselves
    if issue_n is not None and int(issue_n) in policy["issue_set"]:
        row.update({"decision": "KEEP", "reason": f"preserve_issue_number:{int(issue_n)}"})
        return row

    branch_issue = issue_number_from_branch(branch)
    if branch_issue is not None and branch_issue in policy["issue_set"]:
        row.update({"decision": "KEEP", "reason": f"preserve_issue_number:{branch_issue}"})
        return row

    pr_num = int(pr) if str(pr).isdigit() else None
    reason = preserve_reason(branch, policy=policy, pr_number=pr_num)
    if reason:
        row.update({"decision": "KEEP", "reason": reason})
        return row

    state = pr_state if pr_state is not None else (_pr_state(repo, pr) if pr else "NONE")
    row["prState"] = state

    if state == "OPEN":
        row.update({"decision": "KEEP", "reason": f"open_pr:{pr}"})
        return row

    if state == "UNKNOWN":
        row.update({"decision": "DEFERRED", "reason": "pr_state_unknown"})
        return row

    if state in ("MERGED", "CLOSED") and failure_type in (
        "usage_limit",
        "automation_credentials_blocked",
        "packager_author_blocked",
    ):
        row.update(
            {
                "decision": "CANDIDATE",
                "reason": f"immediate_repair_for_{state.lower()}_pr",
                "githubCloseAuthorized": False,
                "note": "Codex/Principal may close; this tool never auto-closes GitHub",
            }
        )
        return row

    if state in ("MERGED", "CLOSED") and str(task.get("resolutionState") or "") == "resolved":
        row.update(
            {
                "decision": "CANDIDATE",
                "reason": "resolved_repair_linked_pr_closed",
                "githubCloseAuthorized": False,
            }
        )
        return row

    if state == "NONE":
        row.update({"decision": "DEFERRED", "reason": "no_linked_pr"})
        return row

    row.update({"decision": "DEFERRED", "reason": "policy_ambiguous"})
    return row


def inventory_github(repo: str, *, policy: dict[str, Any]) -> dict[str, Any]:
    rows = _gh_json(
        [
            "issue",
            "list",
            "--repo",
            repo,
            "--label",
            LABEL_PRIMARY,
            "--state",
            "open",
            "--limit",
            "100",
            "--json",
            "number,title,body,state",
        ]
    )
    if rows is None:
        return {
            "mode": "dry-run",
            "backend": "github",
            "repo": repo,
            "error": "gh_issue_list_failed",
            "keeps": [],
            "candidates": [],
            "deferred": [],
            "githubMutation": "none",
        }

    keeps: list[dict[str, Any]] = []
    candidates: list[dict[str, Any]] = []
    deferred: list[dict[str, Any]] = []
    for issue in rows or []:
        task = parse_marker(issue.get("body") or "") or {}
        task["issueNumber"] = issue.get("number")
        classified = classify_repair(task, repo=repo, policy=policy)
        decision = classified.get("decision")
        if decision == "KEEP":
            keeps.append(classified)
        elif decision == "CANDIDATE":
            candidates.append(classified)
        else:
            deferred.append(classified)

    return {
        "mode": "dry-run",
        "backend": "github",
        "repo": repo,
        "keeps": keeps,
        "candidates": candidates,
        "deferred": deferred,
        "githubMutation": "none",
        "applyRefused": "github_issue_close_deferred_to_codex",
        "notes": [
            "Default dry-run only; --apply never closes GitHub repair issues.",
            "Preserve Issues #43/#44/#51 and PR #49; keep repairs tied to OPEN PRs.",
        ],
    }


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--repo", default="linktrend/IDE-Development")
    ap.add_argument("--json", action="store_true", help="Emit JSON summary only")
    ap.add_argument(
        "--apply",
        action="store_true",
        help="Refused for GitHub; file-backend uses repair_task plan-cleanup-completed",
    )
    ap.add_argument(
        "--i-understand-close-repairs",
        action="store_true",
        help="Required with --apply; still refuses GitHub closes",
    )
    ap.add_argument(
        "--file-backend",
        action="store_true",
        help="Plan file-backend completed repair cleanup instead of GitHub inventory",
    )
    ap.add_argument("--repair-dir", default="")
    args = ap.parse_args(argv)

    policy = load_preserve_policy()

    if args.file_backend:
        root = Path(
            args.repair_dir
            or os.environ.get("LINKTREND_REPAIR_DIR")
            or os.environ.get("LINKTREND_CONFLICT_DIR")
            or ".git/linktrend-repair-tasks"
        )
        apply = bool(args.apply and args.i_understand_close_repairs)
        if args.apply and not args.i_understand_close_repairs:
            print(
                "REFUSED: --apply requires --i-understand-close-repairs "
                "(file-backend resolved JSON only; never GitHub)",
                file=sys.stderr,
            )
            return 2
        # Caller --repo is authoritative for PR-evidence (default remains
        # linktrend/IDE-Development). Empty/invalid explicit values fail closed
        # so apply authorization never falls through to implicit gh / per-row.
        repo_slug, repo_reason = _caller_repo_for_pr_evidence(args.repo)
        if repo_slug is None:
            print(
                "REFUSED: --repo must be a valid owner/name for file-backend "
                f"PR-evidence authorization ({repo_reason}); "
                "refusing implicit gh / per-row repository fallback",
                file=sys.stderr,
            )
            return 2
        plan = plan_completed_repair_cleanup(root, apply=apply, repo=repo_slug)
        print(json.dumps(plan, indent=2))
        return 0

    if args.apply:
        print(
            "REFUSED: GitHub repair issue close is not authorized by cleanup_stale_records.py. "
            "Report candidates to Codex/Principal. "
            "Exact single-task close remains repair_task.py resolve when policy is unambiguous.",
            file=sys.stderr,
        )
        report = inventory_github(args.repo, policy=policy)
        report["applyRefused"] = "github_issue_close_not_authorized"
        print(json.dumps(report, indent=2))
        return 2

    report = inventory_github(args.repo, policy=policy)
    if args.json:
        print(json.dumps(report, indent=2))
        return 0

    print(f"cleanup_stale_records mode=dry-run repo={args.repo}")
    for row in report.get("keeps") or []:
        print(f"KEEP: repair#{row.get('issueNumber')} — {row.get('reason')}")
    for row in report.get("candidates") or []:
        print(f"CANDIDATE: repair#{row.get('issueNumber')} — {row.get('reason')}")
    for row in report.get("deferred") or []:
        print(f"DEFERRED: repair#{row.get('issueNumber')} — {row.get('reason')}")
    print(json.dumps({k: report[k] for k in ("mode", "backend", "githubMutation", "applyRefused")}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
