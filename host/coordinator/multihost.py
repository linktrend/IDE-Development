"""Central multi-host queue facade.

This module is the coordinator-owned control plane.  Workers pull leases from
one queue; they do not create peer queues or decide policy.  Candidate identity
and the global attempt number remain in the central SQLite store when a lease
expires and another isolated worker takes over.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Optional

from .queue import QueueRequest, QueueResult, QueueStore
from .workers import Worker, WorkerRegistry


@dataclass(frozen=True)
class CoordinatorAdmissionConfig:
    """Immutable coordinator-owned global admission policy.

    The hard ceilings are deliberately part of the coordinator contract:
    registrations may advertise less capacity, but can never raise these
    limits or change the pressure gates.
    """

    max_fast_jobs: int = 2
    max_heavy_jobs: int = 1
    pause_cpu_percent: float = 80.0
    pause_memory_percent: float = 80.0
    minimum_free_disk_gib: float = 20.0

    def __post_init__(self) -> None:
        if not 0 <= self.max_fast_jobs <= 2:
            raise ValueError("coordinator max_fast_jobs must be from 0 through 2")
        if not 0 <= self.max_heavy_jobs <= 1:
            raise ValueError("coordinator max_heavy_jobs must be from 0 through 1")
        if not 0 < self.pause_cpu_percent <= 100 or not 0 < self.pause_memory_percent <= 100:
            raise ValueError("coordinator pressure thresholds must be in (0, 100]")
        if self.minimum_free_disk_gib < 0:
            raise ValueError("coordinator minimum free disk must be non-negative")

    @classmethod
    def from_mapping(cls, value: Any = None) -> "CoordinatorAdmissionConfig":
        if value is None:
            return cls()
        if isinstance(value, cls):
            return value
        if isinstance(value, Mapping):
            nested = value.get("resourceLimits") if isinstance(value.get("resourceLimits"), Mapping) else value
            def read(*names: str, default: Any) -> Any:
                for name in names:
                    if name in value:
                        return value[name]
                    if name in nested:
                        return nested[name]
                return default
            return cls(
                max_fast_jobs=int(read("maxFastJobs", "max_fast_jobs", default=2)),
                max_heavy_jobs=int(read("maxHeavyJobs", "max_heavy_jobs", default=1)),
                pause_cpu_percent=float(read("pauseCpuPercent", "pause_cpu_percent", default=80)),
                pause_memory_percent=float(read("pauseMemoryPercent", "pause_memory_percent", default=80)),
                minimum_free_disk_gib=float(read("minimumFreeDiskGiB", "minimum_free_disk_gib", default=20)),
            )
        raise TypeError("coordinator admission config must be a mapping")

    def to_mapping(self) -> dict[str, Any]:
        return {
            "maxFastJobs": self.max_fast_jobs,
            "maxHeavyJobs": self.max_heavy_jobs,
            "pauseCpuPercent": self.pause_cpu_percent,
            "pauseMemoryPercent": self.pause_memory_percent,
            "minimumFreeDiskGiB": self.minimum_free_disk_gib,
        }


@dataclass(frozen=True)
class Lease:
    job_id: str
    lease_id: str
    worker_id: str
    attempt: int
    candidate_identity: Mapping[str, Any]
    capability: str
    expires_at: float

    @classmethod
    def from_job(cls, job: Mapping[str, Any]) -> "Lease":
        return cls(
            job_id=str(job["id"]), lease_id=str(job["leaseId"]), worker_id=str(job["worker_id"]),
            attempt=int(job["attempt_count"]), candidate_identity=dict(job["candidate_identity"]),
            capability=str(job["required_capability"]), expires_at=float(job["lease_expires_at"]),
        )


class MultiHostCoordinator:
    """Coordinate multiple unprivileged candidate workers through one queue."""

    def __init__(self, database: str | Path = ":memory:", *, coordinator_id: str = "local-coordinator", coordinator_version: str = "2.3.0", store: Optional[QueueStore] = None, registry: Optional[WorkerRegistry] = None, admission_config: CoordinatorAdmissionConfig | Mapping[str, Any] | None = None) -> None:
        self.store = store or QueueStore(database)
        self.registry = registry or WorkerRegistry(database)
        self.coordinator_id = coordinator_id
        self.coordinator_version = coordinator_version
        self.admission_config = CoordinatorAdmissionConfig.from_mapping(admission_config)

    def close(self) -> None:
        self.registry.close()
        if self.store is not None:
            self.store.close()

    def register_worker(self, worker: Worker | Mapping[str, Any]) -> Worker:
        return self.registry.register(worker)

    def heartbeat(self, worker_id: str, *, now: Optional[float] = None) -> Worker:
        return self.registry.heartbeat(worker_id, now=now)

    def enqueue(self, request: QueueRequest | Mapping[str, Any]) -> QueueResult:
        return self.store.enqueue(request)

    def claim(
        self,
        worker_id: str,
        *,
        snapshot: Optional[Mapping[str, Any]] = None,
        lease_seconds: int = 120,
        now: Optional[float] = None,
        admission_limits: Optional[Mapping[str, Any]] = None,
        allowed_repositories: Optional[set[str]] = None,
    ) -> Optional[Lease]:
        self.store.recover_expired_leases(now=now)
        worker = self.registry.get(worker_id, now=now)
        if worker is None:
            return None
        policy = CoordinatorAdmissionConfig.from_mapping(admission_limits) if admission_limits is not None else self.admission_config
        effective = CoordinatorAdmissionConfig(
            max_fast_jobs=min(self.admission_config.max_fast_jobs, policy.max_fast_jobs),
            max_heavy_jobs=min(self.admission_config.max_heavy_jobs, policy.max_heavy_jobs),
            pause_cpu_percent=min(self.admission_config.pause_cpu_percent, policy.pause_cpu_percent),
            pause_memory_percent=min(self.admission_config.pause_memory_percent, policy.pause_memory_percent),
            minimum_free_disk_gib=max(self.admission_config.minimum_free_disk_gib, policy.minimum_free_disk_gib),
        )
        job = self.store.claim_next(
            worker.to_dict(), snapshot=snapshot, lease_seconds=lease_seconds, now=now,
            admission_limits=effective.to_mapping(), allowed_repositories=allowed_repositories,
        )
        return Lease.from_job(job) if job else None

    def renew(self, lease: Lease | Mapping[str, Any], *, lease_seconds: int = 120, now: Optional[float] = None) -> bool:
        if isinstance(lease, Lease):
            job_id, lease_id, worker_id = lease.job_id, lease.lease_id, lease.worker_id
        else:
            job_id = str(lease.get("jobId", lease.get("job_id")))
            lease_id = str(lease.get("leaseId", lease.get("lease_id")))
            worker_id = str(lease.get("workerId", lease.get("worker_id")))
        return self.store.renew_lease(job_id, lease_id, worker_id, lease_seconds=lease_seconds, now=now)

    def complete(self, lease: Lease | Mapping[str, Any], status: str, result: Optional[Mapping[str, Any]] = None) -> dict[str, Any]:
        if isinstance(lease, Lease):
            job_id, lease_id, worker_id = lease.job_id, lease.lease_id, lease.worker_id
        else:
            job_id, lease_id, worker_id = str(lease["jobId"]), str(lease["leaseId"]), str(lease["workerId"])
        return self.store.record_lease_result(job_id, lease_id, worker_id, status, result)

    def receipt_metadata(self, lease: Lease, *, execution_environment: Mapping[str, Any]) -> dict[str, Any]:
        """Return the W4 provenance fields callers add before ``write_receipt``."""
        worker = self.registry.get(lease.worker_id)
        if worker is None:
            raise ValueError("receipt worker no longer exists")
        return {
            "workerId": worker.worker_id,
            "workerCapabilities": sorted(worker.capabilities),
            "workerTrust": worker.trust,
            "coordinatorIdentity": self.coordinator_id,
            "coordinatorVersion": self.coordinator_version,
            "executionEnvironment": dict(execution_environment),
        }

    def recover_lost_workers(self, *, now: Optional[float] = None) -> list[str]:
        return self.store.recover_expired_leases(now=now)

    def inspect(self) -> dict[str, Any]:
        return {
            "coordinatorId": self.coordinator_id,
            "coordinatorVersion": self.coordinator_version,
            "workers": self.registry.inspect(),
            "jobs": self.store.list_jobs(),
        }


__all__ = ["CoordinatorAdmissionConfig", "Lease", "MultiHostCoordinator"]
