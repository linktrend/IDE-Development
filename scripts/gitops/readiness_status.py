#!/usr/bin/env python3
"""Out-of-diff review-ready signal via GitHub commit statuses (or test file backend).

Context: Linktrend Review Ready
Success on exact SHA ⇒ branch tip is packager-eligible.
Later commits are automatically unready (new SHA has no success status).
Withdrawal posts a non-success status for the same context.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any

CONTEXT = "Linktrend Review Ready"
DEFAULT_BACKEND = "github"  # or "file" for tests (LINKTREND_STATUS_DIR)


@dataclass
class ReadyStatus:
    state: str  # success | pending | failure | error
    description: str
    target_url: str
    context: str = CONTEXT
    created_at: float = 0.0

    @property
    def is_ready(self) -> bool:
        return self.state == "success"


def _gh_token() -> str:
    # Prefer App automation token for autonomous GitOps (discover/evaluate/promote).
    # Do not let the workflow GITHUB_TOKEN shadow a minted App token.
    return (
        os.environ.get("AUTOMATION_TOKEN")
        or os.environ.get("LINKTREND_APP_TOKEN")
        or os.environ.get("GH_TOKEN")
        or os.environ.get("GITHUB_TOKEN")
        or ""
    )


def _repo_slug() -> str:
    if os.environ.get("GITHUB_REPOSITORY"):
        return os.environ["GITHUB_REPOSITORY"]
    try:
        url = subprocess.check_output(
            ["gh", "repo", "view", "--json", "nameWithOwner", "--jq", ".nameWithOwner"],
            text=True,
        ).strip()
        return url
    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        raise RuntimeError("cannot resolve repository slug") from e


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
            "User-Agent": "linktrend-review-ready",
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


class FileStatusBackend:
    """Test/offline backend storing statuses under LINKTREND_STATUS_DIR/<sha>.json."""

    def __init__(self, root: Path):
        self.root = root
        self.root.mkdir(parents=True, exist_ok=True)

    def _path(self, sha: str) -> Path:
        return self.root / f"{sha.lower()}.json"

    def get_latest(self, sha: str) -> ReadyStatus | None:
        p = self._path(sha)
        if not p.is_file():
            return None
        rows = json.loads(p.read_text(encoding="utf-8"))
        if not rows:
            return None
        last = rows[-1]
        return ReadyStatus(
            state=last["state"],
            description=last.get("description") or "",
            target_url=last.get("target_url") or "",
            created_at=float(last.get("created_at") or 0),
        )

    def post(self, sha: str, state: str, description: str, target_url: str = "") -> ReadyStatus:
        p = self._path(sha)
        rows = json.loads(p.read_text(encoding="utf-8")) if p.is_file() else []
        entry = {
            "state": state,
            "description": description,
            "target_url": target_url,
            "context": CONTEXT,
            "created_at": time.time(),
        }
        # Idempotent success: do not duplicate identical success
        if rows:
            last = rows[-1]
            if (
                last.get("state") == state
                and last.get("description") == description
                and state == "success"
            ):
                return ReadyStatus(
                    state=state,
                    description=description,
                    target_url=target_url,
                    created_at=float(last.get("created_at") or 0),
                )
        rows.append(entry)
        p.write_text(json.dumps(rows, indent=2) + "\n", encoding="utf-8")
        return ReadyStatus(state=state, description=description, target_url=target_url, created_at=entry["created_at"])


class GitHubStatusBackend:
    def __init__(self, repo: str | None = None, token: str | None = None):
        self.repo = repo or _repo_slug()
        self.token = token or _gh_token()
        if not self.token:
            raise RuntimeError(
                "AUTOMATION_TOKEN (preferred) or GH_TOKEN/GITHUB_TOKEN required "
                "for GitHub status backend"
            )

    def get_latest(self, sha: str) -> ReadyStatus | None:
        url = f"https://api.github.com/repos/{self.repo}/commits/{sha}/statuses"
        rows = _api("GET", url, self.token)
        mine = [r for r in rows if (r.get("context") or "") == CONTEXT]
        if not mine:
            return None
        # API returns newest first
        last = mine[0]
        return ReadyStatus(
            state=last.get("state") or "error",
            description=last.get("description") or "",
            target_url=last.get("target_url") or "",
            created_at=0.0,
        )

    def post(self, sha: str, state: str, description: str, target_url: str = "") -> ReadyStatus:
        existing = self.get_latest(sha)
        if (
            existing
            and existing.state == state
            and existing.description == description
            and state == "success"
        ):
            return existing
        body = {
            "state": state,
            "description": description[:140],
            "context": CONTEXT,
        }
        if target_url:
            body["target_url"] = target_url
        _api("POST", f"https://api.github.com/repos/{self.repo}/statuses/{sha}", self.token, body)
        return ReadyStatus(state=state, description=description, target_url=target_url)


def get_backend():
    backend = (os.environ.get("LINKTREND_STATUS_BACKEND") or DEFAULT_BACKEND).lower()
    if backend == "file":
        root = Path(os.environ.get("LINKTREND_STATUS_DIR") or ".git/linktrend-ready-status")
        return FileStatusBackend(root)
    return GitHubStatusBackend()


def is_sha_review_ready(sha: str) -> tuple[bool, str]:
    st = get_backend().get_latest(sha)
    if not st:
        return False, "no_ready_status"
    if st.is_ready:
        return True, st.description or "ready"
    return False, f"status_{st.state}"


def mark_sha(sha: str, issue_id: str, notes: str = "", target_url: str = "") -> ReadyStatus:
    desc = f"issue={issue_id}"
    if notes:
        desc = f"{desc}; {notes}"[:140]
    return get_backend().post(sha, "success", desc, target_url=target_url)


def withdraw_sha(sha: str, reason: str = "withdrawn") -> ReadyStatus:
    return get_backend().post(sha, "failure", reason[:140])


def main(argv: list[str]) -> int:
    if len(argv) < 2:
        print(
            "Usage: readiness_status.py <get|mark|withdraw> <sha> [issue_id] [notes]",
            file=sys.stderr,
        )
        return 2
    cmd = argv[1]
    if cmd == "get":
        sha = argv[2]
        ok, detail = is_sha_review_ready(sha)
        print(json.dumps({"sha": sha, "ready": ok, "detail": detail}))
        return 0 if ok else 1
    if cmd == "mark":
        sha, issue_id = argv[2], argv[3]
        notes = argv[4] if len(argv) > 4 else ""
        st = mark_sha(sha, issue_id, notes)
        print(json.dumps({"sha": sha, "state": st.state, "description": st.description}))
        return 0
    if cmd == "withdraw":
        sha = argv[2]
        reason = argv[3] if len(argv) > 3 else "withdrawn"
        st = withdraw_sha(sha, reason)
        print(json.dumps({"sha": sha, "state": st.state, "description": st.description}))
        return 0
    print(f"unknown command {cmd}", file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
