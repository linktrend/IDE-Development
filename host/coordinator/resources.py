"""Admission control and host pressure modelling.

Admission is intentionally a pure decision.  It does not start a process,
inspect a candidate checkout, or call Docker.  That separation makes resource
limits testable and prevents a rejected candidate from consuming an attempt.
"""

from dataclasses import dataclass, field
from typing import Any, Iterable, Mapping, Optional, Tuple


def _value(value: Any, *names: str, default: Any = None) -> Any:
    if isinstance(value, Mapping):
        for name in names:
            if name in value:
                return value[name]
        return default
    for name in names:
        if hasattr(value, name):
            return getattr(value, name)
    return default


@dataclass(frozen=True)
class ResourceLimits:
    """Validated bounds used for both admission and Docker invocation."""

    max_fast_jobs: int = 2
    max_heavy_jobs: int = 1
    fast_cpus: float = 1.0
    fast_memory_mib: int = 2048
    heavy_cpus: float = 2.0
    heavy_memory_mib: int = 4096
    pids_limit: int = 768
    pause_cpu_percent: float = 80.0
    pause_memory_percent: float = 80.0
    minimum_free_disk_gib: float = 20.0
    docker_binary: str = "docker"
    default_timeout_seconds: int = 300
    fast_memory_swap_mib: Optional[int] = None
    heavy_memory_swap_mib: Optional[int] = None

    def __post_init__(self) -> None:
        if self.max_fast_jobs < 0 or self.max_heavy_jobs < 0:
            raise ValueError("job limits must be non-negative")
        if self.fast_cpus <= 0 or self.heavy_cpus <= 0:
            raise ValueError("CPU limits must be positive")
        if self.fast_memory_mib <= 0 or self.heavy_memory_mib <= 0:
            raise ValueError("memory limits must be positive")
        if self.pids_limit <= 0 or self.default_timeout_seconds <= 0:
            raise ValueError("PID and timeout limits must be positive")
        if not 0 < self.pause_cpu_percent <= 100:
            raise ValueError("pause_cpu_percent must be in (0, 100]")
        if not 0 < self.pause_memory_percent <= 100:
            raise ValueError("pause_memory_percent must be in (0, 100]")
        if self.minimum_free_disk_gib < 0:
            raise ValueError("minimum_free_disk_gib must be non-negative")
        if not self.docker_binary or any(ch.isspace() for ch in self.docker_binary):
            raise ValueError("docker_binary must be one executable token")

    @classmethod
    def from_mapping(cls, payload: Mapping[str, Any]) -> "ResourceLimits":
        """Load frozen-interface camelCase or Python-style resource keys."""

        nested = payload.get("resourceLimits") if isinstance(payload, Mapping) else None
        if isinstance(nested, Mapping):
            payload = nested

        def get(*names: str, default: Any = None) -> Any:
            return _value(payload, *names, default=default)

        return cls(
            max_fast_jobs=int(get("max_fast_jobs", "maxFastJobs", default=2)),
            max_heavy_jobs=int(get("max_heavy_jobs", "maxHeavyJobs", default=1)),
            fast_cpus=float(get("fast_cpus", "fastCpus", default=1.0)),
            fast_memory_mib=int(get("fast_memory_mib", "fastMemoryMiB", default=2048)),
            heavy_cpus=float(get("heavy_cpus", "heavyCpus", default=2.0)),
            heavy_memory_mib=int(get("heavy_memory_mib", "heavyMemoryMiB", default=4096)),
            pids_limit=int(get("pids_limit", "pidsLimit", default=768)),
            pause_cpu_percent=float(get("pause_cpu_percent", "pauseCpuPercent", default=80)),
            pause_memory_percent=float(get("pause_memory_percent", "pauseMemoryPercent", default=80)),
            minimum_free_disk_gib=float(
                get("minimum_free_disk_gib", "minimumFreeDiskGiB", default=20)
            ),
            docker_binary=str(get("docker_binary", "dockerBinary", default="docker")),
            default_timeout_seconds=int(
                get("default_timeout_seconds", "defaultTimeoutSeconds", default=300)
            ),
            fast_memory_swap_mib=(
                int(get("fast_memory_swap_mib", "fastMemorySwapMiB"))
                if get("fast_memory_swap_mib", "fastMemorySwapMiB") is not None
                else None
            ),
            heavy_memory_swap_mib=(
                int(get("heavy_memory_swap_mib", "heavyMemorySwapMiB"))
                if get("heavy_memory_swap_mib", "heavyMemorySwapMiB") is not None
                else None
            ),
        )

    def limits_for(self, profile: str) -> Tuple[float, int, int]:
        if profile == "fast":
            memory = self.fast_memory_mib
            swap = self.fast_memory_swap_mib or memory * 2
            return self.fast_cpus, memory, swap
        memory = self.heavy_memory_mib
        swap = self.heavy_memory_swap_mib or memory * 2
        return self.heavy_cpus, memory, swap


@dataclass(frozen=True)
class HostSnapshot:
    """Point-in-time host facts supplied by the coordinator sampler."""

    cpu_percent: float = 0.0
    memory_percent: float = 0.0
    free_disk_gib: float = 100.0
    docker_available: bool = True
    interactive_use: bool = False

    @classmethod
    def from_mapping(cls, payload: Mapping[str, Any]) -> "HostSnapshot":
        return cls(
            cpu_percent=float(_value(payload, "cpu_percent", "cpuPercent", default=0)),
            memory_percent=float(_value(payload, "memory_percent", "memoryPercent", default=0)),
            free_disk_gib=float(_value(payload, "free_disk_gib", "freeDiskGiB", default=100)),
            docker_available=bool(
                _value(payload, "docker_available", "dockerAvailable", default=True)
            ),
            interactive_use=bool(
                _value(payload, "interactive_use", "interactiveUse", default=False)
            ),
        )


@dataclass(frozen=True)
class AdmissionVerdict:
    admitted: bool
    reason: str
    job_class: str
    fast_running: int = 0
    heavy_running: int = 0
    pressure_reasons: Tuple[str, ...] = field(default_factory=tuple)

    @property
    def allowed(self) -> bool:
        """Compatibility spelling for callers that use an allow/deny verdict."""

        return self.admitted


def _job_profile(job: Any) -> str:
    profile = _value(job, "test_profile", "testProfile", "profile", default="fast")
    profile = str(profile).lower()
    if profile not in ("fast", "full", "release"):
        raise ValueError("test_profile must be fast, full, or release")
    return profile


def _is_active(job: Any) -> bool:
    status = str(_value(job, "status", "state", default="running")).lower()
    return status not in {"completed", "passed", "failed", "cancelled", "timed_out", "obsolete"}


def _pressure(snapshot: HostSnapshot, limits: ResourceLimits) -> Tuple[str, ...]:
    reasons = []
    if snapshot.cpu_percent >= limits.pause_cpu_percent:
        reasons.append("cpu_pressure")
    if snapshot.memory_percent >= limits.pause_memory_percent:
        reasons.append("memory_pressure")
    if snapshot.free_disk_gib < limits.minimum_free_disk_gib:
        reasons.append("disk_pressure")
    if not snapshot.docker_available:
        reasons.append("docker_unavailable")
    if snapshot.interactive_use:
        reasons.append("interactive_use")
    return tuple(reasons)


def admit_job(request: Any, host_snapshot: Any, running_jobs: Iterable[Any], limits: Any = None) -> AdmissionVerdict:
    """Return an admission decision without starting candidate execution.

    ``limits`` may be a :class:`ResourceLimits` or the resourceLimits mapping
    from the frozen delivery configuration.  Heavy means full or release.
    """

    limits = limits if isinstance(limits, ResourceLimits) else ResourceLimits.from_mapping(limits or {})
    snapshot = host_snapshot if isinstance(host_snapshot, HostSnapshot) else HostSnapshot.from_mapping(host_snapshot or {})
    profile = _job_profile(request)
    job_class = "fast" if profile == "fast" else "heavy"
    active = [job for job in running_jobs if _is_active(job)]
    fast_running = sum(_job_profile(job) == "fast" for job in active)
    heavy_running = sum(_job_profile(job) != "fast" for job in active)
    pressure = _pressure(snapshot, limits)
    if pressure:
        return AdmissionVerdict(False, "host_pressure", job_class, fast_running, heavy_running, pressure)
    if job_class == "fast" and fast_running >= limits.max_fast_jobs:
        return AdmissionVerdict(False, "fast_capacity_exhausted", job_class, fast_running, heavy_running)
    if job_class == "heavy" and heavy_running >= limits.max_heavy_jobs:
        return AdmissionVerdict(False, "heavy_capacity_exhausted", job_class, fast_running, heavy_running)
    return AdmissionVerdict(True, "admitted", job_class, fast_running, heavy_running)
