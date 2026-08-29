"""OpenClaw-only customization-scoped v2.5.2 admission.

Checks LiNKtrend Prime customization paths from a validated consumer
manifest plus v2.5.2 managed/transaction-changed destinations. Untouched
upstream OpenClaw is never scanned and never required to be repaired.
"""

from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path
from typing import Any, Callable, Mapping

from .errors import InvalidPackageError
from .hashing import sha256_bytes

KIND = "openclaw-customization-admission"
MANIFEST_KIND = "openclaw-prime-customization-manifest"
INSTALLER_VERSION = "2.5.2"
REPOSITORY = "linktrend/openclaw_prime"
SCHEMA_REL = "core/managed-core/schemas/openclaw-customization-admission.schema.json"
PACKAGE_MANIFEST_REL = "core/managed-core/MANIFEST.json"
INSTALLED_STATE_REL = ".ide-development/installed-state.json"
HEX40 = re.compile(r"^[0-9a-f]{40}$")
DIGEST = re.compile(r"^sha256:[0-9a-f]{64}$")
SKIPPED_KIND = "skipped_input"
Scanner = Callable[[list[str]], Mapping[str, Any]]


class OpenClawAdmissionError(InvalidPackageError):
    """Fail-closed OpenClaw customization admission refusal."""


def _canonical_bytes(payload: Mapping[str, Any]) -> bytes:
    return (json.dumps(payload, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")


def _require_oid(value: Any, code: str) -> str:
    if not isinstance(value, str) or not HEX40.fullmatch(value):
        raise OpenClawAdmissionError(code)
    return value


def _require_relpath(value: Any, code: str) -> str:
    if not isinstance(value, str) or not value or value.startswith("/") or "\\" in value or ".." in Path(value).parts:
        raise OpenClawAdmissionError(code)
    return value.replace("\\", "/")


def _identity(raw: Any, code: str) -> dict[str, str]:
    if not isinstance(raw, Mapping):
        raise OpenClawAdmissionError(code)
    return {
        "commit": _require_oid(raw.get("commit"), code),
        "tree": _require_oid(raw.get("tree"), code),
    }


def _git(root: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=root,
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        raise OpenClawAdmissionError("stale-manifest")
    return (result.stdout or "").strip()


def _live_consumer_identity(root: Path) -> dict[str, str]:
    return {
        "commit": _require_oid(_git(root, "rev-parse", "HEAD"), "stale-manifest"),
        "tree": _require_oid(_git(root, "rev-parse", "HEAD^{tree}"), "stale-manifest"),
    }


def _load_json(path: Path, code: str) -> Any:
    if path.is_symlink() or not path.is_file():
        raise OpenClawAdmissionError(code)
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise OpenClawAdmissionError(code) from exc


def _manifest_digest(payload: Mapping[str, Any]) -> str:
    body = {key: value for key, value in payload.items() if key != "contentDigest"}
    return sha256_bytes(_canonical_bytes(body))


def _load_consumer_manifest(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise OpenClawAdmissionError("missing-manifest")
    payload = _load_json(path, "stale-manifest")
    if not isinstance(payload, dict):
        raise OpenClawAdmissionError("stale-manifest")
    digest = payload.get("contentDigest")
    if not isinstance(digest, str) or not DIGEST.fullmatch(digest):
        raise OpenClawAdmissionError("stale-manifest")
    if digest != _manifest_digest(payload):
        raise OpenClawAdmissionError("stale-manifest")
    if payload.get("schemaVersion") != 1 or payload.get("kind") != MANIFEST_KIND:
        raise OpenClawAdmissionError("stale-manifest")
    if payload.get("repository") != REPOSITORY or payload.get("installerVersion") != INSTALLER_VERSION:
        raise OpenClawAdmissionError("stale-manifest")
    paths = payload.get("customizationPaths")
    if not isinstance(paths, list) or not paths:
        raise OpenClawAdmissionError("stale-manifest")
    seen: set[str] = set()
    customization: list[str] = []
    for item in paths:
        rel = _require_relpath(item, "stale-manifest")
        if rel in seen:
            raise OpenClawAdmissionError("stale-manifest")
        seen.add(rel)
        customization.append(rel)
    findings = payload.get("acceptedFindings") or []
    if not isinstance(findings, list):
        raise OpenClawAdmissionError("stale-manifest")
    return {
        "consumer": _identity(payload.get("consumer"), "stale-manifest"),
        "upstream": _identity(payload.get("upstream"), "upstream-identity-drift"),
        "customizationPaths": customization,
        "acceptedFindings": [_finding(row, "stale-manifest") for row in findings],
        "contentDigest": digest,
    }


def _finding(raw: Any, code: str) -> dict[str, Any]:
    if not isinstance(raw, Mapping):
        raise OpenClawAdmissionError(code)
    row: dict[str, Any] = {
        "kind": raw.get("kind"),
        "path": _require_relpath(raw.get("path"), code),
        "rule": raw.get("rule"),
    }
    if not isinstance(row["kind"], str) or not row["kind"]:
        raise OpenClawAdmissionError(code)
    if not isinstance(row["rule"], str) or not row["rule"]:
        raise OpenClawAdmissionError(code)
    if "line" in raw:
        line = raw["line"]
        if not isinstance(line, int) or isinstance(line, bool) or line < 1:
            raise OpenClawAdmissionError(code)
        row["line"] = line
    if "field" in raw:
        field = raw["field"]
        if not isinstance(field, str) or not field:
            raise OpenClawAdmissionError(code)
        row["field"] = field
    if "digest" in raw:
        digest = raw["digest"]
        if not isinstance(digest, str) or not DIGEST.fullmatch(digest):
            raise OpenClawAdmissionError(code)
        row["digest"] = digest
    if "detail" in raw:
        detail = raw["detail"]
        if not isinstance(detail, str) or not detail:
            raise OpenClawAdmissionError(code)
        row["detail"] = detail
    return row


def _finding_key(row: Mapping[str, Any]) -> tuple[Any, ...]:
    return (
        row.get("kind"),
        row.get("path"),
        row.get("rule"),
        row.get("line"),
        row.get("field"),
        row.get("digest"),
    )


def _managed_transaction_paths(package_root: Path) -> set[str]:
    """v2.5.2 managed destinations plus the installer transaction state path."""
    payload = _load_json(package_root / PACKAGE_MANIFEST_REL, "stale-manifest")
    if not isinstance(payload, dict):
        raise OpenClawAdmissionError("stale-manifest")
    if str(payload.get("packageVersion") or "").lstrip("v") != INSTALLER_VERSION:
        raise OpenClawAdmissionError("stale-manifest")
    paths = {INSTALLED_STATE_REL}
    files = payload.get("files")
    if not isinstance(files, list):
        raise OpenClawAdmissionError("stale-manifest")
    for entry in files:
        if not isinstance(entry, Mapping):
            continue
        destination = entry.get("destination")
        if isinstance(destination, str) and destination:
            paths.add(_require_relpath(destination, "stale-manifest"))
    return paths


def _run_scanner(scanner: Scanner, paths: list[str]) -> Mapping[str, Any]:
    try:
        result = scanner(paths)
    except TimeoutError as exc:
        raise OpenClawAdmissionError("scanner-timeout") from exc
    except OpenClawAdmissionError:
        raise
    except Exception as exc:
        raise OpenClawAdmissionError("scanner-error") from exc
    if not isinstance(result, Mapping):
        raise OpenClawAdmissionError("scanner-error")
    error_type = result.get("errorType")
    if error_type == "timeout":
        raise OpenClawAdmissionError("scanner-timeout")
    if error_type:
        raise OpenClawAdmissionError("scanner-error")
    return result


def admit_openclaw_customization(
    *,
    consumer_root: Path,
    package_root: Path,
    manifest_path: Path,
    observed_upstream: Mapping[str, Any],
    scanner: Scanner,
    timeout_seconds: int | None = None,
) -> dict[str, Any]:
    """Admit only customization plus v2.5.2 managed/transaction-changed paths."""
    del timeout_seconds  # Bound is owned by the injected scanner; TimeoutError fails closed.
    consumer_root = consumer_root.resolve()
    package_root = package_root.resolve()
    manifest_path = Path(manifest_path)
    manifest = _load_consumer_manifest(manifest_path)
    live = _live_consumer_identity(consumer_root)
    if live != manifest["consumer"]:
        raise OpenClawAdmissionError("stale-manifest")
    upstream = _identity(observed_upstream, "upstream-identity-drift")
    if upstream != manifest["upstream"]:
        raise OpenClawAdmissionError("upstream-identity-drift")
    checked = sorted(set(manifest["customizationPaths"]) | _managed_transaction_paths(package_root))
    scan = _run_scanner(scanner, checked)
    raw_findings = scan.get("findings") or []
    if not isinstance(raw_findings, list):
        raise OpenClawAdmissionError("scanner-error")
    checked_set = set(checked)
    scoped = [
        _finding(row, "scanner-error")
        for row in raw_findings
        if isinstance(row, Mapping) and row.get("path") in checked_set
    ]
    accepted = {_finding_key(row) for row in manifest["acceptedFindings"]}
    for row in scoped:
        key = _finding_key(row)
        if key in accepted:
            continue
        if row["kind"] == SKIPPED_KIND:
            raise OpenClawAdmissionError("new-skipped-input")
        raise OpenClawAdmissionError("new-or-changed-finding")
    return {
        "schemaVersion": 1,
        "kind": KIND,
        "installerVersion": INSTALLER_VERSION,
        "repository": REPOSITORY,
        "consumer": live,
        "upstream": upstream,
        "manifest": {
            "path": manifest_path.name,
            "contentDigest": manifest["contentDigest"],
            "customizationPaths": list(manifest["customizationPaths"]),
        },
        "checkedPaths": checked,
        "findings": scoped,
        "verdict": "admitted",
        "noUpstreamScanOrMutation": True,
    }
