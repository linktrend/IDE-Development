"""Versioned local coordinator daemon orchestration boundary."""

from __future__ import annotations

import json
import threading
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Mapping, Optional

from scripts.gitops.coordinator.config import ConfigError, DeliveryConfig, load_delivery_config
from scripts.gitops.coordinator.state import load_state, transition

from .executor import Job, run_job
from .github_client import GitHubClient, GitHubError, validate_main_approval
from .queue import QueueRequest, QueueResult, QueueStore, configure_default_store, priority_for
from .resources import HostSnapshot, ResourceLimits, admit_job


COORDINATOR_VERSION = "2.0.0"
STATUS_CONTEXTS = {
    "fast-gate": "Linktrend Fast Gate",
    "full-gate": "Linktrend Full Suite",
    "staging-gate": "Linktrend Staging Gate",
    "release-gate": "Linktrend Release Gate",
}


@dataclass(frozen=True)
class RepositoryRegistration:
    repository: str
    root: str
    default_branch: str


class CoordinatorDaemon:
    """Own one allowlisted registry and one transactional queue."""

    def __init__(self, database: str | Path, *, github: Optional[GitHubClient] = None, runner: Optional[Callable[..., Any]] = None) -> None:
        self.store = QueueStore(database)
        configure_default_store(self.store)
        self.github = github or GitHubClient()
        self.runner = runner or run_job
        self._protected_configs: dict[str, DeliveryConfig] = {}
        self._paused = self.store.runtime("paused", "0") == "1"
        self._pause_lock = threading.Lock()

    def close(self) -> None:
        self.store.close()

    def register(self, repository: str, root: str, default_branch: str = "development") -> RepositoryRegistration:
        self.store.register_repository(repository, root, default_branch)
        return RepositoryRegistration(repository, str(Path(root).resolve()), default_branch)

    def registrations(self) -> list[dict[str, Any]]:
        rows = self.store._connection.execute("SELECT * FROM repositories WHERE allowlisted=1 ORDER BY repository").fetchall()
        return [dict(row) for row in rows]

    def load_protected_config(self, repository: str, *, candidate_ref: Optional[str] = None) -> DeliveryConfig:
        registration = self.store.repository(repository)
        if registration is None:
            raise GitHubError("repository_not_allowlisted", repository)
        payload, protected_branch = self.github.load_protected_policy(repository, candidate_ref=candidate_ref)
        if protected_branch != registration["default_branch"]:
            raise GitHubError("protected_branch_mismatch", "GitHub default branch does not match registered protected branch")
        try:
            config = load_delivery_config(payload)
            self._protected_configs[repository] = config
            return config
        except ConfigError as exc:
            raise GitHubError("protected_policy_invalid", str(exc)) from exc

    def enqueue_request(self, request: QueueRequest | Mapping[str, Any]) -> QueueResult:
        repository = request.repository if isinstance(request, QueueRequest) else request.get("repository")
        if not repository or self.store.repository(str(repository)) is None:
            raise GitHubError("repository_not_allowlisted", str(repository))
        return self.store.enqueue(request)

    def poll_once(self, repository: str) -> dict[str, Any]:
        registration = self.store.repository(repository)
        if registration is None:
            raise GitHubError("repository_not_allowlisted", repository)
        # Policy is refreshed from the protected default branch before PR
        # events are admitted.  A candidate ref is never consulted here.
        self.load_protected_config(repository)
        poll = self.store.poll_state(repository)
        if poll["next_poll_at"] > time.time():
            return {"status": "backoff", "nextPollAt": poll["next_poll_at"]}
        endpoint = "/repos/{}/pulls?state=open&per_page=100".format(repository)
        result = self.github.poll(endpoint, etag=poll["etag"], failures=poll["failures"])
        if result.failed_closed:
            self.store.update_poll(repository, failures=int(poll["failures"]) + 1, next_poll_at=time.time() + result.next_delay_seconds, last_status=result.response.status or None, last_error=result.message)
            return {"status": "failed-closed", "message": result.message, "retryIn": result.next_delay_seconds}
        if result.response.not_modified:
            # Do not touch queue rows or candidate state on a conditional 304.
            self.store.update_poll(repository, next_poll_at=time.time() + result.next_delay_seconds, last_status=304, last_error=None)
            return {"status": "not-modified", "retryIn": result.next_delay_seconds}
        etag = result.response.etag
        self.store.update_poll(repository, etag=etag, failures=0, next_poll_at=time.time() + result.next_delay_seconds, last_status=result.response.status, last_error=None)
        observed = result.response.payload if isinstance(result.response.payload, list) else []
        jobs: list[str] = []
        observed_prs: set[int] = set()
        for pr in observed:
            if not isinstance(pr, Mapping) or not pr.get("number"):
                continue
            observed_prs.add(int(pr["number"]))
            identity = pr.get("candidateIdentity", pr.get("candidate_identity"))
            if not pr.get("state", "open") == "open" or pr.get("closed_at"):
                jobs.extend(self.store.cancel_obsolete(repository, int(pr["number"]), None))
                continue
            if identity is None:
                continue
            gate = str(pr.get("gate", "fast-gate"))
            priority = priority_for(gate, active_phase=bool(pr.get("phaseActive", True)))
            queued = self.enqueue_request(QueueRequest(repository, gate, identity, priority=priority, pr_number=int(pr["number"]), phase_id=pr.get("phaseId"), payload={"pullRequest": int(pr["number"])}))
            jobs.append(queued.job_id)
            self.store.cancel_obsolete(repository, int(pr["number"]), identity)
        # A closed PR is absent from the open-PR response.  Existing work for
        # it is obsolete and is cancelled without consuming an attempt.
        for job in self.store.list_jobs(statuses={"queued", "running"}):
            if job["repository"] == repository and job.get("pr_number") is not None and int(job["pr_number"]) not in observed_prs:
                jobs.extend(self.store.cancel_obsolete(repository, int(job["pr_number"]), None))
        return {"status": "updated", "jobs": jobs, "observed": len(observed), "etag": etag}

    def cancel_obsolete(self, repository: str, pr_number: Optional[int], live_identity: Any = None) -> list[str]:
        return self.store.cancel_obsolete(repository, pr_number, live_identity)

    def run_next(self, *, host_snapshot: Optional[HostSnapshot] = None) -> Optional[dict[str, Any]]:
        with self._pause_lock:
            if self._paused:
                return {"status": "paused"}
        queued = self.store.next_job()
        if queued is None:
            return None
        try:
            config = self._protected_configs.get(queued["repository"]) or self.load_protected_config(queued["repository"])
        except GitHubError as exc:
            # Policy/credential failures happen before mark_started, so they
            # cannot consume one of the candidate's two execution attempts.
            return {"status": "failed-closed", "jobId": queued["id"], "reason": str(exc)}
        limits = ResourceLimits.from_mapping({})
        verdict = admit_job(queued, host_snapshot or HostSnapshot(), self.store.list_jobs(statuses={"running"}), limits)
        if not verdict.admitted:
            return {"status": "deferred", "jobId": queued["id"], "reason": verdict.reason, "pressure": verdict.pressure_reasons}
        started = self.store.mark_started(queued["id"])
        if not started.get("started"):
            return {"status": "not-started", "jobId": queued["id"], "reason": started.get("reason")}
        row = started["job"]
        registration = self.store.repository(row["repository"])
        payload = row["payload"]
        profile = config.test_profiles.get(row["candidate_identity"]["testProfile"]) if config.test_profiles else None
        commands = profile.commands if profile else ()
        command = commands[0] if commands else ("true",)
        job = Job(job_id=row["id"], checkout_path=registration["root"], workspace_root=str(Path(registration["root"]).parent), image=str(payload.get("image", "alpine:3.20")), command=tuple(command), test_profile=row["candidate_identity"]["testProfile"], timeout_seconds=int(payload.get("timeoutSeconds", 300)), repository=row["repository"])
        try:
            result = self.runner(job, limits, lambda: self.store.get(row["id"])["status"] == "cancelled")
            result_status = "completed" if getattr(result, "status", "") == "passed" else "cancelled" if getattr(result, "status", "") == "cancelled" else "failed"
            data = {"status": getattr(result, "status", "unknown"), "sanitized": getattr(result, "stdout", "") + "\n" + getattr(result, "stderr", ""), "error": getattr(result, "error", None)}
            final = self.store.record_result(row["id"], result_status, data, evidence_location=payload.get("evidence", "") if isinstance(payload, Mapping) else "")
            if final.get("alert") and hasattr(self.github, "upsert_alert"):
                alert = final["alert"]
                self.github.upsert_alert(row["repository"], "Linktrend coordinator stopped after two failures", json.dumps(alert, sort_keys=True), marker=alert["alert_key"])
            context = STATUS_CONTEXTS.get(row["gate"])
            if context and row["candidate_identity"].get("sourceSha"):
                self.github.publish_status(row["repository"], row["candidate_identity"]["sourceSha"], context, "success" if result_status == "completed" else "failure", "coordinator result: " + result_status, "https://github.com/{}/commit/{}/checks".format(row["repository"], row["candidate_identity"]["sourceSha"]))
            return {"status": result_status, "jobId": row["id"], "attempt": row["attempt_count"], "result": final}
        except Exception as exc:
            self.store.record_result(row["id"], "failed", {"error": str(exc), "sanitized": str(exc)})
            return {"status": "failed", "jobId": row["id"], "error": str(exc)}

    def pause(self) -> None:
        with self._pause_lock:
            self._paused = True
            self.store.set_runtime("paused", "1")

    def resume(self) -> None:
        with self._pause_lock:
            self._paused = False
            self.store.set_runtime("paused", "0")

    @property
    def paused(self) -> bool:
        with self._pause_lock:
            return self._paused

    def status(self) -> dict[str, Any]:
        return {"version": COORDINATOR_VERSION, "paused": self.paused, "repositories": self.registrations(), "jobs": self.store.list_jobs(), "alerts": self.store.alerts()}

    def doctor(self) -> dict[str, Any]:
        checks = {
            "database": True,
            "allowlistedRepositories": len(self.registrations()),
            "tokenPresent": bool(self.github.token),
            "paused": self.paused,
        }
        checks["ok"] = bool(checks["database"] and checks["allowlistedRepositories"] >= 0)
        return checks

    def approve_main(self, approval: Mapping[str, Any], *, current_staging_sha: str, current_main_base_sha: str, current_pr_head_sha: str, current_receipt_identity: str) -> dict[str, Any]:
        validate_main_approval(approval, staging_source_sha=current_staging_sha, main_base_sha=current_main_base_sha, pr_head_sha=current_pr_head_sha, receipt_identity=current_receipt_identity)
        key = "|".join((current_staging_sha, current_main_base_sha, current_pr_head_sha, current_receipt_identity))
        self.store.approve(key, approval)
        return {"approved": True, "approvalKey": key}


def publish_status(repository: str, sha: str, context: str, state: str, description: str, target_url: str, *, client: Optional[GitHubClient] = None) -> None:
    (client or GitHubClient()).publish_status(repository, sha, context, state, description, target_url)


__all__ = ["COORDINATOR_VERSION", "CoordinatorDaemon", "RepositoryRegistration", "STATUS_CONTEXTS", "load_state", "publish_status", "transition"]
