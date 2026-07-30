#!/usr/bin/env python3
"""Discover Main Approve packages for Lisa (authoritative GitHub PR store).

Store = open same-repo promote/main/<12-char> → main PRs with:
  <!-- linktrend-promote: {schemaVersion:1, stage:main, ...} -->

Produces a Lisa-compatible MainApprovePackage:
  packageId, mondayDate, claimExpiresAt, createdAt, items[]

Live mode queries GitHub for PRs, remote tips, and release-gate checks.
Fixture mode accepts explicit tips/checks for hermetic tests.

Never prints credentials. No OpenClaw sidecars.
Contract: docs/contracts/LISA-MAIN-APPROVE-DISPATCH.md
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from packager_logic import fast_gate_status, parse_required_checks  # noqa: E402

MARKER_RE = re.compile(r"<!--\s*linktrend-promote:\s*(\{.*?\})\s*-->", re.S)
SHA40_RE = re.compile(r"^[0-9a-f]{40}$")
PROMOTE_BRANCH_RE = re.compile(r"^promote/main/([0-9a-f]{12})$")
CONTRACT = "docs/contracts/LISA-MAIN-APPROVE-DISPATCH.md"
STORE = "github_promote_pr_marker"
TZ = ZoneInfo("Asia/Taipei")
DEFAULT_RELEASE_GATE_CHECKS = "Verify IDE Development,Enforce allowed PR source branches"


def emit(payload: dict[str, Any]) -> None:
    print(json.dumps(payload, indent=2, sort_keys=False))


def run_gh(args: list[str]) -> str:
    env = os.environ.copy()
    return subprocess.check_output(["gh", *args], text=True, env=env).strip()


def normalize_sha(value: Any) -> str | None:
    s = str(value or "").strip().lower()
    if SHA40_RE.match(s):
        return s
    return None


def parse_marker(body: str) -> tuple[dict[str, Any] | None, str]:
    m = MARKER_RE.search(body or "")
    if not m:
        return None, "marker_missing"
    try:
        meta = json.loads(m.group(1))
    except json.JSONDecodeError:
        return None, "marker_json_invalid"
    if not isinstance(meta, dict):
        return None, "marker_not_object"
    try:
        if int(meta.get("schemaVersion") or 0) != 1:
            return None, "marker_schema_unsupported"
    except (TypeError, ValueError):
        return None, "marker_schema_unsupported"
    if meta.get("stage") != "main":
        return None, "marker_stage_not_main"
    if meta.get("sourceBranch") != "staging":
        return None, "marker_source_branch_not_staging"
    if meta.get("targetBranch") != "main":
        return None, "marker_target_branch_not_main"
    source = normalize_sha(meta.get("sourceSha"))
    target = normalize_sha(meta.get("targetSha"))
    candidate = normalize_sha(meta.get("candidateHead"))
    if not source:
        return None, "marker_source_sha_invalid"
    if not target:
        return None, "marker_target_sha_invalid"
    if not candidate:
        return None, "marker_candidate_sha_invalid"
    branch = str(meta.get("promoteBranch") or "").strip()
    bm = PROMOTE_BRANCH_RE.match(branch)
    if not bm:
        return None, "marker_promote_branch_invalid"
    if bm.group(1) != source[:12]:
        return None, "marker_promote_branch_prefix_mismatch"
    meta = {
        **meta,
        "schemaVersion": 1,
        "stage": "main",
        "sourceBranch": "staging",
        "targetBranch": "main",
        "sourceSha": source,
        "targetSha": target,
        "candidateHead": candidate,
        "promoteBranch": branch,
    }
    return meta, ""


def plain_description(repository: str) -> str:
    # Carlos-facing: no SHAs / no hex tip fragments.
    _ = repository
    return "staging to main promote package"


def asia_taipei_monday(now: datetime) -> datetime:
    local = now.astimezone(TZ)
    monday = local - timedelta(days=local.weekday())  # Monday=0
    return monday.replace(hour=0, minute=0, second=0, microsecond=0)


def claim_expires_at(monday: datetime) -> str:
    """Expiry policy: end of that Monday (Asia/Taipei 23:59:59)."""
    end = monday.replace(hour=23, minute=59, second=59, microsecond=0)
    return end.isoformat()


def package_id(monday_date: str, items: list[dict[str, Any]]) -> str:
    material = []
    for it in items:
        material.append(
            f"{it['repository']}|{it['promotionPrNumber']}|{it['stagingSha']}|"
            f"{it['priorMainSha']}|{it['promotionHeadSha']}|{it['gateResult']}"
        )
    digest = hashlib.sha256("\n".join(material).encode("utf-8")).hexdigest()[:16]
    return f"main-approve-{monday_date}-{digest}"


def resolve_release_gate_checks(
    repo: str, override: str | None = None, *, fixture: bool = False
) -> list[str]:
    if override and override.strip():
        return parse_required_checks(override)
    env = (
        os.environ.get("LINKTREND_RELEASE_GATE_CHECKS")
        or os.environ.get("RELEASE_GATE_CHECKS")
        or ""
    ).strip()
    if env:
        return parse_required_checks(env)
    if fixture:
        return parse_required_checks(DEFAULT_RELEASE_GATE_CHECKS)
    # Live: read Actions variable when present
    try:
        raw = run_gh(
            [
                "api",
                f"repos/{repo}/actions/variables/LINKTREND_RELEASE_GATE_CHECKS",
                "--jq",
                ".value",
            ]
        )
        if raw.strip():
            return parse_required_checks(raw)
    except subprocess.CalledProcessError:
        pass
    return parse_required_checks(DEFAULT_RELEASE_GATE_CHECKS)


def remote_tip(repo: str, branch: str) -> str | None:
    try:
        sha = run_gh(
            [
                "api",
                f"repos/{repo}/git/ref/heads/{branch}",
                "--jq",
                ".object.sha",
            ]
        )
        return normalize_sha(sha)
    except subprocess.CalledProcessError:
        return None


def live_pr_checks(repo: str, pr_number: int) -> list[dict[str, Any]]:
    raw = run_gh(
        [
            "pr",
            "checks",
            str(pr_number),
            "--repo",
            repo,
            "--json",
            "name,state,bucket,completedAt,startedAt",
        ]
    )
    return json.loads(raw or "[]")


def evaluate_gates(
    *,
    required: list[str],
    checks: list[dict[str, Any]],
) -> tuple[str, dict[str, Any]]:
    status, detail = fast_gate_status(checks, required)
    by_name = {str(c.get("name") or ""): c for c in checks}
    evidence = {
        "requiredChecks": required,
        "status": status,
        "detail": detail,
        "checks": [
            {
                "name": name,
                "state": str((by_name.get(name) or {}).get("state") or "MISSING"),
                "present": name in by_name,
            }
            for name in required
        ],
    }
    if status == "success":
        return "Clear", evidence
    # missing/pending/failed/neutral/cancelled → Issues (never Unknown for usable items)
    return "Issues", evidence


def validate_candidate(
    *,
    repository: str,
    pr: dict[str, Any],
    staging_tip: str | None,
    main_tip: str | None,
    required_checks: list[str],
    checks: list[dict[str, Any]] | None,
    now: datetime,
    fixture: bool,
) -> tuple[dict[str, Any] | None, dict[str, Any] | None]:
    """Return (item, rejection). Exactly one is non-None."""
    pr_number = int(pr.get("number") or 0)
    body = str(pr.get("body") or "")
    head_branch = str(pr.get("headRefName") or "")
    head_sha = normalize_sha(pr.get("headRefOid"))
    base = str(pr.get("baseRefName") or "")
    state = str(pr.get("state") or "").upper()
    is_cross = bool(pr.get("isCrossRepository"))
    head_repo = ""
    head_repo_obj = pr.get("headRepository")
    if isinstance(head_repo_obj, dict):
        owner = (head_repo_obj.get("owner") or {})
        if isinstance(owner, dict):
            head_repo = f"{owner.get('login')}/{head_repo_obj.get('name')}"
        else:
            head_repo = str(head_repo_obj.get("nameWithOwner") or "")
    if not head_repo:
        head_repo = str(pr.get("headRepositoryNameWithOwner") or "")

    def reject(reason: str, **extra: Any) -> tuple[None, dict[str, Any]]:
        return None, {
            "repository": repository,
            "promotionPrNumber": pr_number or None,
            "reason": reason,
            "requiresRepackage": True,
            **extra,
        }

    if state and state not in {"OPEN", ""}:
        return reject("pr_not_open", state=state)
    if base and base != "main":
        return reject("base_not_main", base=base)
    if is_cross:
        return reject("cross_repository_head")
    if head_repo and head_repo.lower() != repository.lower():
        return reject("head_repository_mismatch", headRepository=head_repo)

    bm = PROMOTE_BRANCH_RE.match(head_branch)
    if not bm:
        return reject("head_branch_invalid", headBranch=head_branch)

    meta, mreason = parse_marker(body)
    if not meta:
        return reject(mreason or "marker_invalid")

    if meta["promoteBranch"] != head_branch:
        return reject(
            "promote_branch_mismatch",
            markerBranch=meta["promoteBranch"],
            headBranch=head_branch,
        )
    if bm.group(1) != meta["sourceSha"][:12]:
        return reject("head_branch_prefix_mismatch")

    if not head_sha:
        return reject("head_sha_invalid")
    if head_sha != meta["candidateHead"]:
        return reject(
            "candidate_head_drift",
            markerCandidate=meta["candidateHead"],
            liveHead=head_sha,
        )

    if staging_tip is None:
        return reject("staging_tip_unresolved")
    if main_tip is None:
        return reject("main_tip_unresolved")
    if meta["sourceSha"] != staging_tip:
        return reject(
            "staging_tip_drift",
            markerSource=meta["sourceSha"],
            liveStaging=staging_tip,
        )
    if meta["targetSha"] != main_tip:
        return reject(
            "main_tip_drift",
            markerTarget=meta["targetSha"],
            liveMain=main_tip,
        )

    if checks is None:
        if fixture:
            return reject("fixture_checks_required")
        try:
            checks = live_pr_checks(repository, pr_number)
        except subprocess.CalledProcessError as exc:
            return reject("gate_query_failed", detail=str(exc))

    gate_result, gate_evidence = evaluate_gates(required=required_checks, checks=checks)
    if gate_result not in {"Clear", "Issues"}:
        return reject("gate_result_invalid", gateResult=gate_result)

    # Re-read sealed bindings for dispatch (freshness already proven).
    item = {
        "index": 0,  # filled later
        "plainDescription": plain_description(repository),
        "repository": repository,
        "promotionPrNumber": pr_number,
        "stagingSha": meta["sourceSha"],
        "priorMainSha": meta["targetSha"],
        "promotionHeadSha": meta["candidateHead"],
        "gateResult": gate_result,
        "promoteBranch": meta["promoteBranch"],
        "marker": meta,
        "gateEvidence": gate_evidence,
        "workflowInputs": {
            "action": "approve-merge",
            "expected_sha": meta["sourceSha"],
            "expected_main_sha": meta["targetSha"],
            "expected_promote_head": meta["candidateHead"],
            "promote_pr_number": str(pr_number),
        },
        "freshness": {
            "stagingTip": staging_tip,
            "mainTip": main_tip,
            "verifiedAt": now.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        },
    }
    return item, None


def build_package(
    *,
    repos: list[str],
    items: list[dict[str, Any]],
    rejected: list[dict[str, Any]],
    now: datetime,
    created_at: datetime | None = None,
) -> dict[str, Any]:
    monday = asia_taipei_monday(now)
    monday_date = monday.date().isoformat()
    expires = claim_expires_at(monday)
    created = (created_at or now).astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    for i, it in enumerate(items, start=1):
        it["index"] = i
    # Ambiguous: >1 valid item for same repository → reject all for that repo
    by_repo: dict[str, list[dict[str, Any]]] = {}
    for it in items:
        by_repo.setdefault(it["repository"], []).append(it)
    final_items: list[dict[str, Any]] = []
    for repo, group in by_repo.items():
        if len(group) > 1:
            rejected.append(
                {
                    "repository": repo,
                    "reason": "ambiguous_duplicate_packages",
                    "requiresRepackage": True,
                    "count": len(group),
                    "promotionPrNumbers": [g["promotionPrNumber"] for g in group],
                }
            )
            continue
        final_items.extend(group)
    for i, it in enumerate(final_items, start=1):
        it["index"] = i

    # Expiry policy: after mondayDate 23:59:59 Asia/Taipei, omit items (Lisa expired_claim).
    expired = now.astimezone(TZ) > datetime.fromisoformat(expires)
    if expired and final_items:
        for it in final_items:
            rejected.append(
                {
                    "repository": it["repository"],
                    "promotionPrNumber": it["promotionPrNumber"],
                    "reason": "package_expired",
                    "requiresRepackage": True,
                    "claimExpiresAt": expires,
                }
            )
        final_items = []

    pkg = {
        "packageId": package_id(monday_date, final_items) if final_items else f"main-approve-{monday_date}-empty",
        "mondayDate": monday_date,
        "claimExpiresAt": expires,
        "createdAt": created,
        "timezone": "Asia/Taipei",
        "expired": expired,
        "items": [
            {
                "index": it["index"],
                "plainDescription": it["plainDescription"],
                "repository": it["repository"],
                "promotionPrNumber": it["promotionPrNumber"],
                "stagingSha": it["stagingSha"],
                "priorMainSha": it["priorMainSha"],
                "promotionHeadSha": it["promotionHeadSha"],
                "gateResult": it["gateResult"],
            }
            for it in final_items
        ],
    }
    return {
        "schemaVersion": 1,
        "available": True,
        "store": STORE,
        "contract": CONTRACT,
        "repositories": repos,
        "package": pkg,
        "itemCount": len(final_items),
        "items": final_items,  # full rows incl. workflowInputs/gateEvidence for dispatch
        "rejected": rejected,
        "approveMergeTemplate": (
            "gh workflow run linktrend-staging-to-main.yml "
            "--repo <owner/repo> "
            "-f action=approve-merge "
            "-f expected_sha=<stagingSha> "
            "-f expected_main_sha=<priorMainSha> "
            "-f expected_promote_head=<promotionHeadSha>"
        ),
        "expiryPolicy": (
            "claimExpiresAt is 23:59:59 Asia/Taipei on mondayDate "
            "(same Monday Main Approve window). After that, Lisa must treat the "
            "claim as expired and re-discover/repackage."
        ),
        "notes": [
            "Authoritative store is GitHub promote PR metadata (marker), not OpenClaw sidecars.",
            "Carlos-facing text must omit SHAs; use plainDescription only.",
            "Usable items never have gateResult=Unknown; Clear requires all named release-gate checks SUCCESS.",
            "Stale tips/heads and fork/cross-repo PRs are rejected with requiresRepackage=true.",
        ],
    }


def reread_before_dispatch(
    *,
    repository: str,
    item: dict[str, Any],
    staging_tip: str | None,
    main_tip: str | None,
    now: datetime,
) -> tuple[dict[str, Any] | None, dict[str, Any] | None]:
    """Re-verify tips/head before sealing approve-merge inputs. Fail closed on drift."""
    pr_num = int(item["promotionPrNumber"])

    def reject(reason: str, **extra: Any) -> tuple[None, dict[str, Any]]:
        return None, {
            "repository": repository,
            "promotionPrNumber": pr_num,
            "reason": reason,
            "requiresRepackage": True,
            **extra,
        }

    try:
        live = json.loads(
            run_gh(
                [
                    "pr",
                    "view",
                    str(pr_num),
                    "--repo",
                    repository,
                    "--json",
                    "headRefOid,state,headRefName,baseRefName,isCrossRepository",
                ]
            )
        )
    except subprocess.CalledProcessError as exc:
        return reject("dispatch_reread_failed", detail=str(exc))

    if str(live.get("state") or "").upper() not in {"OPEN", ""}:
        return reject("pr_not_open_on_reread", state=live.get("state"))
    if bool(live.get("isCrossRepository")):
        return reject("cross_repository_head_on_reread")
    head = normalize_sha(live.get("headRefOid"))
    if staging_tip != item["stagingSha"]:
        return reject(
            "staging_tip_drift_on_reread",
            markerSource=item["stagingSha"],
            liveStaging=staging_tip,
        )
    if main_tip != item["priorMainSha"]:
        return reject(
            "main_tip_drift_on_reread",
            markerTarget=item["priorMainSha"],
            liveMain=main_tip,
        )
    if head != item["promotionHeadSha"]:
        return reject(
            "candidate_head_drift_on_reread",
            markerCandidate=item["promotionHeadSha"],
            liveHead=head,
        )
    item = {
        **item,
        "freshness": {
            "stagingTip": staging_tip,
            "mainTip": main_tip,
            "verifiedAt": now.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        },
        "workflowInputs": {
            "action": "approve-merge",
            "expected_sha": item["stagingSha"],
            "expected_main_sha": item["priorMainSha"],
            "expected_promote_head": item["promotionHeadSha"],
            "promote_pr_number": str(pr_num),
        },
    }
    return item, None


def list_open_promote_prs(repo: str) -> list[dict[str, Any]]:
    raw = run_gh(
        [
            "pr",
            "list",
            "--repo",
            repo,
            "--base",
            "main",
            "--state",
            "open",
            "--json",
            "number,title,body,headRefName,headRefOid,baseRefName,state,isCrossRepository,headRepository,url,createdAt",
            "--limit",
            "50",
        ]
    )
    rows = json.loads(raw or "[]")
    out = []
    for row in rows:
        head = str(row.get("headRefName") or "")
        if head.startswith("promote/main/"):
            out.append(row)
    return out


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--repo", action="append", dest="repos", default=[])
    ap.add_argument("--from-body-file", help="Fixture: PR body path")
    ap.add_argument("--repository", help="Fixture: owner/repo")
    ap.add_argument("--pr-number", type=int, default=0)
    ap.add_argument("--head-sha", default="")
    ap.add_argument("--head-branch", default="")
    ap.add_argument("--head-repository", default="", help="Fixture: head repo nameWithOwner")
    ap.add_argument("--is-cross-repository", action="store_true")
    ap.add_argument("--base-ref", default="main")
    ap.add_argument("--pr-state", default="OPEN")
    ap.add_argument("--staging-tip", default="", help="Fixture/live override remote staging tip")
    ap.add_argument("--main-tip", default="", help="Fixture/live override remote main tip")
    ap.add_argument("--checks-json", default="", help="Fixture: path to gh pr checks JSON array")
    ap.add_argument("--release-gate-checks", default="", help="Override release-gate check names")
    ap.add_argument("--now", default="", help="ISO timestamp for expiry/monday calculation")
    ap.add_argument("--created-at", default="", help="ISO package createdAt override")
    ap.add_argument(
        "--second-body-file",
        default="",
        help="Fixture: second PR body to simulate duplicate packages",
    )
    ap.add_argument("--second-pr-number", type=int, default=0)
    ap.add_argument("--second-head-sha", default="")
    args = ap.parse_args(argv)

    now = datetime.now(tz=TZ)
    if args.now:
        raw = args.now
        if raw.endswith("Z"):
            raw = raw[:-1] + "+00:00"
        now = datetime.fromisoformat(raw)
        if now.tzinfo is None:
            now = now.replace(tzinfo=TZ)
        else:
            now = now.astimezone(TZ)
    created_at = None
    if args.created_at:
        raw = args.created_at
        if raw.endswith("Z"):
            raw = raw[:-1] + "+00:00"
        created_at = datetime.fromisoformat(raw)
        if created_at.tzinfo is None:
            created_at = created_at.replace(tzinfo=timezone.utc)

    fixture = bool(args.from_body_file)

    def process_pr_dict(
        repo: str,
        pr: dict[str, Any],
        *,
        staging_tip: str | None,
        main_tip: str | None,
        checks: list[dict[str, Any]] | None,
    ) -> tuple[dict[str, Any] | None, dict[str, Any] | None]:
        required = resolve_release_gate_checks(
            repo, args.release_gate_checks or None, fixture=fixture
        )
        return validate_candidate(
            repository=repo,
            pr=pr,
            staging_tip=staging_tip,
            main_tip=main_tip,
            required_checks=required,
            checks=checks,
            now=now,
            fixture=fixture,
        )

    if fixture:
        repo = (args.repository or os.environ.get("GITHUB_REPOSITORY") or "owner/repo").strip()
        body = Path(args.from_body_file).read_text(encoding="utf-8")
        meta, mreason = parse_marker(body)
        if not meta and mreason:
            # still allow trust failures via other fields
            pass
        head_sha = normalize_sha(args.head_sha) or (meta or {}).get("candidateHead") or ""
        head_branch = args.head_branch or (meta or {}).get("promoteBranch") or ""
        staging_tip = normalize_sha(args.staging_tip) or (meta or {}).get("sourceSha")
        main_tip = normalize_sha(args.main_tip) or (meta or {}).get("targetSha")
        checks: list[dict[str, Any]] | None = None
        if args.checks_json:
            checks = json.loads(Path(args.checks_json).read_text(encoding="utf-8"))
        else:
            # Default fixture: all required checks SUCCESS when tips match
            required = resolve_release_gate_checks(
                repo, args.release_gate_checks or None, fixture=True
            )
            checks = [{"name": n, "state": "SUCCESS"} for n in required]

        pr = {
            "number": int(args.pr_number or 0),
            "body": body,
            "headRefName": head_branch,
            "headRefOid": head_sha,
            "baseRefName": args.base_ref,
            "state": args.pr_state,
            "isCrossRepository": bool(args.is_cross_repository),
            "headRepositoryNameWithOwner": args.head_repository or repo,
        }
        items: list[dict[str, Any]] = []
        rejected: list[dict[str, Any]] = []
        item, rej = process_pr_dict(repo, pr, staging_tip=staging_tip, main_tip=main_tip, checks=checks)
        if item:
            items.append(item)
        if rej:
            rejected.append(rej)

        if args.second_body_file:
            body2 = Path(args.second_body_file).read_text(encoding="utf-8")
            meta2, _ = parse_marker(body2)
            pr2 = {
                "number": int(args.second_pr_number or 100),
                "body": body2,
                "headRefName": (meta2 or {}).get("promoteBranch") or head_branch,
                "headRefOid": normalize_sha(args.second_head_sha)
                or (meta2 or {}).get("candidateHead")
                or head_sha,
                "baseRefName": "main",
                "state": "OPEN",
                "isCrossRepository": False,
                "headRepositoryNameWithOwner": repo,
            }
            item2, rej2 = process_pr_dict(
                repo, pr2, staging_tip=staging_tip, main_tip=main_tip, checks=checks
            )
            if item2:
                items.append(item2)
            if rej2:
                rejected.append(rej2)

        payload = build_package(
            repos=[repo], items=items, rejected=rejected, now=now, created_at=created_at
        )
        emit(payload)
        if payload["package"].get("expired"):
            return 3
        return 0 if payload["itemCount"] > 0 else 2

    # Live mode
    repos = list(args.repos)
    if not repos:
        env_repo = (os.environ.get("GITHUB_REPOSITORY") or os.environ.get("GH_REPO") or "").strip()
        if env_repo:
            repos = [env_repo]
        else:
            try:
                repos = [run_gh(["repo", "view", "--json", "nameWithOwner", "-q", ".nameWithOwner"])]
            except subprocess.CalledProcessError as exc:
                emit(
                    {
                        "schemaVersion": 1,
                        "available": False,
                        "store": STORE,
                        "contract": CONTRACT,
                        "error": f"repo_unresolved:{exc}",
                        "itemCount": 0,
                        "items": [],
                        "rejected": [],
                    }
                )
                return 1

    all_items: list[dict[str, Any]] = []
    all_rejected: list[dict[str, Any]] = []
    for repo in repos:
        try:
            staging_tip = normalize_sha(args.staging_tip) or remote_tip(repo, "staging")
            main_tip = normalize_sha(args.main_tip) or remote_tip(repo, "main")
            prs = list_open_promote_prs(repo)
        except subprocess.CalledProcessError as exc:
            emit(
                {
                    "schemaVersion": 1,
                    "available": False,
                    "store": STORE,
                    "contract": CONTRACT,
                    "error": f"gh_failed:{repo}:{exc}",
                    "itemCount": 0,
                    "items": [],
                    "rejected": [],
                }
            )
            return 1
        repo_items: list[dict[str, Any]] = []
        for pr in prs:
            # Enrich head repository if nested object missing nameWithOwner
            if isinstance(pr.get("headRepository"), dict) and not pr.get(
                "headRepositoryNameWithOwner"
            ):
                hr = pr["headRepository"]
                owner = hr.get("owner") if isinstance(hr.get("owner"), dict) else {}
                login = owner.get("login") if isinstance(owner, dict) else None
                name = hr.get("name")
                if login and name:
                    pr["headRepositoryNameWithOwner"] = f"{login}/{name}"
            item, rej = process_pr_dict(
                repo, pr, staging_tip=staging_tip, main_tip=main_tip, checks=None
            )
            if item:
                repo_items.append(item)
            if rej:
                all_rejected.append(rej)

        # Re-read tips/heads before sealing approval-dispatch inputs.
        live_stg = normalize_sha(args.staging_tip) or remote_tip(repo, "staging")
        live_main = normalize_sha(args.main_tip) or remote_tip(repo, "main")
        for it in repo_items:
            sealed, rej = reread_before_dispatch(
                repository=repo,
                item=it,
                staging_tip=live_stg,
                main_tip=live_main,
                now=now,
            )
            if sealed:
                all_items.append(sealed)
            if rej:
                all_rejected.append(rej)

    payload = build_package(
        repos=repos, items=all_items, rejected=all_rejected, now=now, created_at=created_at
    )
    emit(payload)
    if payload["package"].get("expired"):
        return 3
    return 0 if payload["itemCount"] > 0 else 2


if __name__ == "__main__":
    raise SystemExit(main())
