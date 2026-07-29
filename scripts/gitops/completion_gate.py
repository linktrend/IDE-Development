#!/usr/bin/env python3
"""Agent completion gate: checkpoint | review-ready | blocked | status.

Exit codes:
  0  ok
  78 incomplete claim (e.g. review_ready asserted without Ready status)
  2  blocked
  1  failed
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

# Allow import of sibling readiness_status
SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

try:
    import readiness_status as rs
except ImportError:
    rs = None  # type: ignore

EXIT_OK = 0
EXIT_FAILED = 1
EXIT_BLOCKED = 2
EXIT_INCOMPLETE = 78

STATES = (
    "checkpointed_unfinished",
    "review_ready",
    "blocked",
    "failed",
)


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def run(cmd: list[str], cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, cwd=str(cwd) if cwd else None, text=True, capture_output=True)


def emit(payload: dict) -> None:
    print(json.dumps(payload, indent=2))


def tree_clean(workdir: Path) -> bool:
    p = run(["git", "status", "--porcelain"], cwd=workdir)
    return p.returncode == 0 and not (p.stdout or "").strip()


def head_sha(workdir: Path) -> str:
    p = run(["git", "rev-parse", "HEAD"], cwd=workdir)
    if p.returncode != 0:
        return ""
    return (p.stdout or "").strip()


def branch_name(workdir: Path) -> str:
    p = run(["git", "rev-parse", "--abbrev-ref", "HEAD"], cwd=workdir)
    return (p.stdout or "").strip() if p.returncode == 0 else ""


def origin_tip_matches(workdir: Path) -> tuple[bool, str]:
    branch = branch_name(workdir)
    if not branch or branch == "HEAD":
        return False, "detached_or_missing_branch"
    run(["git", "fetch", "origin", branch], cwd=workdir)
    head = head_sha(workdir)
    p = run(["git", "rev-parse", f"origin/{branch}"], cwd=workdir)
    if p.returncode != 0:
        return False, "missing_origin_tip"
    tip = (p.stdout or "").strip()
    if head != tip:
        return False, f"head_ne_origin ({head[:8]}!={tip[:8]})"
    return True, head


def tests_ok(args: argparse.Namespace) -> bool:
    if args.tests_ok:
        return True
    return os.environ.get("COMPLETION_TESTS_OK", "").strip() in ("1", "true", "yes")


def evidence_ok(args: argparse.Namespace) -> bool:
    if args.evidence:
        return True
    return bool(os.environ.get("COMPLETION_EVIDENCE", "").strip())


def ready_status_ok(sha: str) -> tuple[bool, str]:
    if rs is None:
        return False, "readiness_status_unavailable"
    # Prefer file backend in tests
    ok, detail = rs.is_sha_review_ready(sha)
    return ok, detail


def write_blocker(path: Path, blocker: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(blocker, indent=2) + "\n", encoding="utf-8")


def cmd_checkpoint(args: argparse.Namespace) -> int:
    workdir = Path(args.workdir).resolve()
    payload = {
        "mode": "checkpoint",
        "state": "checkpointed_unfinished",
        "at": utc_now(),
        "branch": branch_name(workdir),
        "sha": head_sha(workdir),
        "clean": tree_clean(workdir),
        "detail": "checkpoint recorded; unfinished work may continue; no PR by implementer",
    }
    emit(payload)
    return EXIT_OK


def cmd_review_ready(args: argparse.Namespace) -> int:
    workdir = Path(args.workdir).resolve()
    missing: list[str] = []
    if not evidence_ok(args):
        missing.append("evidence_not_declared")
    if not tests_ok(args):
        missing.append("tests_not_declared_passed")
    if not tree_clean(workdir):
        missing.append("dirty_tree")
    tip_ok, tip_detail = origin_tip_matches(workdir)
    if not tip_ok:
        missing.append(f"origin_tip:{tip_detail}")
    sha = head_sha(workdir)
    ready, ready_detail = ready_status_ok(sha) if sha else (False, "no_sha")
    if not ready:
        missing.append(f"review_ready_status:{ready_detail}")

    if missing:
        emit(
            {
                "mode": "review-ready",
                "state": "failed",
                "claim": "incomplete",
                "missing": missing,
                "sha": sha,
                "at": utc_now(),
            }
        )
        return EXIT_INCOMPLETE

    emit(
        {
            "mode": "review-ready",
            "state": "review_ready",
            "sha": sha,
            "branch": branch_name(workdir),
            "at": utc_now(),
            "detail": "Packager may open PR; implementer must not open PR",
        }
    )
    return EXIT_OK


def cmd_blocked(args: argparse.Namespace) -> int:
    workdir = Path(args.workdir).resolve()
    blocker = {
        "schemaVersion": 1,
        "state": "blocked",
        "at": utc_now(),
        "repository": os.environ.get("GITHUB_REPOSITORY") or os.environ.get("GH_REPO") or "",
        "branch": branch_name(workdir),
        "sha": head_sha(workdir),
        "reason": args.reason or os.environ.get("COMPLETION_BLOCKER_REASON") or "unspecified",
        "nextAction": args.next_action
        or os.environ.get("COMPLETION_BLOCKER_NEXT")
        or "Resolve blocker then re-run completion_gate",
        "evidence": args.evidence or os.environ.get("COMPLETION_EVIDENCE") or "",
    }
    out = Path(args.blocker_file or os.environ.get("COMPLETION_BLOCKER_FILE") or "completion-blocker.json")
    if not out.is_absolute():
        out = workdir / out
    write_blocker(out, blocker)
    emit({"mode": "blocked", "state": "blocked", "blockerFile": str(out), **blocker})
    return EXIT_BLOCKED


def cmd_status(args: argparse.Namespace) -> int:
    workdir = Path(args.workdir).resolve()
    sha = head_sha(workdir)
    tip_ok, tip_detail = origin_tip_matches(workdir)
    ready, ready_detail = ready_status_ok(sha) if sha else (False, "no_sha")
    state = "checkpointed_unfinished"
    if ready and tip_ok and tree_clean(workdir):
        state = "review_ready"
    emit(
        {
            "mode": "status",
            "state": state,
            "sha": sha,
            "branch": branch_name(workdir),
            "clean": tree_clean(workdir),
            "originTipOk": tip_ok,
            "originTipDetail": tip_detail,
            "reviewReady": ready,
            "reviewReadyDetail": ready_detail,
            "at": utc_now(),
        }
    )
    return EXIT_OK


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "mode",
        choices=["checkpoint", "review-ready", "blocked", "status"],
    )
    ap.add_argument("--workdir", default=os.environ.get("GITOPS_WORKDIR") or ".")
    ap.add_argument("--tests-ok", action="store_true")
    ap.add_argument("--evidence", default="")
    ap.add_argument("--reason", default="")
    ap.add_argument("--next-action", default="")
    ap.add_argument("--blocker-file", default="")
    args = ap.parse_args(argv)

    try:
        if args.mode == "checkpoint":
            return cmd_checkpoint(args)
        if args.mode == "review-ready":
            return cmd_review_ready(args)
        if args.mode == "blocked":
            return cmd_blocked(args)
        if args.mode == "status":
            return cmd_status(args)
    except Exception as e:  # noqa: BLE001 — fail closed
        emit({"mode": args.mode, "state": "failed", "error": str(e), "at": utc_now()})
        return EXIT_FAILED
    return EXIT_FAILED


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
