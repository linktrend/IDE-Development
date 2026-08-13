"""Versioned local coordinator daemon orchestration boundary."""

from __future__ import annotations

import json
import shlex
import hashlib
import shutil
import subprocess
import tempfile
import threading
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Mapping, Optional

from scripts.gitops.coordinator.config import ConfigError, DeliveryConfig, load_delivery_config
from scripts.gitops.coordinator.receipts import GateReceipt, write_receipt
from scripts.gitops.coordinator.state import load_state, transition

from .executor import Job, run_job
from .github_client import GitHubClient, GitHubError, validate_main_approval
from .multihost import MultiHostCoordinator
from .queue import QueueRequest, QueueResult, QueueStore, configure_default_store, priority_for
from .resources import HostSnapshot, ResourceLimits
from .workers import Worker, WorkerRegistry, current_mac_mini_fixture


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
        self._receipt_root = Path(database).expanduser().parent / "receipts"
        self.workers = WorkerRegistry(database)
        self.scheduler = MultiHostCoordinator(store=self.store, registry=self.workers, coordinator_version=COORDINATOR_VERSION)
        if not self.workers.inspect():
            # The current Mac Mini is the only enabled default registration.
            # Additional workers remain an explicit operator action.
            self.workers.register(current_mac_mini_fixture())
        configure_default_store(self.store)
        self.github = github or GitHubClient()
        self.runner = runner or run_job
        self._protected_configs: dict[str, DeliveryConfig] = {}
        self._paused = self.store.runtime("paused", "0") == "1"
        self._pause_lock = threading.Lock()

    def close(self) -> None:
        self.scheduler.close()

    def register_worker(self, worker: Worker | Mapping[str, Any]) -> Worker:
        """Register only an isolated candidate worker; no privileged role."""
        return self.workers.register(worker)

    def worker_heartbeat(self, worker_id: str) -> Worker:
        return self.workers.heartbeat(worker_id)

    def worker_command(self, command: str, worker_id: str) -> Worker | bool:
        commands = {
            "enable": self.workers.enable,
            "disable": self.workers.disable,
            "drain": self.workers.drain,
            "offline": self.workers.mark_offline,
        }
        if command == "remove":
            return self.workers.remove(worker_id)
        if command not in commands:
            raise ValueError("unknown worker lifecycle command")
        return commands[command](worker_id)

    def inspect_workers(self, worker_id: Optional[str] = None) -> list[dict[str, Any]]:
        return self.workers.inspect(worker_id)

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
                identity = self._candidate_identity_from_pull(repository, pr)
            if identity is None:
                # Do not fabricate a testable identity if the API head cannot
                # be fetched and content-bound locally.
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

    def _candidate_identity_from_pull(self, repository: str, pull: Mapping[str, Any]) -> Optional[dict[str, Any]]:
        """Bind normal GitHub pull-list payloads to an exact local tree."""
        head = pull.get("head") if isinstance(pull.get("head"), Mapping) else {}
        sha = str(head.get("sha", ""))
        registration = self.store.repository(repository)
        config = self._protected_configs.get(repository)
        if not registration or not config or len(sha) != 40 or any(char not in "0123456789abcdef" for char in sha):
            return None
        root = str(registration["root"])
        try:
            subprocess.run(("git", "-C", root, "fetch", "--no-tags", "origin", sha), check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=60)
            tree = subprocess.check_output(("git", "-C", root, "rev-parse", sha + "^{tree}"), text=True, timeout=15).strip()
            digests = {}
            for path in config.dependency_files:
                data = subprocess.check_output(("git", "-C", root, "show", sha + ":" + path), timeout=15)
                digests[path] = "sha256:" + hashlib.sha256(data).hexdigest()
        except (OSError, subprocess.SubprocessError):
            return None
        return {"repository": repository, "sourceSha": sha, "gitTreeSha": tree, "dependencyDigests": digests, "testProfile": "fast"}

    @staticmethod
    def _disposable_checkout(repository_root: str, source_sha: str) -> Optional[str]:
        """Create a per-lease, detached exact checkout outside the operator tree."""
        if len(source_sha) != 40 or any(char not in "0123456789abcdef" for char in source_sha):
            return None
        parent = tempfile.mkdtemp(prefix="linktrend-coordinator-")
        checkout = str(Path(parent) / "candidate")
        try:
            subprocess.run(("git", "-C", repository_root, "cat-file", "-e", source_sha + "^{commit}"), check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=15)
            # PR heads are often unadvertised objects in the operator clone.
            # Fetch the verified object directly instead of relying on clone's
            # advertised-ref negotiation, which would make a valid candidate
            # checkout fail closed merely because its ref is not advertised.
            subprocess.run(("git", "init", "--quiet", checkout), check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=30)
            subprocess.run(("git", "-C", checkout, "fetch", "--no-tags", repository_root, source_sha), check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=120)
            subprocess.run(("git", "-C", checkout, "checkout", "--detach", "FETCH_HEAD"), check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=60)
            resolved = subprocess.check_output(("git", "-C", checkout, "rev-parse", "HEAD"), text=True, timeout=15).strip()
            if resolved != source_sha:
                raise subprocess.CalledProcessError(1, ("git", "rev-parse", "HEAD"))
            return checkout
        except (OSError, subprocess.SubprocessError):
            shutil.rmtree(parent, ignore_errors=True)
            return None

    @staticmethod
    def _reclaim_unregistered_checkout(checkout_path: str) -> None:
        """Best-effort fallback for a checkout whose executor never registered.

        The executor normally owns removal after registering the job.  This
        path is deliberately narrower: it recognizes only the exact private
        `mkdtemp` layout created above, and never recurses through an operator
        repository or a mocked/foreign workspace.
        """
        checkout = Path(checkout_path)
        parent = checkout.parent
        if checkout.name != "candidate" or not parent.name.startswith("linktrend-coordinator-"):
            return
        shutil.rmtree(checkout, ignore_errors=True)
        try:
            parent.rmdir()
        except OSError:
            pass

    def _write_execution_receipt(self, row: Mapping[str, Any], lease: Any, result: Any) -> str:
        """Persist one atomic, exact-identity receipt for a passed lease only."""
        identity = row["candidate_identity"]
        source_sha = str(identity["sourceSha"])
        evidence = (str(getattr(result, "stdout", "")) + "\n" + str(getattr(result, "stderr", ""))).encode("utf-8")
        provenance = self.scheduler.receipt_metadata(
            lease,
            execution_environment={"container": str(getattr(result, "container_name", "")), "network": "none"},
        )
        receipt = GateReceipt(
            schema_version=1, status="passed", repository=str(identity["repository"]),
            gate=str(row["gate"]), source_sha=source_sha, tested_checkout_sha=source_sha,
            git_tree_sha=str(identity["gitTreeSha"]), dependency_digests=dict(identity["dependencyDigests"]),
            test_profile=str(identity["testProfile"]), attempt=int(row["attempt_count"]),
            coordinator_version=COORDINATOR_VERSION, started_at=str(getattr(result, "started_at", "")),
            completed_at=str(getattr(result, "completed_at", "")),
            evidence_digests={"logs/{}.txt".format(row["id"]): "sha256:" + hashlib.sha256(evidence).hexdigest()},
            github={"pullRequest": row.get("pr_number"), "runUrl": None}, worker_id=str(provenance["workerId"]),
            worker_capabilities=tuple(provenance["workerCapabilities"]), worker_trust=str(provenance["workerTrust"]),
            coordinator_identity=str(provenance["coordinatorIdentity"]),
            execution_environment=dict(provenance["executionEnvironment"]),
        )
        # Receipts are reusable for an identical tree and dependency identity,
        # including a no-ff promotion commit whose SHA necessarily differs.
        path = self._receipt_root / (str(identity["gitTreeSha"]) + "-" + str(row["gate"]) + ".json")
        write_receipt(receipt, path)
        return str(path)

    def cancel_obsolete(self, repository: str, pr_number: Optional[int], live_identity: Any = None) -> list[str]:
        return self.store.cancel_obsolete(repository, pr_number, live_identity)

    def run_next(self, *, host_snapshot: Optional[HostSnapshot] = None) -> Optional[dict[str, Any]]:
        with self._pause_lock:
            if self._paused:
                return {"status": "paused"}
        queued = self.store.next_job()
        if queued is None:
            return None
        configs: dict[str, DeliveryConfig] = {}
        policy_errors: dict[str, str] = {}
        for candidate in self.store.list_jobs(statuses={"queued"}):
            repository = candidate["repository"]
            if repository in configs or repository in policy_errors:
                continue
            try:
                configs[repository] = self._protected_configs.get(repository) or self.load_protected_config(repository)
            except GitHubError as exc:
                policy_errors[repository] = str(exc)
        if not configs:
            # Policy/credential failures happen before any lease, so they
            # cannot consume one of the candidate's execution attempts.
            return {"status": "failed-closed", "jobId": queued["id"], "reason": policy_errors.get(queued["repository"], "no protected policy available")}

        lease = None
        # The coordinator owns the local Mac Mini registration and refreshes
        # only that identity. Remote workers must present their own heartbeat.
        try:
            self.workers.heartbeat("mac-mini-primary")
        except KeyError:
            pass
        snapshot = self._snapshot_mapping(host_snapshot or HostSnapshot())
        for worker in self.workers.list():
            lease = self.scheduler.claim(
                worker.worker_id, snapshot=snapshot,
                admission_limits=self._coordinator_admission(configs.values()),
                allowed_repositories=set(configs),
            )
            if lease is not None:
                break
        if lease is None:
            return {"status": "deferred", "jobId": queued["id"], "reason": "no-eligible-worker"}

        row = self.store.get(lease.job_id)
        if row is None:
            return {"status": "failed-closed", "jobId": lease.job_id, "reason": "leased job disappeared"}
        config = configs[row["repository"]]
        worker = self.workers.get(lease.worker_id)
        registration = self.store.repository(row["repository"])
        if worker is None or registration is None:
            self.scheduler.complete(lease, "rejected", {"error": "lease context disappeared", "sanitized": "lease context disappeared"})
            return {"status": "failed-closed", "jobId": row["id"], "reason": "lease context disappeared"}
        payload = row["payload"]
        profile = config.test_profiles.get(row["candidate_identity"]["testProfile"]) if config.test_profiles else None
        commands = profile.commands if profile else ()
        if not commands:
            # A protected profile that does not name tests is invalid for an
            # executable gate; never turn that into a successful no-op.
            self.scheduler.complete(lease, "rejected", {"error": "protected test profile has no commands", "sanitized": "protected test profile has no commands"})
            return {"status": "failed-closed", "jobId": row["id"], "reason": "protected test profile has no commands"}
        # Profiles are protected coordinator policy. Preserve every command in
        # order instead of silently running only the first one.
        command = ("/bin/sh", "-ec", " && ".join(shlex.join(tuple(item)) for item in commands))
        limits = self._execution_limits(config)
        checkout = self._disposable_checkout(str(registration["root"]), row["candidate_identity"]["sourceSha"])
        if checkout is None:
            self.scheduler.complete(lease, "rejected", {"error": "exact candidate checkout unavailable", "sanitized": "exact candidate checkout unavailable"})
            return {"status": "failed-closed", "jobId": row["id"], "reason": "exact candidate checkout unavailable"}
        job = Job(
            job_id=row["id"], checkout_path=checkout,
            workspace_root=str(Path(checkout).parent), temporary_checkout=True,
            # Every daemon checkout is a newly fetched, per-lease private
            # copy.  Some protected reproducibility tests generate files in
            # that copy; no operator checkout or privileged mount is writable.
            writable_workspace=True,
            # Container selection is protected policy, never candidate payload.
            image=profile.image if profile else "alpine:3.20", command=tuple(command),
            test_profile=row["candidate_identity"]["testProfile"],
            timeout_seconds=int(payload.get("timeoutSeconds", profile.timeout_seconds if profile else 300)),
            repository=row["repository"], worker_id=worker.worker_id,
            worker_trust=worker.trust, worker_capabilities=tuple(sorted(worker.capabilities)),
            worker_arch=worker.arch,
            nested_docker=bool(payload.get("nestedDocker", False)),
            protected_nested_config=payload.get("protectedNestedConfig"),
        )
        renewal_stop = threading.Event()
        def renew_lease() -> None:
            while not renewal_stop.wait(30):
                if not self.scheduler.renew(lease, lease_seconds=120):
                    return
        renewal = threading.Thread(target=renew_lease, daemon=True)
        renewal.start()
        try:
            result = self.runner(job, limits, lambda: self._lease_cancelled(lease))
            result_status = "completed" if getattr(result, "status", "") == "passed" else "cancelled" if getattr(result, "status", "") == "cancelled" else "failed"
            data = {"status": getattr(result, "status", "unknown"), "sanitized": getattr(result, "stdout", "") + "\n" + getattr(result, "stderr", ""), "error": getattr(result, "error", None)}
            if result_status == "completed":
                try:
                    data["receiptPath"] = self._write_execution_receipt(row, lease, result)
                except Exception as receipt_error:
                    result_status = "failed"
                    data["error"] = "receipt recording failed: {}".format(receipt_error)
                    data["sanitized"] = data["error"]
            final = self.scheduler.complete(lease, result_status, data)
        except Exception as exc:
            data = {"error": str(exc), "sanitized": str(exc)}
            try:
                final = self.scheduler.complete(lease, "failed", data)
            except Exception as completion_error:
                return {"status": "failed-closed", "jobId": row["id"], "error": str(completion_error)}
            result_status = "failed"
        finally:
            renewal_stop.set()
            renewal.join(timeout=1)
            self._reclaim_unregistered_checkout(checkout)

        if final.get("alert") and hasattr(self.github, "upsert_alert"):
            alert = final["alert"]
            self.github.upsert_alert(row["repository"], "Linktrend coordinator stopped after two failures", json.dumps(alert, sort_keys=True), marker=alert["alert_key"])
        context = STATUS_CONTEXTS.get(row["gate"])
        if context and row["candidate_identity"].get("sourceSha"):
            self.github.publish_status(row["repository"], row["candidate_identity"]["sourceSha"], context, "success" if result_status == "completed" else "failure", "coordinator result: " + result_status, "https://github.com/{}/commit/{}/checks".format(row["repository"], row["candidate_identity"]["sourceSha"]))
        return {"status": result_status, "jobId": row["id"], "attempt": row["attempt_count"], "result": final, "workerId": lease.worker_id}

    @staticmethod
    def _snapshot_mapping(snapshot: HostSnapshot) -> dict[str, Any]:
        return {
            "cpuPercent": snapshot.cpu_percent, "memoryPercent": snapshot.memory_percent,
            "freeDiskGiB": snapshot.free_disk_gib, "dockerAvailable": snapshot.docker_available,
            "interactiveUse": snapshot.interactive_use,
        }

    @staticmethod
    def _execution_limits(config: DeliveryConfig) -> ResourceLimits:
        payload = config.resource_limits.to_dict() if config.resource_limits else {}
        payload.update({"maxFastJobs": config.max_fast_jobs, "maxHeavyJobs": config.max_heavy_jobs})
        return ResourceLimits.from_mapping(payload)

    @staticmethod
    def _coordinator_admission(configs: Any) -> dict[str, Any]:
        values = list(configs)
        return {
            "maxFastJobs": min(config.max_fast_jobs for config in values),
            "maxHeavyJobs": min(config.max_heavy_jobs for config in values),
            "pauseCpuPercent": min((config.resource_limits.pause_cpu_percent for config in values if config.resource_limits), default=80),
            "pauseMemoryPercent": min((config.resource_limits.pause_memory_percent for config in values if config.resource_limits), default=80),
            "minimumFreeDiskGiB": max((config.resource_limits.minimum_free_disk_gib for config in values if config.resource_limits), default=20),
        }

    def _lease_cancelled(self, lease: Any) -> bool:
        current = self.store.get(lease.job_id)
        return not current or current.get("status") != "running" or current.get("lease_id") != lease.lease_id

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
        return {"version": COORDINATOR_VERSION, "paused": self.paused, "repositories": self.registrations(), "workers": self.inspect_workers(), "jobs": self.store.list_jobs(), "alerts": self.store.alerts()}

    def service_once(self, *, execute: bool = False) -> dict[str, Any]:
        """Run one safe coordinator service pass.

        The launchd-facing command deliberately does not execute queued
        candidates by default.  It refreshes only the allowlisted repository
        observations and reports local state.  A missing credential (or any
        other GitHub fail-closed condition) is isolated to that repository so
        the local service remains healthy and available for ``status``.
        """
        # launchd deliberately keeps candidate execution opt-in, but its
        # regular observation pass is the local Mac Mini's liveness signal.
        # Without this refresh an otherwise healthy idle service ages its only
        # enabled worker offline and cannot accept the next eligible lease.
        try:
            self.workers.heartbeat("mac-mini-primary")
        except KeyError:
            # A registry with only remote workers must not manufacture a
            # privileged/local identity.
            pass

        polls: list[dict[str, Any]] = []
        for registration in self.registrations():
            repository = registration["repository"]
            try:
                polls.append(self.poll_once(repository))
            except GitHubError as exc:
                polls.append({"status": "failed-closed", "repository": repository, "reason": str(exc)})
        execution = self.run_next() if execute else {"status": "disabled-by-default"}
        return {"status": "healthy", "polls": polls, "execution": execution, "state": self.status()}

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
