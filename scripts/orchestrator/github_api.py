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
from typing import Any, Iterable, Mapping, Sequence

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

# Required checks count only when a check run's app.slug is in this allowlist.
# ``--check-app`` on merge_check.py replaces it. Commit statuses never join it.
DEFAULT_ALLOWED_APPS = ("github-actions",)

# Expected workflow file when the check-run payload exposes one. The list
# check-runs API often omits it; then the app slug is the producer check.
EXPECTED_WORKFLOWS = {
    "Verify IDE Development": ".github/workflows/ci.yml",
    "Linktrend Fast Checks": ".github/workflows/ci.yml",
    "Linktrend Branch Source Policy": ".github/workflows/branch-source-policy.yml",
}


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
        # ``filter=all`` so a later same-name run from another app cannot hide
        # the github-actions run. Latest-per-(name, app) is applied locally.
        return self.paginate(
            f"/repos/{validate_repo(repo)}/commits/{validate_sha(sha)}/check-runs",
            {"filter": "all"},
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


def app_slug(run: Mapping[str, Any]) -> str:
    app = run.get("app") or {}
    return str(app.get("slug") or "") if isinstance(app, dict) else ""


def _workflow_file_matches(value: str, expected: str) -> bool:
    norm = value.replace("\\", "/").lstrip("./")
    exp = expected.lstrip("./")
    return norm == exp or norm.endswith("/" + exp)


def exposed_workflow(run: Mapping[str, Any]) -> tuple[str | None, str | None]:
    """Return ``(path, name)`` when the payload exposes a workflow file.

    Looks at ``check_suite`` and a nested Actions run (``path`` or ``name``).
    The check run's own ``name`` is the job, not the workflow, and is ignored.
    ``(None, None)`` means the API did not expose a workflow.
    """
    containers: list[Mapping[str, Any]] = []
    suite = run.get("check_suite") if isinstance(run.get("check_suite"), dict) else {}
    if suite:
        containers.append(suite)
        for key in ("workflow", "workflow_run"):
            nested = suite.get(key)
            if isinstance(nested, dict):
                containers.append(nested)
    for key in ("workflow", "workflow_run"):
        nested = run.get(key)
        if isinstance(nested, dict):
            containers.append(nested)
    path: str | None = None
    name: str | None = None
    for container in containers:
        if path is None and isinstance(container.get("path"), str) and container.get("path"):
            path = str(container["path"])
        if path is None and isinstance(container.get("workflow_path"), str) and container.get("workflow_path"):
            path = str(container["workflow_path"])
        if name is None and isinstance(container.get("name"), str) and container.get("name"):
            name = str(container["name"])
    return path, name


def workflow_gate(run: Mapping[str, Any], expected: str | None) -> tuple[bool, bool, str | None]:
    """Return ``(ok, exposed, identity)``.

    When ``expected`` is set and the payload exposes a path, that path must be
    the workflow file. A name is used only when no path is present. When the
    API exposes nothing, ``ok`` is True and ``exposed`` is False: the caller
    still requires the app slug.
    """
    path, name = exposed_workflow(run)
    if not expected:
        return True, bool(path or name), path or name
    if path:
        return _workflow_file_matches(path, expected), True, path
    if name:
        return _workflow_file_matches(name, expected), True, name
    return True, False, None


def latest_checks(
    check_runs: Iterable[Mapping[str, Any]],
    statuses: Iterable[Mapping[str, Any]] = (),
    *,
    allowed_apps: Sequence[str] = DEFAULT_ALLOWED_APPS,
) -> dict[str, dict[str, Any]]:
    """Latest check run per ``(name, app)``, plus reported commit statuses.

    A required check is satisfied only by a completed check run whose
    ``app.slug`` is in ``allowed_apps`` (never by a commit status). When that
    run exposes a workflow, it must match ``EXPECTED_WORKFLOWS``. A later run
    for the same ``(name, app)`` overrides an earlier one, including a later
    failure. Statuses are returned on ``statusReport`` and never count as
    success; a failing status is still a gate failure for the caller.
    """
    allowed = tuple(allowed_apps)
    by_key: dict[tuple[str, str], Mapping[str, Any]] = {}
    for run in check_runs:
        name = str(run.get("name") or "")
        if not name:
            continue
        key = (name, app_slug(run))
        prev = by_key.get(key)
        if prev is None or _run_order(run) >= _run_order(prev):
            by_key[key] = run

    # The statuses endpoint lists newest first; the first entry per context wins.
    status_first: dict[str, Mapping[str, Any]] = {}
    for status in statuses:
        name = str(status.get("context") or "")
        if name and name not in status_first:
            status_first[name] = status

    names = {name for name, _app in by_key} | set(status_first)
    out: dict[str, dict[str, Any]] = {}
    for name in names:
        chosen: Mapping[str, Any] | None = None
        for app in allowed:
            run = by_key.get((name, app))
            if run is not None and (chosen is None or _run_order(run) >= _run_order(chosen)):
                chosen = run
        foreign = sorted({app for (run_name, app) in by_key if run_name == name and app not in allowed})
        status = status_first.get(name)
        status_report = None
        if status is not None:
            state = str(status.get("state") or "")
            status_report = {
                "state": state,
                "conclusion": STATUS_STATE_TO_CONCLUSION.get(state),
                "countsAsSuccess": False,
                "url": status.get("target_url"),
            }
        expected = EXPECTED_WORKFLOWS.get(name)
        if chosen is not None:
            wf_ok, wf_exposed, wf_id = workflow_gate(chosen, expected)
            completed = chosen.get("status") == "completed"
            out[name] = {
                "status": chosen.get("status"),
                "conclusion": chosen.get("conclusion") if completed and wf_ok else None,
                "source": "check_run",
                "app": app_slug(chosen),
                "workflow": wf_id,
                "workflowExposed": wf_exposed,
                "workflowOk": wf_ok,
                "url": chosen.get("html_url"),
                "countsAsCheck": bool(wf_ok and app_slug(chosen) in allowed),
                "foreignApps": foreign,
                "statusReport": status_report,
            }
        else:
            out[name] = {
                "status": None,
                "conclusion": None,
                "source": "status" if status is not None else ("check_run" if foreign else None),
                "app": None,
                "workflow": None,
                "workflowExposed": False,
                "workflowOk": True,
                "url": status.get("target_url") if status else None,
                "countsAsCheck": False,
                "foreignApps": foreign,
                "statusReport": status_report,
            }
    return out


def head_checks(
    api: Any, repo: str, sha: str, *, allowed_apps: Sequence[str] = DEFAULT_ALLOWED_APPS
) -> dict[str, dict[str, Any]]:
    return latest_checks(api.check_runs(repo, sha), api.commit_statuses(repo, sha), allowed_apps=allowed_apps)


def check_succeeded(
    api: Any, repo: str, sha: str, name: str, *, allowed_apps: Sequence[str] = DEFAULT_ALLOWED_APPS
) -> dict[str, Any]:
    check = head_checks(api, repo, sha, allowed_apps=allowed_apps).get(name)
    counts = bool(check and check.get("countsAsCheck"))
    conclusion = check.get("conclusion") if counts else None
    report = (check or {}).get("statusReport") or {}
    status_failed = report.get("conclusion") in FAILING_CONCLUSIONS
    if status_failed:
        conclusion = report.get("conclusion")
    return {
        "name": name,
        "sha": sha,
        "status": check.get("status") if check else None,
        "conclusion": conclusion,
        "url": (check or {}).get("url"),
        "app": (check or {}).get("app"),
        "ok": conclusion == "success" and counts and not status_failed,
    }


def repo_from_remote_url(url: str) -> str | None:
    match = re.search(r"github\.com[:/]+([A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+?)(?:\.git)?/?$", url.strip())
    return match.group(1) if match else None
