"""Exclusive transaction lock for mutating installer operations.

Lock file lives under the resolved git meta dir (``git_meta_dir(target)/lock``),
never under a worktree ``.git`` gitfile path. Plan/dry-run must not acquire this
lock; install/update/rollback/recover hold it for the whole mutating apply.
"""

from __future__ import annotations

import os
import sys
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

from .errors import ConflictError
from .paths import git_meta_dir

_LOCK_FILENAME = "lock"


def lock_path(target_root: Path) -> Path:
    """Return the exclusive lock path under the resolved git meta directory."""
    return git_meta_dir(target_root) / _LOCK_FILENAME


def _acquire_posix(fd: int) -> None:
    import fcntl

    try:
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError as exc:
        raise ConflictError(
            "Another installer transaction holds the exclusive lock "
            "(concurrent install/update/rollback/recover is not allowed)",
            details={"errno": getattr(exc, "errno", None)},
        ) from exc
    except OSError as exc:
        # Some platforms raise EAGAIN/EACCES/EWOULDBLOCK as OSError
        err = getattr(exc, "errno", None)
        if err in {getattr(os, "EAGAIN", -1), getattr(os, "EWOULDBLOCK", -2), getattr(os, "EACCES", -3)}:
            raise ConflictError(
                "Another installer transaction holds the exclusive lock "
                "(concurrent install/update/rollback/recover is not allowed)",
                details={"errno": err},
            ) from exc
        raise


def _acquire_windows(fd: int) -> None:
    import msvcrt

    try:
        # LK_NBLCK: non-blocking exclusive lock on 1 byte — fail closed, no hang.
        msvcrt.locking(fd, msvcrt.LK_NBLCK, 1)
    except OSError as exc:
        raise ConflictError(
            "Another installer transaction holds the exclusive lock "
            "(concurrent install/update/rollback/recover is not allowed)",
            details={"errno": getattr(exc, "errno", None)},
        ) from exc


def _release_posix(fd: int) -> None:
    import fcntl

    fcntl.flock(fd, fcntl.LOCK_UN)


def _release_windows(fd: int) -> None:
    import msvcrt

    try:
        msvcrt.locking(fd, msvcrt.LK_UNLCK, 1)
    except OSError:
        pass


@contextmanager
def exclusive_transaction_lock(target_root: Path) -> Iterator[Path]:
    """Acquire a non-blocking exclusive lock under ``git_meta_dir(target)/lock``.

    Yields the lock file path. Always releases in ``finally``. Concurrent
    second mutator fails closed with ``ConflictError`` (does not wait forever).
    """
    path = lock_path(target_root)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd = os.open(str(path), os.O_RDWR | os.O_CREAT, 0o644)
    acquired = False
    try:
        if sys.platform == "win32":
            _acquire_windows(fd)
        else:
            _acquire_posix(fd)
        acquired = True
        yield path
    finally:
        if acquired:
            try:
                if sys.platform == "win32":
                    _release_windows(fd)
                else:
                    _release_posix(fd)
            except OSError:
                pass
        try:
            os.close(fd)
        except OSError:
            pass
