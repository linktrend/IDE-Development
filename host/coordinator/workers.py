"""Durable, fail-closed registry for isolated candidate workers.

The registry describes capacity and reachability only.  It never grants a
worker GitHub, repository, host, or coordinator authority.  In particular,
``privileged-coordinator`` and equivalent trust claims are rejected at
registration, including for VPS/Linux workers.
"""

from __future__ import annotations

import json
import sqlite3
import threading
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Optional


CAPABILITIES = frozenset({"fast", "heavy", "nestedDocker"})
TRUST = "isolated-candidate"
STATUSES = frozenset({"enabled", "draining", "offline", "disabled"})


def _now() -> float:
    return time.time()


@dataclass(frozen=True)
class Worker:
    worker_id: str
    platform: str
    arch: str
    trust: str = TRUST
    capabilities: frozenset[str] = frozenset({"fast"})
    max_fast_jobs: int = 1
    max_heavy_jobs: int = 0
    cpu_limit: float = 1.0
    memory_mib: int = 2048
    pids_limit: int = 768
    heartbeat_interval_seconds: int = 30
    last_heartbeat: float = 0.0
    enabled: bool = True
    draining: bool = False
    offline: bool = False
    repositories: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.worker_id or any(ch.isspace() for ch in self.worker_id) or len(self.worker_id) > 128:
            raise ValueError("worker_id must be a stable non-empty token")
        if self.platform not in {"macos", "linux"} or not self.arch or "/" in self.arch:
            raise ValueError("worker platform or architecture is invalid")
        if not isinstance(self.trust, str) or self.trust != TRUST or self.trust.lower() in {"privileged", "coordinator", "admin", "root"}:
            raise ValueError("privileged or non-isolated worker trust is not registerable")
        if not self.capabilities or not set(self.capabilities).issubset(CAPABILITIES):
            raise ValueError("worker capabilities must be fast, heavy, or explicit nestedDocker")
        if self.max_fast_jobs < 0 or self.max_heavy_jobs < 0 or self.cpu_limit <= 0 or self.memory_mib <= 0 or self.pids_limit <= 0:
            raise ValueError("worker resource limits must be positive")
        if self.heartbeat_interval_seconds <= 0:
            raise ValueError("heartbeat interval must be positive")
        if any(not isinstance(repo, str) or "/" not in repo for repo in self.repositories):
            raise ValueError("worker repository allowlist must contain owner/name values")

    @property
    def status(self) -> str:
        if not self.enabled:
            return "disabled"
        if self.offline:
            return "offline"
        if self.draining:
            return "draining"
        return "enabled"

    def is_heartbeat_fresh(self, now: Optional[float] = None) -> bool:
        return self.last_heartbeat > 0 and (_now() if now is None else now) - self.last_heartbeat <= self.heartbeat_interval_seconds * 3

    def to_dict(self) -> dict[str, Any]:
        return {
            "workerId": self.worker_id,
            "platform": self.platform,
            "arch": self.arch,
            "trust": self.trust,
            "capabilities": sorted(self.capabilities),
            "maxFastJobs": self.max_fast_jobs,
            "maxHeavyJobs": self.max_heavy_jobs,
            "cpuLimit": self.cpu_limit,
            "memoryMiB": self.memory_mib,
            "pidsLimit": self.pids_limit,
            "resourceLimits": {"cpus": self.cpu_limit, "memoryMiB": self.memory_mib, "pidsLimit": self.pids_limit},
            "heartbeatIntervalSeconds": self.heartbeat_interval_seconds,
            "lastHeartbeat": self.last_heartbeat,
            "enabled": self.enabled,
            "draining": self.draining,
            "offline": self.offline,
            "status": self.status,
            "repositories": list(self.repositories),
        }

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> "Worker":
        data = dict(value)
        limits = data.get("resourceLimits") if isinstance(data.get("resourceLimits"), Mapping) else {}
        # A role is deliberately not silently translated into trust.
        role = str(data.get("role", ""))
        if role and role not in {"isolated-candidate", "candidate"}:
            raise ValueError("worker role cannot grant privileged coordinator authority")
        return cls(
            worker_id=str(data.get("workerId", data.get("worker_id", ""))),
            platform=str(data.get("platform", "")),
            arch=str(data.get("arch", "")),
            trust=str(data.get("trust", TRUST)),
            capabilities=frozenset(data.get("capabilities", ())),
            max_fast_jobs=int(data.get("maxFastJobs", data.get("max_fast_jobs", 1))),
            max_heavy_jobs=int(data.get("maxHeavyJobs", data.get("max_heavy_jobs", 0))),
            cpu_limit=float(data.get("cpuLimit", data.get("cpu_limit", limits.get("cpus", 1.0)))),
            memory_mib=int(data.get("memoryMiB", data.get("memory_mib", limits.get("memoryMiB", 2048)))),
            pids_limit=int(data.get("pidsLimit", data.get("pids_limit", limits.get("pidsLimit", 768)))),
            heartbeat_interval_seconds=int(data.get("heartbeatIntervalSeconds", data.get("heartbeat_interval_seconds", 30))),
            last_heartbeat=float(data.get("lastHeartbeat", data.get("last_heartbeat", 0.0))),
            enabled=bool(data.get("enabled", True)),
            draining=bool(data.get("draining", False)),
            offline=bool(data.get("offline", False)),
            repositories=tuple(sorted(set(data.get("repositories", data.get("repoAllowlist", ())) or ()))),
        )


class WorkerRegistry:
    """SQLite-backed worker registry with safe lifecycle commands."""

    def __init__(self, path: str | Path = ":memory:") -> None:
        self.path = str(path) if str(path) == ":memory:" else str(Path(path).expanduser())
        if self.path != ":memory:":
            Path(self.path).parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()
        self._db = sqlite3.connect(self.path, check_same_thread=False, isolation_level=None)
        self._db.row_factory = sqlite3.Row
        self._db.execute("PRAGMA journal_mode=WAL")
        self._db.execute(
            """CREATE TABLE IF NOT EXISTS workers (
                worker_id TEXT PRIMARY KEY, payload TEXT NOT NULL,
                registered_at REAL NOT NULL, updated_at REAL NOT NULL
            )"""
        )

    def close(self) -> None:
        with self._lock:
            self._db.close()

    def register(self, worker: Worker | Mapping[str, Any]) -> Worker:
        candidate = worker if isinstance(worker, Worker) else Worker.from_mapping(worker)
        if candidate.trust != TRUST:
            raise ValueError("candidate workers cannot register privileged trust")
        with self._lock, self._db:
            old = self.get(candidate.worker_id)
            registered_at = stamp = _now()
            if old:
                registered_at_row = self._db.execute("SELECT registered_at FROM workers WHERE worker_id=?", (candidate.worker_id,)).fetchone()
                registered_at = float(registered_at_row[0]) if registered_at_row else stamp
            if old and (old.platform != candidate.platform or old.arch != candidate.arch or old.trust != candidate.trust):
                raise ValueError("stable worker identity cannot change platform, architecture, or trust")
            self._db.execute(
                "INSERT INTO workers(worker_id, payload, registered_at, updated_at) VALUES(?,?,?,?) ON CONFLICT(worker_id) DO UPDATE SET payload=excluded.payload, updated_at=excluded.updated_at",
                (candidate.worker_id, json.dumps(candidate.to_dict(), sort_keys=True), registered_at, stamp),
            )
        return candidate

    def get(self, worker_id: str, *, now: Optional[float] = None) -> Optional[Worker]:
        row = self._db.execute("SELECT payload FROM workers WHERE worker_id=?", (worker_id,)).fetchone()
        if not row:
            return None
        worker = Worker.from_mapping(json.loads(row["payload"]))
        if worker.enabled and not worker.offline and not worker.is_heartbeat_fresh(now):
            worker = Worker.from_mapping({**worker.to_dict(), "offline": True})
        return worker

    def list(self, *, now: Optional[float] = None) -> list[Worker]:
        rows = self._db.execute("SELECT worker_id FROM workers ORDER BY worker_id").fetchall()
        result: list[Worker] = []
        for row in rows:
            worker = self.get(row["worker_id"], now=now)
            if worker is not None:
                result.append(worker)
        return result

    def heartbeat(self, worker_id: str, *, now: Optional[float] = None) -> Worker:
        worker = self.get(worker_id, now=now)
        if worker is None:
            raise KeyError(worker_id)
        stamp = _now() if now is None else float(now)
        refreshed = Worker.from_mapping({**worker.to_dict(), "lastHeartbeat": stamp, "offline": False})
        with self._lock, self._db:
            self._db.execute("UPDATE workers SET payload=?, updated_at=? WHERE worker_id=?", (json.dumps(refreshed.to_dict(), sort_keys=True), stamp, worker_id))
        return refreshed

    def _change(self, worker_id: str, **changes: Any) -> Worker:
        worker = self.get(worker_id)
        if worker is None:
            raise KeyError(worker_id)
        updated = Worker.from_mapping({**worker.to_dict(), **changes})
        with self._lock, self._db:
            self._db.execute("UPDATE workers SET payload=?, updated_at=? WHERE worker_id=?", (json.dumps(updated.to_dict(), sort_keys=True), _now(), worker_id))
        return updated

    def enable(self, worker_id: str) -> Worker:
        return self._change(worker_id, enabled=True, draining=False, offline=False)

    def disable(self, worker_id: str) -> Worker:
        return self._change(worker_id, enabled=False, draining=False)

    def drain(self, worker_id: str) -> Worker:
        return self._change(worker_id, draining=True)

    def mark_offline(self, worker_id: str) -> Worker:
        return self._change(worker_id, offline=True)

    def remove(self, worker_id: str) -> bool:
        with self._lock, self._db:
            return self._db.execute("DELETE FROM workers WHERE worker_id=?", (worker_id,)).rowcount == 1

    def inspect(self, worker_id: Optional[str] = None) -> list[dict[str, Any]]:
        values = [self.get(worker_id)] if worker_id else self.list()
        return [worker.to_dict() for worker in values if worker is not None]


def current_mac_mini_fixture() -> dict[str, Any]:
    """The current production fixture: one enabled Mac Mini worker only."""
    return Worker(
        worker_id="mac-mini-primary", platform="macos", arch="arm64",
        trust=TRUST, capabilities=frozenset({"fast", "heavy"}),
        max_fast_jobs=2, max_heavy_jobs=1, cpu_limit=4.0, memory_mib=8192,
        repositories=("linktrend/IDE-Development",), last_heartbeat=_now(),
    ).to_dict()


__all__ = ["CAPABILITIES", "STATUSES", "TRUST", "Worker", "WorkerRegistry", "current_mac_mini_fixture"]
