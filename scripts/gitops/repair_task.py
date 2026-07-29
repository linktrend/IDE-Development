#!/usr/bin/env python3
"""Unified repair-task upsert (extends conflict_task schema).

IDE owns the schema (docs/contracts/REPAIR-DISPATCHER.md).
Lisa owns ACP dispatch. GitHub never spawns Cursor.

Wraps conflict_task backends for promotion conflicts and generalizes
failure types: ci_failure | merge_conflict | promotion_conflict | immediate_*.
Immediate types do not auto-repair.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from pathlib import Path
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import conflict_task as ct  # noqa: E402

MAX_ATTEMPTS = ct.MAX_ATTEMPTS
SCHEMA_VERSION = 2

ORDINARY_TYPES = frozenset(
    {"ci_failure", "merge_conflict", "promotion_conflict"}
)
IMMEDIATE_PREFIX = "immediate_"


def failure_id(
    repository: str,
    failure_type: str,
    *,
    pr: str = "",
    workflow: str = "",
    check: str = "",
    branch: str = "",
    head_sha: str = "",
    base_sha: str = "",
) -> str:
    raw = "|".join(
        [
            repository,
            failure_type,
            pr,
            workflow,
            check,
            branch,
            head_sha,
            base_sha,
        ]
    ).encode()
    return hashlib.sha256(raw).hexdigest()[:16]


def is_immediate(failure_type: str) -> bool:
    return failure_type.startswith(IMMEDIATE_PREFIX)


def normalize_task(task: dict[str, Any]) -> dict[str, Any]:
    out = dict(task)
    out["schemaVersion"] = SCHEMA_VERSION
    out.setdefault("failureId", out.get("id") or "")
    if out.get("failureId") and not out.get("id"):
        out["id"] = out["failureId"]
    out.setdefault("maxAttempts", MAX_ATTEMPTS)
    out.setdefault("attemptCount", 0)
    out.setdefault("severity", "immediate" if is_immediate(out.get("failureType", "")) else "ordinary")
    out.setdefault("repairStatus", "recorded")
    out.setdefault("lisaDispatchState", "pending" if out["severity"] == "ordinary" else "do_not_dispatch")
    out.setdefault("resolutionState", "open")
    out.setdefault("evidence", {})
    out.setdefault("nextAction", "")
    # Promote-script compatibility fields
    if out.get("failureType") == "promotion_conflict":
        out.setdefault("status", "conflict_blocked")
        out.setdefault("stage", out.get("stage") or "staging")
    if is_immediate(out.get("failureType", "")):
        out["lisaDispatchState"] = "do_not_dispatch"
        out["repairStatus"] = "immediate_no_auto_repair"
        out["nextAction"] = out.get("nextAction") or (
            "Immediate failure — do not auto-repair; report Issues / await Principal."
        )
    return out


def escalate_if_needed(task: dict[str, Any]) -> dict[str, Any]:
    attempts = int(task.get("attemptCount") or 0)
    if attempts >= MAX_ATTEMPTS and task.get("resolutionState") != "resolved":
        task["repairStatus"] = "escalated_issues"
        task["resolutionState"] = "Issues"
        task["lisaDispatchState"] = "exhausted"
        task["status"] = "Issues"
        task["nextAction"] = (
            task.get("nextAction")
            or "Max repair attempts reached. Report Issues to Principal."
        )
    return task


def upsert(task: dict[str, Any], *, increment: bool) -> dict[str, Any]:
    task = normalize_task(task)
    if is_immediate(task.get("failureType", "")):
        # Still durable-record, but never increment repair attempts for auto-dispatch
        increment = False
    backend = ct.get_backend(task["repository"])
    # conflict_task backend keys on id
    task["id"] = task["failureId"]
    out = backend.upsert(task, increment=increment)
    out = normalize_task(out)
    out = escalate_if_needed(out)
    # Persist escalation if status flipped
    if out.get("resolutionState") == "Issues" or out.get("status") == "Issues":
        out = backend.upsert(out, increment=False)
        out = normalize_task(out)
    return out


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    sub = ap.add_subparsers(dest="cmd", required=True)

    up = sub.add_parser("upsert")
    up.add_argument("--repo", required=True)
    up.add_argument("--failure-type", required=True)
    up.add_argument("--branch", default="")
    up.add_argument("--head-sha", default="")
    up.add_argument("--base-sha", default="")
    up.add_argument("--pr", default="")
    up.add_argument("--workflow-id", default="")
    up.add_argument("--check-id", default="")
    up.add_argument("--severity", choices=["ordinary", "immediate"], default="")
    up.add_argument("--next-action", default="")
    up.add_argument("--evidence-json", default="")
    up.add_argument("--stage", default="")  # promotion compat
    up.add_argument("--source-branch", default="")
    up.add_argument("--target-branch", default="")
    up.add_argument("--promote-pr", default="")
    up.add_argument("--increment-attempt", action="store_true")

    # Compat alias for conflict_task callers that want unified path
    up.add_argument("--status", default="")

    rs = sub.add_parser("resolve")
    rs.add_argument("--repo", required=True)
    rs.add_argument("--id", required=True)

    sh = sub.add_parser("show")
    sh.add_argument("--repo", required=True)
    sh.add_argument("--id", required=True)

    args = ap.parse_args(argv)

    if args.cmd == "upsert":
        fid = failure_id(
            args.repo,
            args.failure_type,
            pr=args.pr or args.promote_pr,
            workflow=args.workflow_id,
            check=args.check_id,
            branch=args.branch or args.source_branch,
            head_sha=args.head_sha,
            base_sha=args.base_sha,
        )
        evidence: dict[str, Any] = {}
        if args.evidence_json:
            evidence = json.loads(args.evidence_json)
        sev = args.severity or (
            "immediate" if is_immediate(args.failure_type) else "ordinary"
        )
        task: dict[str, Any] = {
            "failureId": fid,
            "id": fid,
            "repository": args.repo,
            "failureType": args.failure_type,
            "pr": args.pr or args.promote_pr,
            "workflowId": args.workflow_id,
            "checkId": args.check_id,
            "branch": args.branch or args.source_branch,
            "headSha": args.head_sha,
            "baseSha": args.base_sha,
            "severity": sev,
            "attemptCount": 0,
            "maxAttempts": MAX_ATTEMPTS,
            "repairStatus": "recorded",
            "evidence": evidence,
            "nextAction": args.next_action
            or "Lisa ACP Repair Dispatcher may dispatch Cursor ACP (ordinary only).",
            "lisaDispatchState": "do_not_dispatch" if sev == "immediate" else "pending",
            "resolutionState": "open",
            "stage": args.stage,
            "sourceBranch": args.source_branch or args.branch,
            "targetBranch": args.target_branch,
            "sourceSha": args.head_sha,
            "targetSha": args.base_sha,
            "promotePr": args.promote_pr or args.pr,
            "status": args.status
            or ("conflict_blocked" if args.failure_type == "promotion_conflict" else "open"),
        }
        out = upsert(task, increment=args.increment_attempt)
        print(json.dumps(out, indent=2))
        return 0

    backend = ct.get_backend(args.repo)
    if args.cmd == "resolve":
        out = backend.resolve(args.id)
        print(json.dumps(out or {}, indent=2))
        return 0 if out else 1
    if args.cmd == "show":
        out = backend.get(args.id)
        print(json.dumps(out or {}, indent=2))
        return 0 if out else 1
    return 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
