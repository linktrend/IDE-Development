"""Validation for an exact protected-commit preimage adoption receipt.

This is deliberately narrower than a force or ignore-conflict switch.  It
only reconciles installed-state for managed files whose current bytes are
proved to be the exact blob from an identified protected commit that is
already in the target's protected development ancestry.
"""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

from .constants import MANAGED_CORE_DIR, SAME_VERSION_REPAIR_VERSION
from .errors import InvalidPackageError
from .hashing import sha256_file
from .manifest import Manifest
from .paths import as_posix_rel, join_under_nofollow, path_is_symlink
from .state import InstalledState


KIND = "ide-managed-protected-preimage-adoption"
SCHEMA_VERSION = 1
OID = re.compile(r"^[0-9a-f]{40}$")
DIGEST = re.compile(r"^sha256:[0-9a-f]{64}$")
TRUSTED_PROTECTED_BASE_REF = "origin/development"
TRUSTED_PROTECTED_REMOTE_REF = "refs/heads/development"


@dataclass(frozen=True)
class AdoptionPath:
    path: str
    installed_source_digest: str
    prior_installed_digest: str
    current_digest: str
    git_blob: str


@dataclass(frozen=True)
class ProtectedPreimageAdoption:
    receipt_path: Path
    target_worktree: str
    package_version: str
    installed_manifest_digest: str
    repository: str
    base_ref: str
    base_commit: str
    commit: str
    tree: str
    ancestor: str
    paths: tuple[AdoptionPath, ...]
    receipt_digest: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "kind": KIND,
            "schemaVersion": SCHEMA_VERSION,
            "targetWorktree": self.target_worktree,
            "packageVersion": self.package_version,
            "installedManifestDigest": self.installed_manifest_digest,
            "protected": {
                "repository": self.repository,
                "baseRef": self.base_ref,
                "baseCommit": self.base_commit,
                "commit": self.commit,
                "tree": self.tree,
                "ancestor": self.ancestor,
            },
            "paths": [
                {
                    "path": item.path,
                    "installedSourceDigest": item.installed_source_digest,
                    "priorInstalledDigest": item.prior_installed_digest,
                    "currentDigest": item.current_digest,
                    "gitBlob": item.git_blob,
                }
                for item in self.paths
            ],
        }


def _load(path: Path) -> tuple[dict[str, Any], bytes]:
    if path.is_symlink() or not path.is_file():
        raise InvalidPackageError(f"Protected preimage receipt must be a physical file: {path}")
    try:
        raw_bytes = path.read_bytes()
        raw = json.loads(raw_bytes.decode("utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise InvalidPackageError(f"Protected preimage receipt is not valid JSON: {path}") from exc
    if not isinstance(raw, dict):
        raise InvalidPackageError("Protected preimage receipt must be a JSON object")
    return raw, raw_bytes


def _oid(value: Any, field: str) -> str:
    if not isinstance(value, str) or not OID.fullmatch(value):
        raise InvalidPackageError(f"Protected preimage {field} must be a 40-character Git OID")
    return value


def _digest(value: Any, field: str) -> str:
    if not isinstance(value, str) or not DIGEST.fullmatch(value):
        raise InvalidPackageError(f"Protected preimage {field} must be a sha256 digest")
    return value


def _git(root: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", *args], cwd=root, text=True, capture_output=True, check=False
    )
    if result.returncode:
        raise InvalidPackageError(
            "Protected preimage Git evidence is unavailable",
            details={"stderr": result.stderr.strip()},
        )
    return result.stdout.strip()


def _is_ancestor(root: Path, ancestor: str, descendant: str) -> bool:
    result = subprocess.run(
        ["git", "merge-base", "--is-ancestor", ancestor, descendant],
        cwd=root,
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode not in (0, 1):
        raise InvalidPackageError(
            "Protected preimage ancestry evidence is unavailable",
            details={"stderr": result.stderr.strip()},
        )
    return result.returncode == 0


def _fresh_remote_tip(root: Path) -> str:
    """Read the protected branch tip from the configured remote, not a local ref."""
    result = subprocess.run(
        [
            "git",
            "ls-remote",
            "--exit-code",
            "--refs",
            "origin",
            TRUSTED_PROTECTED_REMOTE_REF,
        ],
        cwd=root,
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode:
        raise InvalidPackageError(
            "Protected preimage authoritative remote development ref is unavailable",
            details={"stderr": result.stderr.strip()},
        )
    rows = [line.split() for line in result.stdout.splitlines() if line.strip()]
    if len(rows) != 1 or len(rows[0]) != 2 or rows[0][1] != TRUSTED_PROTECTED_REMOTE_REF or not OID.fullmatch(rows[0][0]):
        raise InvalidPackageError("Protected preimage authoritative remote development ref is malformed")
    return rows[0][0]


def _normalize_remote(value: str) -> str:
    remote = value.strip()
    if remote.startswith("git@") and ":" in remote:
        host, path = remote[4:].split(":", 1)
        remote = f"https://{host}/{path}"
    remote = remote.rstrip("/")
    if remote.endswith(".git"):
        remote = remote[:-4]
    return remote


def _path(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value:
        raise InvalidPackageError(f"Protected preimage {field} must be a path")
    normalized = as_posix_rel(value)
    if normalized != value or value == MANAGED_CORE_DIR:
        raise InvalidPackageError(f"Protected preimage {field} must be a normalized file path")
    return normalized


def load_and_validate_protected_preimage_adoption(
    receipt_path: Path,
    *,
    target_root: Path,
    manifest: Manifest,
    prior: InstalledState | None,
) -> ProtectedPreimageAdoption:
    """Validate every receipt claim before an adoption transaction can start."""
    raw, raw_bytes = _load(receipt_path.resolve(strict=False))
    if raw.get("schemaVersion") != SCHEMA_VERSION or raw.get("kind") != KIND:
        raise InvalidPackageError("Unsupported protected preimage receipt kind/version")
    if raw.get("packageVersion") != SAME_VERSION_REPAIR_VERSION or manifest.package_version != SAME_VERSION_REPAIR_VERSION:
        raise InvalidPackageError("Protected preimage adoption is available only for packageVersion 2.5.2")
    if prior is None or prior.package_version != SAME_VERSION_REPAIR_VERSION:
        raise InvalidPackageError("Protected preimage adoption requires an installed packageVersion of 2.5.2")

    target_worktree = raw.get("targetWorktree")
    if not isinstance(target_worktree, str) or str(Path(target_worktree).resolve(strict=False)) != str(target_root.resolve()):
        raise InvalidPackageError("Protected preimage targetWorktree does not exactly match target")

    installed_manifest_digest = _digest(raw.get("installedManifestDigest"), "installedManifestDigest")
    manifest_path = target_root / f"{MANAGED_CORE_DIR}/MANIFEST.json"
    if prior.manifest_hash != installed_manifest_digest or not manifest_path.is_file() or path_is_symlink(manifest_path):
        raise InvalidPackageError("Protected preimage installed manifest identity is stale")
    if sha256_file(manifest_path) != installed_manifest_digest:
        raise InvalidPackageError("Protected preimage installed manifest bytes are stale")
    package_manifest_digest = sha256_file(manifest.path)
    if package_manifest_digest != installed_manifest_digest:
        raise InvalidPackageError("Protected preimage package must match the installed 2.5.2 manifest")

    protected = raw.get("protected")
    if not isinstance(protected, Mapping):
        raise InvalidPackageError("Protected preimage protected identity is required")
    repository = protected.get("repository")
    base_ref = protected.get("baseRef")
    if not isinstance(repository, str) or not repository.strip():
        raise InvalidPackageError("Protected preimage protected.repository is required")
    if base_ref != TRUSTED_PROTECTED_BASE_REF:
        raise InvalidPackageError(
            "Protected preimage protected.baseRef must be the authoritative origin/development ref"
        )
    remote = _normalize_remote(_git(target_root, "remote", "get-url", "origin"))
    if _normalize_remote(repository) != remote:
        raise InvalidPackageError("Protected preimage repository does not match origin")
    base_commit = _oid(protected.get("baseCommit"), "protected.baseCommit")
    commit = _oid(protected.get("commit"), "protected.commit")
    tree = _oid(protected.get("tree"), "protected.tree")
    ancestor = _oid(protected.get("ancestor"), "protected.ancestor")
    resolved_base = _git(target_root, "rev-parse", "--verify", f"{base_ref}^{{commit}}")
    if resolved_base != base_commit:
        raise InvalidPackageError("Protected preimage local base ref identity is stale")
    if _fresh_remote_tip(target_root) != base_commit:
        raise InvalidPackageError("Protected preimage remote protected base identity is stale")
    if _git(target_root, "rev-parse", "--verify", f"{commit}^{{commit}}") != commit:
        raise InvalidPackageError("Protected preimage commit is unavailable")
    if _git(target_root, "rev-parse", "--verify", f"{commit}^{{tree}}") != tree:
        raise InvalidPackageError("Protected preimage tree identity is stale")
    parents = _git(target_root, "rev-list", "--parents", "-n", "1", commit).split()
    if len(parents) != 2 or parents[1] != ancestor:
        raise InvalidPackageError("Protected preimage ancestor is not the exact commit parent")
    head = _git(target_root, "rev-parse", "--verify", "HEAD^{commit}")
    if not _is_ancestor(target_root, commit, base_commit) or not _is_ancestor(target_root, base_commit, head):
        raise InvalidPackageError("Protected preimage is outside the protected base ancestry")

    rows = raw.get("paths")
    if not isinstance(rows, list) or not rows:
        raise InvalidPackageError("Protected preimage paths must be a non-empty array")
    entries = {entry.destination: entry for entry in manifest.active_entries()}
    parsed: list[AdoptionPath] = []
    seen: set[str] = set()
    for index, row in enumerate(rows):
        if not isinstance(row, Mapping):
            raise InvalidPackageError(f"Protected preimage paths[{index}] is invalid")
        rel = _path(row.get("path"), f"paths[{index}].path")
        if rel in seen:
            raise InvalidPackageError("Protected preimage paths contain a duplicate")
        seen.add(rel)
        entry = entries.get(rel)
        previous = prior.files.get(rel)
        destination = join_under_nofollow(target_root, rel)
        if entry is None or previous is None or entry.ownership_class == "external-state":
            raise InvalidPackageError("Protected preimage path is not an IDE-managed file", details={"path": rel})
        if path_is_symlink(destination) or not destination.is_file():
            raise InvalidPackageError("Protected preimage destination is missing or unsafe", details={"path": rel})
        source_digest = _digest(row.get("installedSourceDigest"), f"paths[{index}].installedSourceDigest")
        prior_digest = _digest(row.get("priorInstalledDigest"), f"paths[{index}].priorInstalledDigest")
        current_digest = _digest(row.get("currentDigest"), f"paths[{index}].currentDigest")
        git_blob = _oid(row.get("gitBlob"), f"paths[{index}].gitBlob")
        if source_digest != previous.source_hash or prior_digest != previous.content_hash:
            raise InvalidPackageError("Protected preimage installed-state identity is stale", details={"path": rel})
        actual_digest = sha256_file(destination)
        if actual_digest != current_digest or actual_digest == prior_digest:
            raise InvalidPackageError("Protected preimage current bytes are stale", details={"path": rel})
        protected_blob = _git(target_root, "rev-parse", "--verify", f"{commit}:{rel}")
        head_blob = _git(target_root, "rev-parse", "--verify", f"HEAD:{rel}")
        ancestor_blob = _git(target_root, "rev-parse", "--verify", f"{ancestor}:{rel}")
        actual_blob = _git(target_root, "hash-object", "--no-filters", "--", rel)
        if protected_blob != git_blob or head_blob != git_blob or actual_blob != git_blob:
            raise InvalidPackageError("Protected preimage blob identity is stale", details={"path": rel})
        if ancestor_blob == protected_blob:
            raise InvalidPackageError("Protected preimage path was not changed by the protected commit", details={"path": rel})
        parsed.append(
            AdoptionPath(
                path=rel,
                installed_source_digest=source_digest,
                prior_installed_digest=prior_digest,
                current_digest=current_digest,
                git_blob=git_blob,
            )
        )

    return ProtectedPreimageAdoption(
        receipt_path=receipt_path.resolve(strict=False),
        target_worktree=target_worktree,
        package_version=SAME_VERSION_REPAIR_VERSION,
        installed_manifest_digest=installed_manifest_digest,
        repository=_normalize_remote(repository),
        base_ref=base_ref,
        base_commit=base_commit,
        commit=commit,
        tree=tree,
        ancestor=ancestor,
        paths=tuple(sorted(parsed, key=lambda item: item.path)),
        receipt_digest="sha256:" + hashlib.sha256(raw_bytes).hexdigest(),
    )
