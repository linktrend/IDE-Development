#!/usr/bin/env python3
"""Rebuild, verify, and (optionally) publish managed-core immutable releases.

Trusted-default-branch helper for:
  .github/workflows/linktrend-managed-core-release-publisher.yml

Hard rules:
- Rebuild from the requested source tree; never reuse historical RC artifacts.
- Bind source SHA, package version, tag, manifest hash, and archive checksums.
- Fail closed on tag/release/checksum conflicts.
- Idempotent retry may continue only when an existing tag (if any) is bound to the
  requested commit and any existing release/assets match the exact
  source/version/manifest/checksum contract; otherwise refuse.
- Mutating GitHub calls require the trusted Mac Mini automation token.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Optional

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from ide_development.constants import (  # noqa: E402
    PACKAGE_NAME,
    PACKAGE_VERSION_TARGET,
)
from ide_development.release_candidate import (  # noqa: E402
    create_release_candidate,
    verify_release_candidate_archive,
)

RELEASE_SCHEMA_VERSION = 1
RELEASE_KIND = "ide-development-managed-core-release"
RELEASE_SCHEMA_REL = "core/managed-core/schemas/managed-core-release.schema.json"
PUBLISHER_ID = "linktrend-managed-core-release-publisher"
DEFAULT_TAG = f"v{PACKAGE_VERSION_TARGET}"
FULL_SHA_RE = re.compile(r"^[0-9a-f]{40}$")

ApiFn = Callable[[str, str, Optional[dict[str, Any]], Optional[bytes]], Any]


class ReleasePublishError(RuntimeError):
    """Fail-closed release publication error with stable code."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


@dataclass(frozen=True)
class Binding:
    source_sha: str
    version: str
    tag: str
    manifest_hash: str
    archives: list[dict[str, Any]]
    package_name: str = PACKAGE_NAME


@dataclass(frozen=True)
class PublicationState:
    """Remote tag/release observation relative to the requested binding."""

    tag_sha: str | None
    release: dict[str, Any] | None
    matched_assets: frozenset[str]
    missing_assets: frozenset[str]

    @property
    def complete(self) -> bool:
        return (
            self.tag_sha is not None
            and self.release is not None
            and not self.missing_assets
        )


def _reject(code: str, message: str) -> None:
    raise ReleasePublishError(code, message)


def _normalize_digest(value: str) -> str:
    raw = (value or "").strip().lower()
    if not raw:
        return ""
    if raw.startswith("sha256:"):
        return raw
    return f"sha256:{raw}"


def _release_asset_digests(release: dict[str, Any]) -> dict[str, str]:
    out: dict[str, str] = {}
    for asset in release.get("assets") or []:
        name = str(asset.get("name") or "")
        if not name:
            continue
        out[name] = _normalize_digest(str(asset.get("digest") or asset.get("sha256") or ""))
    return out


def _assert_release_matches_binding(binding: Binding, release: dict[str, Any]) -> None:
    """Fail closed unless an existing release matches source/version/tag/manifest."""
    tag_name = str(release.get("tag_name") or "")
    if tag_name and tag_name != binding.tag:
        _reject(
            "release_tag_conflict",
            f"release tag_name {tag_name} != requested {binding.tag}",
        )
    release_name = str(release.get("name") or "")
    expected_name = f"managed-core {binding.version}"
    if release_name and release_name != expected_name:
        _reject(
            "release_version_conflict",
            f"release name {release_name!r} != expected {expected_name!r}",
        )
    target = str(release.get("target_commitish") or "").strip().lower()
    if FULL_SHA_RE.fullmatch(target) and target != binding.source_sha:
        _reject(
            "release_source_conflict",
            f"release target_commitish {target} != requested {binding.source_sha}",
        )
    body = str(release.get("body") or "")
    source_marker = f"sourceCommit: `{binding.source_sha}`"
    manifest_marker = f"manifestHash: `{binding.manifest_hash}`"
    if source_marker not in body:
        _reject(
            "release_source_conflict",
            "existing release body does not bind the requested sourceCommit",
        )
    if manifest_marker not in body:
        _reject(
            "release_manifest_conflict",
            "existing release body does not bind the requested manifestHash",
        )


def _classify_release_assets(
    binding: Binding, release: dict[str, Any]
) -> tuple[frozenset[str], frozenset[str]]:
    """Return (matched, missing) archive names; fail closed on digest conflicts."""
    asset_digests = _release_asset_digests(release)
    matched: set[str] = set()
    missing: set[str] = set()
    for row in binding.archives:
        name = str(row["name"])
        local = _normalize_digest(str(row["sha256"]))
        if name not in asset_digests:
            missing.add(name)
            continue
        remote = asset_digests[name]
        if not remote:
            _reject(
                "checksum_unverified",
                f"existing release asset {name} has no digest; refuse unsafe retry",
            )
        if remote != local:
            _reject(
                "checksum_conflict",
                f"release asset {name} digest {remote} != rebuilt {local}",
            )
        matched.add(name)
    return frozenset(matched), frozenset(missing)


def require_automation_token(
    *,
    token: str | None = None,
    token_source: str | None = None,
) -> str:
    """Require the scoped built-in Actions token for release mutations."""
    source = (token_source or os.environ.get("AUTOMATION_TOKEN_SOURCE") or "builtin_github_token").strip()
    value = (token or os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN") or "").strip()
    if source != "builtin_github_token":
        _reject("automation_credentials_blocked", "release publisher requires scoped built-in token")
    if not value:
        _reject(
            "automation_credentials_blocked",
            "scoped built-in GitHub token missing",
        )
    return value


def github_api(
    method: str,
    url: str,
    *,
    token: str,
    body: dict[str, Any] | None = None,
    raw_body: bytes | None = None,
    content_type: str | None = None,
) -> Any:
    data: bytes | None
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": PUBLISHER_ID,
    }
    if raw_body is not None:
        data = raw_body
        headers["Content-Type"] = content_type or "application/octet-stream"
    elif body is not None:
        data = json.dumps(body).encode("utf-8")
        headers["Content-Type"] = "application/json"
    else:
        data = None
    req = urllib.request.Request(url, data=data, headers=headers, method=method.upper())
    try:
        with urllib.request.urlopen(req) as resp:
            raw = resp.read()
            if not raw:
                return None
            ctype = (resp.headers.get("Content-Type") or "").lower()
            if "json" in ctype or raw[:1] in (b"{", b"["):
                return json.loads(raw.decode("utf-8"))
            return raw
    except urllib.error.HTTPError as e:
        detail = e.read().decode("utf-8", errors="replace")
        raise ReleasePublishError(
            "github_api_error",
            f"API {method.upper()} {url} -> {e.code}: {detail}",
        ) from e


def fetch_default_branch_tip(
    *,
    repository: str,
    default_branch: str,
    token: str,
    api: ApiFn | None = None,
) -> str:
    call = api or (
        lambda method, url, body=None, raw=None: github_api(
            method, url, token=token, body=body, raw_body=raw
        )
    )
    enc = urllib.parse.quote(default_branch, safe="")
    payload = call("GET", f"https://api.github.com/repos/{repository}/branches/{enc}", None, None)
    tip = ((payload or {}).get("commit") or {}).get("sha") or ""
    tip = str(tip).lower()
    if not FULL_SHA_RE.fullmatch(tip):
        _reject("default_branch_tip_invalid", "remote default-branch tip SHA missing/malformed")
    return tip


def bind_source_sha_to_default_tip(
    *,
    source_sha: str,
    repository: str,
    default_branch: str,
    token: str,
    api: ApiFn | None = None,
) -> str:
    tip = fetch_default_branch_tip(
        repository=repository,
        default_branch=default_branch,
        token=token,
        api=api,
    )
    want = source_sha.lower()
    if tip != want:
        _reject(
            "source_sha_mismatch",
            f"requested source_sha={want} does not equal {default_branch} tip={tip}",
        )
    return tip


def rebuild_from_source(
    *,
    source_root: Path,
    expected_version: str = PACKAGE_VERSION_TARGET,
    expected_source_sha: str,
    output_dir: Path | None = None,
    allow_dirty: bool = False,
    skip_install_verify: bool = False,
    baseline_sha: str | None = None,
    baseline_ref: str | None = None,
) -> Binding:
    """Rebuild archives from source_root using trusted packaging code."""
    root = source_root.resolve()
    if not root.is_dir():
        _reject("source_root_missing", f"source root missing: {root}")

    # Force the builder to hash/bind the intended immutable source commit.
    # create_release_candidate reads git HEAD; ensure callers checked out source_sha.
    result = create_release_candidate(
        repo_root=root,
        output_dir=output_dir,
        allow_dirty=allow_dirty,
        skip_install_verify=skip_install_verify,
        skip_evidence=False,
        candidate_baseline_sha=baseline_sha,
        candidate_baseline_ref=baseline_ref,
    )
    version = str(result.get("packageVersion") or "")
    source_commit = str(result.get("sourceCommit") or "").lower()
    manifest_hash = str(result.get("manifestHash") or "")
    archives = list(result.get("archives") or [])

    if version != expected_version:
        _reject(
            "version_binding_failed",
            f"rebuilt packageVersion={version} expected={expected_version}",
        )
    if source_commit != expected_source_sha.lower():
        _reject(
            "source_commit_binding_failed",
            f"rebuilt sourceCommit={source_commit} expected={expected_source_sha.lower()}",
        )
    if not manifest_hash.startswith("sha256:") or len(manifest_hash) != 71:
        _reject("manifest_hash_invalid", f"invalid manifestHash: {manifest_hash}")
    if len(archives) < 2:
        _reject("archives_incomplete", "expected tar.gz and zip archives")

    # Independent verify of each archive (extract + disposable install).
    for row in archives:
        rel = str(row.get("path") or "")
        archive_path = root / rel
        if not archive_path.is_file():
            # output_dir may be absolute outside repo_root relative layout
            if output_dir is not None:
                archive_path = Path(output_dir) / Path(rel).name
            if not archive_path.is_file():
                _reject("archive_missing", f"missing rebuilt archive for {rel}")
        verify_release_candidate_archive(
            archive_path=archive_path,
            expected_version=expected_version,
        )
        from ide_development.hashing import sha256_file

        digest = str(row.get("sha256") or "")
        file_digest = sha256_file(archive_path)
        if digest != file_digest:
            _reject(
                "checksum_mismatch",
                f"archive checksum drift for {archive_path.name}: meta={digest} file={file_digest}",
            )

    return Binding(
        source_sha=source_commit,
        version=version,
        tag=f"v{version}",
        manifest_hash=manifest_hash,
        archives=[
            {
                "format": a["format"],
                "name": Path(str(a["path"])).name,
                "path": a["path"],
                "sha256": a["sha256"],
                "bytes": a["bytes"],
            }
            for a in archives
        ],
    )


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def resolve_tag_object_sha(
    *,
    repository: str,
    tag: str,
    token: str,
    api: ApiFn | None = None,
) -> str | None:
    call = api or (
        lambda method, url, body=None, raw=None: github_api(
            method, url, token=token, body=body, raw_body=raw
        )
    )
    # GitHub expects path segments …/git/ref/tags/{tag}, not a single
    # URL-encoded "tags%2F…" segment (that 404s even when the tag exists).
    enc_tag = urllib.parse.quote(tag, safe="")
    try:
        ref = call(
            "GET",
            f"https://api.github.com/repos/{repository}/git/ref/tags/{enc_tag}",
            None,
            None,
        )
    except ReleasePublishError as e:
        if "-> 404:" in e.message:
            return None
        raise
    obj = (ref or {}).get("object") or {}
    sha = str(obj.get("sha") or "").lower()
    obj_type = str(obj.get("type") or "")
    if obj_type == "tag":
        tag_obj = call(
            "GET",
            f"https://api.github.com/repos/{repository}/git/tags/{sha}",
            None,
            None,
        )
        sha = str(((tag_obj or {}).get("object") or {}).get("sha") or "").lower()
    if sha and not FULL_SHA_RE.fullmatch(sha):
        _reject("tag_object_invalid", f"tag {tag} object SHA malformed")
    return sha or None


def resolve_release_by_tag(
    *,
    repository: str,
    tag: str,
    token: str,
    api: ApiFn | None = None,
) -> dict[str, Any] | None:
    call = api or (
        lambda method, url, body=None, raw=None: github_api(
            method, url, token=token, body=body, raw_body=raw
        )
    )
    enc = urllib.parse.quote(tag, safe="")
    try:
        return call(
            "GET",
            f"https://api.github.com/repos/{repository}/releases/tags/{enc}",
            None,
            None,
        )
    except ReleasePublishError as e:
        if "-> 404:" in e.message:
            return None
        raise


def assert_no_conflict_or_replay(
    *,
    binding: Binding,
    repository: str,
    token: str,
    api: ApiFn | None = None,
) -> PublicationState:
    """Fail closed on conflicts; allow consistent partial/complete retry.

    A retry may continue only when:
    - any existing tag is bound to the requested commit, and
    - any existing release/assets match the exact source/version/manifest/checksum
      contract.

    Complete identical publication is treated as idempotent replay success (no
    reject). Divergent tag/release/checksum state remains blocked.
    """
    existing_sha = resolve_tag_object_sha(
        repository=repository, tag=binding.tag, token=token, api=api
    )
    if existing_sha is not None and existing_sha != binding.source_sha:
        _reject(
            "tag_conflict",
            f"tag {binding.tag} exists at {existing_sha}, requested {binding.source_sha}",
        )

    existing_release = resolve_release_by_tag(
        repository=repository, tag=binding.tag, token=token, api=api
    )
    matched: frozenset[str] = frozenset()
    missing = frozenset(str(row["name"]) for row in binding.archives)
    if existing_release is not None:
        _assert_release_matches_binding(binding, existing_release)
        matched, missing = _classify_release_assets(binding, existing_release)

    return PublicationState(
        tag_sha=existing_sha,
        release=existing_release,
        matched_assets=matched,
        missing_assets=missing,
    )


def build_release_evidence(
    *,
    binding: Binding,
    repository: str,
    publication_status: str,
    release_url: str | None = None,
    release_id: int | None = None,
    dry_run: bool = False,
    notes: str = "",
) -> dict[str, Any]:
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    evidence = {
        "schemaVersion": RELEASE_SCHEMA_VERSION,
        "kind": RELEASE_KIND,
        "packageName": binding.package_name,
        "packageVersion": binding.version,
        "tag": binding.tag,
        "sourceCommit": binding.source_sha,
        "manifestHash": binding.manifest_hash,
        "repository": repository,
        "releaseUrl": release_url,
        "releaseId": release_id,
        "archives": [
            {
                "format": a["format"],
                "name": a["name"],
                "sha256": a["sha256"],
                "bytes": a["bytes"],
            }
            for a in binding.archives
        ],
        "publisher": PUBLISHER_ID,
        "publicationStatus": publication_status,
        "dryRun": dry_run,
        "createdAt": now,
        "locator": {
            "tag": binding.tag,
            "sourceCommit": binding.source_sha,
            "manifestHash": binding.manifest_hash,
            "primaryArchive": next(
                (
                    {
                        "format": a["format"],
                        "name": a["name"],
                        "sha256": a["sha256"],
                        "bytes": a["bytes"],
                    }
                    for a in binding.archives
                    if a["format"] == "tar.gz"
                ),
                {
                    "format": binding.archives[0]["format"],
                    "name": binding.archives[0]["name"],
                    "sha256": binding.archives[0]["sha256"],
                    "bytes": binding.archives[0]["bytes"],
                },
            ),
        },
    }
    if notes:
        evidence["notes"] = notes
    return evidence


def create_tag_and_release(
    *,
    binding: Binding,
    repository: str,
    token: str,
    archive_paths: dict[str, Path],
    api: ApiFn | None = None,
) -> dict[str, Any]:
    """Create or complete tag/release/assets idempotently under fail-closed checks."""
    call = api or (
        lambda method, url, body=None, raw=None: github_api(
            method, url, token=token, body=body, raw_body=raw
        )
    )
    existing_sha = resolve_tag_object_sha(
        repository=repository, tag=binding.tag, token=token, api=api
    )
    tag_obj_sha = ""
    if existing_sha is None:
        # Annotated tag object + ref.
        tag_payload = call(
            "POST",
            f"https://api.github.com/repos/{repository}/git/tags",
            {
                "tag": binding.tag,
                "message": (
                    f"managed-core {binding.version}\n\n"
                    f"sourceCommit={binding.source_sha}\n"
                    f"manifestHash={binding.manifest_hash}\n"
                ),
                "object": binding.source_sha,
                "type": "commit",
                "tagger": {
                    "name": "LiNKtrend GitOps",
                    "email": "gitops@linktrend.local",
                    "date": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
                },
            },
            None,
        )
        tag_obj_sha = str((tag_payload or {}).get("sha") or "")
        if not tag_obj_sha:
            _reject("tag_create_failed", "git tag object SHA missing from API response")
        call(
            "POST",
            f"https://api.github.com/repos/{repository}/git/refs",
            {"ref": f"refs/tags/{binding.tag}", "sha": tag_obj_sha},
            None,
        )
    elif existing_sha != binding.source_sha:
        _reject(
            "tag_conflict",
            f"tag {binding.tag} exists at {existing_sha}, requested {binding.source_sha}",
        )
    else:
        # Tag already points at the requested commit; continue to release/assets.
        tag_obj_sha = existing_sha

    body_lines = [
        f"Immutable managed-core release `{binding.version}`.",
        "",
        f"- sourceCommit: `{binding.source_sha}`",
        f"- manifestHash: `{binding.manifest_hash}`",
        f"- publisher: `{PUBLISHER_ID}`",
        "",
        "Archives are rebuilt and verified before upload. Do not reuse pre-correction RC artifacts.",
    ]
    for a in binding.archives:
        body_lines.append(f"- {a['name']}: `{a['sha256']}` ({a['bytes']} bytes)")

    release = resolve_release_by_tag(
        repository=repository, tag=binding.tag, token=token, api=api
    )
    if release is None:
        release = call(
            "POST",
            f"https://api.github.com/repos/{repository}/releases",
            {
                "tag_name": binding.tag,
                "target_commitish": binding.source_sha,
                "name": f"managed-core {binding.version}",
                "body": "\n".join(body_lines),
                "draft": False,
                "prerelease": False,
                "generate_release_notes": False,
            },
            None,
        )
    else:
        _assert_release_matches_binding(binding, release)
        _classify_release_assets(binding, release)

    upload_url_template = str((release or {}).get("upload_url") or "")
    release_url = str((release or {}).get("html_url") or "")
    release_id = (release or {}).get("id")
    if not upload_url_template or not release_url:
        _reject("release_create_failed", "release upload_url/html_url missing")

    existing_assets = _release_asset_digests(release or {})
    base_upload = upload_url_template.split("{", 1)[0]
    for a in binding.archives:
        name = a["name"]
        expected = _normalize_digest(str(a["sha256"]))
        if name in existing_assets:
            remote = existing_assets[name]
            if not remote:
                _reject(
                    "checksum_unverified",
                    f"existing release asset {name} has no digest; refuse unsafe retry",
                )
            if remote != expected:
                _reject(
                    "checksum_conflict",
                    f"release asset {name} digest {remote} != rebuilt {expected}",
                )
            continue
        path = archive_paths.get(name)
        if path is None or not path.is_file():
            _reject("upload_archive_missing", f"local archive missing for upload: {name}")
        raw = path.read_bytes()
        file_digest = f"sha256:{hashlib.sha256(raw).hexdigest()}"
        if file_digest != expected:
            _reject(
                "upload_checksum_mismatch",
                f"refusing upload of {name}: {file_digest} != {expected}",
            )
        q = urllib.parse.urlencode({"name": name, "label": name})
        url = f"{base_upload}?{q}"
        # Use github_api directly for binary upload (api shim may ignore content-type).
        if api is None:
            github_api(
                "POST",
                url,
                token=token,
                raw_body=raw,
                content_type="application/octet-stream",
            )
        else:
            api("POST", url, None, raw)

    return {
        "releaseUrl": release_url,
        "releaseId": release_id,
        "tag": binding.tag,
        "tagObjectSha": tag_obj_sha,
    }


def run_publish(
    *,
    source_root: Path,
    source_sha: str,
    version: str,
    tag: str,
    repository: str,
    default_branch: str,
    action: str,
    dry_run: bool,
    token: str | None = None,
    token_source: str | None = None,
    output_dir: Path | None = None,
    allow_dirty: bool = False,
    skip_install_verify: bool = False,
    skip_remote_checks: bool = False,
    baseline_sha: str | None = None,
    baseline_ref: str | None = None,
    api: ApiFn | None = None,
) -> dict[str, Any]:
    if version != PACKAGE_VERSION_TARGET:
        _reject("version_not_authorized", f"only {PACKAGE_VERSION_TARGET} authorized")
    if tag != f"v{version}":
        _reject("tag_version_mismatch", f"tag {tag} must equal v{version}")

    outcome: dict[str, Any] = {
        "mode": PUBLISHER_ID,
        "action": action,
        "sourceSha": source_sha.lower(),
        "version": version,
        "tag": tag,
        "repository": repository,
        "defaultBranch": default_branch,
        "dryRun": dry_run,
        "published": False,
    }

    app_token = ""
    if not skip_remote_checks:
        app_token = require_automation_token(token=token, token_source=token_source)
        bind_source_sha_to_default_tip(
            source_sha=source_sha,
            repository=repository,
            default_branch=default_branch,
            token=app_token,
            api=api,
        )

    binding = rebuild_from_source(
        source_root=source_root,
        expected_version=version,
        expected_source_sha=source_sha,
        output_dir=output_dir,
        allow_dirty=allow_dirty,
        skip_install_verify=skip_install_verify,
        baseline_sha=baseline_sha,
        baseline_ref=baseline_ref,
    )
    if binding.tag != tag:
        _reject("tag_binding_failed", f"binding tag {binding.tag} != requested {tag}")

    outcome["manifestHash"] = binding.manifest_hash
    outcome["archives"] = binding.archives

    publication_state: PublicationState | None = None
    if not skip_remote_checks:
        publication_state = assert_no_conflict_or_replay(
            binding=binding,
            repository=repository,
            token=app_token,
            api=api,
        )
        outcome["publicationState"] = {
            "tagPresent": publication_state.tag_sha is not None,
            "releasePresent": publication_state.release is not None,
            "matchedAssets": sorted(publication_state.matched_assets),
            "missingAssets": sorted(publication_state.missing_assets),
            "complete": publication_state.complete,
        }

    if action == "verify-only" or dry_run:
        status = "dry_run_ok" if dry_run else "verify_only_ok"
        evidence = build_release_evidence(
            binding=binding,
            repository=repository,
            publication_status="pending_governed_publish" if dry_run or action == "verify-only" else "verified",
            dry_run=dry_run,
            notes=(
                "Validation/rebuild passed; tag and GitHub Release were not created "
                f"(action={action}, dry_run={dry_run})."
            ),
        )
        outcome["status"] = status
        outcome["evidence"] = evidence
        outcome["detail"] = (
            "Rebuild/verify/bindings passed; publication skipped "
            f"(action={action}, dry_run={dry_run})"
        )
        return outcome

    if action != "publish":
        _reject("action_invalid", f"unsupported action: {action}")

    archive_paths: dict[str, Path] = {}
    for a in binding.archives:
        candidate = source_root / str(a.get("path") or "")
        if not candidate.is_file() and output_dir is not None:
            candidate = Path(output_dir) / a["name"]
        archive_paths[a["name"]] = candidate

    published = create_tag_and_release(
        binding=binding,
        repository=repository,
        token=app_token,
        archive_paths=archive_paths,
        api=api,
    )
    evidence = build_release_evidence(
        binding=binding,
        repository=repository,
        publication_status="published",
        release_url=published["releaseUrl"],
        release_id=published.get("releaseId"),
        dry_run=False,
        notes="Published via normal-token managed-core release publisher.",
    )
    outcome["published"] = True
    outcome["status"] = "published"
    outcome["releaseUrl"] = published["releaseUrl"]
    outcome["releaseId"] = published.get("releaseId")
    outcome["evidence"] = evidence
    outcome["detail"] = "Tag and GitHub Release created after rebuild/verify"
    return outcome


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--source-root", type=Path, required=True)
    p.add_argument("--source-sha", required=True)
    p.add_argument("--version", default=PACKAGE_VERSION_TARGET)
    p.add_argument("--tag", default=DEFAULT_TAG)
    p.add_argument("--repository", default=os.environ.get("GITHUB_REPOSITORY", ""))
    p.add_argument("--default-branch", default="main")
    p.add_argument("--action", default="publish", choices=["publish", "verify-only"])
    p.add_argument("--dry-run", default="false")
    p.add_argument("--output-dir", type=Path, default=None)
    p.add_argument("--allow-dirty", action="store_true")
    p.add_argument("--skip-install-verify", action="store_true")
    p.add_argument("--baseline-sha", help="Runtime-supplied exact target baseline SHA")
    p.add_argument("--baseline-ref", help="Runtime-supplied authoritative target baseline ref")
    p.add_argument(
        "--skip-remote-checks",
        action="store_true",
        help="Local rebuild/evidence only; never mutate GitHub (tests / WP evidence)",
    )
    p.add_argument("--evidence-out", type=Path, default=None)
    p.add_argument("--outcome-out", type=Path, default=None)
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    dry = str(args.dry_run).strip().lower() in {"1", "true", "yes", "y", "on"}
    try:
        outcome = run_publish(
            source_root=args.source_root,
            source_sha=args.source_sha,
            version=args.version,
            tag=args.tag,
            repository=args.repository,
            default_branch=args.default_branch,
            action=args.action,
            dry_run=dry,
            output_dir=args.output_dir,
            allow_dirty=args.allow_dirty,
            skip_install_verify=args.skip_install_verify,
            skip_remote_checks=args.skip_remote_checks,
            baseline_sha=args.baseline_sha,
            baseline_ref=args.baseline_ref,
        )
    except ReleasePublishError as e:
        payload = {"ok": False, "status": e.code, "error": e.code, "detail": e.message}
        print(json.dumps(payload, indent=2))
        if args.outcome_out:
            args.outcome_out.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
        return 1

    payload = {"ok": True, **outcome}
    print(json.dumps(payload, indent=2))
    if args.outcome_out:
        args.outcome_out.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    evidence = outcome.get("evidence")
    if args.evidence_out and isinstance(evidence, dict):
        args.evidence_out.parent.mkdir(parents=True, exist_ok=True)
        args.evidence_out.write_text(json.dumps(evidence, indent=2) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
