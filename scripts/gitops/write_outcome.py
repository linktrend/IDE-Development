#!/usr/bin/env python3
"""Honest outcome helper for GitOps automation jobs."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))
from bugbot_user_credentials import scrub_carlos_token_env  # noqa: E402

VALID = {
    "packaged",
    "waiting",
    "skipped",
    "blocked",
    "failed",
    "bugbot_requested",
    "merged",
    "automation_credentials_blocked",
    "bugbot_user_credentials_blocked",
}


def write_outcome(path: Path, status: str, detail: str, **extra: Any) -> dict[str, Any]:
    if status not in VALID:
        raise SystemExit(f"invalid status {status}")
    payload = {"status": status, "detail": detail, **extra}
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(f"OUTCOME_STATUS={status}")
    print(f"OUTCOME_DETAIL={detail}")
    return payload


def post_check_run(
    *,
    name: str,
    head_sha: str,
    status: str,
    detail: str,
    repo: str,
    token: str,
) -> None:
    if not head_sha or not token or not repo:
        return
    env = scrub_carlos_token_env(os.environ)
    env["GH_TOKEN"] = token
    env["GITHUB_TOKEN"] = token
    # Map outcome → check conclusion. success only for documented terminal successes.
    conclusion = "neutral"
    if status in {"merged", "bugbot_requested", "packaged"}:
        conclusion = "success"
    elif status in {
        "failed",
        "automation_credentials_blocked",
        "bugbot_user_credentials_blocked",
    }:
        conclusion = "failure"
    elif status in {"blocked"}:
        conclusion = "neutral"
    elif status in {"waiting", "skipped"}:
        conclusion = "neutral"
    body = {
        "name": name,
        "head_sha": head_sha,
        "status": "completed",
        "conclusion": conclusion,
        "output": {
            "title": f"{name}: {status}",
            "summary": detail[:65000],
        },
    }
    subprocess.run(
        [
            "gh",
            "api",
            "--method",
            "POST",
            f"repos/{repo}/check-runs",
            "--input",
            "-",
        ],
        input=json.dumps(body),
        text=True,
        check=False,
        env=env,
    )


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--file", default="gitops-outcome.json")
    ap.add_argument("--status", required=True)
    ap.add_argument("--detail", required=True)
    ap.add_argument("--check-name", default="")
    ap.add_argument("--head-sha", default="")
    ap.add_argument("--repo", default=os.environ.get("GITHUB_REPOSITORY", ""))
    ap.add_argument("--token-env", default="AUTOMATION_TOKEN")
    args = ap.parse_args()
    extra = {}
    write_outcome(Path(args.file), args.status, args.detail, **extra)
    if args.check_name and args.head_sha:
        # Autonomous check mutations require an explicit token env (App).
        # Never silently fall back to the ordinary workflow GITHUB_TOKEN.
        token = (os.environ.get(args.token_env) or os.environ.get("GH_TOKEN") or "").strip()
        if not token:
            print(
                "WARN: skipping check-run post; no App/automation token in "
                f"--token-env={args.token_env}",
                file=sys.stderr,
            )
        else:
            post_check_run(
                name=args.check_name,
                head_sha=args.head_sha,
                status=args.status,
                detail=args.detail,
                repo=args.repo,
                token=token,
            )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
