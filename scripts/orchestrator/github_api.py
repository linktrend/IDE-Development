#!/usr/bin/env python3
"""Read-only GitHub REST helper for the v3 orchestrator delivery scripts.

Standard library only. Token: ``GH_TOKEN``, else ``GITHUB_TOKEN``; unauthenticated
requests work for public repositories (60 requests/hour). The token is sent only
in the ``Authorization`` header and never appears in errors or output.
"""

from __future__ import annotations

import json
import os
import re
import urllib.error
import urllib.parse
import urllib.request
from typing import Any, Iterable, Mapping

API_BASE = os.environ.get("GITHUB_API_URL", "https://api.github.com")
TOKEN_ENVS = ("GH_TOKEN", "GITHUB_TOKEN")
DEFAULT_TIMEOUT_S = 30
MAX_PAGES = 20
REPO_RE = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")
SHA40_RE = re.compile(r"^[0-9a-f]{40}$")
NEXT_LINK_RE = re.compile(r'<([^>]+)>;\s*rel="next"')

# Conclusions that fail a head regardless of whether the check is required.
FAILING_CONCLUSIONS = frozenset({"failure", "cancelled", "timed_out"})
STATUS_STATE_TO_CONCLUSION = {"success": "success", "failure": "failure", "error": "failure", "pending": None}


class GitHubApiError(RuntimeError):
    def __init__(self, code: str, message: str, **detail: Any) -> None:
        super().__init__(message)
        self.code = code
        self.detail = detail

    def as_dict(self) -> dict[str, Any]:
        return {"ok": False, "error": self.code, "message": str(self), **self.detail}


def validate_repo(repo: str) -> str:
    if not REPO_RE.match(repo or ""):
        raise GitHubApiError("bad_repo", "repo must look like owner/name", repo=repo)
    return repo


def validate_sha(sha: str) -> str:
    if not SHA40_RE.match(sha or ""):
        raise GitHubApiError("bad_sha", "sha must be a full lowercase 40-hex commit SHA", sha=sha)
    return sha


class GitHubApi:
    def __init__(self, token: str | None = None, base: str = API_BASE, timeout: float = DEFAULT_TIMEOUT_S) -> None:
        self._token = token or None
        self.base = base.rstrip("/")
        self.timeout = timeout

    @property
    def authenticated(self) -> bool:
        return self._token is not None

    def _request(self, url: str) -> tuple[Any, str | None]:
        headers = {
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "linktrend-ide-orchestrator",
        }
        if self._token:
            headers["Authorization"] = f"Bearer {self._token}"
        req = urllib.request.Request(url, headers=headers, method="GET")
        path = urllib.parse.urlsplit(url).path
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                raw = resp.read()
                link = resp.headers.get("Link")
        except urllib.error.HTTPError as exc:
            body = exc.read()[:500].decode(errors="replace")
            message = _error_message(body)
            if exc.code in (403, 429) and exc.headers.get("X-RateLimit-Remaining") == "0":
                raise GitHubApiError(
                    "rate_limited",
                    f"GET {path} hit the GitHub rate limit; set GH_TOKEN or wait",
                    status=exc.code,
                ) from None
            code = {401: "unauthorized", 403: "forbidden", 404: "not_found"}.get(exc.code, "http_error")
            hint = " (private repo or wrong name? set GH_TOKEN)" if exc.code == 404 and not self._token else ""
            raise GitHubApiError(code, f"GET {path} returned {exc.code}{hint}", status=exc.code, body=message) from None
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            reason = getattr(exc, "reason", exc)
            raise GitHubApiError("network_error", f"GET {path} failed: {reason}") from None
        try:
            return (json.loads(raw) if raw else None), link
        except json.JSONDecodeError:
            raise GitHubApiError("bad_json", f"GET {path} did not return JSON") from None

    def _url(self, path: str, params: Mapping[str, Any] | None = None) -> str:
        url = self.base + path
        if params:
            url += "?" + urllib.parse.urlencode(params)
        return url

    def get(self, path: str, params: Mapping[str, Any] | None = None) -> Any:
        payload, _ = self._request(self._url(path, params))
        return payload

    def paginate(self, path: str, params: Mapping[str, Any] | None = None, *, key: str | None = None) -> list[Any]:
        """Follow ``Link: rel="next"``. ``key`` selects the list inside object responses."""
        items: list[Any] = []
        url: str | None = self._url(path, {"per_page": 100, **(params or {})})
        for _ in range(MAX_PAGES):
            if url is None:
                return items
            payload, link = self._request(url)
            page = payload.get(key) if key and isinstance(payload, dict) else payload
            if not isinstance(page, list):
                raise GitHubApiError("bad_payload", f"expected a list at {path}" + (f" key {key!r}" if key else ""))
            items.extend(page)
            match = NEXT_LINK_RE.search(link or "")
            url = match.group(1) if match else None
        raise GitHubApiError("too_many_pages", f"{path} exceeded {MAX_PAGES} pages")

    # ------------------------------------------------------------- endpoints

    def pull(self, repo: str, number: int) -> dict[str, Any]:
        return self.get(f"/repos/{validate_repo(repo)}/pulls/{int(number)}")

    def check_runs(self, repo: str, sha: str) -> list[dict[str, Any]]:
        return self.paginate(
            f"/repos/{validate_repo(repo)}/commits/{validate_sha(sha)}/check-runs",
            {"filter": "latest"},
            key="check_runs",
        )

    def commit_statuses(self, repo: str, sha: str) -> list[dict[str, Any]]:
        return self.paginate(f"/repos/{validate_repo(repo)}/commits/{validate_sha(sha)}/statuses")


def _error_message(body: str) -> str:
    try:
        parsed = json.loads(body)
    except json.JSONDecodeError:
        return body[:200]
    return str(parsed.get("message", ""))[:200] if isinstance(parsed, dict) else body[:200]


def token_from_env(env: Mapping[str, str] | None = None) -> str | None:
    env = os.environ if env is None else env
    for name in TOKEN_ENVS:
        if env.get(name):
            return env[name]
    return None


def from_env() -> GitHubApi:
    return GitHubApi(token_from_env())


# ------------------------------------------------------------ check summaries


def _run_order(run: Mapping[str, Any]) -> tuple[str, int]:
    return (str(run.get("started_at") or run.get("completed_at") or ""), int(run.get("id") or 0))


def latest_checks(
    check_runs: Iterable[Mapping[str, Any]], statuses: Iterable[Mapping[str, Any]] = ()
) -> dict[str, dict[str, Any]]:
    """Latest result per check name, merging check runs and legacy commit statuses.

    Returns ``{name: {status, conclusion, source, url}}``; ``conclusion`` is None
    while a check is queued or in progress.
    """
    latest: dict[str, Mapping[str, Any]] = {}
    for run in check_runs:
        name = str(run.get("name") or "")
        if name and (name not in latest or _run_order(run) >= _run_order(latest[name])):
            latest[name] = run
    out: dict[str, dict[str, Any]] = {
        name: {
            "status": run.get("status"),
            "conclusion": run.get("conclusion") if run.get("status") == "completed" else None,
            "source": "check_run",
            "url": run.get("html_url"),
        }
        for name, run in latest.items()
    }
    # The statuses endpoint lists newest first; the first entry per context wins.
    for status in statuses:
        name = str(status.get("context") or "")
        if not name or name in out:
            continue
        state = str(status.get("state") or "")
        conclusion = STATUS_STATE_TO_CONCLUSION.get(state)
        out[name] = {
            "status": "completed" if conclusion else "pending",
            "conclusion": conclusion,
            "source": "status",
            "url": status.get("target_url"),
        }
    return out


def head_checks(api: Any, repo: str, sha: str) -> dict[str, dict[str, Any]]:
    return latest_checks(api.check_runs(repo, sha), api.commit_statuses(repo, sha))


def check_succeeded(api: Any, repo: str, sha: str, name: str) -> dict[str, Any]:
    check = head_checks(api, repo, sha).get(name)
    conclusion = check.get("conclusion") if check else None
    return {
        "name": name,
        "sha": sha,
        "status": check.get("status") if check else None,
        "conclusion": conclusion,
        "url": check.get("url") if check else None,
        "ok": conclusion == "success",
    }


def repo_from_remote_url(url: str) -> str | None:
    match = re.search(r"github\.com[:/]+([A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+?)(?:\.git)?/?$", url.strip())
    return match.group(1) if match else None
