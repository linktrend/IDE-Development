"""Small, fail-closed GitHub REST adapter for the host coordinator.

Only normal-token requests are supported.  The adapter has no App fallback and
never writes Bugbot reviews; Bugbot is an observed external result.
"""

from __future__ import annotations

import base64
import json
import os
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from typing import Any, Callable, Mapping, Optional

from .executor import sanitize_output


API_ROOT = "https://api.github.com"
_STATUS_STATES = {"error", "failure", "pending", "success"}
_NORMAL_CONTEXTS = {
    "Linktrend Fast Gate",
    "Linktrend Full Suite",
    "Linktrend Phase Ready",
    "Linktrend Staging Gate",
    "Linktrend Release Gate",
    "Linktrend Coordinator",
}


class GitHubError(RuntimeError):
    def __init__(self, code: str, message: str, *, retryable: bool = False, status: Optional[int] = None, retry_after: Optional[int] = None) -> None:
        self.code = code
        self.retryable = retryable
        self.status = status
        self.retry_after = retry_after
        super().__init__(message)


@dataclass(frozen=True)
class GitHubResponse:
    status: int
    payload: Any = None
    etag: Optional[str] = None
    not_modified: bool = False
    retry_after: Optional[int] = None


@dataclass(frozen=True)
class PollResult:
    response: GitHubResponse
    next_delay_seconds: int
    failed_closed: bool = False
    message: str = ""


@dataclass(frozen=True)
class MainApprovalBinding:
    staging_source_sha: str
    main_base_sha: str
    pr_head_sha: str
    receipt_identity: str

    def to_dict(self) -> dict[str, str]:
        return {
            "stagingSourceSha": self.staging_source_sha,
            "mainBaseSha": self.main_base_sha,
            "prHeadSha": self.pr_head_sha,
            "receiptIdentity": self.receipt_identity,
        }


def _sha(value: Any) -> bool:
    return isinstance(value, str) and len(value) == 40 and all(char in "0123456789abcdef" for char in value)


def validate_main_approval(binding: Mapping[str, Any], *, staging_source_sha: str, main_base_sha: str, pr_head_sha: str, receipt_identity: str) -> None:
    expected = MainApprovalBinding(staging_source_sha, main_base_sha, pr_head_sha, receipt_identity).to_dict()
    if dict(binding) != expected:
        raise GitHubError("approval_binding_mismatch", "approve-main is not bound to the current staging SHA, main base, PR head, and receipt")
    for name, value in expected.items():
        if name != "receiptIdentity" and not _sha(value):
            raise GitHubError("approval_binding_invalid", name + " must be a lowercase 40-character SHA")
    if not receipt_identity:
        raise GitHubError("approval_binding_invalid", "receipt identity is required")


class Backoff:
    def __init__(self, base_seconds: int = 5, maximum_seconds: int = 300) -> None:
        self.base_seconds = max(1, int(base_seconds))
        self.maximum_seconds = max(self.base_seconds, int(maximum_seconds))

    def delay(self, failures: int, retry_after: Optional[int] = None) -> int:
        if retry_after is not None:
            return max(1, min(self.maximum_seconds, int(retry_after)))
        return min(self.maximum_seconds, self.base_seconds * (2 ** max(0, min(int(failures), 8))))


class GitHubClient:
    """REST client whose request boundary can be replaced by a test transport."""

    def __init__(self, token: Optional[str] = None, *, api_root: str = API_ROOT, transport: Optional[Callable[..., Any]] = None, backoff: Optional[Backoff] = None) -> None:
        self.token = token if token is not None else os.environ.get("LINKTREND_AUTOMATION_TOKEN")
        self.api_root = api_root.rstrip("/")
        self.transport = transport
        self.backoff = backoff or Backoff()
        self.request_log: list[dict[str, Any]] = []

    def _headers(self, etag: Optional[str] = None) -> dict[str, str]:
        if not self.token:
            raise GitHubError("automation_credentials_blocked", "LINKTREND_AUTOMATION_TOKEN is absent; refusing GitHub mutation or poll")
        headers = {
            "Accept": "application/vnd.github+json",
            "Authorization": "Bearer " + self.token,
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "linktrend-ide-coordinator",
        }
        if etag:
            headers["If-None-Match"] = etag
        return headers

    @staticmethod
    def _decode_response(raw: Any) -> GitHubResponse:
        if isinstance(raw, GitHubResponse):
            return raw
        if isinstance(raw, Mapping):
            return GitHubResponse(int(raw.get("status", 200)), raw.get("payload", raw.get("json")), raw.get("etag"), bool(raw.get("not_modified", raw.get("status") == 304)), raw.get("retry_after"))
        status = int(getattr(raw, "status", getattr(raw, "code", 200)))
        headers = getattr(raw, "headers", {})
        etag = headers.get("ETag") or headers.get("etag") if headers else None
        retry = headers.get("Retry-After") if headers else None
        body = getattr(raw, "payload", None)
        return GitHubResponse(status, body, etag, status == 304, int(retry) if retry else None)

    def request(self, method: str, path: str, *, etag: Optional[str] = None, payload: Any = None) -> GitHubResponse:
        if not path.startswith("/"):
            raise GitHubError("invalid_endpoint", "GitHub endpoint must be relative")
        headers = self._headers(etag)
        body = None if payload is None else json.dumps(payload, sort_keys=True).encode("utf-8")
        if body is not None:
            headers["Content-Type"] = "application/json"
        url = self.api_root + path
        # The log is intentionally metadata-only; it never stores the token or
        # request body, which keeps diagnostics secret-free.
        self.request_log.append({"method": method.upper(), "path": path, "etag": etag})
        try:
            if self.transport is not None:
                raw = self.transport(method.upper(), url, headers, body)
                response = self._decode_response(raw)
            else:
                request = urllib.request.Request(url, data=body, headers=headers, method=method.upper())
                with urllib.request.urlopen(request, timeout=30) as raw_response:
                    raw_body = raw_response.read().decode("utf-8")
                    response = GitHubResponse(raw_response.status, json.loads(raw_body) if raw_body else None, raw_response.headers.get("ETag"), raw_response.status == 304, int(raw_response.headers.get("Retry-After")) if raw_response.headers.get("Retry-After") else None)
        except urllib.error.HTTPError as exc:
            retry_after = exc.headers.get("Retry-After") if exc.headers else None
            if exc.code in {403, 429}:
                raise GitHubError("rate_limited", "GitHub rate limit or abuse response", retryable=True, status=exc.code, retry_after=int(retry_after) if retry_after else None) from exc
            if 500 <= exc.code <= 599:
                raise GitHubError("github_unavailable", "GitHub server error", retryable=True, status=exc.code) from exc
            raise GitHubError("github_http_error", "GitHub request failed with status " + str(exc.code), status=exc.code) from exc
        except (OSError, ValueError, TypeError) as exc:
            raise GitHubError("network_error", sanitize_output(exc), retryable=True) from exc
        if response.status in {403, 429}:
            raise GitHubError("rate_limited", "GitHub rate limit or abuse response", retryable=True, status=response.status, retry_after=response.retry_after)
        if 500 <= response.status <= 599:
            raise GitHubError("github_unavailable", "GitHub server error", retryable=True, status=response.status)
        if response.status < 200 or (response.status >= 300 and response.status != 304):
            raise GitHubError("github_http_error", "GitHub request failed with status " + str(response.status), status=response.status)
        return response

    def poll(self, path: str, *, etag: Optional[str] = None, failures: int = 0) -> PollResult:
        try:
            response = self.request("GET", path, etag=etag)
            # A 304 is a truthful no-op.  The caller must not rewrite queue or
            # repository state merely because polling happened.
            return PollResult(response, self.backoff.delay(0), False, "not-modified" if response.not_modified else "ok")
        except GitHubError as exc:
            delay = self.backoff.delay(failures + 1, exc.retry_after)
            return PollResult(GitHubResponse(exc.status or 0), delay, True, exc.code + ": " + str(exc))

    def repository_metadata(self, repository: str) -> GitHubResponse:
        return self.request("GET", "/repos/" + urllib.parse.quote(repository, safe="/"))

    def load_protected_policy(self, repository: str, *, candidate_ref: Optional[str] = None) -> tuple[dict[str, Any], str]:
        metadata = self.repository_metadata(repository)
        if not isinstance(metadata.payload, Mapping) or not metadata.payload.get("default_branch"):
            raise GitHubError("protected_policy_unavailable", "repository default branch is unavailable")
        default_branch = str(metadata.payload["default_branch"])
        # candidate_ref is deliberately ignored.  The policy request is bound
        # to GitHub's reported default branch, never to a PR or candidate ref.
        path = "/repos/{}/contents/.github/linktrend-delivery-mode.json?ref={}".format(urllib.parse.quote(repository, safe="/"), urllib.parse.quote(default_branch, safe=""))
        response = self.request("GET", path)
        payload = response.payload if isinstance(response.payload, Mapping) else {}
        encoded = payload.get("content")
        if not isinstance(encoded, str):
            raise GitHubError("protected_policy_unavailable", "protected policy content is missing")
        try:
            decoded = base64.b64decode(encoded.replace("\n", ""), validate=True).decode("utf-8")
            policy = json.loads(decoded)
        except (ValueError, UnicodeError, json.JSONDecodeError) as exc:
            raise GitHubError("protected_policy_invalid", "protected default-branch policy is not valid JSON") from exc
        if not isinstance(policy, dict):
            raise GitHubError("protected_policy_invalid", "protected policy must be an object")
        return policy, default_branch

    def publish_status(self, repository: str, sha: str, context: str, state: str, description: str, target_url: str) -> None:
        if not _sha(sha):
            raise GitHubError("invalid_sha", "status SHA is invalid")
        if state not in _STATUS_STATES:
            raise GitHubError("invalid_status", "status state is invalid")
        if context not in _NORMAL_CONTEXTS:
            raise GitHubError("invalid_status_context", "only frozen normal coordinator contexts may be published")
        if not target_url or not target_url.startswith(("https://", "http://")):
            raise GitHubError("invalid_target_url", "status target URL is required")
        self.request("POST", "/repos/{}/statuses/{}".format(urllib.parse.quote(repository, safe="/"), sha), payload={"state": state, "context": context, "description": sanitize_output(description)[:140], "target_url": target_url})

    def observe_bugbot(self, repository: str, pr_number: int) -> GitHubResponse:
        return self.request("GET", "/repos/{}/issues/{}/comments".format(urllib.parse.quote(repository, safe="/"), int(pr_number)))

    def upsert_alert(self, repository: str, title: str, body: str, *, marker: str) -> GitHubResponse:
        issues = self.request("GET", "/repos/{}/issues?state=open&labels=linktrend-coordinator".format(urllib.parse.quote(repository, safe="/")))
        found = None
        for issue in issues.payload if isinstance(issues.payload, list) else []:
            if isinstance(issue, Mapping) and marker in str(issue.get("body", "")):
                found = issue
                break
        clean_body = sanitize_output(body)[:20000] + "\n\n<!-- " + marker + " -->"
        if found and found.get("number"):
            return self.request("PATCH", "/repos/{}/issues/{}".format(urllib.parse.quote(repository, safe="/"), int(found["number"])), payload={"title": title, "body": clean_body})
        return self.request("POST", "/repos/{}/issues".format(urllib.parse.quote(repository, safe="/")), payload={"title": title, "body": clean_body, "labels": ["linktrend-coordinator"]})


__all__ = ["Backoff", "GitHubClient", "GitHubError", "GitHubResponse", "MainApprovalBinding", "PollResult", "validate_main_approval"]
