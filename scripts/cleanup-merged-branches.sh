#!/usr/bin/env bash
# Safe cleanup for merged/abandoned work + promotion branches.
# Default: dry-run. Never deletes by name alone. Preserves caller checkout.
#
# Usage:
#   cleanup-merged-branches.sh [--apply] [--remote] [--local]
set -euo pipefail

APPLY=0
DO_REMOTE=1
DO_LOCAL=1
ROOT=""

while [ $# -gt 0 ]; do
  case "$1" in
    --apply) APPLY=1; shift ;;
    --remote) DO_REMOTE=1; DO_LOCAL=0; shift ;;
    --local) DO_LOCAL=1; DO_REMOTE=0; shift ;;
    --repo-root) ROOT="$2"; shift 2 ;;
    -h|--help) sed -n '1,20p' "$0"; exit 0 ;;
    *) echo "Unknown arg: $1" >&2; exit 2 ;;
  esac
done

if [ -z "$ROOT" ]; then
  ROOT="$(git rev-parse --show-toplevel 2>/dev/null)" || {
    echo "FAIL: not a git repository" >&2
    exit 1
  }
fi
cd "$ROOT"
# shellcheck source=gitops/work-branch-allowlist.sh
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/gitops/work-branch-allowlist.sh"

START_BRANCH="$(git rev-parse --abbrev-ref HEAD)"
START_SHA="$(git rev-parse HEAD)"
START_STATUS="$(git status --porcelain)"

MODE="dry-run"
[ "$APPLY" -eq 1 ] && MODE="apply"
echo "cleanup mode=${MODE} remote=${DO_REMOTE} local=${DO_LOCAL}"

is_protected_permanent() {
  case "$1" in
    main|staging|development|HEAD) return 0 ;;
    *) return 1 ;;
  esac
}

decide() { echo "$1: $2 — $3"; }

pr_evidence_for_branch() {
  # prints: MERGED|ABANDONED|NONE <headOid or empty>
  local branch="$1"
  local json
  json="$(gh pr list --head "$branch" --state all --json number,state,mergedAt,labels,headRefOid --limit 10 2>/dev/null || echo '[]')"
  python3 -c '
import json,sys
rows=json.load(sys.stdin)
for r in rows:
    if r.get("state")=="MERGED" or r.get("mergedAt"):
        print("MERGED", r.get("headRefOid") or "")
        raise SystemExit
for r in rows:
    labels=[(l.get("name") if isinstance(l,dict) else l) for l in (r.get("labels") or [])]
    if r.get("state")=="CLOSED" and "abandoned" in labels:
        print("ABANDONED", r.get("headRefOid") or "")
        raise SystemExit
print("NONE", "")
' <<<"$json"
}

branch_tip() {
  local branch="$1"
  if git show-ref --verify --quiet "refs/remotes/origin/${branch}"; then
    git rev-parse "refs/remotes/origin/${branch}"
  elif git show-ref --verify --quiet "refs/heads/${branch}"; then
    git rev-parse "refs/heads/${branch}"
  else
    echo ""
  fi
}

worktree_path_for() {
  local branch="$1"
  git worktree list --porcelain | python3 -c '
import sys
branch=sys.argv[1]
cur=None
for line in sys.stdin.read().splitlines():
    if line.startswith("worktree "):
        cur=line.split(" ",1)[1]
    elif line==f"branch refs/heads/{branch}":
        print(cur or ""); break
' "$branch"
}

# Optional session ownership via .linktrend/session-owners.json
# { "issue/foo": { "owner": "agent-1", "active": true } }
session_owns() {
  local branch="$1"
  local f=".linktrend/session-owners.json"
  [ -f "$f" ] || return 1
  python3 -c '
import json,sys
branch=sys.argv[1]
data=json.load(open(sys.argv[2]))
row=data.get(branch) or {}
sys.exit(0 if row.get("active") else 1)
' "$branch" "$f"
}

maybe_delete_remote() {
  local branch="$1"
  local evidence head_oid tip
  if is_protected_permanent "$branch"; then
    decide "KEEP" "$branch" "protected"
    return 0
  fi
  if ! is_allowed_work_branch "$branch" && ! is_staging_promote_branch "$branch" && ! is_main_promote_branch "$branch"; then
    decide "KEEP" "$branch" "not a cleanup candidate form"
    return 0
  fi
  read -r evidence head_oid <<<"$(pr_evidence_for_branch "$branch")"
  if [ "$evidence" = "NONE" ]; then
    decide "KEEP" "$branch" "no merged/abandoned PR evidence"
    return 0
  fi
  tip="$(branch_tip "$branch")"
  if [ -n "$head_oid" ] && [ -n "$tip" ] && [ "$head_oid" != "$tip" ]; then
    decide "KEEP" "$branch" "PR head ${head_oid} != branch tip ${tip}"
    return 0
  fi
  if [ "$branch" = "$START_BRANCH" ]; then
    decide "KEEP" "$branch" "currently checked out by caller"
    return 0
  fi
  wt="$(worktree_path_for "$branch")"
  if [ -n "$wt" ]; then
    decide "KEEP" "$branch" "active worktree attached (${wt})"
    return 0
  fi
  if session_owns "$branch"; then
    decide "KEEP" "$branch" "active session ownership record"
    return 0
  fi
  if [ "$APPLY" -eq 1 ]; then
    # Prefer non-force; force only with exact merged/abandoned evidence (already verified)
    if git push origin --delete "$branch"; then
      decide "DELETED_REMOTE" "$branch" "${evidence} evidence"
    else
      decide "KEEP" "$branch" "remote delete failed"
    fi
  else
    decide "WOULD_DELETE_REMOTE" "$branch" "${evidence} evidence"
  fi
}

maybe_delete_local() {
  local branch="$1"
  if is_protected_permanent "$branch"; then
    decide "KEEP" "local:$branch" "protected"
    return 0
  fi
  if ! is_allowed_work_branch "$branch" && ! is_staging_promote_branch "$branch" && ! is_main_promote_branch "$branch"; then
    decide "KEEP" "local:$branch" "not candidate"
    return 0
  fi
  if [ "$branch" = "$START_BRANCH" ]; then
    decide "KEEP" "local:$branch" "caller checkout"
    return 0
  fi
  wt="$(worktree_path_for "$branch")"
  if [ -n "$wt" ] && [ -n "$(git -C "$wt" status --porcelain 2>/dev/null || true)" ]; then
    decide "KEEP" "local:$branch" "dirty worktree"
    return 0
  fi
  if session_owns "$branch"; then
    decide "KEEP" "local:$branch" "active session ownership"
    return 0
  fi
  read -r evidence head_oid <<<"$(pr_evidence_for_branch "$branch")"
  if [ "$evidence" = "NONE" ]; then
    decide "KEEP" "local:$branch" "PR not merged/abandoned"
    return 0
  fi
  tip="$(git rev-parse "refs/heads/${branch}" 2>/dev/null || true)"
  if [ -n "$head_oid" ] && [ -n "$tip" ] && [ "$head_oid" != "$tip" ]; then
    decide "KEEP" "local:$branch" "exact-head mismatch"
    return 0
  fi
  if [ "$APPLY" -eq 1 ]; then
    if [ -n "$wt" ]; then
      git worktree remove "$wt" 2>/dev/null || {
        decide "KEEP" "local:$branch" "worktree remove refused without force"
        return 0
      }
    fi
    if git branch -d "$branch" 2>/dev/null; then
      decide "DELETED_LOCAL" "$branch" "${evidence}"
    else
      # force only after exact merged evidence
      git branch -D "$branch"
      decide "DELETED_LOCAL_FORCE" "$branch" "${evidence} after exact evidence"
    fi
  else
    decide "WOULD_DELETE_LOCAL" "$branch" "${evidence}"
  fi
}

if [ "$DO_REMOTE" -eq 1 ]; then
  git fetch origin --prune >/dev/null 2>&1 || true
  while IFS= read -r ref || [ -n "$ref" ]; do
    [ -z "$ref" ] && continue
    branch="${ref#refs/heads/}"
    maybe_delete_remote "$branch"
  done < <(git for-each-ref --format='%(refname)' refs/remotes/origin | sed 's#refs/remotes/origin/#refs/heads/#' | grep -v 'refs/heads/HEAD' || true)
fi

if [ "$DO_LOCAL" -eq 1 ]; then
  while IFS= read -r branch || [ -n "$branch" ]; do
    [ -z "$branch" ] && continue
    maybe_delete_local "$branch"
  done < <(git for-each-ref --format='%(refname:short)' refs/heads)
fi

END_BRANCH="$(git rev-parse --abbrev-ref HEAD)"
END_SHA="$(git rev-parse HEAD)"
END_STATUS="$(git status --porcelain)"
if [ "$START_BRANCH" != "$END_BRANCH" ] || [ "$START_SHA" != "$END_SHA" ] || [ "$START_STATUS" != "$END_STATUS" ]; then
  echo "FAIL: caller checkout changed during cleanup" >&2
  exit 1
fi
echo "CLEANUP_CALLER_UNCHANGED=1"
