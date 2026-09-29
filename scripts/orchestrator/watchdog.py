#!/usr/bin/env python3
"""Orchestrator watchdog: stalled runs, repeated failures, unpushed work.

Run on every tick of the orchestrator's subscription timer. Prints one JSON
report. Exit codes: 0 = nothing found, 1 = findings, 2 = watchdog error.
``--exit-zero`` always returns 0 on success so a timer handler can read the
JSON without treating findings as a crash.

Read-only: never fetches unless ``--fetch`` is given, never pushes, never
edits the run log. The orchestrator decides what to do with each finding
(heartbeat, restart, next repair rung, flag Carlos) and records it.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))

import runlog  # noqa: E402

WORK_BRANCH_PREFIX = "issue/"
STRONG_MODEL_RE = re.compile(r"sol|opus", re.IGNORECASE)


def _finding(kind: str, severity: str, detail: str, **extra: Any) -> dict[str, Any]:
    return {"kind": kind, "severity": severity, "detail": detail, **extra}


def check_stalled(records: list[dict[str, Any]], now: datetime, stall_after: timedelta) -> list[dict[str, Any]]:
    findings = []
    for rec in records:
        if rec["result"] != "running":
            continue
        last = runlog.parse_ts(rec["updated_at"] or rec["started_at"])
        idle = now - last
        if idle >= stall_after:
            findings.append(
                _finding(
                    "stalled_run",
                    "warning",
                    f"{rec['issue']} attempt {rec['attempt']} ({rec['executor']}) idle {int(idle.total_seconds() // 60)} min",
                    issue=rec["issue"],
                    run_key=rec["run_key"],
                    attempt=rec["attempt"],
                    idle_minutes=int(idle.total_seconds() // 60),
                )
            )
    return findings


def check_repeated_failures(records: list[dict[str, Any]], max_failures: int) -> list[dict[str, Any]]:
    by_issue: dict[str, list[dict[str, Any]]] = {}
    for rec in records:
        by_issue.setdefault(rec["issue"], []).append(rec)
    findings = []
    for issue, runs in sorted(by_issue.items()):
        runs.sort(key=lambda r: r["attempt"])
        finished = [r for r in runs if r["result"] != "running"]
        if not finished or finished[-1]["result"] == "success":
            continue
        rung = finished[-1]["repair_rung"]
        streak = 0
        for rec in reversed(finished):
            if rec["result"] in ("failure", "stalled") and rec["repair_rung"] == rung:
                streak += 1
            else:
                break
        # Ladder: rung 0 gets max_failures tries, then Sol/Opus once (rung 1);
        # rung 2 (the other of Sol/Opus) exists only if the Issue started on one.
        limit = max_failures if rung == 0 else 1
        final_rung = 2 if STRONG_MODEL_RE.search(runs[0]["requested_model"]) else 1
        if streak >= limit:
            exhausted = rung >= final_rung
            action = "flag Carlos" if exhausted else f"escalate to repair rung {rung + 1}"
            findings.append(
                _finding(
                    "repeated_failure",
                    "error" if exhausted else "warning",
                    f"{issue}: {streak} consecutive failed attempt(s) at rung {rung}; {action}",
                    issue=issue,
                    repair_rung=rung,
                    consecutive_failures=streak,
                    last_run_key=finished[-1]["run_key"],
                    recommended_action=action,
                )
            )
    return findings


def _git(repo: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True, check=False)


def _worktrees(repo: Path) -> list[dict[str, str]]:
    out = _git(repo, "worktree", "list", "--porcelain")
    if out.returncode != 0:
        raise RuntimeError(f"not a git repository: {repo}: {out.stderr.strip()}")
    trees, current = [], {}
    for line in out.stdout.splitlines() + [""]:
        if not line:
            if current:
                trees.append(current)
            current = {}
            continue
        key, _, value = line.partition(" ")
        current[key] = value
    return trees


def check_unpushed(repo: Path, fetch: bool) -> list[dict[str, Any]]:
    if fetch:
        _git(repo, "fetch", "--quiet", "--prune", "origin")
    findings = []
    checked_out = set()
    for tree in _worktrees(repo):
        branch = tree.get("branch", "").removeprefix("refs/heads/")
        if not branch.startswith(WORK_BRANCH_PREFIX):
            continue
        checked_out.add(branch)
        status = _git(Path(tree["worktree"]), "status", "--porcelain", "--untracked-files=normal")
        if status.returncode == 0 and status.stdout.strip():
            findings.append(
                _finding(
                    "unpushed_work",
                    "warning",
                    f"{branch}: uncommitted changes in {tree['worktree']}",
                    branch=branch,
                    worktree=tree["worktree"],
                    state="dirty",
                    changed_paths=len(status.stdout.splitlines()),
                )
            )
    heads = _git(repo, "for-each-ref", "--format=%(refname:short)", f"refs/heads/{WORK_BRANCH_PREFIX}")
    for branch in sorted(b for b in heads.stdout.splitlines() if b):
        remote = f"refs/remotes/origin/{branch}"
        if _git(repo, "rev-parse", "--verify", "--quiet", remote).returncode != 0:
            findings.append(
                _finding(
                    "unpushed_work",
                    "warning",
                    f"{branch}: never pushed to origin",
                    branch=branch,
                    state="no_remote",
                    checked_out=branch in checked_out,
                )
            )
            continue
        ahead = _git(repo, "rev-list", "--count", f"{remote}..refs/heads/{branch}")
        count = int(ahead.stdout.strip() or 0) if ahead.returncode == 0 else 0
        if count:
            findings.append(
                _finding(
                    "unpushed_work",
                    "warning",
                    f"{branch}: {count} commit(s) not on origin",
                    branch=branch,
                    state="ahead",
                    ahead=count,
                    checked_out=branch in checked_out,
                )
            )
    return findings


def run(args: argparse.Namespace, now: datetime | None = None) -> dict[str, Any]:
    now = now or datetime.now(timezone.utc)
    root = runlog.resolve_root(args.root)
    records = [rec for _, rec in runlog.iter_records(root)]
    findings = check_stalled(records, now, timedelta(minutes=args.stall_minutes))
    findings += check_repeated_failures(records, args.max_failures)
    for repo in args.repo or []:
        findings += check_unpushed(Path(repo), args.fetch)
    return {
        "kind": "ide-watchdog-report",
        "checked_at": now.replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "runlog_root": str(root),
        "runs_seen": len(records),
        "repos_checked": list(args.repo or []),
        "ok": not findings,
        "findings": findings,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--root", help="run-log directory (default $IDE_RUNLOG_DIR or the Project store)")
    parser.add_argument("--repo", action="append", help="git checkout to scan for unpushed issue/* work (repeatable)")
    parser.add_argument("--stall-minutes", type=int, default=90)
    parser.add_argument("--max-failures", type=int, default=3, help="failed tries allowed at repair rung 0")
    parser.add_argument("--fetch", action="store_true", help="git fetch origin before comparing")
    parser.add_argument("--exit-zero", action="store_true")
    args = parser.parse_args(argv)
    try:
        report = run(args)
    except (RuntimeError, runlog.RunLogError, ValueError, OSError) as exc:
        print(json.dumps({"kind": "ide-watchdog-report", "ok": False, "error": str(exc)}))
        return 2
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["ok"] or args.exit_zero else 1


if __name__ == "__main__":
    raise SystemExit(main())
