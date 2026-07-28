#!/usr/bin/env python3
"""Review Packager runner — draft PR → fast-gate → ready → Bugbot once.

Does not request Bugbot until named fast-gate is SUCCESS on the exact PR head.
Marker is written only in the Bugbot request comment after the comment succeeds.
"""

from __future__ import annotations

import base64
import json
import os
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from packager_logic import (  # noqa: E402
    DEFAULT_BUGBOT_COMMAND,
    build_bugbot_comment,
    fast_gate_status,
    is_allowed_work_branch,
    parse_required_checks,
    should_request_bugbot,
)
from validate_review_ready import ReviewReadyError, validate_repo  # noqa: E402

READY_PATH = ".linktrend/review-ready.json"


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


def run(args: list[str]) -> str:
    return subprocess.check_output(args, text=True).strip()


def list_branches(token: str, repo: str) -> list[dict]:
    branches = []
    page = 1
    while True:
        chunk = gh_api(
            "GET",
            f"https://api.github.com/repos/{repo}/branches?per_page=100&page={page}",
            token,
        )
        if not chunk:
            break
        branches.extend(chunk)
        if len(chunk) < 100:
            break
        page += 1
    return branches


def fetch_ready_record(repo: str, branch: str) -> dict | None:
    try:
        content = run(
            [
                "gh",
                "api",
                f"repos/{repo}/contents/{READY_PATH}?ref={branch}",
                "--jq",
                ".content",
            ]
        )
    except subprocess.CalledProcessError:
        return None
    if not content or content == "null":
        return None
    raw = base64.b64decode(content.replace("\n", "")).decode("utf-8")
    return json.loads(raw)


def validate_branch_tip(repo_root: Path, branch: str, sha: str) -> dict:
    tmp = Path(tempfile.mkdtemp(prefix="packager-val-"))
    try:
        subprocess.run(
            ["git", "fetch", "origin", branch],
            cwd=str(repo_root),
            check=False,
            capture_output=True,
        )
        subprocess.run(
            ["git", "worktree", "add", "--detach", str(tmp), sha],
            cwd=str(repo_root),
            check=True,
            capture_output=True,
        )
        return validate_repo(tmp)
    finally:
        subprocess.run(
            ["git", "worktree", "remove", "--force", str(tmp)],
            cwd=str(repo_root),
            capture_output=True,
        )


def ensure_draft_pr(branch: str, sha: str, summary: str) -> dict:
    existing = json.loads(
        run(
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
                "number,url,isDraft,headRefOid,body,title",
            ]
        )
        or "[]"
    )
    title = f"Review: {branch}"
    if summary:
        title = summary[:72] if len(summary) <= 72 else summary[:69] + "..."
    body = (
        f"## Review Packager\n\n"
        f"Draft PR for deterministic fast-gate before Bugbot.\n\n"
        f"- Proposed review SHA (marker tip): `{sha}`\n"
        f"- Bugbot is requested only after fast-gate succeeds on this exact SHA.\n"
        f"- Do not push new commits to this branch while under review.\n"
    )
    if existing:
        pr = existing[0]
        # Keep draft until fast-gate passes
        if not pr.get("isDraft"):
            # Already ready — still OK; do not add pre-request markers to body
            pass
        else:
            run(["gh", "pr", "edit", str(pr["number"]), "--body", body])
        return {
            "number": pr["number"],
            "url": pr["url"],
            "isDraft": bool(pr.get("isDraft")),
            "head": pr.get("headRefOid"),
            "created": False,
        }
    url = run(
        [
            "gh",
            "pr",
            "create",
            "--base",
            "development",
            "--head",
            branch,
            "--title",
            title,
            "--body",
            body,
            "--draft",
        ]
    )
    num = int(run(["gh", "pr", "view", url, "--json", "number", "--jq", ".number"]))
    return {"number": num, "url": url, "isDraft": True, "head": sha, "created": True}


def pr_checks(pr: int) -> list[dict]:
    out = run(
        ["gh", "pr", "checks", str(pr), "--json", "name,state,completedAt,startedAt"]
    )
    return json.loads(out or "[]")


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


def mark_ready(pr: int) -> None:
    run(["gh", "pr", "ready", str(pr)])


def wait_fast_gate(pr: int, required: str, timeout: int, poll: int) -> tuple[str, str]:
    deadline = time.time() + timeout
    last = ("pending", "not_started")
    while time.time() < deadline:
        checks = pr_checks(pr)
        status, detail = fast_gate_status(checks, parse_required_checks(required))
        last = (status, detail)
        if status == "success":
            return last
        if status == "failed":
            return last
        time.sleep(poll)
    return ("missing" if last[0] == "pending" else last[0], f"timeout:{last[1]}")


def main() -> int:
    token = os.environ["GH_TOKEN"]
    repo = os.environ["GITHUB_REPOSITORY"]
    repo_root = Path(os.environ.get("GITHUB_WORKSPACE") or ".")
    command = (
        os.environ.get("BUGBOT_REVIEW_COMMAND")
        or os.environ.get("LINKTREND_BUGBOT_REVIEW_COMMAND")
        or DEFAULT_BUGBOT_COMMAND
    ).strip()
    required = os.environ.get("FAST_GATE_CHECKS") or os.environ.get(
        "LINKTREND_INTEGRATOR_REQUIRED_CHECKS"
    ) or "Verify IDE Development"
    timeout = int(os.environ.get("GATE_WAIT_SECONDS") or "900")
    poll = int(os.environ.get("GATE_POLL_SECONDS") or "20")

    report = []
    for b in list_branches(token, repo):
        name = b.get("name") or ""
        if not is_allowed_work_branch(name):
            continue
        sha = ((b.get("commit") or {}).get("sha") or "").lower()
        if not sha:
            continue
        # Must have readiness file
        try:
            if fetch_ready_record(repo, name) is None:
                continue
        except Exception:  # noqa: BLE001
            continue
        entry: dict = {"branch": name, "headSha": sha}
        try:
            detail = validate_branch_tip(repo_root, name, sha)
        except (ReviewReadyError, subprocess.CalledProcessError, OSError) as e:
            entry.update({"status": "ineligible", "reason": str(e), "action": "skipped"})
            report.append(entry)
            continue
        entry["contentSha"] = detail["contentSha"]
        entry["status"] = "eligible"
        try:
            pr = ensure_draft_pr(name, sha, detail.get("summary") or "")
            head = run(
                ["gh", "pr", "view", str(pr["number"]), "--json", "headRefOid", "--jq", ".headRefOid"]
            ).lower()
            if head != sha:
                entry.update(
                    {
                        "action": "skipped_head_drift",
                        "reason": f"PR head {head} != tip {sha}",
                        "pr": pr["number"],
                    }
                )
                report.append(entry)
                continue
            gate_status, gate_detail = wait_fast_gate(pr["number"], required, timeout, poll)
            entry["fast_gate"] = {"status": gate_status, "detail": gate_detail}
            if gate_status != "success":
                entry["action"] = "queued_fast_gate_blocked"
                entry["pr"] = pr["number"]
                # Stay draft; zero Bugbot requests
                report.append(entry)
                continue
            # Promote to ready for review only after fast-gate success
            mark_ready(pr["number"])
            comments = list_comments(token, repo, pr["number"])
            ok, reason = should_request_bugbot(
                comments=comments, head_sha=sha, fast_gate_ok=True
            )
            if not ok:
                entry.update({"action": reason, "pr": pr["number"]})
                report.append(entry)
                continue
            comment = build_bugbot_comment(command, sha)
            post_comment(token, repo, pr["number"], comment)
            entry.update({"action": "bugbot_requested", "pr": pr["number"], "pr_url": pr["url"]})
            post_comment(
                token,
                repo,
                pr["number"],
                (
                    f"## Review freeze\n\n"
                    f"Branch `{name}` is frozen at `{sha}` for review.\n"
                    f"Continue only on another work branch or worktree.\n"
                ),
            )
        except Exception as e:  # noqa: BLE001
            entry.update({"action": "error", "reason": str(e)})
        report.append(entry)

    Path("packager-report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
