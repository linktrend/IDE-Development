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

# Workflow file that must produce each named check. Identity is never taken
# from the check-run list payload; it is resolved from the Actions run API.
EXPECTED_WORKFLOWS = {
    "Verify IDE Development": ".github/workflows/ci.yml",
    "Linktrend Fast Checks": ".github/workflows/ci.yml",
    "Linktrend Branch Source Policy": ".github/workflows/branch-source-policy.yml",
    "Linktrend Main Receipt Gate": ".github/workflows/linktrend-promote-main.yml",
    "Installer matrix (ubuntu-latest)": ".github/workflows/ide-development-cross-platform.yml",
    "Installer matrix (macos-latest)": ".github/workflows/ide-development-cross-platform.yml",
    "Installer matrix (windows-latest)": ".github/workflows/ide-development-cross-platform.yml",
}
_ACTIONS_RUN_ID_RE = re.compile(r"/actions/runs/([1-9]\d*)(?:/job/[1-9]\d*)?(?:[/?#]|$)")


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

    def pulls_for_commit(self, repo: str, sha: str) -> list[dict[str, Any]]:
        return self.paginate(
            f"/repos/{validate_repo(repo)}/commits/{validate_sha(sha)}/pulls"
        )

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

    def actions_run(self, repo: str, run_id: str) -> dict[str, Any]:
        if not re.fullmatch(r"[1-9]\d*", str(run_id)):
            raise GitHubApiError("bad_run_id", "workflow run id must be a positive integer")
        payload = self.get(f"/repos/{validate_repo(repo)}/actions/runs/{run_id}")
        if not isinstance(payload, dict):
            raise GitHubApiError("bad_payload", "workflow run response was not an object")
        return payload

    def actions_runs_by_suite(self, repo: str, suite_id: int) -> list[Any]:
        if isinstance(suite_id, bool) or not isinstance(suite_id, int) or suite_id < 1:
            raise GitHubApiError("bad_suite_id", "check suite id must be a positive integer")
        return self.paginate(
            f"/repos/{validate_repo(repo)}/actions/runs",
            {"check_suite_id": suite_id},
            key="workflow_runs",
        )

    def pull_files(self, repo: str, number: int) -> list[Any]:
        return self.paginate(f"/repos/{validate_repo(repo)}/pulls/{int(number)}/files")


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


def _parse_actions_run_id(details_url: str | None) -> str | None:
    if not details_url:
        return None
    match = _ACTIONS_RUN_ID_RE.search(details_url)
    return match.group(1) if match else None


def _suite_id(run: Mapping[str, Any]) -> int | None:
    suite = run.get("check_suite")
    if not isinstance(suite, dict):
        return None
    value = suite.get("id")
    if isinstance(value, str) and value.isdigit():
        value = int(value)
    if isinstance(value, bool) or not isinstance(value, int) or value < 1:
        return None
    return value


def resolve_actions_workflow_run(
    api: Any, repo: str, check_run: Mapping[str, Any]
) -> tuple[dict[str, Any] | None, str]:
    """Load the Actions workflow run for a check run.

    The run id comes from ``details_url`` (``/actions/runs/<id>/job/<job>``).
    When that is missing, ``GET .../actions/runs?check_suite_id=`` must return
    exactly one run. The run object itself always comes from
    ``GET .../actions/runs/<id>``. Missing identity or any API error leaves the
    check unresolved.
    """
    if api is None or not repo:
        return None, "workflow run could not be resolved"
    run_id = _parse_actions_run_id(check_run.get("details_url") if isinstance(check_run.get("details_url"), str) else None)
    try:
        if run_id is None:
            suite_id = _suite_id(check_run)
            if suite_id is None:
                return None, "workflow identity is absent"
            listed = api.actions_runs_by_suite(repo, suite_id)
            if (
                not isinstance(listed, list)
                or len(listed) != 1
                or not isinstance(listed[0], dict)
                or listed[0].get("id") in (None, "")
            ):
                return None, "workflow run could not be resolved"
            run_id = str(listed[0]["id"])
        workflow_run = api.actions_run(repo, str(run_id))
    except GitHubApiError:
        return None, "workflow run could not be resolved"
    if not isinstance(workflow_run, dict):
        return None, "workflow run could not be resolved"
    return workflow_run, ""


def validate_workflow_run(
    workflow_run: Mapping[str, Any],
    *,
    expected: str | None,
    sha: str,
    repo: str,
    require_push_on_development: bool = False,
    require_phase_pr_on_development: bool = False,
) -> tuple[bool, str | None, str | None]:
    """Require path, head SHA, and target repository. Return ``(ok, path, reason)``."""
    path = workflow_run.get("path")
    identity = path if isinstance(path, str) and path else None
    if not identity:
        return False, None, "workflow run has no path"
    if expected and identity != expected:
        return False, identity, f"workflow path {identity!r} is not {expected!r}"
    if str(workflow_run.get("head_sha") or "") != sha:
        return False, identity, "workflow run head_sha does not equal the commit"
    head_repo = workflow_run.get("head_repository")
    full_name = head_repo.get("full_name") if isinstance(head_repo, dict) else None
    if full_name != repo:
        return False, identity, f"workflow run head_repository {full_name!r} is not the target repo"
    if require_push_on_development:
        if workflow_run.get("event") != "push":
            return False, identity, f"workflow run event {workflow_run.get('event')!r} is not 'push'"
        if workflow_run.get("head_branch") != "development":
            return False, identity, f"workflow run head_branch {workflow_run.get('head_branch')!r} is not 'development'"
    if require_phase_pr_on_development:
        if workflow_run.get("event") != "pull_request":
            return False, identity, f"workflow run event {workflow_run.get('event')!r} is not 'pull_request'"
        branch = workflow_run.get("head_branch")
        if not isinstance(branch, str) or not branch.startswith("phase/"):
            return False, identity, f"workflow run head_branch {branch!r} is not phase/*"
    return True, identity, None


def assess_check_workflow(
    check_run: Mapping[str, Any],
    expected: str | None,
    *,
    api: Any,
    repo: str | None,
    sha: str,
    require_push_on_development: bool = False,
    require_phase_pr_on_development: bool = False,
) -> tuple[bool, bool, str | None, str | None, str | None, list[Any]]:
    """Return ``(ok, exposed, path, reason)`` for one evidence check run."""
    workflow_run, unresolved = resolve_actions_workflow_run(api, repo or "", check_run)
    if workflow_run is None:
        return False, False, None, unresolved, None, []
    ok, path, reason = validate_workflow_run(
        workflow_run,
        expected=expected,
        sha=sha,
        repo=repo or "",
        require_push_on_development=require_push_on_development,
        require_phase_pr_on_development=require_phase_pr_on_development,
    )
    pulls = workflow_run.get("pull_requests")
    return (
        ok,
        True,
        path,
        reason,
        str(workflow_run.get("id") or "") or None,
        pulls if isinstance(pulls, list) else [],
    )


def workflow_files_changed(files: Iterable[Mapping[str, Any]]) -> list[str]:
    """``.github/workflows/*`` paths changed on a pull request, API order preserved."""
    found: list[str] = []
    for item in files:
        name = str(item.get("filename") or "")
        if name.startswith(".github/workflows/") and name not in found:
            found.append(name)
    return found


def latest_checks(
    check_runs: Iterable[Mapping[str, Any]],
    statuses: Iterable[Mapping[str, Any]] = (),
    *,
    allowed_apps: Sequence[str] = DEFAULT_ALLOWED_APPS,
    api: Any = None,
    repo: str | None = None,
    sha: str | None = None,
    require_push_on_development: bool = False,
    require_phase_pr_on_development: bool = False,
) -> dict[str, dict[str, Any]]:
    """Latest check run per ``(name, app)``, plus reported commit statuses.

    A required check is satisfied only by a completed check run whose
    ``app.slug`` is in ``allowed_apps`` (never by a commit status) and whose
    Actions workflow run resolves to the expected file, the same commit, and
    this repository. A missing or mismatched workflow does not count. A later
    run for the same ``(name, app)`` overrides an earlier one, including a
    later failure. Statuses are returned on ``statusReport`` and never count
    as success; a failing status is still a gate failure for the caller.
    ``require_push_on_development`` additionally demands ``event == push`` and
    ``head_branch == development`` (promotion evidence on a development commit).
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
            wf_ok, wf_exposed, wf_id, wf_reason, wf_run_id, wf_pulls = assess_check_workflow(
                chosen,
                expected,
                api=api,
                repo=repo,
                sha=sha or "",
                require_push_on_development=require_push_on_development,
                require_phase_pr_on_development=require_phase_pr_on_development,
            )
            completed = chosen.get("status") == "completed"
            out[name] = {
                "status": chosen.get("status"),
                "conclusion": chosen.get("conclusion") if completed and wf_ok else None,
                "source": "check_run",
                "app": app_slug(chosen),
                "workflow": wf_id,
                "workflowExposed": wf_exposed,
                "workflowOk": wf_ok,
                "workflowReason": wf_reason,
                "workflowRunId": wf_run_id,
                "workflowPullRequests": wf_pulls,
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
                "workflowReason": None,
                "workflowPullRequests": [],
                "url": status.get("target_url") if status else None,
                "countsAsCheck": False,
                "foreignApps": foreign,
                "statusReport": status_report,
            }
    return out


def head_checks(
    api: Any,
    repo: str,
    sha: str,
    *,
    allowed_apps: Sequence[str] = DEFAULT_ALLOWED_APPS,
    require_push_on_development: bool = False,
    require_phase_pr_on_development: bool = False,
) -> dict[str, dict[str, Any]]:
    return latest_checks(
        api.check_runs(repo, sha),
        api.commit_statuses(repo, sha),
        allowed_apps=allowed_apps,
        api=api,
        repo=repo,
        sha=sha,
        require_push_on_development=require_push_on_development,
        require_phase_pr_on_development=require_phase_pr_on_development,
    )


def check_succeeded(
    api: Any,
    repo: str,
    sha: str,
    name: str,
    *,
    allowed_apps: Sequence[str] = DEFAULT_ALLOWED_APPS,
    require_push_on_development: bool = False,
    require_phase_pr_on_development: bool = False,
) -> dict[str, Any]:
    check = head_checks(
        api,
        repo,
        sha,
        allowed_apps=allowed_apps,
        require_push_on_development=require_push_on_development,
        require_phase_pr_on_development=require_phase_pr_on_development,
    ).get(name)
    return summarize_check(sha, name, check)


def summarize_check(sha: str, name: str, check: Mapping[str, Any] | None) -> dict[str, Any]:
    """Reduce one validated head-check observation to the promotion shape."""
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
        "workflow": (check or {}).get("workflow"),
        "workflowReason": (check or {}).get("workflowReason"),
        "workflowRunId": (check or {}).get("workflowRunId"),
        "workflowPullRequests": (check or {}).get("workflowPullRequests", []),
        "ok": conclusion == "success" and counts and not status_failed,
    }


def repo_from_remote_url(url: str) -> str | None:
    match = re.search(r"github\.com[:/]+([A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+?)(?:\.git)?/?$", url.strip())
    return match.group(1) if match else None
