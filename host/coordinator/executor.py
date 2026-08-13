"""Disposable Linux-container executor for untrusted candidate commands."""

import re
import subprocess
import time
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Mapping, Optional, Sequence, Tuple

from .cleanup import cleanup_job, register_job
from .resources import ResourceLimits


_JOB_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.:-]{0,127}$")
_IMAGE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9./_:@+-]{0,254}$")
_CONTAINER_NAME = re.compile(r"^linktrend-coordinator-[A-Za-z0-9][A-Za-z0-9_.-]{0,100}$")
_TARGET = re.compile(r"^/[A-Za-z0-9][A-Za-z0-9_.-]*(?:/[A-Za-z0-9][A-Za-z0-9_.-]*)*$")


def _get(value: Any, *names: str, default: Any = None) -> Any:
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
class Job:
    """A complete, identity-bound execution request.

    ``command`` is a sequence of arguments, never a shell string.  A temporary
    checkout is removed only when the caller explicitly marks it as owned.
    """

    job_id: str
    checkout_path: str
    image: str
    command: Tuple[str, ...]
    test_profile: str = "fast"
    timeout_seconds: int = 300
    container_name: Optional[str] = None
    workspace_root: Optional[str] = None
    workdir: str = "/workspace"
    temporary_checkout: bool = False
    volumes: Tuple[Any, ...] = ()
    nested_docker: bool = False
    protected_nested_config: Optional[Mapping[str, Any]] = None
    repository: str = ""

    def __post_init__(self) -> None:
        if not _JOB_ID.fullmatch(self.job_id):
            raise ValueError("job_id is not a safe identity")
        if self.test_profile not in ("fast", "full", "release"):
            raise ValueError("test_profile must be fast, full, or release")
        if not self.command or isinstance(self.command, str):
            raise ValueError("command must be a non-empty argument sequence")
        if any(not isinstance(arg, str) or "\x00" in arg for arg in self.command):
            raise ValueError("command arguments must be NUL-free strings")
        if self.timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be positive")


@dataclass(frozen=True)
class ExecutionResult:
    status: str
    job_id: str
    exit_code: Optional[int]
    started_at: Optional[str]
    completed_at: str
    container_name: str
    docker_argv: Tuple[str, ...] = ()
    stdout: str = ""
    stderr: str = ""
    cleanup: Any = None
    error: Optional[str] = None

    @property
    def passed(self) -> bool:
        return self.status == "passed"


def _job(value: Any) -> Job:
    if isinstance(value, Job):
        return value
    command = _get(value, "command", "candidate_command")
    if isinstance(command, str):
        raise ValueError("candidate command must not be a shell string")
    return Job(
        job_id=str(_get(value, "job_id", "jobId")),
        checkout_path=str(_get(value, "checkout_path", "checkoutPath")),
        image=str(_get(value, "image", default="alpine:3.20")),
        command=tuple(command or ()),
        test_profile=str(_get(value, "test_profile", "testProfile", default="fast")),
        timeout_seconds=int(_get(value, "timeout_seconds", "timeoutSeconds", default=300)),
        container_name=_get(value, "container_name", "containerName"),
        workspace_root=_get(value, "workspace_root", "workspaceRoot"),
        workdir=str(_get(value, "workdir", "working_directory", default="/workspace")),
        temporary_checkout=bool(_get(value, "temporary_checkout", "temporaryCheckout", default=False)),
        volumes=tuple(_get(value, "volumes", default=()) or ()),
        nested_docker=bool(_get(value, "nested_docker", "nestedDocker", default=False)),
        protected_nested_config=_get(value, "protected_nested_config", "protectedNestedConfig"),
        repository=str(_get(value, "repository", default="")),
    )


def _safe_checkout(path_value: str, workspace_root: Optional[str]) -> Path:
    path = Path(path_value).expanduser()
    if not path.is_absolute():
        raise ValueError("checkout must be absolute")
    try:
        resolved = path.resolve(strict=True)
    except FileNotFoundError as exc:
        raise ValueError("checkout does not exist") from exc
    if not resolved.is_dir() or resolved == Path(resolved.anchor):
        raise ValueError("checkout must be a non-root directory")
    if workspace_root is not None:
        root = Path(str(workspace_root)).expanduser()
        if not root.is_absolute():
            raise ValueError("workspace_root must be absolute")
        root = root.resolve(strict=True)
        if resolved == root or root not in resolved.parents:
            raise ValueError("checkout is outside the job workspace")
    return resolved


def _container_name(job: Job) -> str:
    name = job.container_name or "linktrend-coordinator-{}".format(job.job_id)
    if not _CONTAINER_NAME.fullmatch(name):
        raise ValueError("container name is not coordinator-scoped")
    if job.job_id not in name:
        raise ValueError("container name is not bound to job identity")
    return name


def _validate_image(image: str) -> None:
    if not _IMAGE.fullmatch(image) or image.startswith("-"):
        raise ValueError("image is not one Docker argument")


def _validate_nested(job: Job) -> None:
    for volume in job.volumes:
        source = _get(volume, "source", "src", default="")
        if str(source).replace("\\", "/") == "/var/run/docker.sock":
            raise ValueError("host Docker socket is forbidden")
    if not job.nested_docker:
        return
    config = job.protected_nested_config
    if not isinstance(config, Mapping) or config.get("protected") is not True:
        raise ValueError("nested Docker requires protected configuration")
    if not config.get("image") or not config.get("memoryMiB") or not config.get("pidsLimit"):
        raise ValueError("nested Docker requires bounded disposable environment")
    _validate_image(str(config["image"]))
    if int(config["memoryMiB"]) <= 0 or int(config["pidsLimit"]) <= 0:
        raise ValueError("nested Docker bounds must be positive")


def _validate_volumes(job: Job, checkout: Path) -> Tuple[Tuple[str, str], ...]:
    volumes = [(str(checkout), "/workspace")]
    for volume in job.volumes:
        source = Path(str(_get(volume, "source", "src", default=""))).expanduser()
        target = str(_get(volume, "target", "dst", default=""))
        if not source.is_absolute() or not _TARGET.fullmatch(target):
            raise ValueError("volume is not an absolute scoped mount")
        source = source.resolve(strict=True)
        if source != checkout and checkout not in source.parents:
            raise ValueError("volume is outside the job checkout")
        if target == "/" or target == "/workspace":
            raise ValueError("volume target is reserved or broad")
        volumes.append((str(source), target))
    return tuple(volumes)


def build_docker_invocation(job_value: Any, limits_value: Any = None, docker_binary: Optional[str] = None) -> Tuple[str, ...]:
    """Build the only command form accepted by :func:`run_job`."""

    job = _job(job_value)
    limits = limits_value if isinstance(limits_value, ResourceLimits) else ResourceLimits.from_mapping(limits_value or {})
    checkout = _safe_checkout(job.checkout_path, job.workspace_root)
    _validate_image(job.image)
    _validate_nested(job)
    mounts = _validate_volumes(job, checkout)
    name = _container_name(job)
    cpus, memory_mib, memory_swap_mib = limits.limits_for(job.test_profile)
    binary = docker_binary or limits.docker_binary
    if not binary or any(ch.isspace() for ch in binary):
        raise ValueError("docker binary must be one executable token")
    argv = [
        binary,
        "run",
        "--rm",
        "--platform",
        "linux/amd64",
        "--name",
        name,
        "--label",
        "com.linktrend.coordinator=true",
        "--label",
        "com.linktrend.job-id=" + job.job_id,
        "--label",
        "com.linktrend.repository=" + (job.repository or "unregistered"),
        "--label",
        "com.linktrend.timeout-seconds=" + str(job.timeout_seconds),
        "--cpus",
        str(cpus),
        "--memory",
        "{}m".format(memory_mib),
        "--memory-swap",
        "{}m".format(memory_swap_mib),
        "--pids-limit",
        str(limits.pids_limit),
        "--stop-timeout",
        str(max(1, min(job.timeout_seconds, 120))),
        "--network",
        "none",
        "--read-only",
        "--tmpfs",
        "/tmp:rw,noexec,nosuid,size=64m",
    ]
    for source, target in mounts:
        argv.extend(["--mount", "type=bind,src={},dst={},readonly".format(source, target)])
    if not job.workdir.startswith("/") or ".." in Path(job.workdir).parts:
        raise ValueError("working directory must be an absolute container path")
    argv.extend(["--workdir", job.workdir, job.image])
    argv.extend(job.command)
    return tuple(argv)


_SECRET_PATTERNS = (
    (re.compile(r"(?i)(authorization\s*:\s*bearer\s+)[^\s]+"), r"\1[REDACTED]"),
    (re.compile(r"(?i)(bearer\s+)[A-Za-z0-9._~+/=-]+"), r"\1[REDACTED]"),
    (re.compile(r"(?i)\b(ghp_|github_pat_|sk-|xox[baprs]-)[A-Za-z0-9_-]+"), r"\1[REDACTED]"),
    (re.compile(r"(?i)\b(password|passwd|secret|token|api[_-]?key)\s*[=:]\s*[^\s,;]+"), r"\1=[REDACTED]"),
)


def sanitize_output(value: Any) -> str:
    """Return bounded, credential-redacted text suitable for evidence."""

    text = str(value or "")
    for pattern, replacement in _SECRET_PATTERNS:
        text = pattern.sub(replacement, text)
    if len(text) > 20000:
        text = text[:20000] + "\n[TRUNCATED]"
    return text


def _cancelled(cancellation: Any) -> bool:
    if cancellation is None:
        return False
    if callable(cancellation):
        return bool(cancellation())
    if hasattr(cancellation, "is_set"):
        return bool(cancellation.is_set())
    if hasattr(cancellation, "cancelled"):
        value = cancellation.cancelled
        return bool(value() if callable(value) else value)
    return bool(cancellation)


def _stamp() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _finish_process(process: Any, force: bool = False) -> None:
    try:
        process.terminate()
        process.wait(timeout=2)
    except Exception:
        if force:
            try:
                process.kill()
                process.wait(timeout=2)
            except Exception:
                pass


def run_job(job_value: Any, limits_value: Any, cancellation: Any) -> ExecutionResult:
    """Execute a candidate only through Docker and return sanitized evidence."""

    job_id = str(_get(job_value, "job_id", "jobId", default="unknown"))
    started = None
    try:
        job = _job(job_value)
        limits = limits_value if isinstance(limits_value, ResourceLimits) else ResourceLimits.from_mapping(limits_value or {})
        argv = build_docker_invocation(job, limits)
        name = _container_name(job)
    except (TypeError, ValueError) as exc:
        return ExecutionResult("rejected", job_id, None, None, _stamp(), "", error=sanitize_output(exc))

    register_job(
        job.job_id,
        container_name=name,
        checkout_path=job.checkout_path,
        workspace_root=job.workspace_root,
        temporary_checkout=job.temporary_checkout,
    )
    if _cancelled(cancellation):
        result = ExecutionResult("cancelled", job.job_id, None, None, _stamp(), name, argv)
        result_cleanup = cleanup_job(job.job_id)
        return ExecutionResult(result.status, result.job_id, result.exit_code, result.started_at, result.completed_at, result.container_name, result.docker_argv, cleanup=result_cleanup)

    started = _stamp()
    process = None
    try:
        process = subprocess.Popen(
            list(argv),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            shell=False,
            start_new_session=True,
        )
        deadline = time.monotonic() + job.timeout_seconds
        status = "running"
        while process.poll() is None:
            if _cancelled(cancellation):
                status = "cancelled"
                _finish_process(process, force=True)
                break
            if time.monotonic() >= deadline:
                status = "timed_out"
                _finish_process(process, force=True)
                break
            time.sleep(0.02)
        try:
            stdout, stderr = process.communicate(timeout=2)
        except Exception as exc:
            stdout, stderr = "", str(exc)
        exit_code = process.returncode
        if status == "running":
            status = "passed" if exit_code == 0 else "failed"
        result_cleanup = cleanup_job(job.job_id)
        if not result_cleanup.success and status in ("passed", "failed"):
            status = "cleanup_failed"
        return ExecutionResult(
            status,
            job.job_id,
            exit_code,
            started,
            _stamp(),
            name,
            tuple(sanitize_output(arg) for arg in argv),
            sanitize_output(stdout),
            sanitize_output(stderr),
            result_cleanup,
        )
    except FileNotFoundError as exc:
        result_cleanup = cleanup_job(job.job_id)
        return ExecutionResult("error", job.job_id, None, started, _stamp(), name, argv, cleanup=result_cleanup, error=sanitize_output(exc))
    except Exception as exc:
        if process is not None and process.poll() is None:
            _finish_process(process, force=True)
        result_cleanup = cleanup_job(job.job_id)
        return ExecutionResult("error", job.job_id, None, started, _stamp(), name, argv, cleanup=result_cleanup, error=sanitize_output(exc))
