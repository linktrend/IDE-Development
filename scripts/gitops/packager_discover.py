#!/usr/bin/env python3
"""Packager discovery: ready tips → draft PRs. Preserves existing PR title/body.

Updates only a delimited managed section. No Bugbot. No serial CI wait.
Requires automation App token (fail closed).
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from packager_logic import is_allowed_work_branch  # noqa: E402
from readiness_status import is_sha_review_ready  # noqa: E402
from write_outcome import write_outcome  # noqa: E402

BEGIN = "<!-- linktrend-packager:begin -->"
END = "<!-- linktrend-packager:end -->"
SECTION_RE = re.compile(
    re.escape(BEGIN) + r".*?" + re.escape(END),
    re.DOTALL,
)


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


def managed_section(sha: str, branch: str) -> str:
    return (
        f"{BEGIN}\n"
        f"## Review Packager (managed)\n\n"
        f"- Candidate tip SHA: `{sha}`\n"
        f"- Branch: `{branch}`\n"
        f"- Phase: discovery — draft only; Bugbot is requested only after fast-gate "
        f"on this exact SHA (evaluate / workflow_run path).\n"
        f"{END}\n"
    )


def merge_body(existing: str, sha: str, branch: str) -> str:
    section = managed_section(sha, branch)
    if SECTION_RE.search(existing or ""):
        return SECTION_RE.sub(section.strip(), existing)
    base = (existing or "").rstrip()
    if base:
        return base + "\n\n" + section
    return section


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


def ensure_draft_pr(token: str, branch: str, sha: str) -> dict:
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
                "number,url,isDraft,headRefOid,title,body",
            ],
            token,
        )
        or "[]"
    )
    if existing:
        pr = existing[0]
        # Ready/frozen PRs: never rewrite title/body (preserve human/agent content).
        if not bool(pr.get("isDraft")):
            return {
                "number": pr["number"],
                "url": pr["url"],
                "isDraft": False,
                "created": False,
                "title_preserved": True,
                "body_untouched": True,
            }
        new_body = merge_body(pr.get("body") or "", sha, branch)
        if new_body != (pr.get("body") or ""):
            run(["gh", "pr", "edit", str(pr["number"]), "--body", new_body], token)
        # Never overwrite title
        return {
            "number": pr["number"],
            "url": pr["url"],
            "isDraft": bool(pr.get("isDraft")),
            "created": False,
            "title_preserved": True,
        }

    title = f"Review: {branch}"
    body = merge_body("", sha, branch)
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
        ],
        token,
    )
    num = int(run(["gh", "pr", "view", url, "--json", "number", "--jq", ".number"], token))
    return {"number": num, "url": url, "isDraft": True, "created": True, "title_preserved": True}


def main() -> int:
    token = os.environ.get("AUTOMATION_TOKEN") or ""
    if not token or os.environ.get("AUTOMATION_TOKEN_SOURCE") != "github_app":
        write_outcome(
            Path("gitops-outcome.json"),
            "automation_credentials_blocked",
            "Packager discover requires GitHub App token (LINKTREND_GITOPS_APP_*)",
        )
        return 0

    repo = os.environ["GITHUB_REPOSITORY"]
    report = []
    packaged = 0
    for b in list_branches(token, repo):
        name = b.get("name") or ""
        if not is_allowed_work_branch(name):
            continue
        sha = ((b.get("commit") or {}).get("sha") or "").lower()
        if not sha:
            continue
        ok, detail = is_sha_review_ready(sha)
        entry: dict = {"branch": name, "headSha": sha, "ready": ok, "detail": detail}
        if not ok:
            entry["action"] = "skipped_not_ready"
            report.append(entry)
            continue
        try:
            pr = ensure_draft_pr(token, name, sha)
            head = run(
                ["gh", "pr", "view", str(pr["number"]), "--json", "headRefOid", "--jq", ".headRefOid"],
                token,
            ).lower()
            if head != sha:
                entry.update({"action": "skipped_head_drift", "pr": pr["number"]})
            else:
                entry.update({"action": "draft_ensured", "pr": pr["number"], "pr_url": pr["url"]})
                packaged += 1
        except Exception as e:  # noqa: BLE001
            entry.update({"action": "error", "reason": str(e)})
        report.append(entry)

    Path("packager-discover-report.json").write_text(
        json.dumps(report, indent=2) + "\n", encoding="utf-8"
    )
    status = "packaged" if packaged else "skipped"
    write_outcome(
        Path("gitops-outcome.json"),
        status,
        f"discover packaged_or_refreshed={packaged}",
        report=report,
    )
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
