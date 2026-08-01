"""Safe path helpers with Windows/POSIX and spaces support."""

from __future__ import annotations

import os
import sys
from pathlib import Path, PurePosixPath

from .errors import ConflictError, InvalidPackageError


def resolve_dir(path: Path) -> Path:
    if not path.exists():
        raise InvalidPackageError(f"Path does not exist: {path}")
    if not path.is_dir():
        raise InvalidPackageError(f"Path is not a directory: {path}")
    return path.resolve()


def is_git_repo(path: Path) -> bool:
    return (path / ".git").exists()


def require_git_repo(path: Path) -> Path:
    root = resolve_dir(path)
    if not is_git_repo(root):
        raise InvalidPackageError(f"Target is not a git repository: {root}")
    return root


def as_posix_rel(path: str | PurePosixPath | Path) -> str:
    text = str(path).replace("\\", "/")
    while text.startswith("./"):
        text = text[2:]
    if text.startswith("/") or text.startswith("~"):
        raise InvalidPackageError(f"Absolute paths are not allowed: {path}")
    # Reject Windows drive letters
    if len(text) >= 2 and text[1] == ":":
        raise InvalidPackageError(f"Drive-letter paths are not allowed: {path}")
    parts = PurePosixPath(text).parts
    if ".." in parts:
        raise InvalidPackageError(f"Parent traversal is not allowed: {path}")
    if not text or text == ".":
        raise InvalidPackageError("Empty relative path is not allowed")
    return PurePosixPath(text).as_posix()


def join_under(root: Path, rel: str | PurePosixPath) -> Path:
    """Join a relative path under root and ensure the result stays inside root."""
    rel_posix = as_posix_rel(rel)
    candidate = root.joinpath(*PurePosixPath(rel_posix).parts)
    root_resolved = root.resolve()
    candidate_resolved = candidate.resolve(strict=False)
    try:
        candidate_resolved.relative_to(root_resolved)
    except ValueError as exc:
        raise ConflictError(
            f"Path escapes repository root: {rel_posix}",
            details={"path": rel_posix, "root": str(root_resolved)},
        ) from exc
    return candidate


def path_is_symlink(path: Path) -> bool:
    try:
        return path.is_symlink()
    except OSError:
        return False


def current_os_token() -> str:
    if sys.platform.startswith("win"):
        return "windows"
    if sys.platform == "darwin":
        return "darwin"
    if sys.platform.startswith("linux"):
        return "linux"
    return "posix"


def os_matches(declared: str | None, *, current: str | None = None) -> bool:
    token = (declared or "all").lower()
    if token == "all":
        return True
    cur = (current or current_os_token()).lower()
    if token == "posix":
        return cur in {"darwin", "linux", "posix"} and cur != "windows"
    return token == cur


def platform_matches(declared: str | None) -> bool:
    """Platform is a discovery scope, not an OS filter. All scopes are installable."""
    token = (declared or "all").lower()
    return token in {"all", "cursor", "codex", "github", "none"}


def encode_backup_name(rel_posix: str) -> str:
    return rel_posix.replace("%", "%25").replace("/", "%2F")


def decode_backup_name(name: str) -> str:
    return name.replace("%2F", "/").replace("%25", "%")


def same_path(a: Path, b: Path) -> bool:
    try:
        return os.path.normcase(str(a.resolve())) == os.path.normcase(str(b.resolve()))
    except OSError:
        return os.path.normcase(str(a)) == os.path.normcase(str(b))
