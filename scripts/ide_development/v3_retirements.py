"""Generate the v3 retired-file migrations from the published v2 packages.

Every destination in the v2.5.2 ``core/managed-core/MANIFEST.json`` (release
commit ``5a64f7f``) that the current manifest no longer declares becomes an
exact-hash ``remove`` entry in ``core/managed-core/migrations/catalog.json``:
one with the v2.5.2 hash (identity = path) and one per distinct older hash the
same path had in an earlier published v2 release (identity = ``path@<first
release with those bytes>``), so a consumer on any published v2 release is
upgraded without deleting anything that was never released.

Every distinct published v2 template of a root workflow that
``scripts/sync-managed-workflows.sh`` rendered into consumer
``.github/workflows/`` is written as reviewed known bytes (named by the first
release tag that shipped it) so ``retired_workflows`` can rebuild each
consumer-specific identity.  Consumers often kept older renderings because the
sync was not re-run on every package update.

Usage (from ``scripts/``; needs local git objects and release tags)::

  python3 -m ide_development.v3_retirements --write
  python3 -m ide_development.v3_retirements --check
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

try:
    from .retired_workflows import (
        KNOWN_BYTES_DIR_REL,
        KNOWN_BYTES_PREFIX,
        RETIRED_ROOT_WORKFLOWS,
        known_bytes_rel,
        release_key,
    )
except ImportError:  # pragma: no cover - direct script entrypoint
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    from ide_development.retired_workflows import (  # type: ignore
        KNOWN_BYTES_DIR_REL,
        KNOWN_BYTES_PREFIX,
        RETIRED_ROOT_WORKFLOWS,
        known_bytes_rel,
        release_key,
    )

REPO_ROOT = Path(__file__).resolve().parents[2]
V252_REF = "5a64f7f03d3463804b424cc59c4ee048473d9a51"
V252_VERSION = "2.5.2"
SINCE_VERSION = "3.0.0"
MANIFEST_REL = "core/managed-core/MANIFEST.json"
CATALOG_REL = "core/managed-core/migrations/catalog.json"
TEMPLATE_DIR_REL = "core/github/managed-workflows"

# First match wins; ordered from most to least specific.
COMPONENTS: tuple[tuple[str, str], ...] = (
    ("review_ready", "Review Ready publisher"),
    ("review-ready", "Review Ready publisher"),
    ("completion_gate", "completion-gate evidence"),
    ("linktrend_review_gate", "review-gate classifier"),
    ("linktrend-review-gate", "review-gate classifier"),
    ("LINKTREND-REVIEW-GATE", "review-gate classifier"),
    ("bugbot_user", "Bugbot user-token dispatch"),
    ("repair_", "repair observer and repair dispatcher"),
    ("write_outcome", "repair observer and repair dispatcher"),
    ("conflict_task", "repair observer and repair dispatcher"),
    ("staging", "staging branch"),
    ("promote_main", "receipt-gated promotion, replaced by linktrend-promote-main.yml"),
    ("main_approve_package", "receipt-gated promotion, replaced by linktrend-promote-main.yml"),
    ("receipt", "promotion receipts"),
    ("RECEIPT", "promotion receipts"),
    ("gate_receipt", "promotion receipts"),
    ("transition-receipt", "promotion receipts"),
    ("manifest_persistence", "promotion receipts: manifest persistence"),
    ("manifest-persistence", "promotion receipts: manifest persistence"),
    ("MANIFEST-PERSISTENCE", "promotion receipts: manifest persistence"),
    ("portfolio", "Lisa ship/pull waves: portfolio control loop"),
    ("heartbeat", "Mac Mini coordinator"),
    ("administrator_recovery", "Mac Mini coordinator"),
    ("packager", "packager"),
    ("coordinator", "packager"),
    ("phase-handoff", "packager"),
    ("phase-record", "packager"),
    ("delivery", "delivery controller"),
    ("integrator", "delivery controller"),
    ("candidate_lifecycle", "delivery controller"),
    ("verify_reconciled", "delivery controller"),
    ("wait_named_gate", "delivery controller"),
    ("resolve_event_pr", "delivery controller"),
)


def component_for(path: str) -> str:
    for needle, component in COMPONENTS:
        if needle in path:
            return component
    raise ValueError(f"no v3 retirement component for {path}; extend COMPONENTS")


def _git_show(ref: str, rel: str, *, repo: Path) -> bytes:
    proc = subprocess.run(
        ["git", "-C", str(repo), "show", f"{ref}:{rel}"],
        capture_output=True,
        check=False,
    )
    if proc.returncode != 0:
        raise RuntimeError(
            f"git object {ref}:{rel} unavailable ({proc.stderr.decode().strip()}); "
            "fetch the v2.5.2 release commit first"
        )
    return proc.stdout


def _manifest_files(raw: bytes) -> list[dict[str, Any]]:
    obj = json.loads(raw.decode("utf-8"))
    return list(obj.get("files") or [])


def retired_manifest_rows(*, repo: Path = REPO_ROOT, ref: str = V252_REF) -> list[dict[str, Any]]:
    old = _manifest_files(_git_show(ref, MANIFEST_REL, repo=repo))
    current = _manifest_files((repo / MANIFEST_REL).read_bytes())
    live = {row["destination"] for row in current}
    return sorted(
        (row for row in old if row["destination"] not in live),
        key=lambda row: row["destination"],
    )


def build_entries(*, repo: Path = REPO_ROOT, ref: str = V252_REF) -> list[dict[str, Any]]:
    retired = retired_manifest_rows(repo=repo, ref=ref)
    older = older_hashes(retired, repo=repo)
    entries = []
    for row in retired:
        dest = row["destination"]
        reason = f"Retired in v3 ({component_for(dest)})"
        entries.append(
            {
                "identity": dest,
                "path": dest,
                "contentHash": row["sourceHash"],
                "action": "remove",
                "reason": reason,
                "sincePackageVersion": SINCE_VERSION,
            }
        )
        for release, digest in older.get(dest, []):
            entries.append(
                {
                    "identity": f"{dest}@{release}",
                    "path": dest,
                    "contentHash": digest,
                    "action": "remove",
                    "reason": f"{reason}; bytes as published in {release}",
                    "sincePackageVersion": SINCE_VERSION,
                }
            )
    return entries


def older_hashes(
    retired: list[dict[str, Any]], *, repo: Path = REPO_ROOT
) -> dict[str, list[tuple[str, str]]]:
    """Retired path -> [(first release, hash)] for bytes that differ from v2.5.2."""
    current = {row["destination"]: row["sourceHash"] for row in retired}
    seen: dict[str, set[str]] = {path: {digest} for path, digest in current.items()}
    report: dict[str, list[tuple[str, str]]] = {}
    for release in published_releases(repo=repo):
        if release == f"v{V252_VERSION}":
            continue
        try:
            rows = _manifest_files(_git_show(release, MANIFEST_REL, repo=repo))
        except RuntimeError:
            continue
        for row in rows:
            path, digest = row["destination"], row["sourceHash"]
            if path in seen and digest not in seen[path]:
                seen[path].add(digest)
                report.setdefault(path, []).append((release, digest))
    return report


def render_catalog(*, repo: Path = REPO_ROOT, ref: str = V252_REF) -> dict[str, Any]:
    catalog = json.loads((repo / CATALOG_REL).read_text(encoding="utf-8"))
    generated = build_entries(repo=repo, ref=ref)
    retired_paths = {entry["path"] for entry in generated}
    # Older-release entries for a path v2.5.2 still shipped would compare the
    # v2.5.2 bytes against a stale hash and block every upgrade.
    kept = [
        entry
        for entry in catalog.get("entries") or []
        if entry.get("sincePackageVersion") != SINCE_VERSION and entry["path"] not in retired_paths
    ]
    catalog["packageVersion"] = (repo / "core/managed-core/VERSION").read_text(encoding="utf-8").strip()
    catalog["entries"] = kept + generated
    return catalog


def published_releases(*, repo: Path = REPO_ROOT) -> list[str]:
    """Published v2 release tags up to v2.5.2, oldest first."""
    tags = subprocess.run(
        ["git", "-C", str(repo), "tag", "--list", "v2.*"],
        capture_output=True,
        text=True,
        check=True,
    ).stdout.split()
    limit = release_key(V252_VERSION)
    releases = sorted((t for t in tags if release_key(t) <= limit), key=release_key)
    if f"v{V252_VERSION}" not in releases:
        raise RuntimeError(f"release tag v{V252_VERSION} unavailable; fetch tags first")
    return releases


def known_workflow_bytes(*, repo: Path = REPO_ROOT, ref: str = V252_REF) -> dict[str, bytes]:
    """Each distinct published template blob, keyed by its first-release path."""
    out: dict[str, bytes] = {}
    for name in RETIRED_ROOT_WORKFLOWS:
        seen: set[bytes] = set()
        for release in published_releases(repo=repo):
            source = ref if release == f"v{V252_VERSION}" else release
            try:
                data = _git_show(source, f"{TEMPLATE_DIR_REL}/{name}", repo=repo)
            except RuntimeError:
                continue
            if data not in seen:
                seen.add(data)
                out[known_bytes_rel(name, release)] = data
    return out


def _stale_known_bytes(expected: dict[str, bytes], *, repo: Path) -> list[Path]:
    root = repo / KNOWN_BYTES_DIR_REL
    return sorted(
        path
        for path in root.glob(f"{KNOWN_BYTES_PREFIX}*")
        if f"{KNOWN_BYTES_DIR_REL}/{path.name}" not in expected
    )


def _catalog_text(catalog: dict[str, Any]) -> str:
    return json.dumps(catalog, indent=2, ensure_ascii=False) + "\n"


def write(*, repo: Path = REPO_ROOT, ref: str = V252_REF) -> dict[str, Any]:
    catalog = render_catalog(repo=repo, ref=ref)
    (repo / CATALOG_REL).write_text(_catalog_text(catalog), encoding="utf-8")
    known = known_workflow_bytes(repo=repo, ref=ref)
    for stale in _stale_known_bytes(known, repo=repo):
        stale.unlink()
    for rel, data in known.items():
        path = repo / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
    return catalog


def check(*, repo: Path = REPO_ROOT, ref: str = V252_REF) -> list[str]:
    errors: list[str] = []
    expected = _catalog_text(render_catalog(repo=repo, ref=ref))
    if (repo / CATALOG_REL).read_text(encoding="utf-8") != expected:
        errors.append(f"{CATALOG_REL} is not the generated v3 retirement catalog")
    known = known_workflow_bytes(repo=repo, ref=ref)
    for rel, data in known.items():
        path = repo / rel
        if not path.is_file() or path.read_bytes() != data:
            errors.append(f"{rel} differs from its published release bytes")
    for stale in _stale_known_bytes(known, repo=repo):
        errors.append(f"stale known bytes: {stale.relative_to(repo)}")
    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--write", action="store_true", help="rewrite catalog + known bytes (default)")
    mode.add_argument("--check", action="store_true", help="exit 1 when generated output drifted")
    parser.add_argument("--ref", default=V252_REF, help="v2.5.2 release commit")
    args = parser.parse_args(argv)
    try:
        if args.check:
            errors = check(ref=args.ref)
            for err in errors:
                print(f"FAIL: {err}", file=sys.stderr)
            if not errors:
                print("v3 retirement catalog OK")
            return 1 if errors else 0
        catalog = write(ref=args.ref)
    except RuntimeError as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1
    v3 = [e for e in catalog["entries"] if e.get("sincePackageVersion") == SINCE_VERSION]
    paths = {e["path"] for e in v3}
    print(
        f"Wrote {CATALOG_REL}: {len(paths)} retired paths, {len(v3)} v3 entries "
        f"(incl. older published hashes), {len(catalog['entries'])} entries total"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
