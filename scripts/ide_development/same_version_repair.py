"""Validation for the explicit v2.5.2 same-version source repair receipt."""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

from .constants import MANAGED_CORE_DIR, PACKAGE_VERSION_TARGET
from .errors import ConflictError, InvalidPackageError
from .hashing import modes_match, normalize_mode, sha256_file
from .managed_write_guard import is_read_only_mode, read_only_mode
from .manifest import Manifest
from .paths import as_posix_rel, join_under_nofollow, path_is_symlink
from .state import InstalledState

KIND = "ide-managed-same-version-repair"
SCHEMA_VERSION = 1
HEX40 = re.compile(r"^[0-9a-f]{40}$")
DIGEST = re.compile(r"^sha256:[0-9a-f]{64}$")
OPERATION_REPLACE = "replace"
OPERATION_ADD = "add"
OPERATIONS = frozenset({OPERATION_REPLACE, OPERATION_ADD})
MANIFEST_DEST = f"{MANAGED_CORE_DIR}/MANIFEST.json"


@dataclass(frozen=True)
class RepairPath:
    path: str
    source: str
    old_source_digest: str | None
    old_installed_digest: str | None
    source_digest: str
    source_bytes: int
    operation: str
    noop: bool = False


@dataclass(frozen=True)
class SameVersionRepair:
    receipt_path: Path
    target_worktree: str
    source_repository: str
    source_ref: str
    source_commit: str
    source_tree: str
    manifest_digest: str
    installed_manifest_digest: str
    paths: tuple[RepairPath, ...]
    receipt_digest: str


def _digest(value: Any, field: str) -> str:
    if not isinstance(value, str) or not DIGEST.fullmatch(value):
        raise InvalidPackageError(f"Same-version repair {field} must be a sha256 digest")
    return value


def _oid(value: Any, field: str) -> str:
    if not isinstance(value, str) or not HEX40.fullmatch(value):
        raise InvalidPackageError(f"Same-version repair {field} must be a 40-character Git OID")
    return value


def _git(root: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", *args], cwd=root, text=True, capture_output=True, check=False
    )
    if result.returncode:
        raise InvalidPackageError(
            "Cannot verify exact source identity for same-version repair",
            details={"stderr": result.stderr.strip()},
        )
    return result.stdout.strip()


def _path(value: Any, field: str) -> str:
    if not isinstance(value, str):
        raise InvalidPackageError(f"Same-version repair {field} must be a path")
    normalized = as_posix_rel(value)
    if normalized != value:
        raise InvalidPackageError(f"Same-version repair {field} must be normalized")
    return normalized


def _load(path: Path) -> tuple[dict[str, Any], bytes]:
    if path.is_symlink() or not path.is_file():
        raise InvalidPackageError(f"Same-version repair manifest must be a physical file: {path}")
    try:
        raw_bytes = path.read_bytes()
        raw = json.loads(raw_bytes.decode("utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise InvalidPackageError(f"Same-version repair manifest is not valid JSON: {path}") from exc
    if not isinstance(raw, dict):
        raise InvalidPackageError("Same-version repair manifest must be a JSON object")
    return raw, raw_bytes


def _derive_installed_manifest_digest(
    target_root: Path, prior: InstalledState
) -> str:
    """Derive a missing manifestHash only from its exact managed preimage."""
    manifest_path = join_under_nofollow(target_root, MANIFEST_DEST)
    manifest_state = prior.files.get(MANIFEST_DEST)
    if (
        manifest_state is None
        or path_is_symlink(manifest_path)
        or not manifest_path.is_file()
        or not is_read_only_mode(manifest_path.stat().st_mode & 0o7777)
    ):
        raise InvalidPackageError(
            "installed-state manifestHash is missing and cannot be exactly derived"
        )
    digest = sha256_file(manifest_path)
    if (
        manifest_state.id != "package-manifest"
        or manifest_state.source_hash != digest
        or manifest_state.content_hash != digest
        or manifest_state.package_version != PACKAGE_VERSION_TARGET
        or manifest_state.mutability_policy != "read-only"
        or manifest_state.ownership_class != "managed-core"
        or manifest_state.platform != "all"
        or manifest_state.merge_strategy != "replace"
        or normalize_mode(manifest_state.mode)
        != normalize_mode(manifest_path.stat().st_mode & 0o7777)
    ):
        raise InvalidPackageError(
            "installed-state manifestHash is missing and managed preimage is ambiguous"
        )
    return digest


def _installed_manifest_digest(target_root: Path, prior: InstalledState) -> str:
    """Validate or exactly derive the installed manifest identity."""
    manifest_path = join_under_nofollow(target_root, MANIFEST_DEST)
    if prior.manifest_hash is not None:
        if path_is_symlink(manifest_path) or not manifest_path.is_file():
            raise InvalidPackageError("installed-state manifest preimage is missing or unsafe")
        derived = sha256_file(manifest_path)
        if prior.manifest_hash != derived:
            raise InvalidPackageError("installed-state manifestHash does not match managed preimage")
        return derived
    derived = _derive_installed_manifest_digest(target_root, prior)
    return derived


def _add_collision_is_exact_noop(
    *,
    destination: Path,
    previous: Any,
    entry: Any,
    package_version: str,
) -> bool:
    """Allow an add collision only for an exact current managed file."""
    expected_mode = read_only_mode(entry.mode)
    if (
        previous.id != entry.id
        or previous.source_hash != entry.source_hash
        or previous.owner != entry.owner
        or previous.package_version != package_version
        or previous.mutability_policy != entry.mutability_policy
        or previous.removal_policy != entry.removal_policy
        or previous.ownership_class != entry.ownership_class
        or previous.platform != entry.platform
        or previous.merge_strategy != entry.merge_strategy
        or previous.content_hash != entry.source_hash
        or normalize_mode(previous.mode) != expected_mode
        or path_is_symlink(destination)
        or not destination.is_file()
        or sha256_file(destination) != entry.source_hash
        or not modes_match(destination.stat().st_mode & 0o7777, expected_mode)
    ):
        return False
    return True


def load_and_validate_same_version_repair(
    repair_path: Path,
    *,
    target_root: Path,
    package_root: Path,
    manifest: Manifest,
    prior: InstalledState | None,
) -> SameVersionRepair:
    """Validate an exact receipt before any consumer mutation is possible."""
    raw, raw_bytes = _load(repair_path.resolve(strict=False))
    if raw.get("schemaVersion") != SCHEMA_VERSION or raw.get("kind") != KIND:
        raise InvalidPackageError("Unsupported same-version repair manifest kind/version")
    if raw.get("packageVersion") != PACKAGE_VERSION_TARGET or manifest.package_version != PACKAGE_VERSION_TARGET:
        raise InvalidPackageError("Same-version repair is available only for packageVersion 2.5.2")
    if prior is None or prior.package_version != PACKAGE_VERSION_TARGET:
        raise InvalidPackageError("Same-version repair requires an installed packageVersion of 2.5.2")

    target_worktree = raw.get("targetWorktree")
    if not isinstance(target_worktree, str) or str(Path(target_worktree).resolve(strict=False)) != str(target_root.resolve()):
        raise InvalidPackageError("Same-version repair targetWorktree does not exactly match target")

    source = raw.get("source")
    if not isinstance(source, Mapping):
        raise InvalidPackageError("Same-version repair source identity is required")
    source_repository = source.get("repository")
    source_ref = source.get("ref")
    if not isinstance(source_repository, str) or not source_repository.strip():
        raise InvalidPackageError("Same-version repair source.repository is required")
    if not isinstance(source_ref, str) or not source_ref.strip():
        raise InvalidPackageError("Same-version repair source.ref is required")
    source_commit = _oid(source.get("commit"), "source.commit")
    source_tree = _oid(source.get("tree"), "source.tree")
    manifest_digest = _digest(source.get("manifestDigest"), "source.manifestDigest")
    actual_identity = (
        _git(package_root, "rev-parse", "--verify", "HEAD^{commit}"),
        _git(package_root, "rev-parse", "--verify", "HEAD^{tree}"),
    )
    if (source_commit, source_tree) != actual_identity:
        raise InvalidPackageError("Same-version repair source identity is stale")
    actual_manifest_digest = sha256_file(manifest.path)
    if manifest_digest != actual_manifest_digest:
        raise InvalidPackageError("Same-version repair source manifest digest is stale")

    installed = raw.get("installed")
    if not isinstance(installed, Mapping) or installed.get("packageVersion") != PACKAGE_VERSION_TARGET:
        raise InvalidPackageError("Same-version repair installed package identity is invalid")
    installed_manifest_digest = _digest(
        installed.get("manifestDigest"), "installed.manifestDigest"
    )
    exact_prior_manifest_digest = _installed_manifest_digest(target_root, prior)
    if exact_prior_manifest_digest != installed_manifest_digest:
        raise InvalidPackageError("Same-version repair installed manifest identity is stale")
    if installed_manifest_digest == manifest_digest:
        raise InvalidPackageError("Same-version repair requires a manifest identity difference")

    entries = {entry.destination: entry for entry in manifest.active_entries()}
    rows = raw.get("paths")
    if not isinstance(rows, list) or not rows:
        raise InvalidPackageError("Same-version repair paths must be a non-empty array")
    parsed: list[RepairPath] = []
    seen: set[str] = set()
    for index, row in enumerate(rows):
        if not isinstance(row, Mapping):
            raise InvalidPackageError(f"Same-version repair paths[{index}] is invalid")
        rel = _path(row.get("path"), f"paths[{index}].path")
        if rel in seen or rel == MANIFEST_DEST:
            raise InvalidPackageError("Same-version repair paths contain a duplicate or manifest path")
        seen.add(rel)
        operation = row.get("operation", OPERATION_REPLACE)
        if operation not in OPERATIONS:
            raise InvalidPackageError(f"Same-version repair operation is invalid: {rel}")
        entry = entries.get(rel)
        previous = prior.files.get(rel)
        if entry is None or entry.ownership_class == "external-state":
            raise InvalidPackageError(
                "Same-version repair path is not an IDE-managed file",
                details={"path": rel},
            )
        source_path = row.get("source")
        if source_path != entry.source:
            raise InvalidPackageError(f"Same-version repair source path is not bound to MANIFEST: {rel}")
        new_source = _digest(row.get("sourceDigest"), f"{rel}.sourceDigest")
        source_file = join_under_nofollow(package_root, entry.source)
        destination = join_under_nofollow(target_root, rel)
        if path_is_symlink(source_file) or not source_file.is_file():
            raise InvalidPackageError("Same-version repair source is missing/unsafe", details={"path": rel})
        source_bytes = row.get("sourceBytes")
        if not isinstance(source_bytes, int) or source_bytes < 0 or source_bytes != source_file.stat().st_size:
            raise InvalidPackageError(f"Same-version repair source byte identity is stale: {rel}")
        if not modes_match(source_file.stat().st_mode & 0o7777, entry.mode):
            raise InvalidPackageError(f"Same-version repair source mode is stale: {rel}")
        if new_source != entry.source_hash or sha256_file(source_file) != new_source:
            raise InvalidPackageError(f"Same-version repair source bytes do not match MANIFEST: {rel}")
        if operation == OPERATION_ADD:
            if "installedSourceDigest" in row or "installedDigest" in row:
                raise InvalidPackageError(
                    "Same-version repair addition must not declare an installed preimage",
                    details={"path": rel},
                )
            noop = False
            if previous is not None or path_is_symlink(destination) or destination.exists():
                if previous is None or not _add_collision_is_exact_noop(
                    destination=destination,
                    previous=previous,
                    entry=entry,
                    package_version=manifest.package_version,
                ):
                    raise ConflictError(
                        "Same-version repair refuses an existing collision for a declared addition",
                        details={"path": rel},
                    )
                noop = True
            parsed.append(
                RepairPath(
                    rel,
                    source_path,
                    None,
                    None,
                    new_source,
                    source_bytes,
                    OPERATION_ADD,
                    noop,
                )
            )
            continue
        if previous is None:
            raise InvalidPackageError(
                "Same-version repair path is not an IDE-managed file",
                details={"path": rel},
            )
        old_source = _digest(row.get("installedSourceDigest"), f"{rel}.installedSourceDigest")
        old_installed = _digest(row.get("installedDigest"), f"{rel}.installedDigest")
        if path_is_symlink(destination) or not destination.is_file():
            raise InvalidPackageError(
                "Same-version repair source or destination is missing/unsafe",
                details={"path": rel},
            )
        if old_source != previous.source_hash or old_installed != previous.content_hash:
            raise InvalidPackageError(f"Same-version repair installed preimage is stale: {rel}")
        if sha256_file(destination) != old_installed:
            raise ConflictError(
                "Same-version repair refuses a consumer file changed after receipt",
                details={"path": rel},
            )
        if new_source == old_source:
            raise InvalidPackageError(f"Same-version repair source digest is invalid: {rel}")
        parsed.append(
            RepairPath(rel, source_path, old_source, old_installed, new_source, source_bytes, OPERATION_REPLACE)
        )

    return SameVersionRepair(
        receipt_path=repair_path.resolve(strict=False),
        target_worktree=target_worktree,
        source_repository=source_repository,
        source_ref=source_ref,
        source_commit=source_commit,
        source_tree=source_tree,
        manifest_digest=manifest_digest,
        installed_manifest_digest=installed_manifest_digest,
        paths=tuple(sorted(parsed, key=lambda item: item.path)),
        receipt_digest="sha256:" + hashlib.sha256(raw_bytes).hexdigest(),
    )
