#!/usr/bin/env bash
# Safe cleanup helper for merged/abandoned work branches and local worktrees.
# Default: dry-run. Never deletes by name alone. Never touches protected branches.
#
# Usage:
#   cleanup-merged-branches.sh [--apply] [--remote] [--local] [--repo-root PATH]
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
    -h|--help)
      sed -n '1,20p' "$0"
      exit 0
      ;;
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

MODE="dry-run"
[ "$APPLY" -eq 1 ] && MODE="apply"
echo "cleanup mode=${MODE} remote=${DO_REMOTE} local=${DO_LOCAL}"

is_protected() {
  case "$1" in
    main|staging|development|HEAD) return 0 ;;
    promote/staging/*|promote/main/*) return 0 ;; # keep until explicitly GC'd after merge
    *) return 1 ;;
  esac
}

current_branch="$(git rev-parse --abbrev-ref HEAD)"

decision_log=()
decide() {
  decision_log+=("$1|$2|$3")
  echo "$1: $2 — $3"
}

# --- Remote branches with merged PRs ---
if [ "$DO_REMOTE" -eq 1 ]; then
  git fetch origin --prune >/dev/null 2>&1 || true
  # List remote heads under allowlist
  while IFS= read -r ref || [ -n "$ref" ]; do
    [ -z "$ref" ] && continue
    branch="${ref#refs/heads/}"
    if is_protected "$branch"; then
      decide "KEEP" "$branch" "protected"
      continue
    fi
    if ! is_allowed_work_branch "$branch" && ! is_staging_promote_branch "$branch" && ! is_main_promote_branch "$branch"; then
      decide "KEEP" "$branch" "not an allowed cleanup candidate form"
      continue
    fi
    # Must have a PR that is MERGED or explicitly closed as abandoned with label
    pr_json="$(gh pr list --head "$branch" --state all --json number,state,mergedAt,labels --limit 5 2>/dev/null || echo '[]')"
    merged="$(echo "$pr_json" | python3 -c 'import json,sys; rows=json.load(sys.stdin); print("yes" if any(r.get("state")=="MERGED" or r.get("mergedAt") for r in rows) else "no")')"
    abandoned="$(echo "$pr_json" | python3 -c 'import json,sys; rows=json.load(sys.stdin); print("yes" if any(r.get("state")=="CLOSED" and any((l.get("name") if isinstance(l,dict) else l)=="abandoned" for l in (r.get("labels") or [])) for r in rows) else "no")')"
    if [ "$merged" != "yes" ] && [ "$abandoned" != "yes" ]; then
      decide "KEEP" "$branch" "no merged or abandoned PR confirmation"
      continue
    fi
    # Ancestry: tip should be ancestor of development (for work branches) when merged
    if is_allowed_work_branch "$branch"; then
      if ! git merge-base --is-ancestor "origin/${branch}" origin/development 2>/dev/null; then
        decide "KEEP" "$branch" "tip not ancestor of origin/development"
        continue
      fi
    fi
    if [ "$branch" = "$current_branch" ]; then
      decide "KEEP" "$branch" "currently checked out"
      continue
    fi
    # Active worktree ownership
    if git worktree list --porcelain | grep -q "branch refs/heads/${branch}$"; then
      decide "KEEP" "$branch" "local worktree still attached"
      continue
    fi
    if [ "$APPLY" -eq 1 ]; then
      git push origin --delete "$branch"
      decide "DELETED_REMOTE" "$branch" "merged/abandoned and safe"
    else
      decide "WOULD_DELETE_REMOTE" "$branch" "merged/abandoned and safe"
    fi
  done < <(git for-each-ref --format='%(refname)' refs/remotes/origin | sed 's#refs/remotes/origin/#refs/heads/#' | grep -v 'refs/heads/HEAD' || true)
fi

# --- Local worktrees / branches ---
if [ "$DO_LOCAL" -eq 1 ]; then
  while IFS= read -r branch || [ -n "$branch" ]; do
    [ -z "$branch" ] && continue
    if is_protected "$branch"; then
      decide "KEEP" "local:$branch" "protected"
      continue
    fi
    if ! is_allowed_work_branch "$branch"; then
      decide "KEEP" "local:$branch" "not allowed work-branch form"
      continue
    fi
    if [ "$branch" = "$current_branch" ]; then
      decide "KEEP" "local:$branch" "currently checked out"
      continue
    fi
    # Dirty worktree?
    wt_path="$(git worktree list --porcelain | python3 -c '
import sys
branch="'"$branch"'"
lines=sys.stdin.read().splitlines()
path=None
for i,l in enumerate(lines):
    if l.startswith("worktree "):
        path=l.split(" ",1)[1]
    if l==f"branch refs/heads/{branch}" and path:
        print(path)
        break
')"
    if [ -n "$wt_path" ] && [ -d "$wt_path" ]; then
      if [ -n "$(git -C "$wt_path" status --porcelain 2>/dev/null || true)" ]; then
        decide "KEEP" "local:$branch" "dirty worktree"
        continue
      fi
    fi
    pr_state="$(gh pr list --head "$branch" --state all --json state,mergedAt --limit 1 2>/dev/null || echo '[]')"
    merged="$(echo "$pr_state" | python3 -c 'import json,sys; rows=json.load(sys.stdin); print("yes" if rows and (rows[0].get("state")=="MERGED" or rows[0].get("mergedAt")) else "no")')"
    if [ "$merged" != "yes" ]; then
      decide "KEEP" "local:$branch" "PR not confirmed merged"
      continue
    fi
    if [ "$APPLY" -eq 1 ]; then
      if [ -n "$wt_path" ]; then
        git worktree remove --force "$wt_path" 2>/dev/null || true
      fi
      git branch -D "$branch" 2>/dev/null || true
      decide "DELETED_LOCAL" "$branch" "merged and safe"
    else
      decide "WOULD_DELETE_LOCAL" "$branch" "merged and safe"
    fi
  done < <(git for-each-ref --format='%(refname:short)' refs/heads)
fi

echo "cleanup decisions: ${#decision_log[@]}"
