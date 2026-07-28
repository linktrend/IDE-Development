#!/usr/bin/env python3
"""Packager gate-completion phase: evaluate one draft PR; Bugbot only after fast-gate.

Race-safe: reread head before ready, before comment, and refuse if SHA drifts.
Does not wait serially across many branches — intended to run per PR/check event.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from packager_logic import (  # noqa: E402
    DEFAULT_BUGBOT_COMMAND,
    build_bugbot_comment,
    fast_gate_status,
    parse_required_checks,
    should_request_bugbot,
)
from readiness_status import is_sha_review_ready  # noqa: E402


def run(args: list[str]) -> str:
    return subprocess.check_output(args, text=True).strip()


def gh_api(method: str, url: str, token: str, body=None):
    data = None if body is None else json.dumps(body).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        method=method,
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "linktrend-review-packager",
            "Content-Type": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(req) as resp:
            raw = resp.read().decode("utf-8")
            return json.loads(raw) if raw else {}
    except urllib.error.HTTPError as e:
        detail = e.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"{method} {url} -> {e.code}: {detail}") from e


def pr_head(pr: int) -> str:
    return run(["gh", "pr", "view", str(pr), "--json", "headRefOid", "--jq", ".headRefOid"]).lower()


def pr_meta(pr: int) -> dict:
    return json.loads(
        run(
            [
                "gh",
                "pr",
                "view",
                str(pr),
                "--json",
                "number,url,isDraft,headRefOid,baseRefName,state,headRefName",
            ]
        )
    )


def pr_checks(pr: int) -> list[dict]:
    return json.loads(
        run(["gh", "pr", "checks", str(pr), "--json", "name,state,completedAt,startedAt"]) or "[]"
    )


def list_comments(token: str, repo: str, pr: int) -> list[dict]:
    return gh_api(
        "GET",
        f"https://api.github.com/repos/{repo}/issues/{pr}/comments?per_page=100",
        token,
    )


def post_comment(token: str, repo: str, pr: int, body: str) -> None:
    gh_api(
        "POST",
        f"https://api.github.com/repos/{repo}/issues/{pr}/comments",
        token,
        {"body": body},
    )


def evaluate_pr(pr: int) -> dict:
    token = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN") or ""
    repo = os.environ["GITHUB_REPOSITORY"]
    command = (
        os.environ.get("BUGBOT_REVIEW_COMMAND")
        or os.environ.get("LINKTREND_BUGBOT_REVIEW_COMMAND")
        or DEFAULT_BUGBOT_COMMAND
    ).strip()
    required = (
        os.environ.get("FAST_GATE_CHECKS")
        or os.environ.get("LINKTREND_INTEGRATOR_REQUIRED_CHECKS")
        or "Verify IDE Development"
    )

    meta = pr_meta(pr)
    result = {"pr": pr, "action": None}
    if meta.get("baseRefName") != "development" or meta.get("state") != "OPEN":
        result["action"] = "skip_not_open_development_pr"
        return result

    sha1 = (meta.get("headRefOid") or "").lower()
    ready, detail = is_sha_review_ready(sha1)
    result["headSha"] = sha1
    result["ready_detail"] = detail
    if not ready:
        result["action"] = "skip_not_ready_on_head"
        return result

    checks = pr_checks(pr)
    gate_status, gate_detail = fast_gate_status(checks, parse_required_checks(required))
    result["fast_gate"] = {"status": gate_status, "detail": gate_detail}
    if gate_status != "success":
        result["action"] = "waiting_or_blocked_fast_gate"
        # Stay draft; zero Bugbot
        return result

    # Reread head immediately after gate observation
    sha2 = pr_head(pr)
    if sha2 != sha1:
        result["action"] = "abort_head_changed_after_gate"
        result["headShaNow"] = sha2
        return result

    ready2, _ = is_sha_review_ready(sha2)
    if not ready2:
        result["action"] = "abort_readiness_lost"
        return result

    # Mark ready for review
    if meta.get("isDraft"):
        run(["gh", "pr", "ready", str(pr)])

    # Reread head again before Bugbot comment
    sha3 = pr_head(pr)
    if sha3 != sha1:
        result["action"] = "abort_head_changed_before_bugbot"
        result["headShaNow"] = sha3
        return result

    comments = list_comments(token, repo, pr)
    ok, reason = should_request_bugbot(comments=comments, head_sha=sha3, fast_gate_ok=True)
    if not ok:
        result["action"] = reason
        return result

    comment = build_bugbot_comment(command, sha3)
    post_comment(token, repo, pr, comment)
    # Marker only exists inside the successful comment body (build_bugbot_comment).
    result["action"] = "bugbot_requested"
    result["headSha"] = sha3
    post_comment(
        token,
        repo,
        pr,
        (
            f"## Review freeze\n\n"
            f"Branch `{meta.get('headRefName')}` is frozen at `{sha3}` for review.\n"
            f"Continue only on another work branch or worktree.\n"
        ),
    )
    return result


def resolve_pr_number() -> int | None:
    if os.environ.get("PR_NUMBER"):
        return int(os.environ["PR_NUMBER"])
    # From check_run payload via env HEAD_SHA
    head = os.environ.get("HEAD_SHA") or ""
    if head:
        out = run(
            [
                "gh",
                "pr",
                "list",
                "--base",
                "development",
                "--state",
                "open",
                "--json",
                "number,headRefOid,isDraft",
                "--jq",
                f'[.[] | select(.headRefOid=="{head}")][0].number // empty',
            ]
        )
        return int(out) if out else None
    return None


def main() -> int:
    pr = resolve_pr_number()
    if not pr:
        report = {"action": "no_pr", "detail": "No PR_NUMBER/HEAD_SHA candidate"}
        Path("packager-evaluate-report.json").write_text(
            json.dumps(report, indent=2) + "\n", encoding="utf-8"
        )
        print(json.dumps(report, indent=2))
        return 0
    report = evaluate_pr(pr)
    Path("packager-evaluate-report.json").write_text(
        json.dumps(report, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
