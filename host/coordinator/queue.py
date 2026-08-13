"""Transactional queue and restart-safe coordinator state.

The queue is deliberately independent of GitHub and Docker.  It stores the
candidate identity as canonical JSON, so a commit SHA alone can never make a
job reusable.  All state changes which affect attempts happen in one SQLite
transaction.
"""

from __future__ import annotations

import hashlib
import json
import sqlite3
import threading
import time
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Optional


SCHEMA_VERSION = 3
MAX_ATTEMPTS = 2
_TERMINAL = {"completed", "failed", "cancelled", "stopped", "rejected"}
_ACTIVE = {"queued", "running"}


def _now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


def _candidate(value: Any) -> dict[str, Any]:
    if hasattr(value, "to_dict"):
        value = value.to_dict()
    if not isinstance(value, Mapping):
        raise ValueError("candidate identity must be an object")
    required = {"repository", "sourceSha", "gitTreeSha", "dependencyDigests", "testProfile"}
    if set(value) != required:
        raise ValueError("candidate identity fields are incomplete or unknown")
    result = dict(value)
    if not isinstance(result["repository"], str) or "/" not in result["repository"]:
        raise ValueError("candidate repository must be owner/name")
    for name in ("sourceSha", "gitTreeSha"):
        if not isinstance(result[name], str) or len(result[name]) != 40 or any(c not in "0123456789abcdef" for c in result[name]):
            raise ValueError("candidate SHA must be 40 lowercase hexadecimal characters")
    if result["testProfile"] not in {"fast", "full", "release"}:
        raise ValueError("candidate testProfile is invalid")
    if not isinstance(result["dependencyDigests"], Mapping):
        raise ValueError("candidate dependencyDigests must be an object")
    result["dependencyDigests"] = dict(sorted(result["dependencyDigests"].items()))
    return result


def candidate_key(value: Any) -> str:
    return hashlib.sha256(_json(_candidate(value)).encode("utf-8")).hexdigest()


def priority_for(gate: str, *, urgent: bool = False, active_phase: bool = False, cleanup: bool = False) -> int:
    if urgent:
        return 1
    if active_phase and gate == "fast-gate":
        return 2
    if gate in {"staging-gate", "release-gate"}:
        return 3
    if gate == "full-gate":
        return 4
    if cleanup:
        return 5
    return 4


@dataclass(frozen=True)
class QueueRequest:
    repository: str
    gate: str
    candidate_identity: Any
    priority: int = 4
    pr_number: Optional[int] = None
    phase_id: Optional[str] = None
    payload: Mapping[str, Any] = None
    urgent: bool = False

    def normalized(self) -> dict[str, Any]:
        candidate = _candidate(self.candidate_identity)
        if candidate["repository"] != self.repository:
            raise ValueError("request repository does not match candidate repository")
        if self.gate not in {"fast-gate", "full-gate", "staging-gate", "release-gate", "bugbot"}:
            raise ValueError("unknown gate")
        if not 1 <= int(self.priority) <= 5:
            raise ValueError("priority must be from 1 through 5")
        return {
            "repository": self.repository,
            "gate": self.gate,
            "candidate": candidate,
            "priority": int(self.priority),
            "pr_number": self.pr_number,
            "phase_id": self.phase_id,
            "payload": dict(self.payload or {}),
            "urgent": bool(self.urgent),
        }


@dataclass(frozen=True)
class QueueResult:
    accepted: bool
    job_id: str
    duplicate: bool = False
    message: str = ""

    @property
    def ok(self) -> bool:
        return self.accepted


class QueueStore:
    """A small SQLite state store with explicit migrations and scoped locks."""

    def __init__(self, path: str | Path = ":memory:") -> None:
        self.path = path if str(path) == ":memory:" else str(Path(path).expanduser())
        if self.path != ":memory:":
            Path(self.path).parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()
        self._connection = sqlite3.connect(self.path, check_same_thread=False, isolation_level=None)
        self._connection.row_factory = sqlite3.Row
        self._connection.execute("PRAGMA foreign_keys = ON")
        self._connection.execute("PRAGMA journal_mode = WAL")
        self._migrate()

    def close(self) -> None:
        with self._lock:
            self._connection.close()

    def _migrate(self) -> None:
        with self._lock:
            try:
                self._connection.execute("CREATE TABLE IF NOT EXISTS schema_migrations (version INTEGER PRIMARY KEY, applied_at TEXT NOT NULL)")
                current = self._connection.execute("SELECT COALESCE(MAX(version), 0) FROM schema_migrations").fetchone()[0]
                if current < 1:
                    self._connection.executescript(
                        """
                        BEGIN IMMEDIATE;
                        CREATE TABLE repositories (
                            repository TEXT PRIMARY KEY,
                            root TEXT NOT NULL,
                            default_branch TEXT NOT NULL,
                            allowlisted INTEGER NOT NULL DEFAULT 1,
                            paused INTEGER NOT NULL DEFAULT 0,
                            updated_at TEXT NOT NULL
                        );
                        CREATE TABLE jobs (
                            id TEXT PRIMARY KEY,
                            request_key TEXT NOT NULL UNIQUE,
                            repository TEXT NOT NULL,
                            gate TEXT NOT NULL,
                            candidate_json TEXT NOT NULL,
                            candidate_key TEXT NOT NULL,
                            priority INTEGER NOT NULL,
                            pr_number INTEGER,
                            phase_id TEXT,
                            payload_json TEXT NOT NULL,
                            status TEXT NOT NULL,
                            attempt_count INTEGER NOT NULL DEFAULT 0,
                            cancel_reason TEXT,
                            started_at TEXT,
                            completed_at TEXT,
                            result_json TEXT,
                            created_at TEXT NOT NULL,
                            updated_at TEXT NOT NULL
                        );
                        CREATE INDEX jobs_ready ON jobs(status, priority, created_at);
                        CREATE TABLE attempts (
                            job_id TEXT NOT NULL REFERENCES jobs(id),
                            attempt_number INTEGER NOT NULL,
                            status TEXT NOT NULL,
                            started_at TEXT NOT NULL,
                            completed_at TEXT,
                            result_json TEXT,
                            PRIMARY KEY(job_id, attempt_number)
                        );
                        CREATE TABLE alerts (
                            alert_key TEXT PRIMARY KEY,
                            repository TEXT NOT NULL,
                            gate TEXT NOT NULL,
                            candidate_key TEXT NOT NULL,
                            attempts INTEGER NOT NULL,
                            failure_category TEXT NOT NULL,
                            sanitized_result TEXT NOT NULL,
                            evidence_location TEXT NOT NULL,
                            required_action TEXT NOT NULL,
                            created_at TEXT NOT NULL,
                            updated_at TEXT NOT NULL
                        );
                        CREATE TABLE polls (
                            repository TEXT PRIMARY KEY,
                            etag TEXT,
                            failures INTEGER NOT NULL DEFAULT 0,
                            next_poll_at REAL NOT NULL DEFAULT 0,
                            last_status INTEGER,
                            last_error TEXT
                        );
                        CREATE TABLE approvals (
                            approval_key TEXT PRIMARY KEY,
                            binding_json TEXT NOT NULL,
                            approved_at TEXT NOT NULL
                        );
                        CREATE TABLE runtime (
                            key TEXT PRIMARY KEY,
                            value TEXT NOT NULL,
                            updated_at TEXT NOT NULL
                        );
                        INSERT INTO schema_migrations(version, applied_at) VALUES (1, datetime('now'));
                        COMMIT;
                        """
                    )
                    current = 1
                if current < 2:
                    self._connection.executescript(
                        """
                        BEGIN IMMEDIATE;
                        CREATE TABLE IF NOT EXISTS runtime (
                            key TEXT PRIMARY KEY,
                            value TEXT NOT NULL,
                            updated_at TEXT NOT NULL
                        );
                        INSERT INTO schema_migrations(version, applied_at) VALUES (2, datetime('now'));
                        COMMIT;
                        """
                    )
                    current = 2
                if current < 3:
                    self._connection.executescript(
                        """
                        BEGIN IMMEDIATE;
                        ALTER TABLE jobs ADD COLUMN required_capability TEXT NOT NULL DEFAULT 'fast';
                        ALTER TABLE jobs ADD COLUMN worker_id TEXT;
                        ALTER TABLE jobs ADD COLUMN lease_id TEXT;
                        ALTER TABLE jobs ADD COLUMN lease_expires_at REAL;
                        CREATE INDEX IF NOT EXISTS jobs_leases ON jobs(status, lease_expires_at);
                        UPDATE jobs
                        SET required_capability=CASE
                          WHEN json_extract(candidate_json, '$.testProfile') IN ('full','release') THEN 'heavy'
                          ELSE 'fast' END;
                        INSERT INTO schema_migrations(version, applied_at) VALUES (3, datetime('now'));
                        COMMIT;
                        """
                    )
            except Exception:
                if self._connection.in_transaction:
                    self._connection.execute("ROLLBACK")
                raise

    def register_repository(self, repository: str, root: str, default_branch: str = "development") -> None:
        if not repository or "/" not in repository or not default_branch:
            raise ValueError("repository registration is invalid")
        path = Path(root).expanduser().resolve()
        if not path.is_dir():
            raise ValueError("registered repository root must be a directory")
        with self._lock, self._connection:
            self._connection.execute(
                "INSERT INTO repositories(repository, root, default_branch, updated_at) VALUES(?,?,?,?) "
                "ON CONFLICT(repository) DO UPDATE SET root=excluded.root, default_branch=excluded.default_branch, allowlisted=1, updated_at=excluded.updated_at",
                (repository, str(path), default_branch, _now()),
            )

    def repository(self, repository: str) -> Optional[dict[str, Any]]:
        row = self._connection.execute("SELECT * FROM repositories WHERE repository=? AND allowlisted=1", (repository,)).fetchone()
        return dict(row) if row else None

    def enqueue(self, request: QueueRequest | Mapping[str, Any]) -> QueueResult:
        if isinstance(request, QueueRequest):
            data = request.normalized()
        else:
            data = QueueRequest(
                repository=str(request["repository"]), gate=str(request["gate"]),
                candidate_identity=request.get("candidate_identity", request.get("candidateIdentity", request.get("candidate"))),
                priority=int(request.get("priority", priority_for(str(request["gate"]))),),
                pr_number=request.get("pr_number", request.get("prNumber")), phase_id=request.get("phase_id", request.get("phaseId")),
                payload=request.get("payload", {}), urgent=bool(request.get("urgent", False)),
            ).normalized()
        key = data["repository"] + "|" + data["gate"] + "|" + candidate_key(data["candidate"])
        capability = str(data["payload"].get("requiredCapability") or ("fast" if data["candidate"]["testProfile"] == "fast" else "heavy"))
        if capability not in {"fast", "heavy", "nestedDocker"}:
            raise ValueError("requiredCapability must be fast, heavy, or nestedDocker")
        if capability == "nestedDocker" and data["payload"].get("nestedDocker") is not True:
            raise ValueError("nestedDocker capability must be explicitly requested")
        now = _now()
        job_id = "job-" + uuid.uuid4().hex
        with self._lock:
            self._connection.execute("BEGIN IMMEDIATE")
            try:
                existing = self._connection.execute("SELECT id, status FROM jobs WHERE request_key=?", (key,)).fetchone()
                if existing:
                    self._connection.execute("COMMIT")
                    return QueueResult(True, existing["id"], True, "duplicate request was ignored")
                self._connection.execute(
                    "INSERT INTO jobs(id, request_key, repository, gate, candidate_json, candidate_key, priority, pr_number, phase_id, payload_json, status, required_capability, created_at, updated_at) VALUES(?,?,?,?,?,?,?,?,?,?, 'queued', ?, ?, ?)",
                    (job_id, key, data["repository"], data["gate"], _json(data["candidate"]), candidate_key(data["candidate"]), data["priority"], data["pr_number"], data["phase_id"], _json(data["payload"]), capability, now, now),
                )
                self._connection.execute("COMMIT")
                return QueueResult(True, job_id, False, "queued")
            except Exception:
                self._connection.execute("ROLLBACK")
                raise

    def get(self, job_id: str) -> Optional[dict[str, Any]]:
        row = self._connection.execute("SELECT * FROM jobs WHERE id=?", (job_id,)).fetchone()
        return self._row(row) if row else None

    @staticmethod
    def _row(row: sqlite3.Row) -> dict[str, Any]:
        result = dict(row)
        result["candidate_identity"] = json.loads(result.pop("candidate_json"))
        result["payload"] = json.loads(result.pop("payload_json"))
        if result.get("result_json"):
            result["result"] = json.loads(result.pop("result_json"))
        else:
            result.pop("result_json", None)
        return result

    def list_jobs(self, *, statuses: Optional[set[str]] = None) -> list[dict[str, Any]]:
        rows = self._connection.execute("SELECT * FROM jobs ORDER BY created_at, id").fetchall()
        result = [self._row(row) for row in rows]
        return [item for item in result if statuses is None or item["status"] in statuses]

    def next_job(self) -> Optional[dict[str, Any]]:
        rows = self._connection.execute("SELECT * FROM jobs WHERE status='queued' ORDER BY priority, created_at, id").fetchall()
        if not rows:
            return None
        # Aging gives a background job a bounded wait while preserving the
        # frozen priority order for normal queues.
        now = time.time()
        def score(row: sqlite3.Row) -> tuple[int, str, str]:
            try:
                age = max(0, int(now - time.mktime(time.strptime(row["created_at"], "%Y-%m-%dT%H:%M:%SZ"))))
            except (TypeError, ValueError, OverflowError):
                age = 0
            return (max(1, int(row["priority"]) - age // 300), row["created_at"], row["id"])
        return self._row(min(rows, key=score))

    def mark_started(self, job_id: str) -> dict[str, Any]:
        now = _now()
        with self._lock:
            self._connection.execute("BEGIN IMMEDIATE")
            try:
                row = self._connection.execute("SELECT * FROM jobs WHERE id=?", (job_id,)).fetchone()
                if not row:
                    raise KeyError(job_id)
                if row["status"] == "cancelled":
                    self._connection.execute("COMMIT")
                    return {"started": False, "reason": "cancelled-before-start", "job": self._row(row)}
                if row["status"] != "queued":
                    self._connection.execute("COMMIT")
                    return {"started": False, "reason": "not-queued", "job": self._row(row)}
                attempt = int(row["attempt_count"]) + 1
                if attempt > MAX_ATTEMPTS:
                    self._connection.execute("UPDATE jobs SET status='stopped', updated_at=?, cancel_reason='attempt-limit' WHERE id=?", (now, job_id))
                    self._connection.execute("COMMIT")
                    return {"started": False, "reason": "attempt-limit", "job": self.get(job_id)}
                self._connection.execute("UPDATE jobs SET status='running', attempt_count=?, started_at=?, updated_at=? WHERE id=?", (attempt, now, now, job_id))
                self._connection.execute("INSERT INTO attempts(job_id, attempt_number, status, started_at) VALUES(?,?, 'running', ?)", (job_id, attempt, now))
                self._connection.execute("COMMIT")
                return {"started": True, "attempt": attempt, "job": self.get(job_id)}
            except Exception:
                self._connection.execute("ROLLBACK")
                raise

    def record_result(self, job_id: str, status: str, result: Mapping[str, Any] | None = None, *, failure_category: str = "execution", evidence_location: str = "", required_action: str = "Inspect sanitized evidence and correct the candidate.") -> dict[str, Any]:
        if status not in {"completed", "failed", "cancelled", "timed_out", "rejected"}:
            raise ValueError("invalid job result status")
        now = _now()
        result_data = dict(result or {})
        with self._lock:
            self._connection.execute("BEGIN IMMEDIATE")
            try:
                row = self._connection.execute("SELECT * FROM jobs WHERE id=?", (job_id,)).fetchone()
                if not row:
                    raise KeyError(job_id)
                attempt = int(row["attempt_count"])
                if attempt:
                    self._connection.execute("UPDATE attempts SET status=?, completed_at=?, result_json=? WHERE job_id=? AND attempt_number=?", (status, now, _json(result_data), job_id, attempt))
                job_status = "completed" if status == "completed" else "cancelled" if status == "cancelled" else "failed"
                if status == "rejected":
                    job_status = "rejected"
                alert = None
                if status not in {"completed", "cancelled"} and attempt >= MAX_ATTEMPTS:
                    job_status = "stopped"
                    alert = self._upsert_alert(row, failure_category, str(result_data.get("sanitized", result_data.get("error", "execution failed"))), evidence_location, required_action, now)
                elif status not in {"completed", "cancelled"} and attempt < MAX_ATTEMPTS:
                    job_status = "queued"
                self._connection.execute("UPDATE jobs SET status=?, completed_at=?, result_json=?, updated_at=? WHERE id=?", (job_status, now, _json(result_data), now, job_id))
                self._connection.execute("COMMIT")
                return {"job": self.get(job_id), "alert": alert}
            except Exception:
                self._connection.execute("ROLLBACK")
                raise

    def _upsert_alert(self, row: sqlite3.Row, category: str, sanitized: str, evidence: str, action: str, now: str) -> dict[str, Any]:
        key = row["repository"] + "|" + row["gate"] + "|" + row["candidate_key"]
        self._connection.execute(
            "INSERT INTO alerts(alert_key, repository, gate, candidate_key, attempts, failure_category, sanitized_result, evidence_location, required_action, created_at, updated_at) VALUES(?,?,?,?,?,?,?,?,?,?,?) ON CONFLICT(alert_key) DO UPDATE SET attempts=excluded.attempts, failure_category=excluded.failure_category, sanitized_result=excluded.sanitized_result, evidence_location=excluded.evidence_location, required_action=excluded.required_action, updated_at=excluded.updated_at",
            (key, row["repository"], row["gate"], row["candidate_key"], row["attempt_count"], category, sanitized[:20000], evidence[:1000], action[:1000], now, now),
        )
        alert = self._connection.execute("SELECT * FROM alerts WHERE alert_key=?", (key,)).fetchone()
        return dict(alert)

    def alerts(self) -> list[dict[str, Any]]:
        return [dict(row) for row in self._connection.execute("SELECT * FROM alerts ORDER BY created_at, alert_key")]

    def cancel_obsolete(self, repository: str, pr_number: Optional[int], live_identity: Any = None) -> list[str]:
        live_key = candidate_key(live_identity) if live_identity is not None else None
        params: list[Any] = [repository]
        clauses = ["repository=?", "status IN ('queued','running')"]
        if pr_number is not None:
            clauses.append("pr_number=?")
            params.append(pr_number)
        if live_key is not None:
            clauses.append("candidate_key<>?")
            params.append(live_key)
        query = "SELECT id FROM jobs WHERE " + " AND ".join(clauses)
        with self._lock, self._connection:
            ids = [row["id"] for row in self._connection.execute(query, params)]
            if ids:
                self._connection.executemany("UPDATE jobs SET status='cancelled', cancel_reason='obsolete-pr-or-identity', completed_at=?, updated_at=? WHERE id=?", [(_now(), _now(), job_id) for job_id in ids])
            return ids

    def recover(self) -> list[str]:
        """Mark jobs interrupted by restart; never invent an execution attempt."""
        with self._lock, self._connection:
            rows = self._connection.execute("SELECT id FROM jobs WHERE status='running'").fetchall()
            ids = [row["id"] for row in rows]
            if ids:
                self._connection.executemany("UPDATE jobs SET status='interrupted', updated_at=? WHERE id=?", [(_now(), job_id) for job_id in ids])
            return ids

    def recover_expired_leases(self, now: Optional[float] = None) -> list[str]:
        """Return expired worker leases to the queue without changing attempts.

        A lost worker is an assignment failure, not a new candidate attempt.
        The attempt row is marked ``lost`` and the same attempt number is
        reused by the next worker.  The old lease token is cleared, so a late
        result cannot commit duplicate execution.
        """
        now_value = time.time() if now is None else float(now)
        stamp = _now()
        with self._lock, self._connection:
            rows = self._connection.execute(
                "SELECT id, attempt_count FROM jobs WHERE status='running' AND lease_id IS NOT NULL AND lease_expires_at <= ?",
                (now_value,),
            ).fetchall()
            ids = [row["id"] for row in rows]
            for row in rows:
                if row["attempt_count"]:
                    self._connection.execute(
                        "UPDATE attempts SET status='lost', completed_at=? WHERE job_id=? AND attempt_number=? AND status='running'",
                        (stamp, row["id"], row["attempt_count"]),
                    )
            if ids:
                self._connection.executemany(
                    "UPDATE jobs SET status='queued', worker_id=NULL, lease_id=NULL, lease_expires_at=NULL, updated_at=? WHERE id=?",
                    [(stamp, job_id) for job_id in ids],
                )
            return ids

    def renew_lease(self, job_id: str, lease_id: str, worker_id: str, *, lease_seconds: int = 120, now: Optional[float] = None) -> bool:
        if not lease_id or not worker_id or int(lease_seconds) <= 0:
            raise ValueError("lease renewal requires a worker, lease, and positive duration")
        now_value = time.time() if now is None else float(now)
        with self._lock, self._connection:
            cursor = self._connection.execute(
                "UPDATE jobs SET lease_expires_at=?, updated_at=? WHERE id=? AND status='running' AND worker_id=? AND lease_id=? AND lease_expires_at > ?",
                (now_value + int(lease_seconds), _now(), job_id, worker_id, lease_id, now_value),
            )
            return cursor.rowcount == 1

    def claim_next(
        self,
        worker: Mapping[str, Any],
        *,
        snapshot: Optional[Mapping[str, Any]] = None,
        lease_seconds: int = 120,
        now: Optional[float] = None,
        admission_limits: Optional[Mapping[str, Any]] = None,
        allowed_repositories: Optional[set[str]] = None,
    ) -> Optional[dict[str, Any]]:
        """Atomically claim one eligible job for one isolated worker.

        Selection is global and fair: the highest-priority eligible band is
        selected, then repositories rotate within that band.  Capability,
        allowlist, coordinator-wide/per-worker concurrency, and host-pressure
        checks happen in the same transaction as the lease, preventing
        duplicate pickup. Admission limits are coordinator-owned; worker
        payloads cannot increase the global limits or pressure thresholds.
        """
        worker_id = str(worker.get("workerId", worker.get("worker_id", "")))
        capabilities = set(worker.get("capabilities", ()))
        repositories = set(worker.get("repositories", worker.get("repoAllowlist", ())) or ())
        if not worker_id or worker.get("trust") != "isolated-candidate" or worker.get("enabled") is False or worker.get("draining") is True or worker.get("offline") is True:
            return None
        now_value = time.time() if now is None else float(now)
        with self._lock:
            self._connection.execute("BEGIN IMMEDIATE")
            try:
                rows = self._connection.execute("SELECT * FROM jobs WHERE status='queued' ORDER BY priority, created_at, id").fetchall()
                active = self._connection.execute("SELECT required_capability, COUNT(*) AS count FROM jobs WHERE status='running' AND worker_id=? GROUP BY required_capability", (worker_id,)).fetchall()
                global_active = self._connection.execute("SELECT required_capability, COUNT(*) AS count FROM jobs WHERE status='running' GROUP BY required_capability").fetchall()
                active_counts = {row["required_capability"]: int(row["count"]) for row in active}
                global_counts = {row["required_capability"]: int(row["count"]) for row in global_active}
                active_heavy = sum(count for capability, count in active_counts.items() if capability != "fast")
                global_heavy = sum(count for capability, count in global_counts.items() if capability != "fast")
                fast_limit = int(worker.get("maxFastJobs", worker.get("max_fast_jobs", 0)))
                heavy_limit = int(worker.get("maxHeavyJobs", worker.get("max_heavy_jobs", 0)))
                limits = dict(admission_limits or {})
                nested_limits = limits.get("resourceLimits") if isinstance(limits.get("resourceLimits"), Mapping) else limits
                global_fast_limit = int(limits.get("maxFastJobs", limits.get("max_fast_jobs", 2)))
                global_heavy_limit = int(limits.get("maxHeavyJobs", limits.get("max_heavy_jobs", 1)))
                snapshot = snapshot or {}
                pressure = (
                    float(snapshot.get("cpuPercent", snapshot.get("cpu_percent", 0))) >= float(limits.get("pauseCpuPercent", limits.get("pause_cpu_percent", nested_limits.get("pauseCpuPercent", nested_limits.get("pause_cpu_percent", 80)))))
                    or float(snapshot.get("memoryPercent", snapshot.get("memory_percent", 0))) >= float(limits.get("pauseMemoryPercent", limits.get("pause_memory_percent", nested_limits.get("pauseMemoryPercent", nested_limits.get("pause_memory_percent", 80)))))
                    or float(snapshot.get("freeDiskGiB", snapshot.get("free_disk_gib", 100))) < float(limits.get("minimumFreeDiskGiB", limits.get("minimum_free_disk_gib", nested_limits.get("minimumFreeDiskGiB", nested_limits.get("minimum_free_disk_gib", 20)))))
                    or snapshot.get("dockerAvailable", snapshot.get("docker_available", True)) is False
                    or bool(snapshot.get("interactiveUse", snapshot.get("interactive_use", False)))
                )
                eligible = []
                for row in rows:
                    capability = row["required_capability"]
                    if capability not in capabilities or row["repository"] not in repositories:
                        continue
                    if allowed_repositories is not None and row["repository"] not in allowed_repositories:
                        continue
                    if capability == "fast" and active_counts.get("fast", 0) >= fast_limit:
                        continue
                    if capability != "fast" and active_heavy >= heavy_limit:
                        continue
                    if capability == "fast" and global_counts.get("fast", 0) >= global_fast_limit:
                        continue
                    if capability != "fast" and global_heavy >= global_heavy_limit:
                        continue
                    if pressure:
                        continue
                    eligible.append(row)
                if not eligible:
                    self._connection.execute("COMMIT")
                    return None
                minimum_priority = min(int(row["priority"]) for row in eligible)
                band = [row for row in eligible if int(row["priority"]) == minimum_priority]
                repositories_in_band = sorted({row["repository"] for row in band})
                cursor_value = self.runtime("fair_cursor", "") or ""
                ordered_repos = repositories_in_band
                if cursor_value in repositories_in_band:
                    index = repositories_in_band.index(cursor_value)
                    ordered_repos = repositories_in_band[index + 1:] + repositories_in_band[:index + 1]
                selected_repo = ordered_repos[0]
                row = next(item for item in band if item["repository"] == selected_repo)
                attempt = int(row["attempt_count"])
                previous = self._connection.execute("SELECT status FROM attempts WHERE job_id=? AND attempt_number=?", (row["id"], attempt)).fetchone() if attempt else None
                if not attempt or not previous or previous["status"] != "lost":
                    attempt += 1
                    if attempt > MAX_ATTEMPTS:
                        self._connection.execute("UPDATE jobs SET status='stopped', cancel_reason='attempt-limit', updated_at=? WHERE id=?", (_now(), row["id"]))
                        self._connection.execute("COMMIT")
                        return None
                    self._connection.execute("INSERT INTO attempts(job_id, attempt_number, status, started_at) VALUES(?,?, 'running', ?)", (row["id"], attempt, _now()))
                else:
                    self._connection.execute("UPDATE attempts SET status='running', completed_at=NULL, result_json=NULL, started_at=? WHERE job_id=? AND attempt_number=?", (_now(), row["id"], attempt))
                lease_id = "lease-" + uuid.uuid4().hex
                self._connection.execute(
                    "UPDATE jobs SET status='running', attempt_count=?, worker_id=?, lease_id=?, lease_expires_at=?, started_at=COALESCE(started_at, ?), updated_at=? WHERE id=?",
                    (attempt, worker_id, lease_id, now_value + int(lease_seconds), _now(), _now(), row["id"]),
                )
                self._connection.execute(
                    "INSERT INTO runtime(key, value, updated_at) VALUES('fair_cursor', ?, ?) ON CONFLICT(key) DO UPDATE SET value=excluded.value, updated_at=excluded.updated_at",
                    (selected_repo, _now()),
                )
                self._connection.execute("COMMIT")
                return dict(self._row(self._connection.execute("SELECT * FROM jobs WHERE id=?", (row["id"],)).fetchone()), leaseId=lease_id)
            except Exception:
                self._connection.execute("ROLLBACK")
                raise

    def record_lease_result(self, job_id: str, lease_id: str, worker_id: str, status: str, result: Optional[Mapping[str, Any]] = None, *, failure_category: str = "execution", evidence_location: str = "", required_action: str = "Inspect sanitized evidence and correct the candidate.") -> dict[str, Any]:
        """Commit a result only from the current lease owner, once."""
        if status not in {"completed", "failed", "cancelled", "timed_out", "rejected"}:
            raise ValueError("invalid job result status")
        with self._lock:
            row = self._connection.execute("SELECT * FROM jobs WHERE id=? AND status='running' AND worker_id=? AND lease_id=?", (job_id, worker_id, lease_id)).fetchone()
            if not row:
                raise ValueError("stale or duplicate lease result")
            result_data = dict(result or {})
            # Fence the lease before a result can make a failed attempt queued.
            # We keep the same lock and SQLite transaction boundary throughout.
            self._connection.execute("UPDATE jobs SET worker_id=NULL, lease_id=NULL, lease_expires_at=NULL WHERE id=?", (job_id,))
            final = self.record_result(job_id, status, result_data, failure_category=failure_category, evidence_location=evidence_location, required_action=required_action)
            return final

    def poll_state(self, repository: str) -> dict[str, Any]:
        row = self._connection.execute("SELECT * FROM polls WHERE repository=?", (repository,)).fetchone()
        if row:
            return dict(row)
        with self._lock, self._connection:
            self._connection.execute("INSERT OR IGNORE INTO polls(repository) VALUES(?)", (repository,))
        return dict(self._connection.execute("SELECT * FROM polls WHERE repository=?", (repository,)).fetchone())

    def update_poll(self, repository: str, *, etag: Optional[str] = None, failures: Optional[int] = None, next_poll_at: Optional[float] = None, last_status: Optional[int] = None, last_error: Optional[str] = None) -> None:
        current = self.poll_state(repository)
        with self._lock, self._connection:
            self._connection.execute("UPDATE polls SET etag=?, failures=?, next_poll_at=?, last_status=?, last_error=? WHERE repository=?", (etag if etag is not None else current["etag"], current["failures"] if failures is None else failures, current["next_poll_at"] if next_poll_at is None else next_poll_at, last_status if last_status is not None else current["last_status"], last_error, repository))

    def approve(self, approval_key: str, binding: Mapping[str, Any]) -> None:
        with self._lock, self._connection:
            self._connection.execute("INSERT OR REPLACE INTO approvals(approval_key, binding_json, approved_at) VALUES(?,?,?)", (approval_key, _json(dict(binding)), _now()))

    def approval(self, approval_key: str) -> Optional[dict[str, Any]]:
        row = self._connection.execute("SELECT * FROM approvals WHERE approval_key=?", (approval_key,)).fetchone()
        if not row:
            return None
        result = dict(row)
        result["binding"] = json.loads(result.pop("binding_json"))
        return result

    def set_runtime(self, key: str, value: str) -> None:
        if not key or not isinstance(value, str):
            raise ValueError("runtime state is invalid")
        with self._lock, self._connection:
            self._connection.execute("INSERT INTO runtime(key, value, updated_at) VALUES(?,?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value, updated_at=excluded.updated_at", (key, value, _now()))

    def runtime(self, key: str, default: Optional[str] = None) -> Optional[str]:
        row = self._connection.execute("SELECT value FROM runtime WHERE key=?", (key,)).fetchone()
        return row["value"] if row else default


_DEFAULT_STORE: Optional[QueueStore] = None


def configure_default_store(store: QueueStore) -> None:
    global _DEFAULT_STORE
    _DEFAULT_STORE = store


def _store() -> QueueStore:
    if _DEFAULT_STORE is None:
        raise RuntimeError("coordinator queue store is not configured")
    return _DEFAULT_STORE


def enqueue(request: QueueRequest | Mapping[str, Any]) -> QueueResult:
    return _store().enqueue(request)


def cancel_obsolete(repository: str, pr_number: Optional[int], live_identity: Any = None) -> list[str]:
    return _store().cancel_obsolete(repository, pr_number, live_identity)


__all__ = ["QueueRequest", "QueueResult", "QueueStore", "SCHEMA_VERSION", "candidate_key", "cancel_obsolete", "configure_default_store", "enqueue", "priority_for"]
