#!/usr/bin/env python3
"""Detect review freeze for Pull waves.

Frozen when any of:
  1) Valid unprocessed readiness marker at branch tip
  2) Open PR into development whose head OID == branch tip (under review)
  3) Explicit .linktrend/review-freeze.json at tip covering this tip SHA
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from validate_review_ready import ReviewReadyError, validate_repo  # noqa: E402


def _run(args: list[str], cwd: Path) -> str:
    p = subprocess.run(args, cwd=str(cwd), text=True, capture_output=True)
    if p.returncode != 0:
        return ""
    return p.stdout.strip()


def has_explicit_freeze(cwd: Path, tip: str) -> bool:
    path = cwd / ".linktrend" / "review-freeze.json"
    if not path.is_file():
        return False
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return False
    frozen = (data.get("frozenSha") or data.get("headSha") or "").lower()
    return bool(frozen) and frozen == tip.lower()


def has_open_review_pr(branch: str, tip: str) -> bool:
    out = _run(
        [
            "gh",
            "pr",
            "list",
            "--head",
            branch,
            "--base",
            "development",
            "--state",
            "open",
            "--json",
            "number,headRefOid,isDraft",
        ],
        Path.cwd(),
    )
    if not out:
        return False
    try:
        rows = json.loads(out)
    except json.JSONDecodeError:
        return False
    for r in rows:
        if (r.get("headRefOid") or "").lower() == tip.lower():
            return True
    return False


def is_frozen(repo_root: Path, branch: str) -> tuple[bool, str]:
    # Resolve tip for branch without checking out when possible
    tip = _run(["git", "rev-parse", f"refs/heads/{branch}"], repo_root)
    if not tip:
        tip = _run(["git", "rev-parse", f"refs/remotes/origin/{branch}"], repo_root)
    if not tip:
        return False, "branch_not_found"

    # Temporary worktree for validation without disturbing caller
    import tempfile
    import shutil

    tmp = Path(tempfile.mkdtemp(prefix="freeze-check-"))
    try:
        subprocess.run(
            ["git", "worktree", "add", "--detach", str(tmp), tip],
            cwd=str(repo_root),
            check=True,
            capture_output=True,
        )
        try:
            validate_repo(tmp)
            return True, "valid_review_ready_marker"
        except ReviewReadyError:
            pass
        if has_explicit_freeze(tmp, tip):
            return True, "explicit_review_freeze_record"
    finally:
        subprocess.run(
            ["git", "worktree", "remove", "--force", str(tmp)],
            cwd=str(repo_root),
            capture_output=True,
        )
        shutil.rmtree(tmp, ignore_errors=True)

    if has_open_review_pr(branch, tip):
        return True, "open_review_pr_at_tip"

    return False, "not_frozen"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-root", default=".")
    ap.add_argument("--branch", required=True)
    args = ap.parse_args()
    frozen, reason = is_frozen(Path(args.repo_root).resolve(), args.branch)
    print(reason)
    return 0 if frozen else 1


if __name__ == "__main__":
    raise SystemExit(main())
