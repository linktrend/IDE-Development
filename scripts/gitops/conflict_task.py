#!/usr/bin/env python3
"""Durable conflict_blocked repair tasks (idempotent upsert + attempt cap).

Storage: .linktrend/conflict-tasks/<id>.json in the repository working tree when
local; for GitHub Actions without committing, also emit GitHub Issue payload JSON
to stdout / artifact path. Automatic agent spawn is NOT claimed — only durable
task + resume hooks are implemented.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

MAX_ATTEMPTS = 3
TASK_DIR = ".linktrend/conflict-tasks"


def task_id(repo: str, stage: str, source_sha: str, target_sha: str) -> str:
    raw = f"{repo}|{stage}|{source_sha}|{target_sha}".encode()
    return hashlib.sha256(raw).hexdigest()[:16]


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def default_path(repo_root: Path, tid: str) -> Path:
    return repo_root / TASK_DIR / f"{tid}.json"


def load_task(path: Path) -> dict[str, Any] | None:
    if not path.is_file():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def upsert(
    repo_root: Path,
    *,
    repo: str,
    stage: str,
    source_branch: str,
    target_branch: str,
    source_sha: str,
    target_sha: str,
    status: str,
    next_action: str,
    increment_attempt: bool = False,
) -> dict[str, Any]:
    tid = task_id(repo, stage, source_sha, target_sha)
    path = default_path(repo_root, tid)
    path.parent.mkdir(parents=True, exist_ok=True)
    existing = load_task(path)
    if existing:
        attempts = int(existing.get("attemptCount") or 0)
        if increment_attempt:
            attempts += 1
        task = dict(existing)
        task.update(
            {
                "status": status,
                "attemptCount": attempts,
                "updatedAt": utc_now(),
                "nextAction": next_action,
                "sourceSha": source_sha,
                "targetSha": target_sha,
            }
        )
    else:
        task = {
            "schemaVersion": 1,
            "id": tid,
            "repository": repo,
            "stage": stage,
            "sourceBranch": source_branch,
            "targetBranch": target_branch,
            "sourceSha": source_sha,
            "targetSha": target_sha,
            "status": status,
            "attemptCount": 1 if increment_attempt else 0,
            "maxAttempts": MAX_ATTEMPTS,
            "nextAction": next_action,
            "createdAt": utc_now(),
            "updatedAt": utc_now(),
        }
    if int(task["attemptCount"]) >= MAX_ATTEMPTS and status == "conflict_blocked":
        task["status"] = "Issues"
        task["nextAction"] = (
            "Max repair attempts reached. Stop automatic repair; report Issues to Principal."
        )
    path.write_text(json.dumps(task, indent=2) + "\n", encoding="utf-8")
    return task


def mark_resume(repo_root: Path, tid: str) -> dict[str, Any]:
    path = default_path(repo_root, tid)
    task = load_task(path)
    if not task:
        raise SystemExit(f"missing task {tid}")
    if task.get("status") == "Issues":
        return task
    task["status"] = "ready_for_reevaluation"
    task["updatedAt"] = utc_now()
    path.write_text(json.dumps(task, indent=2) + "\n", encoding="utf-8")
    return task


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)

    up = sub.add_parser("upsert")
    up.add_argument("--repo", required=True)
    up.add_argument("--stage", required=True)
    up.add_argument("--source-branch", required=True)
    up.add_argument("--target-branch", required=True)
    up.add_argument("--source-sha", required=True)
    up.add_argument("--target-sha", required=True)
    up.add_argument("--status", default="conflict_blocked")
    up.add_argument("--next-action", required=True)
    up.add_argument("--increment-attempt", action="store_true")
    up.add_argument("--root", default=".")

    rs = sub.add_parser("resume")
    rs.add_argument("--id", required=True)
    rs.add_argument("--root", default=".")

    sh = sub.add_parser("show")
    sh.add_argument("--id", required=True)
    sh.add_argument("--root", default=".")

    args = ap.parse_args(argv)
    root = Path(args.root).resolve()

    if args.cmd == "upsert":
        task = upsert(
            root,
            repo=args.repo,
            stage=args.stage,
            source_branch=args.source_branch,
            target_branch=args.target_branch,
            source_sha=args.source_sha,
            target_sha=args.target_sha,
            status=args.status,
            next_action=args.next_action,
            increment_attempt=args.increment_attempt,
        )
        print(json.dumps(task, indent=2))
        return 0
    if args.cmd == "resume":
        print(json.dumps(mark_resume(root, args.id), indent=2))
        return 0
    if args.cmd == "show":
        path = default_path(root, args.id)
        task = load_task(path)
        if not task:
            print("{}", end="")
            return 1
        print(json.dumps(task, indent=2))
        return 0
    return 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
