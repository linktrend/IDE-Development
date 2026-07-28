#!/usr/bin/env python3
"""Resolve PR number + head SHA from a GitHub Actions event payload (trusted fields only).

Never interpolates PR title/body into a shell. Reads GITHUB_EVENT_PATH JSON.
Prints: pr=<n> and head=<sha> (possibly empty) as GITHUB_OUTPUT lines and stdout.
"""

from __future__ import annotations

import json
import os
import sys
import urllib.request
from pathlib import Path


def api_get(url: str, token: str):
    req = urllib.request.Request(
        url,
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "linktrend-gitops-resolve",
        },
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.load(resp)


def resolve(event_name: str, event: dict, token: str, repo: str, *, promote_prefix: str = "") -> tuple[str, str]:
    pr = ""
    head = ""

    if event_name == "pull_request_target" or event_name == "pull_request":
        pr_obj = event.get("pull_request") or {}
        pr = str(pr_obj.get("number") or "")
        head = str((pr_obj.get("head") or {}).get("sha") or "")
        return pr, head

    if event_name == "workflow_dispatch":
        inputs = event.get("inputs") or {}
        pr = str(inputs.get("pr_number") or inputs.get("promote_pr_number") or "")
        head = str(inputs.get("expected_head_sha") or inputs.get("expected_promote_head") or "")
        return pr, head

    if event_name == "workflow_run":
        wr = event.get("workflow_run") or {}
        head = str(wr.get("head_sha") or "")
        prs = wr.get("pull_requests") or []
        if prs:
            pr = str(prs[0].get("number") or "")
        if not pr and head and token and repo:
            # Find open PR whose head matches; optionally filter promote prefix.
            rows = api_get(f"https://api.github.com/repos/{repo}/pulls?state=open&per_page=50", token)
            for row in rows:
                href = str((row.get("head") or {}).get("ref") or "")
                hsha = str((row.get("head") or {}).get("sha") or "")
                if hsha != head:
                    continue
                if promote_prefix and not href.startswith(promote_prefix):
                    continue
                pr = str(row.get("number") or "")
                break
        return pr, head

    if event_name == "check_run":
        cr = event.get("check_run") or {}
        head = str(cr.get("head_sha") or "")
        prs = cr.get("pull_requests") or []
        if prs:
            pr = str(prs[0].get("number") or "")
        if not pr and head and token and repo:
            rows = api_get(
                f"https://api.github.com/repos/{repo}/commits/{head}/pulls",
                token,
            )
            for row in rows:
                href = str((row.get("head") or {}).get("ref") or "")
                if promote_prefix and not href.startswith(promote_prefix):
                    continue
                pr = str(row.get("number") or "")
                break
        return pr, head

    return pr, head


def main() -> int:
    event_path = os.environ.get("GITHUB_EVENT_PATH") or ""
    event_name = os.environ.get("GITHUB_EVENT_NAME") or os.environ.get("EVENT_NAME") or ""
    token = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN") or ""
    repo = os.environ.get("GITHUB_REPOSITORY") or ""
    promote_prefix = os.environ.get("PROMOTE_PREFIX") or ""

    if not event_path or not Path(event_path).is_file():
        print("pr=", flush=True)
        print("head=", flush=True)
        return 0

    event = json.loads(Path(event_path).read_text(encoding="utf-8"))
    pr, head = resolve(event_name, event, token, repo, promote_prefix=promote_prefix)

    lines = [f"pr={pr}", f"head={head}"]
    out = os.environ.get("GITHUB_OUTPUT")
    if out:
        with open(out, "a", encoding="utf-8") as fh:
            fh.write("\n".join(lines) + "\n")
    for line in lines:
        print(line)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
