#!/usr/bin/env python3
"""Fixture-aware secret scanner for managed Fast/Full.

Scans every tracked file. Synthetic fixtures pass only through an exact
versioned non-production declaration bound to path, line/field, digest,
candidate content tree, and scanner policy. Realistic credential formats
can never be approved. Repository-owned scanners stay additive and blocking.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

SCANNER_POLICY_VERSION = "secret-scan-policy/v1"
SYNTHETIC_PREFIX = "ltfx."
DECLARATION_REL = ".github/linktrend-secret-scan-fixtures.json"
REPO_SCANNERS_REL = ".github/linktrend-repository-secret-scanners.json"

KIND_CREDENTIAL = "credential_finding"
KIND_APPROVED = "approved_synthetic_fixture"
KIND_STALE = "stale_fixture_declaration"
KIND_SCOPE = "fixture_scope_violation"

RULE_ASSIGNMENT_SECRET = "assignment.secret"
RULE_GITHUB = "format.github"
RULE_CLOUD = "format.cloud"
RULE_DATABASE = "format.database"
RULE_PRIVATE_KEY = "format.private_key"
RULE_HIGH_ENTROPY = "format.high_entropy"
RULE_BINDING_TREE = "binding.candidate_tree"
RULE_BINDING_POLICY = "binding.scanner_policy"
RULE_UNKNOWN = "declaration.unknown_rule"
RULE_REPO_SCANNER = "repository_scanner.failure"

KNOWN_RULES = frozenset(
    {
        RULE_ASSIGNMENT_SECRET,
        RULE_GITHUB,
        RULE_CLOUD,
        RULE_DATABASE,
        RULE_PRIVATE_KEY,
        RULE_HIGH_ENTROPY,
    }
)

CREDENTIAL_FIELDS = (
    "secret",
    "token",
    "password",
    "passwd",
    "api_key",
    "apikey",
    "api-key",
    "private_key",
    "private-key",
    "key",
    "url",
)

ASSIGNMENT_RE = re.compile(
    r"(?i)\b(?P<field>"
    + "|".join(re.escape(name) for name in CREDENTIAL_FIELDS)
    + r")\b\s*[:=]\s*(?P<quote>['\"])(?P<value>[^'\"\n]+)(?P=quote)"
)
JSON_FIELD_RE = re.compile(
    r"(?i)(?P<q>['\"])(?P<field>"
    + "|".join(re.escape(name) for name in CREDENTIAL_FIELDS)
    + r")(?P=q)\s*:\s*(?P<quote>['\"])(?P<value>[^'\"\n]+)(?P=quote)"
)
SYNTHETIC_ASSIGNMENT_RE = re.compile(
    r"(?i)\b(?P<field>[A-Za-z_][A-Za-z0-9_]*)\b\s*[:=]\s*(?P<quote>['\"])"
    rf"(?P<value>{re.escape(SYNTHETIC_PREFIX)}[^'\"\n]+)(?P=quote)"
)
MIN_ASSIGNMENT_LEN = 12
GITHUB_RE = re.compile(r"\b(ghp_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,}|gho_[A-Za-z0-9]{20,})\b")
CLOUD_RE = re.compile(r"\b(AKIA[0-9A-Z]{16}|ASIA[0-9A-Z]{16}|AIza[0-9A-Za-z\-_]{20,})\b")
DATABASE_RE = re.compile(
    r"\b(?:postgres|postgresql|mysql|mongodb(?:\+srv)?)://[^\s'\"\\]+",
    re.IGNORECASE,
)
PRIVATE_KEY_RE = re.compile(r"-----BEGIN (?:RSA |OPENSSH |EC |DSA )?PRIVATE KEY-----")
SKIP_SUFFIXES = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".ico", ".woff", ".woff2", ".pdf"}


class SecretScanError(Exception):
    def __init__(self, code: str, detail: str = "") -> None:
        super().__init__(f"{code}:{detail}" if detail else code)
        self.code = code
        self.detail = detail


def digest_bytes(raw: bytes) -> str:
    return "sha256:" + hashlib.sha256(raw).hexdigest()


def _git(root: Path, *args: str) -> str:
    result = subprocess.run(["git", *args], cwd=root, text=True, capture_output=True, check=False)
    if result.returncode:
        raise SecretScanError("git_failed", (result.stderr or result.stdout).strip())
    return result.stdout


def tracked_files(root: Path) -> list[str]:
    text = _git(root, "ls-files", "-z")
    return [item.replace("\\", "/") for item in text.split("\0") if item]


def candidate_content_tree(root: Path) -> str:
    """40-hex identity of tracked content excluding the fixture declaration file."""
    digest = hashlib.sha1()
    for rel in tracked_files(root):
        if rel == DECLARATION_REL:
            continue
        blob = _git(root, "hash-object", rel).strip()
        digest.update(rel.encode("utf-8"))
        digest.update(b"\0")
        digest.update(blob.encode("ascii"))
        digest.update(b"\n")
    return digest.hexdigest()


def _shannon(value: str) -> float:
    counts: dict[str, int] = {}
    for char in value:
        counts[char] = counts.get(char, 0) + 1
    length = len(value)
    return -sum((n / length) * math.log2(n / length) for n in counts.values())


def is_realistic_value(value: str) -> bool:
    if GITHUB_RE.search(value) or CLOUD_RE.search(value) or DATABASE_RE.search(value):
        return True
    if PRIVATE_KEY_RE.search(value):
        return True
    compact = re.sub(r"\s+", "", value)
    if len(compact) >= 40 and _shannon(compact) >= 3.5 and not compact.startswith(SYNTHETIC_PREFIX):
        return True
    return False


def is_synthetic_value(value: str) -> bool:
    return value.startswith(SYNTHETIC_PREFIX) and not is_realistic_value(value)


def _add_detection(
    detections: list[dict[str, Any]],
    *,
    path: str,
    line: int,
    field: str,
    rule: str,
    value: str,
) -> None:
    key = (path, line, field, rule, value)
    if any(
        (row["path"], row["line"], row["field"], row["rule"], row["value"]) == key
        for row in detections
    ):
        return
    detections.append(
        {
            "path": path,
            "line": line,
            "field": field,
            "rule": rule,
            "value": value,
            "digest": digest_bytes(value.encode("utf-8")),
            "realistic": is_realistic_value(value),
        }
    )


def scan_text(path: str, text: str) -> list[dict[str, Any]]:
    detections: list[dict[str, Any]] = []
    for index, raw_line in enumerate(text.splitlines(), start=1):
        for match in ASSIGNMENT_RE.finditer(raw_line):
            field = match.group("field").lower().replace("-", "_")
            value = match.group("value")
            if len(value) < MIN_ASSIGNMENT_LEN and not value.startswith(SYNTHETIC_PREFIX):
                continue
            rule = RULE_ASSIGNMENT_SECRET
            if GITHUB_RE.search(value):
                rule = RULE_GITHUB
            elif CLOUD_RE.search(value):
                rule = RULE_CLOUD
            elif DATABASE_RE.search(value):
                rule = RULE_DATABASE
            elif len(value) >= 40 and _shannon(value) >= 3.5 and not value.startswith(SYNTHETIC_PREFIX):
                rule = RULE_HIGH_ENTROPY
            _add_detection(detections, path=path, line=index, field=field, rule=rule, value=value)
        for match in JSON_FIELD_RE.finditer(raw_line):
            field = match.group("field").lower().replace("-", "_")
            value = match.group("value")
            if len(value) < MIN_ASSIGNMENT_LEN and not value.startswith(SYNTHETIC_PREFIX):
                continue
            _add_detection(
                detections,
                path=path,
                line=index,
                field=field,
                rule=RULE_ASSIGNMENT_SECRET,
                value=value,
            )
        for match in SYNTHETIC_ASSIGNMENT_RE.finditer(raw_line):
            field = match.group("field").lower().replace("-", "_")
            value = match.group("value")
            _add_detection(
                detections,
                path=path,
                line=index,
                field=field,
                rule=RULE_ASSIGNMENT_SECRET,
                value=value,
            )
        for match in GITHUB_RE.finditer(raw_line):
            _add_detection(
                detections,
                path=path,
                line=index,
                field="token",
                rule=RULE_GITHUB,
                value=match.group(0),
            )
        for match in CLOUD_RE.finditer(raw_line):
            _add_detection(
                detections,
                path=path,
                line=index,
                field="key",
                rule=RULE_CLOUD,
                value=match.group(0),
            )
        for match in DATABASE_RE.finditer(raw_line):
            _add_detection(
                detections,
                path=path,
                line=index,
                field="url",
                rule=RULE_DATABASE,
                value=match.group(0),
            )
        if PRIVATE_KEY_RE.search(raw_line):
            _add_detection(
                detections,
                path=path,
                line=index,
                field="private_key",
                rule=RULE_PRIVATE_KEY,
                value=raw_line.strip(),
            )
    return detections


def _load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise SecretScanError("declaration_malformed", str(exc)) from exc


def _validate_declaration(payload: Any) -> dict[str, Any]:
    if not isinstance(payload, dict):
        raise SecretScanError("declaration_malformed", "root must be an object")
    required = {
        "schemaVersion",
        "kind",
        "scannerPolicyVersion",
        "candidateTree",
        "fixtures",
    }
    missing = required - set(payload)
    if missing:
        raise SecretScanError("declaration_malformed", f"missing {sorted(missing)}")
    if payload.get("schemaVersion") != 1 or payload.get("kind") != "secret-scan-fixtures":
        raise SecretScanError("declaration_malformed", "schema or kind")
    if not isinstance(payload.get("candidateTree"), str) or not re.fullmatch(
        r"[0-9a-f]{40}", str(payload["candidateTree"])
    ):
        raise SecretScanError("declaration_malformed", "candidateTree")
    fixtures = payload.get("fixtures")
    if not isinstance(fixtures, list):
        raise SecretScanError("declaration_malformed", "fixtures")
    for row in fixtures:
        if not isinstance(row, dict):
            raise SecretScanError("declaration_malformed", "fixture")
        for key in ("id", "path", "line", "field", "rule", "digest", "purpose", "production"):
            if key not in row:
                raise SecretScanError("declaration_malformed", f"fixture.{key}")
        if row.get("production") is not False:
            raise SecretScanError("declaration_malformed", "production must be false")
        if not str(row.get("purpose") or "").strip():
            raise SecretScanError("declaration_malformed", "purpose")
    return payload


def _finding(
    *,
    kind: str,
    path: str,
    line: int | None,
    field: str | None,
    rule: str,
    digest: str | None,
    fixture_id: str | None = None,
    scanner_id: str | None = None,
    detail: str | None = None,
) -> dict[str, Any]:
    row: dict[str, Any] = {"kind": kind, "path": path, "rule": rule}
    if line is not None:
        row["line"] = line
    if field is not None:
        row["field"] = field
    if digest is not None:
        row["digest"] = digest
    if fixture_id is not None:
        row["fixtureId"] = fixture_id
    if scanner_id is not None:
        row["scannerId"] = scanner_id
    if detail is not None:
        row["detail"] = detail
    return row


def _evaluate_declarations(
    detections: list[dict[str, Any]],
    declaration: dict[str, Any] | None,
    content_tree: str,
) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    fixtures = list((declaration or {}).get("fixtures") or [])
    bindings_valid = True
    if declaration is not None:
        if declaration.get("scannerPolicyVersion") != SCANNER_POLICY_VERSION:
            bindings_valid = False
            findings.append(
                _finding(
                    kind=KIND_STALE,
                    path=DECLARATION_REL,
                    line=None,
                    field=None,
                    rule=RULE_BINDING_POLICY,
                    digest=None,
                    detail="scannerPolicyVersion",
                )
            )
        if declaration.get("candidateTree") != content_tree:
            bindings_valid = False
            findings.append(
                _finding(
                    kind=KIND_STALE,
                    path=DECLARATION_REL,
                    line=None,
                    field=None,
                    rule=RULE_BINDING_TREE,
                    digest=None,
                    detail="candidateTree",
                )
            )
        for row in fixtures:
            if row["rule"] not in KNOWN_RULES:
                bindings_valid = False
                findings.append(
                    _finding(
                        kind=KIND_SCOPE,
                        path=str(row["path"]),
                        line=int(row["line"]),
                        field=str(row["field"]),
                        rule=RULE_UNKNOWN,
                        digest=str(row["digest"]),
                        fixture_id=str(row["id"]),
                    )
                )

    used: set[str] = set()
    for detection in detections:
        match = None
        if bindings_valid:
            for row in fixtures:
                if (
                    row["path"] == detection["path"]
                    and int(row["line"]) == detection["line"]
                    and str(row["field"]) == detection["field"]
                    and str(row["rule"]) == detection["rule"]
                    and str(row["digest"]) == detection["digest"]
                ):
                    match = row
                    break
        if match is not None and not detection["realistic"] and is_synthetic_value(detection["value"]):
            used.add(str(match["id"]))
            findings.append(
                _finding(
                    kind=KIND_APPROVED,
                    path=detection["path"],
                    line=detection["line"],
                    field=detection["field"],
                    rule=detection["rule"],
                    digest=detection["digest"],
                    fixture_id=str(match["id"]),
                )
            )
            continue
        kind = KIND_CREDENTIAL
        fixture_id = None
        if detection["realistic"]:
            kind = KIND_CREDENTIAL
            if match is not None:
                fixture_id = str(match["id"])
        elif match is not None and not is_synthetic_value(detection["value"]):
            kind = KIND_CREDENTIAL
            fixture_id = str(match["id"])
        elif declaration is not None and not bindings_valid:
            kind = KIND_STALE
        else:
            near = [
                row
                for row in fixtures
                if row["path"] == detection["path"] or str(row["digest"]) == detection["digest"]
            ]
            if near:
                kind = KIND_STALE if any(str(row["digest"]) != detection["digest"] for row in near) else KIND_SCOPE
                fixture_id = str(near[0]["id"])
        findings.append(
            _finding(
                kind=kind,
                path=detection["path"],
                line=detection["line"],
                field=detection["field"],
                rule=detection["rule"],
                digest=detection["digest"],
                fixture_id=fixture_id,
            )
        )

    if bindings_valid:
        for row in fixtures:
            if str(row["id"]) in used:
                continue
            findings.append(
                _finding(
                    kind=KIND_STALE,
                    path=str(row["path"]),
                    line=int(row["line"]),
                    field=str(row["field"]),
                    rule=str(row["rule"]),
                    digest=str(row["digest"]),
                    fixture_id=str(row["id"]),
                    detail="unused_or_stale_declaration",
                )
            )
    return findings


def _run_repository_scanners(root: Path) -> list[dict[str, Any]]:
    path = root / REPO_SCANNERS_REL
    if not path.is_file():
        return []
    payload = _load_json(path)
    if not isinstance(payload, dict) or not isinstance(payload.get("scanners"), list):
        raise SecretScanError("repository_scanners_malformed", REPO_SCANNERS_REL)
    findings: list[dict[str, Any]] = []
    for row in payload["scanners"]:
        if not isinstance(row, dict) or not row.get("id") or not isinstance(row.get("command"), list):
            raise SecretScanError("repository_scanners_malformed", "scanner")
        command = [str(part) for part in row["command"]]
        if not command:
            raise SecretScanError("repository_scanners_malformed", "empty command")
        result = subprocess.run(command, cwd=root, text=True, capture_output=True, check=False)
        if result.returncode != 0:
            findings.append(
                _finding(
                    kind=KIND_CREDENTIAL,
                    path=REPO_SCANNERS_REL,
                    line=None,
                    field=None,
                    rule=RULE_REPO_SCANNER,
                    digest=None,
                    scanner_id=str(row["id"]),
                    detail=f"exit={result.returncode}",
                )
            )
    return findings


def scan_repository(root: Path) -> dict[str, Any]:
    root = root.resolve()
    content_tree = candidate_content_tree(root)
    declaration = None
    declared = root / DECLARATION_REL
    if declared.is_file():
        declaration = _validate_declaration(_load_json(declared))

    detections: list[dict[str, Any]] = []
    for rel in tracked_files(root):
        if rel == DECLARATION_REL:
            continue
        path = root / rel
        if not path.is_file() or path.suffix.lower() in SKIP_SUFFIXES:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            text = path.read_bytes().decode("latin-1", errors="ignore")
        detections.extend(scan_text(rel, text))

    findings = _evaluate_declarations(detections, declaration, content_tree)
    findings.extend(_run_repository_scanners(root))
    ok = not any(row["kind"] in {KIND_CREDENTIAL, KIND_STALE, KIND_SCOPE} for row in findings)
    return {
        "schemaVersion": 1,
        "kind": "secret-scan-result",
        "scannerPolicyVersion": SCANNER_POLICY_VERSION,
        "candidateTree": content_tree,
        "ok": ok,
        "findings": findings,
    }


def identify_synthetic_candidates(root: Path) -> list[dict[str, Any]]:
    """Identify likely synthetic fixtures. Never writes an approval."""
    root = root.resolve()
    candidates: list[dict[str, Any]] = []
    for rel in tracked_files(root):
        if rel == DECLARATION_REL:
            continue
        path = root / rel
        if not path.is_file() or path.suffix.lower() in SKIP_SUFFIXES:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        for detection in scan_text(rel, text):
            if detection["realistic"]:
                continue
            if is_synthetic_value(detection["value"]) or detection["rule"] == RULE_ASSIGNMENT_SECRET:
                candidates.append(
                    {
                        "path": detection["path"],
                        "line": detection["line"],
                        "field": detection["field"],
                        "rule": detection["rule"],
                        "digest": detection["digest"],
                    }
                )
    return candidates


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", default=".")
    parser.add_argument("--json-output")
    args = parser.parse_args(argv)
    root = Path(args.repo)
    try:
        result = scan_repository(root)
    except SecretScanError as exc:
        payload = {"ok": False, "error": exc.code, "detail": exc.detail}
        if args.json_output:
            Path(args.json_output).write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(payload, sort_keys=True))
        return 2
    text = json.dumps(result, indent=2) + "\n"
    if args.json_output:
        Path(args.json_output).write_text(text, encoding="utf-8")
    print(text, end="")
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
