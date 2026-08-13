#!/usr/bin/env python3
"""Plan narrowly owned external cleanup without contacting external systems.

The source-system operator supplies a redacted inventory captured during W3
preflight.  This tool only validates that inventory and produces a plan.  The
optional apply path is deliberately fixture-only so tests can prove deletion
semantics without GitHub, launchd, Docker, or credential access.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any

SCHEMA_VERSION = 1
OWNER = "IDE Development"
SCOPES = {
    "repository": {"github-app", "github-secret-name", "github-runner"},
    "host": {
        "launchd-service",
        "docker-container",
        "docker-image",
        "docker-volume",
        "docker-network",
    },
}
SECRET_VALUE_KEYS = re.compile(r"(token|secret|private.?key|password|credential|value)", re.I)
WILDCARD = re.compile(r"[*?\[\]{}]" )


class InventoryError(ValueError):
    """An inventory that cannot be safely authorized."""


def _canonical(value: Any) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode()


def _digest(value: Any) -> str:
    return "sha256:" + hashlib.sha256(_canonical(value)).hexdigest()


def _redact(value: Any, *, key: str = "") -> Any:
    if isinstance(value, dict):
        return {
            k: ("[REDACTED]" if SECRET_VALUE_KEYS.search(k) and k not in {"secretName", "secretNames", "secretOutput"}
                else _redact(v, key=k))
            for k, v in value.items()
        }
    if isinstance(value, list):
        return [_redact(item, key=key) for item in value]
    return value


def _exact_identifier(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.strip() or WILDCARD.search(value):
        raise InventoryError(f"{field} must be one exact non-wildcard identifier")
    return value.strip()


def load_inventory(path: Path, scope: str) -> dict[str, Any]:
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise InventoryError(f"cannot read inventory: {exc}") from exc
    if not isinstance(raw, dict) or raw.get("schemaVersion") != SCHEMA_VERSION:
        raise InventoryError("inventory schemaVersion must be 1")
    if raw.get("repository") != "linktrend/IDE-Development":
        raise InventoryError("inventory repository must be linktrend/IDE-Development")
    if raw.get("scope") != scope:
        raise InventoryError(f"inventory scope must be {scope}")
    resources = raw.get("resources")
    if not isinstance(resources, list):
        raise InventoryError("inventory resources must be an array")
    allowed = SCOPES[scope]
    normalized: list[dict[str, Any]] = []
    for index, resource in enumerate(resources):
        if not isinstance(resource, dict):
            raise InventoryError(f"resources[{index}] must be an object")
        kind = resource.get("kind")
        if kind not in allowed:
            raise InventoryError(f"resources[{index}] has unsupported kind {kind!r} for {scope}")
        item = dict(resource)
        item["id"] = _exact_identifier(item.get("id"), f"resources[{index}].id")
        ownership = item.get("ownership")
        if ownership not in {"owned", "lookalike", "ambiguous"}:
            raise InventoryError(f"resources[{index}].ownership must be owned, lookalike, or ambiguous")
        if ownership == "owned":
            if item.get("owner") != OWNER or item.get("ownershipEvidence") != "recorded-ide-owned":
                raise InventoryError(f"resources[{index}] lacks positive IDE ownership evidence")
        if kind == "github-secret-name":
            item["secretName"] = _exact_identifier(item.get("secretName"), f"resources[{index}].secretName")
            if any(SECRET_VALUE_KEYS.search(str(key)) and key != "secretName" for key in item):
                raise InventoryError(f"resources[{index}] contains a secret value/key; names only")
        if "selector" in item or "pattern" in item:
            raise InventoryError(f"resources[{index}] uses a broad selector; exact resources only")
        normalized.append(item)
    return {**raw, "resources": normalized}


def build_plan(inventory: dict[str, Any], inventory_path: Path) -> dict[str, Any]:
    candidates = []
    preserved = []
    for resource in inventory["resources"]:
        public = _redact(resource)
        public.pop("fixturePath", None)
        if resource["ownership"] == "owned":
            candidates.append(public)
        else:
            public["decision"] = "PRESERVE"
            public["reason"] = f"ownership_{resource['ownership']}"
            preserved.append(public)
    return {
        "schemaVersion": SCHEMA_VERSION,
        "mode": "dry-run",
        "scope": inventory["scope"],
        "repository": inventory["repository"],
        "inventory": str(inventory_path),
        "beforeStateDigest": _digest(inventory),
        "candidates": candidates,
        "preserved": preserved,
        "externalMutation": "none",
        "secretOutput": "names-only",
        "applyRequirement": "fixture-root-and-apply-required",
    }


def _fixture_target(root: Path, resource: dict[str, Any]) -> Path:
    relative = resource.get("fixturePath")
    if not isinstance(relative, str) or not relative or Path(relative).is_absolute() or ".." in Path(relative).parts:
        raise InventoryError(f"owned resource {resource['id']} lacks a safe fixturePath")
    target = (root / relative).resolve()
    if root.resolve() not in target.parents:
        raise InventoryError(f"fixturePath escapes fixture root for {resource['id']}")
    return target


def apply_fixture(inventory: dict[str, Any], fixture_root: Path) -> list[str]:
    deleted: list[str] = []
    for resource in inventory["resources"]:
        if resource["ownership"] != "owned":
            continue
        target = _fixture_target(fixture_root, resource)
        if not target.is_file() or target.is_symlink():
            raise InventoryError(f"owned fixture target is not a regular file: {resource['id']}")
        target.unlink()
        deleted.append(resource["id"])
    return deleted


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scope", choices=sorted(SCOPES), required=True)
    parser.add_argument("--inventory", type=Path, required=True)
    parser.add_argument("--apply", action="store_true", help="apply only to an explicit local fixture")
    parser.add_argument("--fixture-root", type=Path, help="required with --apply; never a live host/repository path")
    parser.add_argument("--output", type=Path, help="write the redacted plan/receipt here")
    args = parser.parse_args(argv)
    try:
        inventory = load_inventory(args.inventory, args.scope)
        plan = build_plan(inventory, args.inventory)
        if args.apply:
            if args.fixture_root is None:
                raise InventoryError("--apply requires --fixture-root; live apply is not supported")
            plan["mode"] = "fixture-apply"
            plan["deleted"] = apply_fixture(inventory, args.fixture_root.resolve())
            plan["externalMutation"] = "none-fixture-only"
        elif args.fixture_root is not None:
            raise InventoryError("--fixture-root is valid only with --apply")
    except InventoryError as exc:
        print(f"REFUSED: {exc}", file=sys.stderr)
        return 2
    rendered = json.dumps(_redact(plan), indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
