"""Label- and job-identity-scoped Docker and checkout cleanup."""

import re
import shutil
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, Mapping, Optional, Sequence, Set, Tuple


_JOB_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.:-]{0,127}$")
_CONTAINER_ID = re.compile(r"^[a-f0-9]{12,64}$")
_CONTAINER_NAME = re.compile(r"^linktrend-coordinator-[A-Za-z0-9][A-Za-z0-9_.-]{0,100}$")


@dataclass(frozen=True)
class CleanupResult:
    success: bool
    job_id: str
    removed_containers: Tuple[str, ...] = ()
    removed_paths: Tuple[str, ...] = ()
    errors: Tuple[str, ...] = ()
    inspected: Tuple[str, ...] = ()


@dataclass(frozen=True)
class _OwnedJob:
    job_id: str
    container_name: str
    checkout_path: Optional[str] = None
    workspace_root: Optional[str] = None
    temporary_checkout: bool = False


_OWNED: Dict[str, _OwnedJob] = {}


def _validate_job_id(job_id: str) -> str:
    if not _JOB_ID.fullmatch(job_id):
        raise ValueError("job_id is not a safe cleanup identity")
    return job_id


def register_job(
    job_id: str,
    *,
    container_name: str,
    checkout_path: Optional[str] = None,
    workspace_root: Optional[str] = None,
    temporary_checkout: bool = False,
) -> None:
    """Record exact resources owned by one job for later scoped cleanup."""

    _validate_job_id(job_id)
    if not _CONTAINER_NAME.fullmatch(container_name) or job_id not in container_name:
        raise ValueError("container name is not bound to job identity")
    if checkout_path is not None:
        if temporary_checkout and workspace_root is None:
            raise ValueError("owned checkout requires workspace_root")
        checkout = Path(checkout_path).expanduser()
        if not checkout.is_absolute():
            raise ValueError("cleanup paths must be absolute")
        if workspace_root is not None and not Path(workspace_root).expanduser().is_absolute():
            raise ValueError("cleanup paths must be absolute")
    _OWNED[job_id] = _OwnedJob(job_id, container_name, checkout_path, workspace_root, temporary_checkout)


def _run(
    argv: Sequence[str],
    runner: Optional[Callable[..., Any]],
) -> Any:
    if runner is not None:
        return runner(list(argv))
    return subprocess.run(list(argv), stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, shell=False)


def _output(result: Any) -> str:
    return str(getattr(result, "stdout", "") or "").strip()


def _returncode(result: Any) -> int:
    return int(getattr(result, "returncode", 0))


def _validate_container_ids(output: str) -> Tuple[str, ...]:
    ids = tuple(line.strip() for line in output.splitlines() if line.strip())
    if any(not _CONTAINER_ID.fullmatch(value) for value in ids):
        raise ValueError("Docker returned an invalid cleanup target")
    return ids


def _remove_containers(
    job_id: str,
    owned: _OwnedJob,
    docker_binary: str,
    runner: Optional[Callable[..., Any]],
) -> Tuple[Tuple[str, ...], Tuple[str, ...], Tuple[str, ...]]:
    if not docker_binary or any(ch.isspace() for ch in docker_binary):
        return (), (), ("invalid Docker binary",)
    # Both the coordinator label and exact job/name filters are required.  No
    # shell expansion or broad `docker rm $(...)` operation is permitted.
    listed = _run(
        [
            docker_binary,
            "ps",
            "-aq",
            "--filter",
            "label=com.linktrend.coordinator=true",
            "--filter",
            "label=com.linktrend.job-id=" + job_id,
            "--filter",
            "name=^{}$".format(owned.container_name),
        ],
        runner,
    )
    if _returncode(listed) != 0:
        return (), (), ("Docker inventory failed: " + _output(listed)[:500],)
    try:
        container_ids = _validate_container_ids(_output(listed))
    except ValueError as exc:
        return (), (), (str(exc),)
    removed = []
    errors = []
    for container_id in container_ids:
        result = _run([docker_binary, "rm", "-f", container_id], runner)
        if _returncode(result) == 0:
            removed.append(container_id)
        else:
            errors.append("Docker removal failed for {}: {}".format(container_id, _output(result)[:500]))
    return tuple(removed), tuple(container_ids), tuple(errors)


def _remove_owned_checkout(owned: _OwnedJob) -> Tuple[Tuple[str, ...], Tuple[str, ...]]:
    if not owned.temporary_checkout:
        return (), ()
    if not owned.checkout_path or not owned.workspace_root:
        return (), ("temporary checkout has no explicit workspace root",)
    try:
        checkout = Path(owned.checkout_path).expanduser().resolve(strict=True)
        root = Path(owned.workspace_root).expanduser().resolve(strict=True)
    except (FileNotFoundError, OSError) as exc:
        return (), ("checkout validation failed: {}".format(exc),)
    if checkout == root or root not in checkout.parents:
        return (), ("cleanup target is outside its job workspace",)
    if checkout == Path(checkout.anchor):
        return (), ("broad cleanup target rejected",)
    try:
        shutil.rmtree(str(checkout))
    except OSError as exc:
        return (), ("checkout removal failed: {}".format(exc),)
    return (str(checkout),), ()


def cleanup_job(
    job_id: str,
    *,
    docker_binary: str = "docker",
    runner: Optional[Callable[..., Any]] = None,
) -> CleanupResult:
    """Remove only resources registered for ``job_id``.

    Unknown identities are a visible failure, never a reason to issue a broad
    cleanup command.  The registry is process-local by design; restart
    recovery uses :func:`recover_orphans` and Docker's coordinator labels.
    """

    try:
        _validate_job_id(job_id)
    except ValueError as exc:
        return CleanupResult(False, str(job_id), errors=(str(exc),))
    owned = _OWNED.get(job_id)
    if owned is None:
        return CleanupResult(False, job_id, errors=("unknown job identity",))
    removed, inspected, errors = _remove_containers(job_id, owned, docker_binary, runner)
    removed_paths, path_errors = _remove_owned_checkout(owned) if not errors else ((), ())
    errors = tuple(errors) + tuple(path_errors)
    success = not errors
    if success:
        _OWNED.pop(job_id, None)
    return CleanupResult(success, job_id, removed, removed_paths, errors, inspected)


def recover_orphans(
    active_job_ids: Set[str],
    *,
    docker_binary: str = "docker",
    runner: Optional[Callable[..., Any]] = None,
) -> CleanupResult:
    """Remove only Docker containers carrying the coordinator label.

    A missing or malformed job label is left in place and reported, failing
    closed rather than guessing ownership.
    """

    active = set()
    for job_id in active_job_ids:
        try:
            active.add(_validate_job_id(str(job_id)))
        except ValueError:
            return CleanupResult(False, "startup-recovery", errors=("invalid active job identity",))
    inventory = _run(
        [docker_binary, "ps", "-aq", "--filter", "label=com.linktrend.coordinator=true"],
        runner,
    )
    if _returncode(inventory) != 0:
        return CleanupResult(False, "startup-recovery", errors=("Docker inventory failed: " + _output(inventory)[:500],))
    try:
        ids = _validate_container_ids(_output(inventory))
    except ValueError as exc:
        return CleanupResult(False, "startup-recovery", errors=(str(exc),))
    removed = []
    errors = []
    inspected = []
    for container_id in ids:
        inspected.append(container_id)
        detail = _run(
            [
                docker_binary,
                "inspect",
                "--format",
                '{{ index .Config.Labels "com.linktrend.job-id" }}',
                container_id,
            ],
            runner,
        )
        if _returncode(detail) != 0:
            errors.append("inspection failed for {}".format(container_id))
            continue
        job_id = _output(detail)
        if not _JOB_ID.fullmatch(job_id):
            errors.append("malformed coordinator job label for {}".format(container_id))
            continue
        if job_id in active:
            continue
        removal = _run([docker_binary, "rm", "-f", container_id], runner)
        if _returncode(removal) == 0:
            removed.append(container_id)
        else:
            errors.append("orphan removal failed for {}".format(container_id))
    return CleanupResult(not errors, "startup-recovery", tuple(removed), (), tuple(errors), tuple(inspected))
