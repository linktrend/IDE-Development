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

    def __init__(self, database: str | Path = ":memory:", *, coordinator_id: str = "local-coordinator", coordinator_version: str = "2.2.0", store: Optional[QueueStore] = None, registry: Optional[WorkerRegistry] = None) -> None:
        self.store = store or QueueStore(database)
        self.registry = registry or WorkerRegistry(database)
        self.coordinator_id = coordinator_id
        self.coordinator_version = coordinator_version

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

    def claim(self, worker_id: str, *, snapshot: Optional[Mapping[str, Any]] = None, lease_seconds: int = 120, now: Optional[float] = None) -> Optional[Lease]:
        self.store.recover_expired_leases(now=now)
        worker = self.registry.get(worker_id, now=now)
        if worker is None:
            return None
        job = self.store.claim_next(worker.to_dict(), snapshot=snapshot, lease_seconds=lease_seconds, now=now)
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


__all__ = ["Lease", "MultiHostCoordinator"]
