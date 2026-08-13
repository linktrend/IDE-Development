"""Host-only bounded execution primitives for the local coordinator.

This package deliberately contains no GitHub, workflow, or promotion code.  It
is the host boundary: admission is evaluated first and candidate code is then
run only as an explicitly-scoped disposable Linux container.
"""

from .cleanup import CleanupResult, cleanup_job, recover_orphans
from .executor import (
    ExecutionResult,
    Job,
    build_docker_invocation,
    run_job,
    sanitize_output,
)
from .resources import (
    AdmissionVerdict,
    HostSnapshot,
    ResourceLimits,
    admit_job,
)
from .multihost import CoordinatorAdmissionConfig, Lease, MultiHostCoordinator
from .workers import Worker, WorkerRegistry

__all__ = [
    "AdmissionVerdict",
    "CleanupResult",
    "ExecutionResult",
    "HostSnapshot",
    "Job",
    "ResourceLimits",
    "admit_job",
    "build_docker_invocation",
    "cleanup_job",
    "recover_orphans",
    "run_job",
    "sanitize_output",
    "Lease",
    "CoordinatorAdmissionConfig",
    "MultiHostCoordinator",
    "Worker",
    "WorkerRegistry",
]
