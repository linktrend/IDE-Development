#!/usr/bin/env python3
"""Durable conflict_blocked repair tasks as GitHub Issues (idempotent).

Fallback file backend for offline tests via LINKTREND_CONFLICT_BACKEND=file
and LINKTREND_CONFLICT_DIR.

Does NOT claim GitHub can spawn Cursor agents.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

MAX_ATTEMPTS = 3
LABEL = "linktrend-conflict-blocked"
MARKER_PREFIX = "<!-- linktrend-conflict-task:"


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def task_key(repo: str, stage: str, source_sha: str, target_sha: str) -> str:
    raw = f"{repo}|{stage}|{source_sha}|{target_sha}".encode()
    return hashlib.sha256(raw).hexdigest()[:16]


def marker(task: dict[str, Any]) -> str:
    return f"{MARKER_PREFIX} {json.dumps(task, separators=(',', ':'))} -->"


def parse_marker(body: str) -> dict[str, Any] | None:
    for line in (body or "").splitlines():
        if MARKER_PREFIX in line:
            try:
                raw = line.split(MARKER_PREFIX, 1)[1]
                raw = raw.strip()
                if raw.endswith("-->"):
                    raw = raw[:-3].strip()
                return json.loads(raw)
            except json.JSONDecodeError:
                return None
    return None


def _token() -> str:
    return os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN") or ""


def _api(method: str, url: str, token: str, body: dict | None = None) -> Any:
    data = None if body is None else json.dumps(body).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        method=method,
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "linktrend-conflict-task",
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


class FileBackend:
    def __init__(self, root: Path):
        self.root = root
        self.root.mkdir(parents=True, exist_ok=True)

    def upsert(self, task: dict[str, Any], *, increment: bool) -> dict[str, Any]:
        path = self.root / f"{task['id']}.json"
        if path.is_file():
            existing = json.loads(path.read_text(encoding="utf-8"))
            attempts = int(existing.get("attemptCount") or 0)
            if increment:
                attempts += 1
            existing.update(task)
            existing["attemptCount"] = attempts
            existing["updatedAt"] = utc_now()
            task = existing
        else:
            task = dict(task)
            task["attemptCount"] = 1 if increment else 0
            task["createdAt"] = utc_now()
            task["updatedAt"] = utc_now()
        if int(task["attemptCount"]) >= MAX_ATTEMPTS and task.get("status") == "conflict_blocked":
            task["status"] = "Issues"
            task["nextAction"] = "Max repair attempts reached. Report Issues to Principal."
        path.write_text(json.dumps(task, indent=2) + "\n", encoding="utf-8")
        return task

    def resolve(self, tid: str) -> dict[str, Any] | None:
        path = self.root / f"{tid}.json"
        if not path.is_file():
            return None
        task = json.loads(path.read_text(encoding="utf-8"))
        task["status"] = "resolved"
        task["updatedAt"] = utc_now()
        path.write_text(json.dumps(task, indent=2) + "\n", encoding="utf-8")
        return task

    def get(self, tid: str) -> dict[str, Any] | None:
        path = self.root / f"{tid}.json"
        if not path.is_file():
            return None
        return json.loads(path.read_text(encoding="utf-8"))


class GitHubIssueBackend:
    def __init__(self, repo: str):
        self.repo = repo
        self.token = _token()
        if not self.token:
            raise RuntimeError("GH_TOKEN required")

    def _ensure_label(self) -> None:
        try:
            _api("GET", f"https://api.github.com/repos/{self.repo}/labels/{LABEL}", self.token)
        except RuntimeError:
            try:
                _api(
                    "POST",
                    f"https://api.github.com/repos/{self.repo}/labels",
                    self.token,
                    {"name": LABEL, "color": "B60205", "description": "LiNKtrend promotion conflict"},
                )
            except RuntimeError:
                pass

    def _find(self, tid: str) -> dict | None:
        q = f'repo:{self.repo} is:issue label:{LABEL} "{tid}" in:body'
        # Prefer gh for search reliability
        try:
            out = subprocess.check_output(
                ["gh", "issue", "list", "--repo", self.repo, "--label", LABEL, "--state", "open", "--json", "number,body,title", "--limit", "50"],
                text=True,
            )
            for row in json.loads(out or "[]"):
                parsed = parse_marker(row.get("body") or "")
                if parsed and parsed.get("id") == tid:
                    return row
        except subprocess.CalledProcessError:
            pass
        return None

    def upsert(self, task: dict[str, Any], *, increment: bool) -> dict[str, Any]:
        self._ensure_label()
        tid = task["id"]
        existing_issue = self._find(tid)
        if existing_issue:
            parsed = parse_marker(existing_issue.get("body") or "") or {}
            attempts = int(parsed.get("attemptCount") or 0)
            if increment:
                attempts += 1
            parsed.update(task)
            parsed["attemptCount"] = attempts
            parsed["updatedAt"] = utc_now()
            parsed.setdefault("createdAt", task.get("createdAt") or utc_now())
            if attempts >= MAX_ATTEMPTS and parsed.get("status") == "conflict_blocked":
                parsed["status"] = "Issues"
                parsed["nextAction"] = "Max repair attempts reached. Report Issues to Principal."
            body = self._body(parsed)
            _api(
                "PATCH",
                f"https://api.github.com/repos/{self.repo}/issues/{existing_issue['number']}",
                self.token,
                {"title": self._title(parsed), "body": body, "labels": [LABEL]},
            )
            parsed["issueNumber"] = existing_issue["number"]
            return parsed

        task = dict(task)
        task["attemptCount"] = 1 if increment else 0
        task["createdAt"] = utc_now()
        task["updatedAt"] = utc_now()
        if task["attemptCount"] >= MAX_ATTEMPTS:
            task["status"] = "Issues"
        body = self._body(task)
        created = _api(
            "POST",
            f"https://api.github.com/repos/{self.repo}/issues",
            self.token,
            {"title": self._title(task), "body": body, "labels": [LABEL]},
        )
        task["issueNumber"] = created.get("number")
        return task

    def resolve(self, tid: str) -> dict[str, Any] | None:
        issue = self._find(tid)
        if not issue:
            return None
        parsed = parse_marker(issue.get("body") or "") or {"id": tid}
        parsed["status"] = "resolved"
        parsed["updatedAt"] = utc_now()
        _api(
            "PATCH",
            f"https://api.github.com/repos/{self.repo}/issues/{issue['number']}",
            self.token,
            {"state": "closed", "body": self._body(parsed), "title": self._title(parsed)},
        )
        parsed["issueNumber"] = issue["number"]
        return parsed

    def get(self, tid: str) -> dict[str, Any] | None:
        issue = self._find(tid)
        if not issue:
            return None
        parsed = parse_marker(issue.get("body") or "")
        if parsed:
            parsed["issueNumber"] = issue["number"]
        return parsed

    def _title(self, task: dict[str, Any]) -> str:
        return (
            f"[conflict_blocked] {task.get('stage')}: "
            f"{task.get('sourceBranch')}→{task.get('targetBranch')} ({task.get('id')})"
        )

    def _body(self, task: dict[str, Any]) -> str:
        return (
            f"## LiNKtrend conflict repair task\n\n"
            f"- repository: `{task.get('repository')}`\n"
            f"- stage: `{task.get('stage')}`\n"
            f"- source: `{task.get('sourceBranch')}` @ `{task.get('sourceSha')}`\n"
            f"- target: `{task.get('targetBranch')}` @ `{task.get('targetSha')}`\n"
            f"- promote PR: `{task.get('promotePr') or 'n/a'}`\n"
            f"- attemptCount: **{task.get('attemptCount')}** / {MAX_ATTEMPTS}\n"
            f"- status: **{task.get('status')}**\n"
            f"- nextAction: {task.get('nextAction')}\n\n"
            f"GitHub does **not** spawn Cursor agents. A human/agent must repair externally; "
            f"PR/check events reevaluate the existing promotion candidate.\n\n"
            f"{marker(task)}\n"
        )


def get_backend(repo: str):
    backend = (os.environ.get("LINKTREND_CONFLICT_BACKEND") or "github").lower()
    if backend == "file":
        return FileBackend(Path(os.environ.get("LINKTREND_CONFLICT_DIR") or ".git/linktrend-conflict-tasks"))
    return GitHubIssueBackend(repo)


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    up = sub.add_parser("upsert")
    up.add_argument("--repo", required=True)
    up.add_argument("--stage", required=True)
    up.add_argument("--source-branch", required=True)
    up.add_argument("--target-branch", required=True)
    up.add_argument("--source-sha", required=True)
    up.add_argument("--target-sha", required=True)
    up.add_argument("--status", default="conflict_blocked")
    up.add_argument("--next-action", required=True)
    up.add_argument("--promote-pr", default="")
    up.add_argument("--increment-attempt", action="store_true")
    rs = sub.add_parser("resolve")
    rs.add_argument("--repo", required=True)
    rs.add_argument("--id", required=True)
    sh = sub.add_parser("show")
    sh.add_argument("--repo", required=True)
    sh.add_argument("--id", required=True)
    args = ap.parse_args(argv)
    backend = get_backend(args.repo)
    if args.cmd == "upsert":
        tid = task_key(args.repo, args.stage, args.source_sha, args.target_sha)
        task = {
            "schemaVersion": 1,
            "id": tid,
            "repository": args.repo,
            "stage": args.stage,
            "sourceBranch": args.source_branch,
            "targetBranch": args.target_branch,
            "sourceSha": args.source_sha,
            "targetSha": args.target_sha,
            "promotePr": args.promote_pr,
            "status": args.status,
            "nextAction": args.next_action,
            "maxAttempts": MAX_ATTEMPTS,
        }
        out = backend.upsert(task, increment=args.increment_attempt)
        print(json.dumps(out, indent=2))
        return 0
    if args.cmd == "resolve":
        out = backend.resolve(args.id)
        print(json.dumps(out or {}, indent=2))
        return 0 if out else 1
    if args.cmd == "show":
        out = backend.get(args.id)
        print(json.dumps(out or {}, indent=2))
        return 0 if out else 1
    return 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
