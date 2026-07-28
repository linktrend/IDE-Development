#!/usr/bin/env python3
"""Packager discovery phase: find ready tips, open/refresh draft PRs. No Bugbot. No CI wait."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from packager_logic import is_allowed_work_branch  # noqa: E402
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
                "number,url,isDraft,headRefOid,title",
            ]
        )
        or "[]"
    )
    title = f"Review: {branch}"
    if summary:
        title = summary[:72] if len(summary) <= 72 else summary[:69] + "..."
    body = (
        f"## Review Packager (discovery)\n\n"
        f"Draft PR only — Bugbot is **not** requested in this phase.\n\n"
        f"- Candidate tip SHA: `{sha}`\n"
        f"- Gate-completion job will request Bugbot only after fast-gate succeeds "
        f"on this exact SHA.\n"
    )
    if existing:
        pr = existing[0]
        run(["gh", "pr", "edit", str(pr["number"]), "--body", body, "--title", title])
        # Ensure draft until evaluate promotes it
        if not pr.get("isDraft"):
            # Leave as-is if already ready (evaluate may have promoted)
            pass
        else:
            pass
        return {
            "number": pr["number"],
            "url": pr["url"],
            "isDraft": bool(pr.get("isDraft")),
            "head": pr.get("headRefOid"),
            "created": False,
        }
    # Convert ready PR creation: always draft
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


def main() -> int:
    token = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN") or ""
    if not token:
        print("FAIL: GH_TOKEN required", file=sys.stderr)
        return 2
    repo = os.environ["GITHUB_REPOSITORY"]
    report = []
    for b in list_branches(token, repo):
        name = b.get("name") or ""
        if not is_allowed_work_branch(name):
            continue
        sha = ((b.get("commit") or {}).get("sha") or "").lower()
        if not sha:
            continue
        ok, detail = is_sha_review_ready(sha)
        entry = {"branch": name, "headSha": sha, "ready": ok, "detail": detail}
        if not ok:
            entry["action"] = "skipped_not_ready"
            report.append(entry)
            continue
        try:
            pr = ensure_draft_pr(name, sha, detail)
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
            else:
                entry.update(
                    {
                        "action": "draft_ensured",
                        "pr": pr["number"],
                        "pr_url": pr["url"],
                        "isDraft": pr["isDraft"],
                    }
                )
        except Exception as e:  # noqa: BLE001
            entry.update({"action": "error", "reason": str(e)})
        report.append(entry)

    Path("packager-discover-report.json").write_text(
        json.dumps(report, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
