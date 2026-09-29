"""Hash-guarded removal of v2 root workflows retired in v3.

v2 ``scripts/sync-managed-workflows.sh`` rendered managed templates into a
consumer's ``.github/workflows/`` using that consumer's
``.github/linktrend-gitops-consumer.json`` and orchestration profile, so the
installed bytes differ per consumer.  This module re-renders every published
v2 template (reviewed bytes under ``migrations/known-bytes/``) with each
published v2 renderer variant, for both v2 profiles, and exposes one migration identity per retired
workflow:

* the file matches a rendering  -> exact-hash removal (transactional);
* the file differs              -> conflict; the file is never deleted;
* the file is absent            -> no-op.

A file that matches no published rendering (local edits, or a consumer config
changed in a way no renderer variant covers) is reported as a conflict and
never deleted (docs/runbooks/v3-upgrade.md).
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

try:
    from .errors import ConflictError
    from .hashing import sha256_bytes, sha256_file
    from .manifest import MigrationCatalog, MigrationEntry
    from .paths import join_under_nofollow_checked
except ImportError:  # pragma: no cover - direct script entrypoint
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    from ide_development.errors import ConflictError  # type: ignore
    from ide_development.hashing import sha256_bytes, sha256_file  # type: ignore
    from ide_development.manifest import MigrationCatalog, MigrationEntry  # type: ignore
    from ide_development.paths import join_under_nofollow_checked  # type: ignore

RETIRED_ROOT_WORKFLOWS = (
    "linktrend-development-to-staging.yml",
    "linktrend-integrator-merge.yml",
    "linktrend-repair-observer.yml",
    "linktrend-review-gate.yml",
    "linktrend-review-packager.yml",
    "linktrend-review-ready-publisher.yml",
    "linktrend-staging-to-main.yml",
)
WORKFLOW_DIR_REL = ".github/workflows"
CONSUMER_CONFIG_REL = ".github/linktrend-gitops-consumer.json"
DELIVERY_MODE_REL = ".github/linktrend-delivery-mode.json"
PROFILES = ("github-actions", "local-coordinator")
# Hash that no file can have; forces a conflict when identity cannot be rebuilt.
UNRESOLVABLE_HASH = "sha256:" + "0" * 64

_LOCAL_COORDINATOR_WORKFLOWS = {
    "linktrend-review-packager.yml",
    "linktrend-integrator-merge.yml",
    "linktrend-repair-observer.yml",
    "linktrend-development-to-staging.yml",
    "linktrend-staging-to-main.yml",
}
_RUNNER = "ubuntu-24.04-arm"


KNOWN_BYTES_DIR_REL = "core/managed-core/migrations/known-bytes"
KNOWN_BYTES_PREFIX = "retired-workflow-"


def known_bytes_rel(name: str, release: str) -> str:
    """Reviewed template bytes of ``name`` as first published in ``release`` (e.g. v2.3.0)."""
    return f"{KNOWN_BYTES_DIR_REL}/{KNOWN_BYTES_PREFIX}{release}-{name}"


def release_key(release: str) -> tuple[int, ...]:
    return tuple(int(part) for part in re.findall(r"\d+", release))


def known_templates(package_root: Path, name: str) -> list[Path]:
    """Known template bytes for ``name``, oldest release first."""
    root = package_root / KNOWN_BYTES_DIR_REL
    prefix = KNOWN_BYTES_PREFIX
    found = [
        path
        for path in root.glob(f"{prefix}v*-{name}")
        if path.is_file() and not path.is_symlink()
    ]
    return sorted(found, key=lambda p: release_key(p.name[len(prefix) : -len(name) - 1]))


def _remove_event_blocks(value: str, prohibited: set[str]) -> str:
    lines = value.splitlines(keepends=True)
    output: list[str] = []
    index = 0
    while index < len(lines):
        if lines[index].rstrip("\r\n") != "on:":
            output.append(lines[index])
            index += 1
            continue
        output.append(lines[index])
        index += 1
        while index < len(lines):
            line = lines[index]
            if line.strip() and not line.startswith(" "):
                break
            match = re.match(r"^  ([A-Za-z0-9_-]+):", line)
            if not match:
                output.append(line)
                index += 1
                continue
            event = match.group(1)
            block = [line]
            index += 1
            while index < len(lines):
                candidate = lines[index]
                if candidate.strip() and not candidate.startswith(" "):
                    break
                if re.match(r"^  [A-Za-z0-9_-]+:", candidate):
                    break
                block.append(candidate)
                index += 1
            if event not in prohibited:
                output.extend(block)
    return "".join(output)


# Runner label pairs (privileged, untrusted) published by v2 renderers.
_RUNNER_SETS = (
    ("ubuntu-24.04-arm", "ubuntu-24.04-arm"),
    ("ubuntu-latest", "ubuntu-latest"),
    ("[self-hosted, macOS, ARM64, linktrend-privileged]", "[self-hosted, Linux, ARM64, linktrend-ci-isolated]"),
)
# Last local-coordinator header line: v2.4.0+ and v2.2.0-v2.3.8.
_HEADER_BUGBOT_LINES = (
    "# Cursor Bugbot remains the provider observation name; required context is Linktrend Review Gate.\n",
    "# Cursor Bugbot remains an external unchanged context.\n",
)


def render_published(
    template: str,
    name: str,
    config: dict[str, Any],
    *,
    profile: str,
    legacy_bugbot: str | None = None,
    runners: tuple[str, str] = _RUNNER_SETS[0],
    header_bugbot_line: str = _HEADER_BUGBOT_LINES[0],
) -> str:
    """Port of the published v2 sync-managed-workflows.sh renderers.

    Defaults reproduce v2.5.2 exactly.  ``legacy_bugbot`` is the value pre-v2.4
    renderers substituted for ``__LINKTREND_BUGBOT_CHECK_NAME__``.
    """
    rendered = template.replace(
        "__LINKTREND_CI_WORKFLOW_NAME__", str(config.get("ciWorkflowName", "")).strip()
    )
    rendered = rendered.replace(
        "__LINKTREND_BRANCH_POLICY_WORKFLOW_NAME__",
        str(config.get("branchPolicyWorkflowName", "")).strip(),
    )
    provider = str(config.get("bugbotProviderCheckName") or "Cursor Bugbot").strip()
    gate = str(
        config.get("reviewGateCheckName") or config.get("bugbotCheckName") or "Linktrend Review Gate"
    ).strip()
    rendered = rendered.replace("__LINKTREND_BUGBOT_PROVIDER_CHECK_NAME__", provider)
    rendered = rendered.replace("__LINKTREND_REVIEW_GATE_CHECK_NAME__", gate)
    rendered = rendered.replace(
        "__LINKTREND_BUGBOT_CHECK_NAME__", gate if legacy_bugbot is None else legacy_bugbot
    )
    rendered = rendered.replace("__LINKTREND_UNTRUSTED_RUNS_ON__", runners[1])
    rendered = rendered.replace("__LINKTREND_RUNS_ON__", runners[0])
    if profile == "local-coordinator" and name in _LOCAL_COORDINATOR_WORKFLOWS:
        rendered = _remove_event_blocks(
            rendered, {"schedule", "check_run", "workflow_run", "pull_request_target"}
        )
        if name == "linktrend-repair-observer.yml" and "\n  workflow_dispatch:" not in rendered:
            rendered = rendered.replace("on:\n", "on:\n  workflow_dispatch:\n", 1)
            rendered = rendered.replace(
                "    if: >\n      (\n",
                "    if: >\n      github.event_name == 'workflow_dispatch' ||\n      (\n",
                1,
            )
        rendered = (
            "# Orchestration profile: local-coordinator\n"
            "# Automatic schedule/check-run/workflow-run/pull-request-target wakes are disabled.\n"
            "# Manual recovery remains available; the local coordinator publishes these frozen contexts:\n"
            "# Linktrend Fast Gate | Linktrend Full Suite | Linktrend Phase Ready\n"
            "# Linktrend Staging Gate | Linktrend Release Gate | Linktrend Coordinator\n"
            + header_bugbot_line
            + rendered
        )
    return rendered


def _render_variants(config: dict[str, Any]):
    legacy_values: list[str | None] = [None]
    for value in (config.get("bugbotCheckName"), config.get("bugbotProviderCheckName"), "Cursor Bugbot"):
        value = str(value).strip() if value else ""
        if value and value not in legacy_values:
            legacy_values.append(value)
    for profile in PROFILES:
        headers = _HEADER_BUGBOT_LINES if profile == "local-coordinator" else _HEADER_BUGBOT_LINES[:1]
        for header in headers:
            for legacy in legacy_values:
                for runners in _RUNNER_SETS:
                    yield {
                        "profile": profile,
                        "legacy_bugbot": legacy,
                        "runners": runners,
                        "header_bugbot_line": header,
                    }


def _load_json(path: Path) -> dict[str, Any] | None:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, ValueError):
        return None
    return value if isinstance(value, dict) else None


def _consumer_config(target_root: Path) -> dict[str, Any]:
    try:
        config_path = join_under_nofollow_checked(target_root, CONSUMER_CONFIG_REL)
    except ConflictError:
        config = {}
    else:
        config = _load_json(config_path) or {}
    # v2.5.2 sync normalized an absent Fast name before rendering.
    config.setdefault("fastWorkflowName", "Linktrend Fast Checks")
    return config


def candidate_hashes(package_root: Path, target_root: Path, name: str) -> list[str]:
    """Hashes of every published v2 rendering this consumer could have received.

    Ordered newest release first so the reported expected hash is v2.5.2's.
    """
    config = _consumer_config(target_root)
    hashes: list[str] = []
    for template_path in reversed(known_templates(package_root, name)):
        template = template_path.read_text(encoding="utf-8")
        for variant in _render_variants(config):
            rendered = render_published(template, name, config, **variant)
            digest = sha256_bytes(rendered.encode("utf-8"))
            if digest not in hashes:
                hashes.append(digest)
    return hashes


def migration_entries(package_root: Path, target_root: Path) -> list[MigrationEntry]:
    entries: list[MigrationEntry] = []
    for name in RETIRED_ROOT_WORKFLOWS:
        rel = f"{WORKFLOW_DIR_REL}/{name}"
        candidates = candidate_hashes(package_root, target_root, name)
        chosen = candidates[0] if candidates else UNRESOLVABLE_HASH
        try:
            dest = join_under_nofollow_checked(target_root, rel)
        except ConflictError:
            dest = None
        if dest is not None and dest.is_file():
            actual = sha256_file(dest)
            if actual in candidates:
                chosen = actual
        entries.append(MigrationEntry(identity=rel, path=rel, content_hash=chosen, action="remove"))
    return entries


def with_retired_workflows(
    catalog: MigrationCatalog, package_root: Path, target_root: Path
) -> MigrationCatalog:
    known = {entry.path for entry in catalog.entries}
    extra = [e for e in migration_entries(package_root, target_root) if e.path not in known]
    merged = sorted((*catalog.entries, *extra), key=lambda e: (e.path, e.identity))
    return MigrationCatalog(
        schema_version=catalog.schema_version, entries=tuple(merged), path=catalog.path
    )


def remove_retired(package_root: Path, target_root: Path, *, dry_run: bool) -> tuple[list[str], list[str]]:
    """Delete exact v2.5.2 renderings. Returns (removed, conflicts)."""
    removed: list[str] = []
    conflicts: list[str] = []
    for entry in migration_entries(package_root, target_root):
        try:
            dest = join_under_nofollow_checked(target_root, entry.path)
        except ConflictError:
            conflicts.append(entry.path)
            continue
        if not dest.exists() and not dest.is_symlink():
            continue
        if not dest.is_file() or sha256_file(dest) != entry.content_hash:
            conflicts.append(entry.path)
            continue
        if not dry_run:
            dest.unlink()
        removed.append(entry.path)
    return removed, conflicts


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Remove retired v2 root workflows (hash-guarded).")
    parser.add_argument("--target", required=True, type=Path)
    parser.add_argument("--package", type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)
    removed, conflicts = remove_retired(
        args.package.resolve(), args.target.resolve(), dry_run=args.dry_run
    )
    verb = "DRY-RUN: would remove" if args.dry_run else "PASS: removed"
    for rel in removed:
        print(f"{verb} retired {rel}")
    for rel in conflicts:
        print(
            f"CONFLICT: retired {rel} is unsafe (symlink/non-file) or differs from every "
            "published v2 rendering; not removed. Review local edits or links, then delete "
            "it deliberately (it is no longer managed).",
            file=sys.stderr,
        )
    return 11 if conflicts else 0


if __name__ == "__main__":
    raise SystemExit(main())
