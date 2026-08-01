"""Atomic filesystem helpers (physical files only)."""

from __future__ import annotations

import os
import tempfile
from pathlib import Path

from .hashing import mode_int
from .paths import path_is_symlink


def ensure_parent(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def atomic_write_bytes(dest: Path, data: bytes, *, mode: str | int) -> None:
    """Write bytes to dest via temp file + os.replace. Never creates symlinks."""
    if path_is_symlink(dest):
        raise OSError(f"Refusing to overwrite symlink: {dest}")
    ensure_parent(dest)
    mode_value = mode_int(mode)
    fd, tmp_name = tempfile.mkstemp(
        prefix=f".{dest.name}.",
        suffix=".tmp",
        dir=str(dest.parent),
    )
    tmp_path = Path(tmp_name)
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        os.chmod(tmp_path, mode_value)
        os.replace(tmp_path, dest)
    except Exception:
        try:
            if tmp_path.exists():
                tmp_path.unlink()
        except OSError:
            pass
        raise


def read_file_bytes(path: Path) -> bytes:
    """Read physical file bytes. Refuses symlink-following (fail closed)."""
    if path_is_symlink(path):
        raise OSError(f"Refusing to read through symlink: {path}")
    flags = os.O_RDONLY
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    try:
        fd = os.open(str(path), flags)
    except OSError:
        if path_is_symlink(path):
            raise OSError(f"Refusing to read through symlink: {path}") from None
        raise
    with os.fdopen(fd, "rb") as handle:
        return handle.read()


def remove_file(path: Path) -> None:
    if path_is_symlink(path):
        path.unlink()
        return
    if path.is_file():
        path.unlink()
        return
    if path.exists():
        raise OSError(f"Refusing to remove non-file path: {path}")


def copy_file_physical(src: Path, dest: Path, *, mode: str | int) -> None:
    data = read_file_bytes(src)
    atomic_write_bytes(dest, data, mode=mode)
