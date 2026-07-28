#!/usr/bin/env python3
"""Review-ready validation (contentSha + marker-commit design).

Design:
  - Final functional commit = contentSha
  - Subsequent marker-only commit adds/updates .linktrend/review-ready.json
  - Record stores contentSha (NOT the marker commit SHA)
  - Packager uses marker tip HEAD as the proposed PR/review SHA
  - Valid when:
      * contentSha == HEAD^
      * tip commit changes only approved readiness artifact paths
      * tip is the marker commit (branch tip)
  - Any later commit invalidates readiness
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any

READY_PATH = ".linktrend/review-ready.json"
ALLOWED_MARKER_PATHS = frozenset(
    {
        ".linktrend/review-ready.json",
        ".linktrend/review-freeze.json",
    }
)


class ReviewReadyError(Exception):
    pass


def _run(git_args: list[str], cwd: Path) -> str:
    proc = subprocess.run(
        ["git", *git_args],
        cwd=str(cwd),
        text=True,
        capture_output=True,
    )
    if proc.returncode != 0:
        raise ReviewReadyError(proc.stderr.strip() or proc.stdout.strip() or f"git {' '.join(git_args)} failed")
    return proc.stdout.strip()


def load_record(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as e:
        raise ReviewReadyError(f"invalid JSON at {path}: {e}") from e
    if not isinstance(data, dict):
        raise ReviewReadyError("review-ready.json must be an object")
    return data


def tip_changed_paths(cwd: Path, tip: str) -> list[str]:
    # Name-status against first parent; marker commits must be non-merge.
    parents = _run(["rev-list", "--parents", "-n", "1", tip], cwd).split()
    if len(parents) != 2:
        raise ReviewReadyError(
            f"marker tip {tip} must have exactly one parent (got {len(parents) - 1})"
        )
    out = _run(["diff-tree", "--no-commit-id", "--name-only", "-r", tip], cwd)
    paths = [p for p in out.splitlines() if p.strip()]
    if not paths:
        raise ReviewReadyError("marker tip changes no files")
    return paths


def validate_repo(cwd: Path, record_path: Path | None = None) -> dict[str, Any]:
    """Validate review-ready at cwd HEAD. Returns detail dict on success."""
    cwd = cwd.resolve()
    path = record_path or (cwd / READY_PATH)
    if not path.is_file():
        raise ReviewReadyError(f"missing {path}")

    data = load_record(path)
    content_sha = (data.get("contentSha") or data.get("commitSha") or "").strip().lower()
    if data.get("commitSha") and not data.get("contentSha"):
        raise ReviewReadyError(
            "legacy commitSha field is not valid; use contentSha (marker-commit design)"
        )
    if not content_sha or len(content_sha) < 40:
        raise ReviewReadyError("contentSha missing or not a full SHA")

    if data.get("deterministicGate") != "pass":
        raise ReviewReadyError(
            f"deterministicGate is not pass (got {data.get('deterministicGate')!r})"
        )

    head = _run(["rev-parse", "HEAD"], cwd).lower()
    parent = _run(["rev-parse", "HEAD^"], cwd).lower()
    if content_sha != parent:
        raise ReviewReadyError(
            f"contentSha ({content_sha}) != HEAD^ ({parent}); record stale or wrong tip"
        )

    paths = tip_changed_paths(cwd, head)
    bad = [p for p in paths if p not in ALLOWED_MARKER_PATHS]
    if bad:
        raise ReviewReadyError(
            f"marker tip changes non-readiness paths: {', '.join(bad)}"
        )
    if READY_PATH not in paths:
        raise ReviewReadyError(f"marker tip must change {READY_PATH}")

    branch = (data.get("branch") or "").strip()
    current = _run(["rev-parse", "--abbrev-ref", "HEAD"], cwd)
    if current != "HEAD" and branch and branch != current:
        raise ReviewReadyError(f"review-ready branch ({branch}) != current ({current})")

    return {
        "ok": True,
        "headSha": head,
        "contentSha": content_sha,
        "branch": branch or current,
        "issueId": data.get("issueId") or "",
        "notes": data.get("notes") or "",
        "summary": data.get("summary") or data.get("notes") or "",
        "record": data,
    }


def write_record(
    cwd: Path,
    *,
    issue_id: str,
    branch: str,
    content_sha: str,
    notes: str = "",
    recorded_at: str,
) -> Path:
    cwd = cwd.resolve()
    linktrend = cwd / ".linktrend"
    linktrend.mkdir(parents=True, exist_ok=True)
    path = linktrend / "review-ready.json"
    payload = {
        "schemaVersion": 2,
        "issueId": issue_id,
        "branch": branch,
        "contentSha": content_sha.lower(),
        "recordedAt": recorded_at,
        "deterministicGate": "pass",
        "notes": notes or "",
    }
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return path


def main(argv: list[str]) -> int:
    if len(argv) >= 2 and argv[1] == "--help":
        print("Usage: validate_review_ready.py [repo_path] [record_path]")
        return 0
    cwd = Path(argv[1]) if len(argv) >= 2 and argv[1].strip() else Path.cwd()
    record = Path(argv[2]) if len(argv) >= 3 and argv[2].strip() else None
    try:
        detail = validate_repo(cwd, record)
    except ReviewReadyError as e:
        print(f"FAIL: {e}", file=sys.stderr)
        return 1
    print(f"PASS: review-ready valid head={detail['headSha']} contentSha={detail['contentSha']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
