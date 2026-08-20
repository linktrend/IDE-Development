"""PKT-07 managed package integration and v2.4 skill migration helpers.

Materializes accepted provider sources, authorizes physical skill removal after
PKT-04 dual-app proof, archives v2.4 rollback bytes, and extends the migration
catalog with exact supersession identities. Does not bump package version to
2.5.0 (final integration only).
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
from pathlib import Path
from typing import Any

from .hashing import sha256_file

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parents[1]
MANAGED = REPO_ROOT / "core" / "managed-core"
LINK_INTEGRATIONS = REPO_ROOT / "core" / "link-integrations"
ARCHIVE_ROOT = REPO_ROOT / "docs" / "archive" / "v24-skill-rollback"
CATALOG_PATH = MANAGED / "migrations" / "catalog.json"

BOOTSTRAP_SKILLS = frozenset({"agentsetup", "agentcomply"})
LOCK_PATHS = (
    LINK_INTEGRATIONS / "skills-lock.json",
    MANAGED / "platforms" / "codex" / "skills-lock.json",
    MANAGED / "platforms" / "cursor" / "skills-lock.json",
)
SKILLS_MANIFEST = MANAGED / "platforms" / "codex" / "skills-manifest.json"
MATERIALIZATION_MANIFEST = MANAGED / "platforms" / "cursor" / "materialization-manifest.json"
PROVIDERS_SRC = LINK_INTEGRATIONS
PROVIDERS_DEST = MANAGED / "platforms" / "providers"
PROVIDERS_EXAMPLE = MANAGED / "config" / "providers.example.json"

PROVIDER_FILES = (
    "autowork.mjs",
    "brain.mjs",
    "clients.mjs",
    "config.mjs",
    "errors.mjs",
    "index.mjs",
    "libraries.mjs",
    "mcp.mjs",
    "pins.mjs",
    "platform.mjs",
    "redaction.mjs",
    "registry.mjs",
    "skills-loader.mjs",
    "skills-lock.json",
    "skills.mjs",
    "transport.mjs",
    "README.md",
)


def _sha256_digest(path: Path) -> str:
    return sha256_file(path)


def _lock_digest(payload: dict[str, Any]) -> str:
    body = json.dumps(payload, indent=2, sort_keys=True) + "\n"
    return f"sha256:{hashlib.sha256(body.encode('utf-8')).hexdigest()}"


def sync_provider_payload() -> list[str]:
    """Copy accepted link-integrations sources into managed-core/platforms/providers/."""
    actions: list[str] = []
    PROVIDERS_DEST.mkdir(parents=True, exist_ok=True)
    for name in PROVIDER_FILES:
        src = PROVIDERS_SRC / name
        if not src.is_file():
            raise FileNotFoundError(src)
        dest = PROVIDERS_DEST / name
        shutil.copy2(src, dest)
        actions.append(f"synced provider {name}")
    PROVIDERS_EXAMPLE.parent.mkdir(parents=True, exist_ok=True)
    if not PROVIDERS_EXAMPLE.is_file():
        PROVIDERS_EXAMPLE.write_text(
            json.dumps(_providers_example_template(), indent=2) + "\n",
            encoding="utf-8",
        )
        actions.append("wrote providers.example.json")
    return actions


def _providers_example_template() -> dict[str, Any]:
    return {
        "schemaVersion": "provider-runtime-config/v1",
        "consumerRepository": "linktrend/example-consumer",
        "environment": "development",
        "providers": {
            "platform": {
                "endpoint": "https://platform.example.invalid",
                "credentialRef": "LINKTREND_PLATFORM_DEV_TOKEN",
                "enabledCapabilities": [
                    "platform.identity.resolve",
                    "platform.capabilities.read",
                ],
            },
            "brain": {
                "endpoint": "https://brain.example.invalid",
                "credentialRef": "LINKTREND_BRAIN_DEV_TOKEN",
                "enabledCapabilities": [
                    "brain.projection.read",
                    "brain.handoff.create",
                ],
            },
            "skills": {
                "endpoint": "https://skills.example.invalid",
                "credentialRef": "LINKTREND_SKILLS_DEV_TOKEN",
                "enabledCapabilities": ["skills.release.read"],
            },
            "libraries": {
                "endpoint": "https://libraries.example.invalid",
                "credentialRef": "LINKTREND_LIBRARIES_DEV_TOKEN",
                "enabledCapabilities": ["libraries.entry.read"],
            },
            "autowork": {
                "endpoint": "https://autowork.example.invalid",
                "credentialRef": "LINKTREND_AUTOWORK_DEV_TOKEN",
                "enabledCapabilities": ["autowork.status.read"],
                "availability": "unavailable",
            },
        },
    }


def archive_and_remove_workflow_skills() -> tuple[list[str], list[dict[str, Any]]]:
    """Archive then delete IDE-owned workflow skill implementations (bootstrap retained)."""
    actions: list[str] = []
    supersessions: list[dict[str, Any]] = []
    lock = json.loads((LINK_INTEGRATIONS / "skills-lock.json").read_text(encoding="utf-8"))
    copies = lock.get("copies") or []
    mirrors = lock.get("packageMirrors") or []

    def add_supersession(consumer_path: str, digest: str | None, skill_id: str) -> None:
        if not digest:
            return
        supersessions.append(
            {
                "identity": consumer_path,
                "path": consumer_path,
                "contentHash": digest,
                "action": "remove",
                "reason": (
                    f"PKT-07 removes packaged v2.4 workflow skill `{skill_id}` after "
                    "PKT-04 dual-app proof; LiNKskills lock is sole workflow authority."
                ),
                "sincePackageVersion": "2.4.0",
            }
        )

    def archive_copy(rel: str) -> None:
        src = REPO_ROOT / rel
        if not src.is_file():
            return
        dest = ARCHIVE_ROOT / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dest)

    for row in copies:
        skill_id = row.get("skillId")
        rel = row.get("path")
        if not isinstance(skill_id, str) or not isinstance(rel, str):
            continue
        if skill_id in BOOTSTRAP_SKILLS:
            continue
        src = REPO_ROOT / rel
        if src.is_file():
            digest = row.get("digest") or _sha256_digest(src)
            archive_copy(rel)
            src.unlink()
            actions.append(f"removed {rel}")
            if rel.startswith("core/skills/"):
                add_supersession(f".agents/skills/{skill_id}/SKILL.md", digest, skill_id)
            elif rel.startswith(".cursor/skills/"):
                add_supersession(rel, digest, skill_id)

    for row in mirrors:
        skill_id = row.get("skillId")
        rel = row.get("path")
        if not isinstance(skill_id, str) or not isinstance(rel, str):
            continue
        if skill_id in BOOTSTRAP_SKILLS:
            continue
        src = REPO_ROOT / rel
        if src.is_file():
            digest = row.get("digest") or _sha256_digest(src)
            archive_copy(rel)
            src.unlink()
            actions.append(f"removed mirror {rel}")
            add_supersession(
                f".ide-development/skills/{skill_id}/SKILL.md",
                digest,
                skill_id,
            )

    # Remove empty skill directories under active trees.
    for root in (
        REPO_ROOT / "core" / "skills",
        REPO_ROOT / ".cursor" / "skills",
        MANAGED / "skills",
    ):
        if not root.is_dir():
            continue
        for child in sorted(root.iterdir()):
            if child.name in BOOTSTRAP_SKILLS:
                continue
            if child.is_dir():
                shutil.rmtree(child)
                actions.append(f"removed dir {child.relative_to(REPO_ROOT)}")

    return actions, supersessions


def update_skills_lock() -> list[str]:
    """Authorize removal and shrink active copy inventory to bootstrap adapters only."""
    actions: list[str] = []
    for path in LOCK_PATHS:
        lock = json.loads(path.read_text(encoding="utf-8"))
        bootstrap_copies = [
            row
            for row in lock.get("copies") or []
            if row.get("skillId") in BOOTSTRAP_SKILLS
        ]
        bootstrap_mirrors = [
            row
            for row in lock.get("packageMirrors") or []
            if row.get("skillId") in BOOTSTRAP_SKILLS
        ]
        lock["packet"] = "PKT-07"
        lock["physicalRemovalAuthorized"] = True
        lock["dualAppProof"] = {"codex": True, "cursor": True}
        lock["copies"] = bootstrap_copies
        lock["copyCount"] = len(bootstrap_copies)
        lock["packageMirrors"] = bootstrap_mirrors
        lock["lockDigest"] = _lock_digest({k: v for k, v in lock.items() if k != "lockDigest"})
        path.write_text(json.dumps(lock, indent=2) + "\n", encoding="utf-8")
        actions.append(f"updated lock {path.relative_to(REPO_ROOT)} copyCount={lock['copyCount']}")
    return actions


def update_skills_manifests() -> list[str]:
    actions: list[str] = []
    manifest = json.loads(SKILLS_MANIFEST.read_text(encoding="utf-8"))
    manifest["approvedRemainingSkills"] = []
    loader = manifest.get("nonSkillLoader") or {}
    loader["note"] = (
        "ISS-04 lock loader. PKT-07 removed physical workflow SKILL.md copies; "
        "LiNKskills provider retrieval is sole workflow authority."
    )
    manifest["nonSkillLoader"] = loader
    SKILLS_MANIFEST.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    actions.append("cleared codex skills-manifest approvedRemainingSkills")

    mat = json.loads(MATERIALIZATION_MANIFEST.read_text(encoding="utf-8"))
    kept = []
    for row in mat.get("entries") or []:
        dest = row.get("destination") or ""
        src = row.get("source") or ""
        if "/skills/" in dest and not any(
            name in dest for name in BOOTSTRAP_SKILLS
        ):
            if dest.endswith("/skills-loader.mjs") or dest.endswith("/skills-lock.json"):
                kept.append(row)
            continue
        if src.startswith("skills/") and not any(name in src for name in BOOTSTRAP_SKILLS):
            continue
        kept.append(row)
    mat["entries"] = kept
    MATERIALIZATION_MANIFEST.write_text(json.dumps(mat, indent=2) + "\n", encoding="utf-8")
    actions.append("trimmed cursor materialization-manifest workflow skills")
    return actions


def extend_migration_catalog(supersessions: list[dict[str, Any]]) -> list[str]:
    catalog = json.loads(CATALOG_PATH.read_text(encoding="utf-8"))
    existing = {row["identity"] for row in catalog.get("entries") or []}
    added = 0
    for row in supersessions:
        identity = row["identity"]
        if identity in existing:
            continue
        if not row.get("contentHash"):
            path = REPO_ROOT / "docs" / "archive" / "v24-skill-rollback" / identity
            if path.is_file():
                row["contentHash"] = _sha256_digest(path)
        catalog.setdefault("entries", []).append(row)
        existing.add(identity)
        added += 1
    catalog["packageVersion"] = "2.4.0"
    CATALOG_PATH.write_text(json.dumps(catalog, indent=2) + "\n", encoding="utf-8")
    return [f"added {added} skill supersession entries to migration catalog"]


def write_file_count_reduction_doc(removed_count: int) -> None:
    doc = REPO_ROOT / "docs" / "evidence" / "pkt-07-file-count-reduction.md"
    doc.parent.mkdir(parents=True, exist_ok=True)
    doc.write_text(
        "# PKT-07 file-count reduction (managed package integration)\n\n"
        f"- Workflow skill physical copies removed from system source: **{removed_count}** files archived under "
        "`docs/archive/v24-skill-rollback/`.\n"
        "- Bootstrap adapters retained: `agentsetup`, `agentcomply` (Codex/Cursor/agents surfaces).\n"
        "- Provider sources materialized under `core/managed-core/platforms/providers/`.\n"
        "- Package version identity remains **2.4.0** until WP25-18 final integration.\n"
        "- Atomic v2.4 rollback identity preserved in skills lock: "
        "`004bd5faa1e14ee100a018e16dcb049f0fb2d8eb` / "
        "`6c55220132cc7e9a1baef06f8c147ee9ac9431e7`.\n",
        encoding="utf-8",
    )


def apply_pkt07(*, dry_run: bool = False) -> dict[str, Any]:
    if dry_run:
        return {"dryRun": True, "repoRoot": str(REPO_ROOT)}

    provider_actions = sync_provider_payload()
    remove_actions, supersessions = archive_and_remove_workflow_skills()
    lock_actions = update_skills_lock()
    manifest_actions = update_skills_manifests()
    catalog_actions = extend_migration_catalog(supersessions)
    write_file_count_reduction_doc(len(remove_actions))

    return {
        "provider": provider_actions,
        "removed": remove_actions,
        "lock": lock_actions,
        "manifests": manifest_actions,
        "catalog": catalog_actions,
        "supersessionCount": len(supersessions),
        "rollbackCommit": "004bd5faa1e14ee100a018e16dcb049f0fb2d8eb",
        "rollbackTree": "6c55220132cc7e9a1baef06f8c147ee9ac9431e7",
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    result = apply_pkt07(dry_run=args.dry_run)
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        for key, value in result.items():
            print(f"{key}: {value}")
    return 0


if __name__ == "__main__":
    if str(SCRIPT_DIR.parent) not in sys.path:
        sys.path.insert(0, str(SCRIPT_DIR.parent))
    raise SystemExit(main())
