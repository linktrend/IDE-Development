#!/usr/bin/env python3
"""Safe cleanup controls for merged/abandoned branches and completed repair records.

Default posture is dry-run / plan-only. Never invent authority to close or delete
live GitHub PRs, issues, or remote branches — that remains gated by
cleanup-merged-branches.sh evidence (MERGED / abandoned) or explicit file-backend
completed-repair --apply after plan review.

Preserve policy (Issue #51): committed defaults in cleanup_preserve.defaults.json,
optionally overlaid by CLEANUP_PRESERVE_JSON path or LINKTREND_CLEANUP_PRESERVE_FILE.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SCHEMA_VERSION = 1
ISSUE_BRANCH_RE = re.compile(r"^issue/(\d+)(?:-|$)")

_HERE = Path(__file__).resolve().parent
DEFAULT_PRESERVE_PATH = _HERE / "cleanup_preserve.defaults.json"


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def load_preserve_policy(path: Path | None = None) -> dict[str, Any]:
    """Load preserve policy; fail closed on missing/invalid schema.

    Merge order (later overlays win for additive sets):
      1. cleanup_preserve.defaults.json (committed)
      2. LINKTREND_CLEANUP_PRESERVE_FILE or --policy path
      3. .linktrend/cleanup-preserve.json (local overlay; gitignored)
      4. LINKTREND_CLEANUP_PRESERVE env (comma-separated exact branch names)
    """
    issues: set[int] = set()
    prs: set[int] = set()
    exact: set[str] = set()
    sources: list[str] = []

    def _merge(data: dict[str, Any], src: str) -> None:
        nonlocal issues, prs, exact
        if data.get("defaults") is False and src != str(DEFAULT_PRESERVE_PATH):
            # Explicit overlay may clear defaults only when it is the primary path.
            pass
        for key_a, key_b in (
            ("preserveIssueNumbers", "issueNumbers"),
            ("preservePrNumbers", "prNumbers"),
            ("preserveBranchExact", "branches"),
        ):
            raw = data.get(key_a)
            if raw is None:
                raw = data.get(key_b)
            if raw is None:
                continue
            if key_a == "preserveIssueNumbers":
                issues |= {int(x) for x in raw}
            elif key_a == "preservePrNumbers":
                prs |= {int(x) for x in raw}
            else:
                exact |= {str(x) for x in raw}
        sources.append(src)

    # 1) Committed defaults
    if DEFAULT_PRESERVE_PATH.is_file():
        defaults = json.loads(DEFAULT_PRESERVE_PATH.read_text(encoding="utf-8"))
        if int(defaults.get("schemaVersion") or 0) != SCHEMA_VERSION:
            raise ValueError(
                f"unsupported preserve schemaVersion={defaults.get('schemaVersion')!r}; "
                f"expected {SCHEMA_VERSION}"
            )
        if defaults.get("defaults") is not False:
            _merge(defaults, str(DEFAULT_PRESERVE_PATH))

    # 2) Explicit path / env file
    candidate = path
    if candidate is None:
        env = (os.environ.get("LINKTREND_CLEANUP_PRESERVE_FILE") or "").strip()
        if env:
            candidate = Path(env)
    if candidate is not None:
        if not candidate.is_file():
            raise FileNotFoundError(f"preserve policy missing: {candidate}")
        data = json.loads(candidate.read_text(encoding="utf-8"))
        if "schemaVersion" in data and int(data.get("schemaVersion") or 0) != SCHEMA_VERSION:
            raise ValueError(
                f"unsupported preserve schemaVersion={data.get('schemaVersion')!r}; "
                f"expected {SCHEMA_VERSION}"
            )
        if data.get("defaults") is False:
            issues.clear()
            prs.clear()
            exact.clear()
            sources.clear()
        _merge(data, str(candidate))

    # 3) Local gitignored overlay
    local = Path(".linktrend/cleanup-preserve.json")
    if local.is_file():
        _merge(json.loads(local.read_text(encoding="utf-8")), str(local))

    # 4) Env branch list
    env_branches = (os.environ.get("LINKTREND_CLEANUP_PRESERVE") or "").strip()
    if env_branches:
        exact |= {b.strip() for b in env_branches.split(",") if b.strip()}
        sources.append("env:LINKTREND_CLEANUP_PRESERVE")

    if not sources and not DEFAULT_PRESERVE_PATH.is_file():
        raise FileNotFoundError(f"preserve policy missing: {DEFAULT_PRESERVE_PATH}")

    return {
        "schemaVersion": SCHEMA_VERSION,
        "path": sources[0] if sources else str(DEFAULT_PRESERVE_PATH),
        "sources": sources,
        "preserveIssueNumbers": sorted(issues),
        "preservePrNumbers": sorted(prs),
        "preserveBranchExact": sorted(exact),
        "issue_set": issues,
        "pr_set": prs,
        "exact_set": exact,
    }


def issue_number_from_branch(branch: str) -> int | None:
    m = ISSUE_BRANCH_RE.match((branch or "").strip())
    if not m:
        return None
    return int(m.group(1))


def preserve_reason(
    branch: str,
    *,
    policy: dict[str, Any] | None = None,
    pr_number: int | None = None,
) -> str | None:
    """Return KEEP reason if branch/PR is explicitly preserved; else None."""
    pol = policy or load_preserve_policy()
    name = (branch or "").strip()
    if not name:
        return None
    if name in pol["exact_set"]:
        return "preserve_branch_exact"
    issue_n = issue_number_from_branch(name)
    if issue_n is not None and issue_n in pol["issue_set"]:
        return f"preserve_issue_number:{issue_n}"
    if pr_number is not None and int(pr_number) in pol["pr_set"]:
        return f"preserve_pr_number:{int(pr_number)}"
    return None


def classify_branch_decision(
    branch: str,
    *,
    evidence: str,
    pr_number: int | None = None,
    policy: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Pure decision helper used by tests and planners.

    evidence: OPEN | MERGED | ABANDONED | NONE (cleanup-merged-branches.sh vocabulary)
    """
    pol = policy or load_preserve_policy()
    reason = preserve_reason(branch, policy=pol, pr_number=pr_number)
    if reason:
        return {
            "branch": branch,
            "decision": "KEEP",
            "reason": reason,
            "evidence": evidence,
            "authorized_delete": False,
        }
    if evidence == "OPEN":
        return {
            "branch": branch,
            "decision": "KEEP",
            "reason": f"open_pr:{pr_number or ''}".rstrip(":"),
            "evidence": evidence,
            "authorized_delete": False,
        }
    if evidence in ("MERGED", "ABANDONED"):
        return {
            "branch": branch,
            "decision": "ELIGIBLE",
            "reason": f"{evidence.lower()}_pr_evidence",
            "evidence": evidence,
            "authorized_delete": True,
        }
    return {
        "branch": branch,
        "decision": "KEEP",
        "reason": "no_merged_or_abandoned_pr_evidence",
        "evidence": evidence,
        "authorized_delete": False,
    }


def list_completed_file_tasks(root: Path) -> list[dict[str, Any]]:
    """List resolved repair task JSON files under a file-backend root."""
    out: list[dict[str, Any]] = []
    if not root.is_dir():
        return out
    for path in sorted(root.glob("*.json")):
        try:
            task = json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue
        if task.get("resolutionState") != "resolved":
            continue
        out.append(
            {
                "failureId": task.get("failureId") or task.get("id") or path.stem,
                "path": str(path),
                "repository": task.get("repository") or "",
                "failureType": task.get("failureType") or "",
                "branch": task.get("branch") or "",
                "updatedAt": task.get("updatedAt") or "",
                "issueNumber": task.get("issueNumber"),
            }
        )
    return out


def plan_completed_repair_cleanup(
    root: Path,
    *,
    apply: bool = False,
) -> dict[str, Any]:
    """Plan (default) or apply file-backend cleanup of completed repair records.

    GitHub Issue records are never closed/deleted here — report only via notes.
    Apply removes only local resolved JSON files under the file backend root.
    """
    completed = list_completed_file_tasks(root)
    actions: list[dict[str, Any]] = []
    for row in completed:
        action = {
            "failureId": row["failureId"],
            "path": row["path"],
            "decision": "WOULD_DELETE_FILE" if not apply else "DELETED_FILE",
            "authorized": True,
            "scope": "file_backend_resolved_only",
        }
        if apply:
            Path(row["path"]).unlink(missing_ok=True)
        actions.append(action)
    return {
        "schemaVersion": SCHEMA_VERSION,
        "mode": "apply" if apply else "dry-run",
        "backend": "file",
        "root": str(root),
        "completedCount": len(completed),
        "actions": actions,
        "githubMutation": "none",
        "notes": [
            "GitHub closed repair issues are not deleted by this control.",
            "Remote branch/PR cleanup remains scripts/cleanup-merged-branches.sh "
            "(MERGED/abandoned evidence + preserve policy).",
        ],
        "generatedAt": utc_now(),
    }


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    sub = ap.add_subparsers(dest="cmd", required=True)

    sh = sub.add_parser("show-preserve", help="Print active preserve policy")
    sh.add_argument("--policy", default="", help="Override preserve JSON path")

    ck = sub.add_parser("check-branch", help="Classify one branch against preserve + evidence")
    ck.add_argument("--branch", required=True)
    ck.add_argument(
        "--evidence",
        default="NONE",
        choices=["OPEN", "MERGED", "ABANDONED", "NONE"],
    )
    ck.add_argument("--pr", type=int, default=0)
    ck.add_argument("--policy", default="")

    pl = sub.add_parser(
        "plan-completed-repairs",
        help="Dry-run (default) or apply file-backend completed repair cleanup",
    )
    pl.add_argument(
        "--repair-dir",
        default="",
        help="File-backend root (default: LINKTREND_REPAIR_DIR or .git/linktrend-repair-tasks)",
    )
    pl.add_argument(
        "--apply",
        action="store_true",
        help="Delete resolved file-backend JSON records only (never GitHub)",
    )

    args = ap.parse_args(argv)
    policy_path = Path(args.policy) if getattr(args, "policy", "") else None

    if args.cmd == "show-preserve":
        pol = load_preserve_policy(policy_path)
        print(
            json.dumps(
                {
                    "schemaVersion": pol["schemaVersion"],
                    "path": pol["path"],
                    "preserveIssueNumbers": pol["preserveIssueNumbers"],
                    "preservePrNumbers": pol["preservePrNumbers"],
                    "preserveBranchExact": pol["preserveBranchExact"],
                },
                indent=2,
            )
        )
        return 0

    if args.cmd == "check-branch":
        pol = load_preserve_policy(policy_path)
        pr = int(args.pr) if args.pr else None
        print(
            json.dumps(
                classify_branch_decision(
                    args.branch,
                    evidence=args.evidence,
                    pr_number=pr,
                    policy=pol,
                ),
                indent=2,
            )
        )
        return 0

    if args.cmd == "plan-completed-repairs":
        root = Path(
            args.repair_dir
            or os.environ.get("LINKTREND_REPAIR_DIR")
            or os.environ.get("LINKTREND_CONFLICT_DIR")
            or ".git/linktrend-repair-tasks"
        )
        plan = plan_completed_repair_cleanup(root, apply=bool(args.apply))
        print(json.dumps(plan, indent=2))
        return 0

    return 2


if __name__ == "__main__":
    raise SystemExit(main())
