#!/usr/bin/env python3
"""Packager evaluate: wake on PR / workflow_run / external check_run.

Trusted scripts only (caller must checkout default branch). Race-safe head rereads.

Credentials:
  - GitHub App (AUTOMATION_TOKEN): reads, undraft, freeze comment, check-runs
  - Carlos BUGBOT_USER_TOKEN: the single `@cursor review` comment only (fail closed)
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
from bugbot_user_credentials import (  # noqa: E402
    BugbotUserCredentialsError,
    require_bugbot_user_token,
)
from packager_logic import (  # noqa: E402
    DEFAULT_BUGBOT_COMMAND,
    build_bugbot_comment,
    fast_gate_status,
    parse_required_checks,
    should_request_bugbot,
)
from readiness_status import is_sha_review_ready  # noqa: E402
from write_outcome import post_check_run, write_outcome  # noqa: E402


def run(args: list[str], token: str | None = None) -> str:
    env = os.environ.copy()
    if token:
        env["GH_TOKEN"] = token
        env["GITHUB_TOKEN"] = token
    return subprocess.check_output(args, text=True, env=env).strip()


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


def pr_head(pr: int, token: str) -> str:
    return run(
        ["gh", "pr", "view", str(pr), "--json", "headRefOid", "--jq", ".headRefOid"], token
    ).lower()


def pr_meta(pr: int, token: str) -> dict:
    return json.loads(
        run(
            [
                "gh",
                "pr",
                "view",
                str(pr),
                "--json",
                "number,url,isDraft,headRefOid,baseRefName,state,headRefName",
            ],
            token,
        )
    )


def pr_checks(pr: int, token: str) -> list[dict]:
    return json.loads(
        run(
            ["gh", "pr", "checks", str(pr), "--json", "name,state,completedAt,startedAt"],
            token,
        )
        or "[]"
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


def resolve_pr_number(token: str) -> int | None:
    if os.environ.get("PR_NUMBER"):
        return int(os.environ["PR_NUMBER"])
    # workflow_run payload may pass HEAD_SHA
    head = (os.environ.get("HEAD_SHA") or "").lower()
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
                "number,headRefOid",
                "--jq",
                f'[.[] | select(.headRefOid=="{head}")][0].number // empty',
            ],
            token,
        )
        return int(out) if out else None
    return None


def evaluate_pr(pr: int, app_token: str) -> dict:
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

    meta = pr_meta(pr, app_token)
    result: dict = {"pr": pr}
    if meta.get("baseRefName") != "development" or meta.get("state") != "OPEN":
        result["status"] = "skipped"
        result["detail"] = "not_open_development_pr"
        return result

    sha1 = (meta.get("headRefOid") or "").lower()
    event_head = (os.environ.get("HEAD_SHA") or "").lower()
    if event_head and event_head != sha1:
        result["status"] = "skipped"
        result["detail"] = f"stale_event_head:{event_head}!={sha1}"
        result["headSha"] = sha1
        return result

    ready, detail = is_sha_review_ready(sha1)
    result["headSha"] = sha1
    if not ready:
        result["status"] = "waiting"
        result["detail"] = f"not_ready:{detail}"
        return result

    checks = pr_checks(pr, app_token)
    gate_status, gate_detail = fast_gate_status(checks, parse_required_checks(required))
    result["fast_gate"] = {"status": gate_status, "detail": gate_detail}
    if gate_status != "success":
        result["status"] = "waiting" if gate_status == "pending" else "blocked"
        result["detail"] = f"fast_gate:{gate_status}:{gate_detail}"
        return result

    sha2 = pr_head(pr, app_token)
    if sha2 != sha1:
        result["status"] = "skipped"
        result["detail"] = f"abort_head_changed_after_gate:{sha2}"
        return result

    ready2, _ = is_sha_review_ready(sha2)
    if not ready2:
        result["status"] = "skipped"
        result["detail"] = "readiness_lost"
        return result

    if meta.get("isDraft"):
        run(["gh", "pr", "ready", str(pr)], app_token)

    sha3 = pr_head(pr, app_token)
    if sha3 != sha1:
        result["status"] = "skipped"
        result["detail"] = f"abort_head_changed_before_bugbot:{sha3}"
        return result

    comments = list_comments(app_token, repo, pr)
    ok, reason = should_request_bugbot(comments=comments, head_sha=sha3, fast_gate_ok=True)
    if not ok:
        result["status"] = "skipped" if reason.startswith("skipped_") else "blocked"
        result["detail"] = reason
        return result

    # Bugbot trigger comment — Carlos user token only. Never App / GITHUB_TOKEN.
    try:
        user_token = require_bugbot_user_token("bugbot_comment")
    except BugbotUserCredentialsError as e:
        result["status"] = "bugbot_user_credentials_blocked"
        result["detail"] = str(e)
        return result

    post_comment(user_token, repo, pr, build_bugbot_comment(command, sha3))
    result["status"] = "bugbot_requested"
    result["detail"] = f"requested_for_{sha3}"
    result["headSha"] = sha3
    result["bugbot_comment_token"] = "bugbot_user"
    # Freeze comment remains App-authored (not a Bugbot trigger).
    post_comment(
        app_token,
        repo,
        pr,
        (
            f"## Review freeze\n\n"
            f"Branch `{meta.get('headRefName')}` is frozen at `{sha3}` for review.\n"
            f"Continue only on another work branch or worktree.\n"
        ),
    )
    return result


def main() -> int:
    token = os.environ.get("AUTOMATION_TOKEN") or ""
    source = os.environ.get("AUTOMATION_TOKEN_SOURCE") or ""
    # Evaluate may use App token; for read+comment prefer App. Fail closed if missing.
    if source != "github_app" or not token:
        write_outcome(
            Path("gitops-outcome.json"),
            "automation_credentials_blocked",
            "Packager evaluate requires GitHub App token",
        )
        return 0

    # Fail closed early: Bugbot comment path requires Carlos user token.
    try:
        require_bugbot_user_token("bugbot_comment")
    except BugbotUserCredentialsError as e:
        write_outcome(
            Path("gitops-outcome.json"),
            "bugbot_user_credentials_blocked",
            f"Packager evaluate requires LINKTREND_BUGBOT_USER_TOKEN for Bugbot comment ({e})",
        )
        head = os.environ.get("HEAD_SHA") or ""
        check_token = os.environ.get("GITHUB_TOKEN") or token
        post_check_run(
            name="Linktrend Packager Result",
            head_sha=head,
            status="bugbot_user_credentials_blocked",
            detail=str(e),
            repo=os.environ.get("GITHUB_REPOSITORY") or "",
            token=check_token,
        )
        return 0

    pr = resolve_pr_number(token)
    if not pr:
        write_outcome(Path("gitops-outcome.json"), "skipped", "no_pr_candidate")
        return 0

    report = evaluate_pr(pr, token)
    status = report.get("status") or "failed"
    detail = report.get("detail") or ""
    write_outcome(Path("gitops-outcome.json"), status, detail, report=report)
    head = report.get("headSha") or os.environ.get("HEAD_SHA") or ""
    # Use GITHUB_TOKEN for check-run if provided separately (job-level)
    check_token = os.environ.get("GITHUB_TOKEN") or token
    post_check_run(
        name="Linktrend Packager Result",
        head_sha=head,
        status=status,
        detail=detail,
        repo=os.environ.get("GITHUB_REPOSITORY") or "",
        token=check_token,
    )
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
