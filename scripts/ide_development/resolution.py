"""Fail-closed v2 managed-core upgrade resolution receipts."""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

from .errors import InvalidPackageError
from .hashing import sha256_file
from .paths import as_posix_rel, path_is_symlink

HEX40 = re.compile(r"^[0-9a-f]{40}$")
DIGEST = re.compile(r"^sha256:[0-9a-f]{64}$")
KIND = "ide-managed-upgrade-resolution"
PROVIDER_REPOSITORY = "linktrend/IDE-Development"
PROVIDER_AUTHORITATIVE_REF = "phase/ide-v2.5.2"
PROVIDER_INSTALLER_VERSION = "2.5.2"
# v2.5.2 is immutable.  The extracted package has no .git directory, so the
# provider commit/tree must be bound by the receipt rather than discovered
# from the package root.
PROVIDER_COMMIT = "2c67523e6b4a0c598224d7905f20343f16254a3f"
PROVIDER_TREE = "77ee2fdb6203732cf750f25c32920b53ef2c8b9b"
PROVIDER_OWNERSHIP_CLASSES = frozenset({"managed", "managed-core", "managed-entrypoint"})
PROVIDER_MIGRATION_PATH = ".github/linktrend-secret-scan-fixtures.json"
PROVIDER_MIGRATION_SOURCE = (
    "core/managed-core/migrations/known-bytes/"
    "linktrading-secret-scan-fixtures-v2.5.2.json"
)
PROVIDER_MIGRATION_CONSUMER_COMMIT = "3e35cb314010a4b4f7678faf764947b4dd34807a"
PROVIDER_MIGRATION_CONSUMER_TREE = "a5c9b0f024b6d78c18ab9a5d35b4935e7a6181d4"
PROVIDER_MIGRATION_BASELINE = "sha256:cd3a24fef8347d5447b6c657b0329f3640c86150c4976e4eda0ce34cb09352e1"
PROVIDER_MIGRATION_CURRENT = "sha256:498e1dea0915a09d40eca1379d4e13e52f0027800f2e94aea07bca8374428ec3"
# These are the only managed files that the IDE provider may supersede in a
# digest-bound upgrade. Keep this set explicit so a provider manifest cannot
# become implicit overwrite authority.
ALLOWED_CONFLICT_PATHS = frozenset({
    ".ide-development/schemas/managed-upgrade-resolution.schema.json",
    ".ide-development/schemas/phase-handoff.schema.json",
    ".ide-development/schemas/phase-record.schema.json",
    ".ide-development/tests/test_delivery_controller.py",
    ".ide-development/tests/test_phase_packager_coordinator.py",
    ".ide-development/tests/test_receipt_seal_and_recovery.py",
    ".ide-development/workflows/linktrend-integrator-merge.yml",
    "scripts/gitops/delivery_controller.py",
    "scripts/gitops/github_auth.py",
    "scripts/gitops/issue_checkpoint.py",
    "scripts/gitops/packager_coordinator.py",
    "scripts/gitops/phase_integrator.py",
    "scripts/gitops/receipt_seal.py",
    "scripts/gitops/secret_scan.py",
    "scripts/ide_development/resolution.py",
})
CHANGE_SCOPED_EVIDENCE_KEY = "changeScopedSecretScan"
CHANGE_SCOPED_EVIDENCE_REQUIRED = frozenset({
    "schemaVersion",
    "kind",
    "repository",
    "authoritativeRemoteRef",
    "baselineCommit",
    "baselineTree",
    "candidateCommit",
    "candidateGitTree",
    "scannerPolicyVersion",
    "managedPaths",
    "configDigest",
    "findings",
})


@dataclass(frozen=True)
class ConflictResolution:
    path: str
    old_digest: str
    current_digest: str
    provider_digest: str
    decision: str

    def to_dict(self) -> dict[str, str]:
        return {"path": self.path, "oldDigest": self.old_digest, "currentDigest": self.current_digest, "providerDigest": self.provider_digest, "decision": self.decision}


@dataclass(frozen=True)
class ProviderSupersedesMigration:
    path: str
    source: str
    old_digest: str
    current_digest: str
    provider_digest: str
    old_bytes: int
    current_bytes: int
    provider_bytes: int
    consumer_commit: str
    consumer_tree: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "path": self.path,
            "startingConsumer": {"commit": self.consumer_commit, "tree": self.consumer_tree},
            "installedBaseline": {"bytes": self.old_bytes, "sha256": self.old_digest},
            "currentConsumer": {"bytes": self.current_bytes, "sha256": self.current_digest},
            "provider": {"source": self.source, "bytes": self.provider_bytes, "sha256": self.provider_digest},
            "decision": "provider-supersedes",
        }


@dataclass(frozen=True)
class UpgradeResolution:
    path: Path
    repository: str
    target_worktree: str
    commit: str
    tree: str
    provider_repository: str
    provider_authoritative_ref: str
    provider_commit: str
    provider_tree: str
    provider_installer_version: str
    provider_source_digest: str
    package_version: str
    conflicts: tuple[ConflictResolution, ...]
    manifest_digest: str
    installed_state_digest: str
    verification: dict[str, Any]
    raw_digest: str
    provider_migrations: tuple[ProviderSupersedesMigration, ...] = ()

    @property
    def paths(self) -> frozenset[str]:
        return frozenset(item.path for item in self.conflicts)

    def to_dict(self) -> dict[str, Any]:
        return {"kind": KIND, "schemaVersion": 2, "repository": self.repository, "targetWorktree": self.target_worktree, "consumer": {"commit": self.commit, "tree": self.tree}, "provider": {"repository": self.provider_repository, "authoritativeRef": self.provider_authoritative_ref, "commit": self.provider_commit, "tree": self.provider_tree, "installerVersion": self.provider_installer_version, "packageSourceDigest": self.provider_source_digest}, "packageVersion": self.package_version, "manifestDigest": self.manifest_digest, "installedStateDigest": self.installed_state_digest, "conflicts": [item.to_dict() for item in self.conflicts], "providerSupersedesMigrations": [item.to_dict() for item in self.provider_migrations], "verification": self.verification, "resolutionDigest": self.raw_digest}

    @property
    def provider_migration_sources(self) -> dict[str, str]:
        return {item.path: item.source for item in self.provider_migrations}


def _git(root: Path, *args: str) -> str:
    result = subprocess.run(["git", *args], cwd=root, text=True, capture_output=True, check=False)
    if result.returncode:
        raise InvalidPackageError("Cannot verify Git identity for managed upgrade resolution", details={"stderr": result.stderr.strip()})
    return result.stdout.strip()


def _digest(value: Any, field: str) -> str:
    if not isinstance(value, str) or not DIGEST.fullmatch(value):
        raise InvalidPackageError(f"Resolution {field} must be a sha256 digest")
    return value


def _oid(value: Any, field: str) -> str:
    if not isinstance(value, str) or not HEX40.fullmatch(value):
        raise InvalidPackageError(f"Resolution {field} must be a 40-character Git OID")
    return value


def _status_paths(root: Path) -> list[str]:
    out = _git(root, "status", "--porcelain=v1", "--untracked-files=all")
    paths: list[str] = []
    for line in out.splitlines():
        if len(line) < 3 or "->" in line or line[:2][0] in "RC" or line[:2][1] in "RC":
            raise InvalidPackageError("Resolution refuses malformed or rename/copy Git state")
        if line[:2] == "!!":
            continue
        # _git() trims the command's surrounding whitespace, so an unstaged
        # ` M path` record may arrive as `M path`.  Parse after the two status
        # columns and the separator instead of dropping the first path byte.
        paths.append(as_posix_rel(line[2:].lstrip(" ")))
    return paths


def _path(value: Any) -> str:
    if not isinstance(value, str) or any(ch in value for ch in "*?[]"):
        raise InvalidPackageError("Resolution path must be an exact non-wildcard string")
    normalized = as_posix_rel(value)
    if normalized != value:
        raise InvalidPackageError(f"Resolution path must be normalized: {value!r}")
    return normalized


def _resolution_raw(path: Path) -> dict[str, Any]:
    if not path.is_file() or path.is_symlink():
        raise InvalidPackageError(f"Resolution manifest must be a physical file: {path}")
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise InvalidPackageError(f"Resolution manifest is not valid JSON: {path}") from exc
    if not isinstance(raw, dict):
        raise InvalidPackageError("Resolution manifest must be a JSON object")
    return raw


def load_provider_migration_hints(resolution_path: Path | None) -> dict[str, str]:
    """Read only the exact source mapping needed to build a migration plan."""
    if resolution_path is None:
        return {}
    raw = _resolution_raw(resolution_path)
    rows = raw.get("providerSupersedesMigrations", [])
    if rows == []:
        return {}
    if not isinstance(rows, list) or len(rows) != 1:
        raise InvalidPackageError("Provider supersedes migrations must contain exactly one migration")
    row = rows[0]
    if not isinstance(row, dict):
        raise InvalidPackageError("Provider supersedes migration must be an object")
    path = _path(row.get("path"))
    provider = row.get("provider")
    if path != PROVIDER_MIGRATION_PATH or not isinstance(provider, dict):
        raise InvalidPackageError("Provider supersedes migration path is not the authorized exact path")
    source = provider.get("source")
    if not isinstance(source, str) or source != PROVIDER_MIGRATION_SOURCE:
        raise InvalidPackageError("Provider supersedes migration source is not the authorized exact preimage")
    return {path: source}


def _canonical_digest(value: Any) -> str:
    """Digest an evidence object without allowing JSON formatting ambiguity."""
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return "sha256:" + hashlib.sha256(encoded).hexdigest()


def _package_source_digest(
    package_root: Path,
    manifest: dict[str, Any],
    *,
    manifest_digest: str,
    provider: dict[str, Any],
    provider_commit: str,
    provider_tree: str,
) -> str:
    """Return the portable, digest-bound identity of an extracted package.

    Release-candidate archives deliberately omit ``.git``.  The manifest and
    every physical source hash therefore form the package identity, with the
    immutable provider provenance included so an old receipt cannot be reused
    for a different source identity.
    """
    rows: list[dict[str, Any]] = []
    for entry in manifest.get("files", []):
        if not isinstance(entry, dict):
            raise InvalidPackageError("Resolution provider MANIFEST contains an invalid file entry")
        source = entry.get("source")
        if not isinstance(source, str) or as_posix_rel(source) != source:
            raise InvalidPackageError("Resolution provider MANIFEST source path is invalid")
        source_path = package_root / source
        if source_path.is_symlink() or not source_path.is_file():
            raise InvalidPackageError(f"Resolution provider source is missing or unsafe: {source}")
        declared = _digest(entry.get("sourceHash"), f"provider.manifest.{source}.sourceHash")
        actual = sha256_file(source_path)
        if actual != declared:
            raise InvalidPackageError(f"Resolution provider source identity is stale: {source}")
        rows.append({
            "source": source,
            "sourceHash": actual,
            "destination": entry.get("destination"),
            "mode": entry.get("mode"),
            "ownershipClass": entry.get("ownershipClass"),
            "platform": entry.get("platform"),
            "os": entry.get("os", "all"),
            "mergeStrategy": entry.get("mergeStrategy"),
        })
    rows.sort(key=lambda item: (item["source"], item["destination"]))
    return _canonical_digest({
        "schemaVersion": 1,
        "repository": provider.get("repository"),
        "authoritativeRef": provider.get("authoritativeRef"),
        "commit": provider_commit,
        "tree": provider_tree,
        "packageVersion": manifest.get("packageVersion"),
        "manifestDigest": manifest_digest,
        "files": rows,
    })


def _validate_provider_source_identity(
    package_root: Path,
    manifest: dict[str, Any],
    *,
    manifest_digest: str,
    provider: dict[str, Any],
    provider_commit: str,
    provider_tree: str,
) -> str:
    if provider.get("repository") != PROVIDER_REPOSITORY or provider.get("authoritativeRef") != PROVIDER_AUTHORITATIVE_REF:
        raise InvalidPackageError("Resolution provider repository/ref identity is invalid")
    if provider_commit != PROVIDER_COMMIT or provider_tree != PROVIDER_TREE:
        raise InvalidPackageError("Resolution provider commit/tree identity is invalid")
    expected = _package_source_digest(
        package_root,
        manifest,
        manifest_digest=manifest_digest,
        provider=provider,
        provider_commit=provider_commit,
        provider_tree=provider_tree,
    )
    actual = _digest(provider.get("packageSourceDigest"), "provider.packageSourceDigest")
    if actual != expected:
        raise InvalidPackageError("Resolution provider package source identity is stale")
    return actual


def _validate_provider_entry(entry: Any, rel: str) -> None:
    if not isinstance(entry, dict) or entry.get("ownershipClass") not in PROVIDER_OWNERSHIP_CLASSES or entry.get("mergeStrategy") != "replace":
        raise InvalidPackageError(f"Provider source/digest is not bound to MANIFEST for {rel}")


def _validate_observed_conflict_paths(
    paths: Iterable[str], *, exact_additional_paths: Iterable[str] = ()
) -> frozenset[str]:
    """Require a non-empty observed subset of the explicit provider allowlist."""
    observed = frozenset(paths)
    if not observed:
        raise InvalidPackageError("Observed conflicts must contain at least one managed path")
    additional = frozenset(_path(path) for path in exact_additional_paths)
    if not observed.issubset(ALLOWED_CONFLICT_PATHS | additional):
        raise InvalidPackageError("Observed conflicts contain an undeclared managed path")
    return observed


def _validate_change_scoped_binding(verification: dict[str, Any]) -> None:
    """Validate the receipt envelope before any transaction can begin.

    The target scanner performs repository/Git/config validation after the
    package is materialized.  This preflight only validates the immutable
    envelope and evidence shape, preventing malformed or silently omitted
    evidence from reaching the post-install hook.
    """
    if CHANGE_SCOPED_EVIDENCE_KEY not in verification:
        return
    binding = verification.get(CHANGE_SCOPED_EVIDENCE_KEY)
    if not isinstance(binding, dict) or set(binding) != {"evidence", "evidenceDigest"}:
        raise InvalidPackageError(
            "Change-scoped secret-scan binding must contain only evidence and evidenceDigest"
        )
    evidence = binding.get("evidence")
    if not isinstance(evidence, dict) or set(evidence) - (CHANGE_SCOPED_EVIDENCE_REQUIRED | {"candidateTree"}):
        raise InvalidPackageError("Change-scoped secret-scan evidence has unknown fields")
    if CHANGE_SCOPED_EVIDENCE_REQUIRED - set(evidence):
        raise InvalidPackageError("Change-scoped secret-scan evidence is missing required identity")
    if evidence.get("schemaVersion") != 1 or evidence.get("kind") != "change-scoped-secret-scan-evidence":
        raise InvalidPackageError("Change-scoped secret-scan evidence schema/kind is invalid")
    if not isinstance(evidence.get("managedPaths"), list) or not evidence["managedPaths"]:
        raise InvalidPackageError("Change-scoped secret-scan managed path identity is required")
    if not isinstance(evidence.get("findings"), list):
        raise InvalidPackageError("Change-scoped secret-scan findings must be an array")
    if _digest(binding.get("evidenceDigest"), "changeScopedSecretScan.evidenceDigest") != _canonical_digest(evidence):
        raise InvalidPackageError("Change-scoped secret-scan evidence digest is stale")


def _validate_provider_migration(
    row: Any,
    *,
    target_root: Path,
    package_root: Path,
    consumer_commit: str,
    consumer_tree: str,
    manifest: dict[str, Any],
) -> ProviderSupersedesMigration:
    if not isinstance(row, dict) or row.get("decision") != "provider-supersedes":
        raise InvalidPackageError("Provider supersedes migration decision is invalid")
    path = _path(row.get("path"))
    if path != PROVIDER_MIGRATION_PATH:
        raise InvalidPackageError("Provider supersedes migration path is not authorized")
    starting = row.get("startingConsumer")
    if not isinstance(starting, dict) or starting.get("commit") != consumer_commit or starting.get("tree") != consumer_tree:
        raise InvalidPackageError("Provider supersedes migration starting consumer identity is stale")
    baseline = row.get("installedBaseline")
    current = row.get("currentConsumer")
    provider = row.get("provider")
    if not isinstance(baseline, dict) or not isinstance(current, dict) or not isinstance(provider, dict):
        raise InvalidPackageError("Provider supersedes migration file identities are incomplete")
    old_digest = _digest(baseline.get("sha256"), f"{path}.installedBaseline")
    current_digest = _digest(current.get("sha256"), f"{path}.currentConsumer")
    provider_digest = _digest(provider.get("sha256"), f"{path}.provider")
    if old_digest != PROVIDER_MIGRATION_BASELINE or current_digest != PROVIDER_MIGRATION_CURRENT:
        raise InvalidPackageError("Provider supersedes migration consumer preimage is not the recorded exact correction")
    if old_digest == current_digest:
        raise InvalidPackageError("Provider supersedes migration must describe a distinct dirty correction")
    source = provider.get("source")
    if not isinstance(source, str) or _path(source) != PROVIDER_MIGRATION_SOURCE:
        raise InvalidPackageError("Provider supersedes migration provider source is not exact")
    provider_source = package_root / source
    if provider_source.is_symlink() or not provider_source.is_file():
        raise InvalidPackageError("Provider supersedes migration preimage is missing or unsafe")
    manifest_sources = {
        entry.get("source")
        for entry in manifest.get("files", [])
        if isinstance(entry, dict)
    }
    if source not in manifest_sources:
        raise InvalidPackageError("Provider supersedes migration preimage is not in the package manifest")
    if sha256_file(provider_source) != provider_digest or provider_source.stat().st_size != provider.get("bytes"):
        raise InvalidPackageError("Provider supersedes migration provider preimage is stale")
    destination = target_root / path
    if destination.is_symlink() or not destination.is_file():
        raise InvalidPackageError("Provider supersedes migration consumer path is not a regular file")
    if sha256_file(destination) != current_digest or destination.stat().st_size != current.get("bytes"):
        raise InvalidPackageError("Provider supersedes migration current consumer preimage is stale")
    if not isinstance(baseline.get("bytes"), int) or baseline.get("bytes") < 0:
        raise InvalidPackageError("Provider supersedes migration baseline byte count is invalid")
    return ProviderSupersedesMigration(
        path=path,
        source=source,
        old_digest=old_digest,
        current_digest=current_digest,
        provider_digest=provider_digest,
        old_bytes=baseline["bytes"],
        current_bytes=current["bytes"],
        provider_bytes=provider["bytes"],
        consumer_commit=consumer_commit,
        consumer_tree=consumer_tree,
    )


def load_and_validate_resolution(resolution_path: Path, *, target_root: Path, package_root: Path, package_version: str, package_manifest_digest: str, prior_package_version: str | None, prior_installed_state_digest: str | None = None, observed_conflicts: Iterable[tuple[str, str, str, str]], observed_migrations: Iterable[tuple[str, str, str, str]] = ()) -> UpgradeResolution:
    path = resolution_path.resolve(strict=False)
    try:
        raw_bytes = path.read_bytes()
        raw = json.loads(raw_bytes.decode("utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise InvalidPackageError(f"Resolution manifest is not valid JSON: {path}") from exc
    if not isinstance(raw, dict) or raw.get("kind") != KIND or raw.get("schemaVersion") != 2:
        raise InvalidPackageError("Unsupported managed-upgrade resolution manifest kind/version")
    dangerous = {"force", "wildcard", "autoMerge", "merge", "preferIncoming", "preferProvider", "overwrite"}
    if any(key in dangerous for key in raw):
        raise InvalidPackageError("Resolution refuses force, wildcard, merge, or overwrite controls")
    target_worktree = raw.get("targetWorktree")
    if not isinstance(target_worktree, str) or str(Path(target_worktree).resolve(strict=False)) != str(target_root.resolve()):
        raise InvalidPackageError("Resolution targetWorktree does not exactly match target")
    consumer = raw.get("consumer")
    if not isinstance(consumer, dict) or not {"commit", "tree"}.issubset(consumer):
        raise InvalidPackageError("Resolution consumer commit/tree identity is required")
    commit, tree = _oid(consumer["commit"], "consumer.commit"), _oid(consumer["tree"], "consumer.tree")
    actual = (_git(target_root, "rev-parse", "--verify", "HEAD^{commit}"), _git(target_root, "rev-parse", "--verify", "HEAD^{tree}"))
    if (commit, tree) != actual:
        raise InvalidPackageError("Resolution consumer Git identity is stale")
    migration_rows = raw.get("providerSupersedesMigrations", [])
    if migration_rows == []:
        migrations: tuple[ProviderSupersedesMigration, ...] = ()
    elif not isinstance(migration_rows, list) or len(migration_rows) != 1:
        raise InvalidPackageError("Provider supersedes migrations must contain exactly one migration")
    else:
        migrations = ()  # validated after provider/package identity is available
    status = _status_paths(target_root)
    migration_paths = {
        _path(row.get("path"))
        for row in migration_rows
        if isinstance(row, dict) and row.get("path") is not None
    }
    if status and set(status) != migration_paths:
        raise InvalidPackageError("Resolution requires a clean consumer worktree except for the exact provider migration", details={"paths": status})
    if migration_rows and migration_paths != {PROVIDER_MIGRATION_PATH}:
        raise InvalidPackageError("Provider supersedes migration path set is not exact")
    provider = raw.get("provider")
    required_provider = {"repository", "authoritativeRef", "commit", "tree", "installerVersion", "phasePullRequest", "independentVerificationReceipt", "managedPackageManifest"}
    if not isinstance(provider, dict) or not required_provider.issubset(provider):
        raise InvalidPackageError("Resolution provider provenance is incomplete")
    provider_commit, provider_tree = _oid(provider["commit"], "provider.commit"), _oid(provider["tree"], "provider.tree")
    if provider.get("repository") != PROVIDER_REPOSITORY or provider.get("authoritativeRef") != PROVIDER_AUTHORITATIVE_REF:
        raise InvalidPackageError("Resolution provider repository/ref identity is invalid")
    if provider_commit != PROVIDER_COMMIT or provider_tree != PROVIDER_TREE:
        raise InvalidPackageError("Resolution provider commit/tree identity is invalid")
    managed = provider["managedPackageManifest"]
    if provider["installerVersion"] != PROVIDER_INSTALLER_VERSION or not isinstance(managed, dict) or managed.get("path") != "core/managed-core/MANIFEST.json":
        raise InvalidPackageError("Resolution provider package provenance is invalid")
    manifest_path = package_root / "core/managed-core/MANIFEST.json"
    if manifest_path.is_symlink() or not manifest_path.is_file() or managed.get("bytes") != manifest_path.stat().st_size or _digest(managed.get("sha256"), "provider.managedPackageManifest.sha256") != package_manifest_digest:
        raise InvalidPackageError("Resolution provider MANIFEST digest/size is stale")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    provider_source_digest = _validate_provider_source_identity(
        package_root,
        manifest,
        manifest_digest=package_manifest_digest,
        provider=provider,
        provider_commit=provider_commit,
        provider_tree=provider_tree,
    )
    if raw.get("allowedConflictPaths") != sorted(ALLOWED_CONFLICT_PATHS):
        raise InvalidPackageError("Resolution allowedConflictPaths must exactly equal canonical scanner paths")
    expected = {rel: (old, current, provider_hash) for rel, old, current, provider_hash in observed_conflicts}
    migration_expected = {rel: (old, current, provider_hash) for rel, old, current, provider_hash in observed_migrations}
    if migration_rows:
        migration_row = migration_rows[0]
        migration_provider = migration_row.get("provider") if isinstance(migration_row, dict) else None
        migration_baseline = migration_row.get("installedBaseline") if isinstance(migration_row, dict) else None
        migration_current = migration_row.get("currentConsumer") if isinstance(migration_row, dict) else None
        if not all(isinstance(item, dict) for item in (migration_baseline, migration_current, migration_provider)):
            raise InvalidPackageError("Provider supersedes migration file identities are incomplete")
        declared_migration = (
            _digest(migration_baseline.get("sha256"), f"{PROVIDER_MIGRATION_PATH}.installedBaseline"),
            _digest(migration_current.get("sha256"), f"{PROVIDER_MIGRATION_PATH}.currentConsumer"),
            _digest(migration_provider.get("sha256"), f"{PROVIDER_MIGRATION_PATH}.provider"),
        )
        if migration_expected != {PROVIDER_MIGRATION_PATH: declared_migration}:
            raise InvalidPackageError("Provider migration does not exactly match the observed correction")
    elif migration_expected:
        raise InvalidPackageError("Observed provider migration is not declared")
    observed_paths = _validate_observed_conflict_paths(expected)
    rows = raw.get("conflicts")
    if not isinstance(rows, list) or len(rows) != len(observed_paths) or {row.get("path") for row in rows if isinstance(row, dict)} != observed_paths:
        raise InvalidPackageError("Resolution conflicts do not exactly match observed managed paths")
    entries = {entry.get("destination"): entry for entry in manifest.get("files", [])}
    resolutions: list[ConflictResolution] = []
    for row in rows:
        if not isinstance(row, dict) or row.get("decision") != "provider-supersedes":
            raise InvalidPackageError("Every conflict requires explicit provider-supersedes decision")
        rel = _path(row.get("path"))
        old = _digest(row.get("installedBaseline", {}).get("sha256"), f"{rel}.installedBaseline")
        current = _digest(row.get("currentConsumer", {}).get("sha256"), f"{rel}.currentConsumer")
        provider_hash = _digest(row.get("provider", {}).get("sha256"), f"{rel}.provider")
        for field, row_key, digest in (("installedBaseline", "installedBaseline", old), ("currentConsumer", "currentConsumer", current), ("provider", "provider", provider_hash)):
            declared_bytes = row.get(row_key, {}).get("bytes")
            if not isinstance(declared_bytes, int) or declared_bytes < 0:
                raise InvalidPackageError(f"Resolution {rel}.{field}.bytes is required")
            if field == "currentConsumer" and declared_bytes != (target_root / rel).stat().st_size:
                raise InvalidPackageError(f"Resolution current byte size is stale: {rel}")
        if (old, current, provider_hash) != expected[rel]:
            raise InvalidPackageError(f"Resolution digest is stale for conflict path: {rel}")
        entry = entries.get(rel)
        _validate_provider_entry(entry, rel)
        if row["provider"].get("source") != entry.get("source") or provider_hash != entry.get("sourceHash"):
            raise InvalidPackageError(f"Provider source/digest is not bound to MANIFEST for {rel}")
        provider_source = package_root / entry["source"]
        if not provider_source.is_file() or provider_source.is_symlink() or row["provider"].get("bytes") != provider_source.stat().st_size or sha256_file(provider_source) != provider_hash:
            raise InvalidPackageError(f"Provider source byte preimage is stale for {rel}")
        dest = target_root / rel
        if path_is_symlink(dest) or not dest.is_file() or sha256_file(dest) != current:
            raise InvalidPackageError(f"Current consumer digest no longer matches: {rel}")
        resolutions.append(ConflictResolution(rel, old, current, provider_hash, "provider_supersedes"))
    baseline = raw.get("installedBaseline", {}).get("installedStatePreimage", {})
    state = target_root / ".ide-development/installed-state.json"
    baseline_digest = _digest(baseline.get("sha256"), "installedStatePreimage.sha256")
    if baseline.get("path") != ".ide-development/installed-state.json" or not state.is_file() or baseline.get("bytes") != state.stat().st_size or baseline_digest != sha256_file(state):
        raise InvalidPackageError("Installed-state preimage is stale")
    if prior_installed_state_digest and prior_installed_state_digest != sha256_file(state):
        raise InvalidPackageError("Installed-state digest changed since planning")
    verification = raw.get("verification")
    if not isinstance(verification, dict) or verification.get("providerReceipt") != provider["independentVerificationReceipt"] or verification.get("providerTreeRequired") is not True or verification.get("consumerTreeRequired") is not True or verification.get("noUpstreamScanOrMutation") is not True:
        raise InvalidPackageError("Independent verification receipt is incomplete or mismatched")
    _validate_change_scoped_binding(verification)
    checks = verification.get("canonicalProviderChecks")
    required_cases = {
        "quoted member and call references are non-findings",
        "binary and undecodable inputs are typed nonblocking skipped_input",
        "oversized decodable text is scanned fully",
        "recognized and high-entropy credential literals remain blocking",
        "stale identity, configuration, and path-set evidence fails closed",
    }
    if not isinstance(checks, dict) or checks.get("fullFixtureAwareSuite") != "41/41 passed" or checks.get("focusedSuite") != "20/20 passed" or set(checks.get("requiredCases", [])) != required_cases:
        raise InvalidPackageError("Canonical provider verification semantics are incomplete")
    rollback = raw.get("backupAndRollback")
    if not isinstance(rollback, dict) or rollback.get("backupRequiredBeforeApply") is not True or rollback.get("transactionRequired") is not True or rollback.get("manualOverwriteForbidden") is not True:
        raise InvalidPackageError("Backup/rollback transaction proof is incomplete")
    resolution = raw.get("resolution")
    if not isinstance(resolution, dict) or resolution.get("deferredPaths") != [] or resolution.get("noExtraPaths") is not True:
        raise InvalidPackageError("Resolution contains deferred or extra paths")
    if prior_package_version is not None and package_version < prior_package_version:
        raise InvalidPackageError("Managed upgrade resolution refuses package downgrade")
    if migration_rows:
        migrations = (_validate_provider_migration(
            migration_rows[0],
            target_root=target_root,
            package_root=package_root,
            consumer_commit=commit,
            consumer_tree=tree,
            manifest=manifest,
        ),)
    return UpgradeResolution(path, str(raw.get("repository", "")), target_worktree, commit, tree, str(provider["repository"]), str(provider["authoritativeRef"]), provider_commit, provider_tree, str(provider["installerVersion"]), provider_source_digest, package_version, tuple(sorted(resolutions, key=lambda item: item.path)), package_manifest_digest, baseline_digest, verification, "sha256:" + hashlib.sha256(raw_bytes).hexdigest(), migrations)
