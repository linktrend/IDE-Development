#!/usr/bin/env python3
"""Out-of-diff review-ready signal via GitHub commit statuses (or test file backend).

Context: Linktrend Review Ready
Success on exact SHA ⇒ branch tip is packager-eligible.
Later commits are automatically unready (new SHA has no success status).
Withdrawal posts a non-success status for the same context.

Privileged publish (mark/withdraw) requires a minted GitHub App token in
AUTOMATION_TOKEN or LINKTREND_APP_TOKEN. Ordinary GH_TOKEN / GITHUB_TOKEN must
never authorize status publication. Local implementers without App credentials
use the App-backed workflow dispatch route (see app_backed_review_ready_route).
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

# Exact safe App-backed publication route (trusted workflow on default branch).
REVIEW_READY_PUBLISHER_WORKFLOW = "linktrend-review-ready-publisher.yml"
REVIEW_READY_PUBLISHER_WORKFLOW_NAME = "Linktrend Review Ready Publisher"
APP_PUBLISH_TOKEN_ENVS = ("AUTOMATION_TOKEN", "LINKTREND_APP_TOKEN")


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


def resolve_app_publish_token() -> str:
    """Return App installation token for privileged status publish only.

    Never falls back to GH_TOKEN, GITHUB_TOKEN, or other ambient credentials.
    """
    for key in APP_PUBLISH_TOKEN_ENVS:
        raw = os.environ.get(key)
        if raw is None:
            continue
        token = raw.strip()
        if token:
            return token
    return ""


def app_backed_review_ready_route(
    *,
    branch: str = "",
    sha: str = "",
    dry_run: bool = False,
) -> str:
    """Exact safe App-backed route for publishing Linktrend Review Ready."""
    br = (branch or "").strip() or "<issue/<number>-<slug>>"
    tip = (sha or "").strip() or "<40-char-immutable-sha>"
    dry = "true" if dry_run else "false"
    return (
        f"gh workflow run {REVIEW_READY_PUBLISHER_WORKFLOW} "
        f"-f branch={br} -f sha={tip} -f dry_run={dry}"
    )


def missing_app_publish_token_error(*, branch: str = "", sha: str = "") -> str:
    """Fail-closed diagnostic when local privileged publish lacks App credentials."""
    route = app_backed_review_ready_route(branch=branch, sha=sha)
    return (
        "privileged_publish_requires_github_app: "
        "AUTOMATION_TOKEN or LINKTREND_APP_TOKEN required; "
        "no GH_TOKEN/GITHUB_TOKEN fallback for Linktrend Review Ready publish. "
        f"Use App-backed route: {route}"
    )


def _read_status_token() -> str:
    """Token for status reads only. Prefer App; ambient tokens allowed for get."""
    return (
        resolve_app_publish_token()
        or (os.environ.get("GH_TOKEN") or "").strip()
        or (os.environ.get("GITHUB_TOKEN") or "").strip()
    )


def _gh_token() -> str:
    """Backward-compatible alias: prefer App token, then ambient read tokens.

    Privileged publish must call resolve_app_publish_token() — never this helper
    alone — so GH_TOKEN/GITHUB_TOKEN cannot authorize mark/withdraw.
    """
    return _read_status_token()


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
        # Explicit/ambient token is for reads only. Publish ignores it.
        self._read_token = (token or _read_status_token()).strip()
        # Compat attribute: never use for privileged publish.
        self.token = self._read_token

    def get_latest(self, sha: str) -> ReadyStatus | None:
        if not self._read_token:
            raise RuntimeError(
                "status read token missing "
                "(AUTOMATION_TOKEN/LINKTREND_APP_TOKEN preferred; "
                "GH_TOKEN/GITHUB_TOKEN allowed for reads only)"
            )
        url = f"https://api.github.com/repos/{self.repo}/commits/{sha}/statuses"
        rows = _api("GET", url, self._read_token)
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

    def post(
        self,
        sha: str,
        state: str,
        description: str,
        target_url: str = "",
        *,
        branch: str = "",
    ) -> ReadyStatus:
        # Privileged publish: App env vars only — never constructor/ambient human tokens.
        pub = resolve_app_publish_token()
        if not pub:
            raise RuntimeError(missing_app_publish_token_error(branch=branch, sha=sha))
        existing = self.get_latest(sha) if self._read_token else None
        if (
            existing
            and existing.state == state
            and existing.description == description
            and state == "success"
        ):
            return existing
        # Idempotent success without a read token: still POST (GitHub accepts duplicates).
        body = {
            "state": state,
            "description": description[:140],
            "context": CONTEXT,
        }
        if target_url:
            body["target_url"] = target_url
        _api("POST", f"https://api.github.com/repos/{self.repo}/statuses/{sha}", pub, body)
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


def publish_review_ready(
    sha: str,
    issue_id: str,
    notes: str = "",
    target_url: str = "",
    *,
    branch: str = "",
) -> ReadyStatus:
    """Reusable privileged publication helper (App token or file backend only)."""
    desc = f"issue={issue_id}"
    if notes:
        desc = f"{desc}; {notes}"[:140]
    backend = get_backend()
    if isinstance(backend, GitHubStatusBackend):
        return backend.post(sha, "success", desc, target_url=target_url, branch=branch)
    return backend.post(sha, "success", desc, target_url=target_url)


def mark_sha(
    sha: str,
    issue_id: str,
    notes: str = "",
    target_url: str = "",
    *,
    branch: str = "",
) -> ReadyStatus:
    return publish_review_ready(
        sha, issue_id, notes, target_url=target_url, branch=branch
    )


def withdraw_sha(sha: str, reason: str = "withdrawn", *, branch: str = "") -> ReadyStatus:
    backend = get_backend()
    if isinstance(backend, GitHubStatusBackend):
        return backend.post(sha, "failure", reason[:140], branch=branch)
    return backend.post(sha, "failure", reason[:140])


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
