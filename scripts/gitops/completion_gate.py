#!/usr/bin/env python3
"""Authoritative agent completion gate.

Modes: checkpoint | review-ready | blocked | status | write-evidence

review-ready is fail-closed and AUTHORITATIVE for publishing Linktrend Review Ready:
  1) validate branch/push/clean tree
  2) validate machine-readable evidence record tied to exact HEAD SHA
  3) only then publish success status via readiness_status

Agents must not call mark-review-ready.sh before this gate.
mark-review-ready.sh is a thin wrapper that delegates here.

Evidence JSON (COMPLETION_EVIDENCE_FILE or --evidence-file), tied to HEAD:
{
  "schemaVersion": 1,
  "headSha": "<40-char sha>",
  "classification": "tests" | "docs_only",
  "acceptance": "…",
  "commands": [{"cmd":"…","exitCode":0,"evidencePath":"optional"}],
  "docsOnlyJustification": "required if docs_only, at least 20 chars"
}

Exit codes: 0 ok | 78 incomplete | 2 blocked | 1 failed
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

try:
    import readiness_status as rs
except ImportError:  # pragma: no cover
    rs = None  # type: ignore

EXIT_OK = 0
EXIT_FAILED = 1
EXIT_BLOCKED = 2
EXIT_INCOMPLETE = 78

BLOCKER_REL = Path(".linktrend/completion-blocker.json")


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def run(cmd: list[str], cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, cwd=str(cwd) if cwd else None, text=True, capture_output=True)


def emit(payload: dict) -> None:
    print(json.dumps(payload, indent=2))


def tree_clean(workdir: Path) -> bool:
    p = run(["git", "status", "--porcelain"], cwd=workdir)
    return p.returncode == 0 and not (p.stdout or "").strip()


def head_sha(workdir: Path) -> str:
    p = run(["git", "rev-parse", "HEAD"], cwd=workdir)
    return (p.stdout or "").strip() if p.returncode == 0 else ""


def branch_name(workdir: Path) -> str:
    p = run(["git", "rev-parse", "--abbrev-ref", "HEAD"], cwd=workdir)
    return (p.stdout or "").strip() if p.returncode == 0 else ""


def origin_tip_matches(workdir: Path) -> tuple[bool, str]:
    branch = branch_name(workdir)
    if not branch or branch == "HEAD":
        return False, "detached_or_missing_branch"
    if branch in {"development", "staging", "main"}:
        return False, f"protected_branch:{branch}"
    run(["git", "fetch", "origin", branch], cwd=workdir)
    head = head_sha(workdir)
    p = run(["git", "rev-parse", f"origin/{branch}"], cwd=workdir)
    if p.returncode != 0:
        # Allow file-backend tests without origin remote
        if os.environ.get("LINKTREND_STATUS_BACKEND") == "file":
            return True, head
        return False, "missing_origin_tip"
    tip = (p.stdout or "").strip()
    if head != tip:
        return False, f"head_ne_origin ({head[:8]}!={tip[:8]})"
    return True, head


def load_evidence(path: Path) -> dict:
    if not path.is_file():
        raise FileNotFoundError(f"evidence file missing: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def validate_evidence(evidence: dict, sha: str) -> list[str]:
    missing: list[str] = []
    if int(evidence.get("schemaVersion") or 0) < 1:
        missing.append("evidence_schemaVersion")
    ev_sha = str(evidence.get("headSha") or "")
    if not ev_sha or ev_sha != sha:
        missing.append(f"evidence_sha_mismatch:{ev_sha[:8] or 'empty'}!={sha[:8]}")
    acceptance = str(evidence.get("acceptance") or "").strip()
    if not acceptance:
        missing.append("acceptance_missing")
    classification = str(evidence.get("classification") or "").strip()
    if classification not in {"tests", "docs_only"}:
        missing.append("classification_invalid")
    if classification == "docs_only":
        just = str(evidence.get("docsOnlyJustification") or "").strip()
        if len(just) < 20:
            missing.append("docs_only_justification_too_short")
    cmds = evidence.get("commands")
    if not isinstance(cmds, list) or not cmds:
        missing.append("commands_missing")
    else:
        for i, c in enumerate(cmds):
            if not isinstance(c, dict):
                missing.append(f"command[{i}]_not_object")
                continue
            if not str(c.get("cmd") or "").strip():
                missing.append(f"command[{i}]_cmd_missing")
            try:
                code = int(c.get("exitCode"))
            except (TypeError, ValueError):
                missing.append(f"command[{i}]_exitCode_invalid")
                continue
            if code != 0:
                missing.append(f"command[{i}]_exitCode_{code}")
    return missing


def parse_evidence_commands(raw_commands: list[str]) -> tuple[list[dict], str]:
    cmds = []
    for raw in raw_commands:
        # format: exitCode|cmd  OR  exitCode|path|cmd
        parts = raw.split("|", 2)
        try:
            if len(parts) == 2:
                code_s, cmd = parts
                cmds.append({"cmd": cmd, "exitCode": int(code_s)})
            elif len(parts) == 3:
                code_s, path, cmd = parts
                cmds.append({"cmd": cmd, "exitCode": int(code_s), "evidencePath": path})
            else:
                return [], f"bad --command format: {raw}"
        except ValueError:
            return [], f"bad --command exit code: {raw}"
    return cmds, ""


def publish_ready(sha: str, issue_id: str, notes: str) -> tuple[bool, str]:
    if rs is None:
        return False, "readiness_status_unavailable"
    try:
        st = rs.mark_sha(sha, issue_id, notes)
        return True, str(st)
    except Exception as e:  # noqa: BLE001
        return False, str(e)


def ready_status_ok(sha: str) -> tuple[bool, str]:
    if rs is None:
        return False, "readiness_status_unavailable"
    return rs.is_sha_review_ready(sha)


def write_blocker(path: Path, blocker: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(blocker, indent=2) + "\n", encoding="utf-8")


def cmd_write_evidence(args: argparse.Namespace) -> int:
    """Helper to write a valid evidence record for the current HEAD."""
    workdir = Path(args.workdir).resolve()
    sha = head_sha(workdir)
    if not sha:
        emit({"state": "failed", "error": "no_sha"})
        return EXIT_FAILED
    classification = args.classification
    payload: dict = {
        "schemaVersion": 1,
        "headSha": sha,
        "classification": classification,
        "acceptance": args.acceptance,
        "commands": [],
        "at": utc_now(),
    }
    cmds, error = parse_evidence_commands(args.command or [])
    if error:
        emit({"state": "failed", "error": error})
        return EXIT_FAILED
    if not cmds:
        emit({"state": "failed", "error": "at least one --command is required"})
        return EXIT_FAILED
    payload["commands"] = cmds
    if classification == "docs_only":
        payload["docsOnlyJustification"] = args.docs_justification
    rel = (
        args.evidence_file
        or os.environ.get("COMPLETION_EVIDENCE_FILE")
        or ".linktrend/completion-evidence.json"
    )
    out = Path(rel)
    if not out.is_absolute():
        out = workdir / out
    if out.exists() and out.is_dir():
        emit({"state": "failed", "error": f"evidence_file_is_directory:{out}"})
        return EXIT_FAILED
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    emit({"mode": "write-evidence", "path": str(out), "headSha": sha})
    return EXIT_OK


def cmd_checkpoint(args: argparse.Namespace) -> int:
    workdir = Path(args.workdir).resolve()
    emit(
        {
            "mode": "checkpoint",
            "state": "checkpointed_unfinished",
            "at": utc_now(),
            "branch": branch_name(workdir),
            "sha": head_sha(workdir),
            "clean": tree_clean(workdir),
            "detail": "checkpoint only; no PR; no Review Ready publish",
        }
    )
    return EXIT_OK


def cmd_review_ready(args: argparse.Namespace) -> int:
    """Validate THEN publish. Never publish on failed validation."""
    workdir = Path(args.workdir).resolve()
    missing: list[str] = []
    sha = head_sha(workdir)
    if not sha:
        missing.append("no_sha")

    if branch_name(workdir) in {"development", "staging", "main", "HEAD", ""}:
        missing.append("protected_or_detached_branch")

    if not tree_clean(workdir):
        missing.append("dirty_tree")

    tip_ok, tip_detail = origin_tip_matches(workdir)
    if not tip_ok:
        missing.append(f"origin_tip:{tip_detail}")

    ev_path = Path(
        args.evidence_file
        or os.environ.get("COMPLETION_EVIDENCE_FILE")
        or ".linktrend/completion-evidence.json"
    )
    if not ev_path.is_absolute():
        ev_path = workdir / ev_path
    try:
        evidence = load_evidence(ev_path)
        missing.extend(validate_evidence(evidence, sha))
    except (OSError, json.JSONDecodeError, FileNotFoundError) as e:
        missing.append(f"evidence_unreadable:{e}")

    # Refuse bare --tests-ok / arbitrary COMPLETION_EVIDENCE text as production proof
    if args.tests_ok or os.environ.get("COMPLETION_TESTS_OK"):
        # Allowed only as supplement when evidence file already validates; never alone
        pass
    if not ev_path.is_file():
        if args.tests_ok or os.environ.get("COMPLETION_EVIDENCE"):
            missing.append("bare_flags_insufficient_use_evidence_file")

    if missing:
        # Ensure we did NOT publish
        emit(
            {
                "mode": "review-ready",
                "state": "failed",
                "claim": "incomplete",
                "published": False,
                "missing": missing,
                "sha": sha,
                "at": utc_now(),
            }
        )
        return EXIT_INCOMPLETE

    issue_id = args.issue_id or os.environ.get("COMPLETION_ISSUE_ID") or ""
    if not issue_id:
        br = branch_name(workdir)
        m = re.match(r"^issue/([A-Za-z0-9._]+)-", br)
        issue_id = m.group(1) if m else "unknown"
    notes = args.notes or os.environ.get("COMPLETION_NOTES") or "completion_gate"
    ok, detail = publish_ready(sha, issue_id, notes)
    if not ok:
        emit(
            {
                "mode": "review-ready",
                "state": "failed",
                "published": False,
                "error": detail,
                "sha": sha,
                "at": utc_now(),
            }
        )
        return EXIT_FAILED

    # Confirm published
    ready, ready_detail = ready_status_ok(sha)
    if not ready:
        emit(
            {
                "mode": "review-ready",
                "state": "failed",
                "published": False,
                "error": f"post_publish_verify_failed:{ready_detail}",
                "sha": sha,
                "at": utc_now(),
            }
        )
        return EXIT_FAILED

    emit(
        {
            "mode": "review-ready",
            "state": "review_ready",
            "published": True,
            "sha": sha,
            "branch": branch_name(workdir),
            "at": utc_now(),
            "detail": "Linktrend Review Ready published after validation; Packager opens PR",
        }
    )
    return EXIT_OK


def cmd_blocked(args: argparse.Namespace) -> int:
    workdir = Path(args.workdir).resolve()
    blocker = {
        "schemaVersion": 1,
        "state": "blocked",
        "at": utc_now(),
        "repository": os.environ.get("GITHUB_REPOSITORY") or os.environ.get("GH_REPO") or "",
        "branch": branch_name(workdir),
        "sha": head_sha(workdir),
        "failure": args.reason or os.environ.get("COMPLETION_BLOCKER_REASON") or "unspecified",
        "evidence": args.evidence or os.environ.get("COMPLETION_EVIDENCE") or "",
        "attemptedRepairs": int(args.attempted_repairs or 0),
        "owner": args.owner or "agent",
        "nextAction": args.next_action
        or os.environ.get("COMPLETION_BLOCKER_NEXT")
        or "Resolve blocker then re-run completion_gate review-ready",
    }
    out = Path(args.blocker_file or os.environ.get("COMPLETION_BLOCKER_FILE") or str(BLOCKER_REL))
    if not out.is_absolute():
        out = workdir / out
    write_blocker(out, blocker)
    emit({"mode": "blocked", "state": "blocked", "blockerFile": str(out), **blocker})
    return EXIT_BLOCKED


def cmd_status(args: argparse.Namespace) -> int:
    workdir = Path(args.workdir).resolve()
    sha = head_sha(workdir)
    tip_ok, tip_detail = origin_tip_matches(workdir)
    ready, ready_detail = ready_status_ok(sha) if sha else (False, "no_sha")
    state = "checkpointed_unfinished"
    if ready and tip_ok and tree_clean(workdir):
        state = "review_ready"
    emit(
        {
            "mode": "status",
            "state": state,
            "sha": sha,
            "branch": branch_name(workdir),
            "clean": tree_clean(workdir),
            "originTipOk": tip_ok,
            "originTipDetail": tip_detail,
            "reviewReady": ready,
            "reviewReadyDetail": ready_detail,
            "at": utc_now(),
        }
    )
    return EXIT_OK


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "mode",
        choices=["checkpoint", "review-ready", "blocked", "status", "write-evidence"],
    )
    ap.add_argument("--workdir", default=os.environ.get("GITOPS_WORKDIR") or ".")
    ap.add_argument("--evidence-file", default="")
    ap.add_argument("--issue-id", default="")
    ap.add_argument("--notes", default="")
    ap.add_argument("--tests-ok", action="store_true", help="ignored alone; evidence file required")
    ap.add_argument("--evidence", default="", help="blocker evidence text")
    ap.add_argument("--reason", default="")
    ap.add_argument("--next-action", default="")
    ap.add_argument("--owner", default="")
    ap.add_argument("--attempted-repairs", default="0")
    ap.add_argument("--blocker-file", default="")
    # write-evidence
    ap.add_argument("--classification", choices=["tests", "docs_only"], default="tests")
    ap.add_argument("--acceptance", default="")
    ap.add_argument("--docs-justification", default="")
    ap.add_argument(
        "--command",
        action="append",
        default=[],
        help="exitCode|cmd  or  exitCode|evidencePath|cmd (repeatable)",
    )
    args = ap.parse_args(argv)

    try:
        if args.mode == "checkpoint":
            return cmd_checkpoint(args)
        if args.mode == "review-ready":
            return cmd_review_ready(args)
        if args.mode == "blocked":
            return cmd_blocked(args)
        if args.mode == "status":
            return cmd_status(args)
        if args.mode == "write-evidence":
            return cmd_write_evidence(args)
    except Exception as e:  # noqa: BLE001
        emit({"mode": args.mode, "state": "failed", "error": str(e), "at": utc_now()})
        return EXIT_FAILED
    return EXIT_FAILED


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
