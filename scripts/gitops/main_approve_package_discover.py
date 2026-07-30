#!/usr/bin/env python3
"""Discover Main Approve packages from the authoritative GitHub PR store.

Store = open promote/main/* → main PRs whose body contains:
  <!-- linktrend-promote: {schemaVersion:1, stage:main, ...} -->

This is the Lisa-facing read API for docs/contracts/LISA-MAIN-APPROVE-DISPATCH.md.
No OpenClaw sidecar files. Never prints credentials.

Stdout JSON:
{
  "schemaVersion": 1,
  "available": true,
  "store": "github_promote_pr_marker",
  "contract": "docs/contracts/LISA-MAIN-APPROVE-DISPATCH.md",
  "items": [ MainApproveItem-shaped rows ... ],
  "approveMergeTemplate": "gh workflow run ..."
}
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

MARKER_RE = re.compile(r"<!--\s*linktrend-promote:\s*(\{.*?\})\s*-->", re.S)
PROMOTE_HEAD_RE = re.compile(r"^promote/main/[0-9a-f]{7,40}$")
CONTRACT = "docs/contracts/LISA-MAIN-APPROVE-DISPATCH.md"
STORE = "github_promote_pr_marker"


def emit(payload: dict[str, Any]) -> None:
    print(json.dumps(payload, indent=2, sort_keys=False))


def run_gh(args: list[str]) -> str:
    env = os.environ.copy()
    # Prefer existing GH_TOKEN/GITHUB_TOKEN; never log them.
    return subprocess.check_output(["gh", *args], text=True, env=env).strip()


def parse_marker(body: str) -> dict[str, Any] | None:
    m = MARKER_RE.search(body or "")
    if not m:
        return None
    try:
        meta = json.loads(m.group(1))
    except json.JSONDecodeError:
        return None
    if not isinstance(meta, dict):
        return None
    if int(meta.get("schemaVersion") or 0) != 1:
        return None
    if meta.get("stage") != "main":
        return None
    required = ("sourceSha", "targetSha", "candidateHead", "promoteBranch")
    if any(not str(meta.get(k) or "").strip() for k in required):
        return None
    return meta


def plain_description(repository: str, promote_branch: str) -> str:
    # Carlos-facing: no SHAs / no hex tip fragments (Lisa rejects \\b[0-9a-f]{7,40}\\b).
    _ = (repository, promote_branch)
    return "staging to main promote package"


def item_from_parts(
    *,
    repository: str,
    pr_number: int,
    head_sha: str,
    head_branch: str,
    body: str,
    gate_result: str = "Unknown",
    index: int = 1,
) -> dict[str, Any] | None:
    meta = parse_marker(body)
    if not meta:
        return None
    if head_branch and not PROMOTE_HEAD_RE.match(head_branch):
        return None
    candidate = str(meta["candidateHead"])
    if head_sha and head_sha != candidate:
        # Live head drifted from sealed package — omit (stale).
        return None
    if meta.get("promoteBranch") and head_branch and meta["promoteBranch"] != head_branch:
        return None
    return {
        "index": index,
        "plainDescription": plain_description(repository, str(meta["promoteBranch"])),
        "repository": repository,
        "promotionPrNumber": int(pr_number),
        "stagingSha": str(meta["sourceSha"]),
        "priorMainSha": str(meta["targetSha"]),
        "promotionHeadSha": candidate,
        "gateResult": gate_result if gate_result in {"Clear", "Issues", "Unknown"} else "Unknown",
        "promoteBranch": str(meta["promoteBranch"]),
        "marker": meta,
        "workflowInputs": {
            "action": "approve-merge",
            "expected_sha": str(meta["sourceSha"]),
            "expected_main_sha": str(meta["targetSha"]),
            "expected_promote_head": candidate,
            "promote_pr_number": str(pr_number),
        },
    }


def discover_repo(repo: str) -> list[dict[str, Any]]:
    raw = run_gh(
        [
            "pr",
            "list",
            "--repo",
            repo,
            "--base",
            "main",
            "--state",
            "open",
            "--json",
            "number,title,body,headRefName,headRefOid,baseRefName,url",
            "--limit",
            "50",
        ]
    )
    rows = json.loads(raw or "[]")
    items: list[dict[str, Any]] = []
    for row in rows:
        head = str(row.get("headRefName") or "")
        if not head.startswith("promote/main/"):
            continue
        item = item_from_parts(
            repository=repo,
            pr_number=int(row["number"]),
            head_sha=str(row.get("headRefOid") or ""),
            head_branch=head,
            body=str(row.get("body") or ""),
        )
        if item:
            items.append(item)
    for i, item in enumerate(items, start=1):
        item["index"] = i
    return items


def envelope(items: list[dict[str, Any]], repos: list[str]) -> dict[str, Any]:
    template = (
        "gh workflow run linktrend-staging-to-main.yml "
        "--repo <owner/repo> "
        "-f action=approve-merge "
        "-f expected_sha=<stagingSha> "
        "-f expected_main_sha=<priorMainSha> "
        "-f expected_promote_head=<promotionHeadSha>"
    )
    return {
        "schemaVersion": 1,
        "available": True,
        "store": STORE,
        "contract": CONTRACT,
        "repositories": repos,
        "itemCount": len(items),
        "items": items,
        "approveMergeTemplate": template,
        "notes": [
            "Authoritative store is GitHub promote PR metadata (marker), not OpenClaw sidecars.",
            "Carlos-facing text must omit SHAs; use plainDescription only.",
            "approve-merge requires all three SHA inputs (non-empty).",
        ],
    }


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--repo",
        action="append",
        dest="repos",
        default=[],
        help="owner/repo to scan (repeatable). Default: GITHUB_REPOSITORY or gh repo view.",
    )
    ap.add_argument("--from-body-file", help="Offline: parse one PR body file (no network)")
    ap.add_argument("--repository", help="Offline: repository field for --from-body-file")
    ap.add_argument("--pr-number", type=int, default=0, help="Offline: PR number")
    ap.add_argument("--head-sha", default="", help="Offline: live head SHA (must match marker)")
    ap.add_argument("--head-branch", default="", help="Offline: head branch (promote/main/...)")
    ap.add_argument("--gate-result", default="Unknown", choices=["Clear", "Issues", "Unknown"])
    args = ap.parse_args(argv)

    if args.from_body_file:
        body = Path(args.from_body_file).read_text(encoding="utf-8")
        repo = (args.repository or os.environ.get("GITHUB_REPOSITORY") or "owner/repo").strip()
        meta = parse_marker(body)
        if not meta:
            emit(
                {
                    "schemaVersion": 1,
                    "available": True,
                    "store": STORE,
                    "contract": CONTRACT,
                    "error": "marker_missing_or_invalid",
                    "itemCount": 0,
                    "items": [],
                }
            )
            return 2
        head_sha = args.head_sha or str(meta["candidateHead"])
        head_branch = args.head_branch or str(meta["promoteBranch"])
        item = item_from_parts(
            repository=repo,
            pr_number=int(args.pr_number or 0),
            head_sha=head_sha,
            head_branch=head_branch,
            body=body,
            gate_result=args.gate_result,
            index=1,
        )
        items = [item] if item else []
        emit(envelope(items, [repo]))
        return 0 if item else 2

    repos = list(args.repos)
    if not repos:
        env_repo = (os.environ.get("GITHUB_REPOSITORY") or os.environ.get("GH_REPO") or "").strip()
        if env_repo:
            repos = [env_repo]
        else:
            try:
                repos = [run_gh(["repo", "view", "--json", "nameWithOwner", "-q", ".nameWithOwner"])]
            except subprocess.CalledProcessError as exc:
                emit(
                    {
                        "schemaVersion": 1,
                        "available": False,
                        "store": STORE,
                        "contract": CONTRACT,
                        "error": f"repo_unresolved:{exc}",
                        "itemCount": 0,
                        "items": [],
                    }
                )
                return 1

    all_items: list[dict[str, Any]] = []
    for repo in repos:
        try:
            all_items.extend(discover_repo(repo))
        except subprocess.CalledProcessError as exc:
            emit(
                {
                    "schemaVersion": 1,
                    "available": False,
                    "store": STORE,
                    "contract": CONTRACT,
                    "error": f"gh_failed:{repo}:{exc}",
                    "itemCount": 0,
                    "items": [],
                }
            )
            return 1
    for i, item in enumerate(all_items, start=1):
        item["index"] = i
    emit(envelope(all_items, repos))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
