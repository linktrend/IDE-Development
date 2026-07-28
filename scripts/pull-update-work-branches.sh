#!/usr/bin/env bash
# Pull/update unfinished work branches from origin/development.
# Skips frozen reviewed branches. Never force-pushes. Never discards dirty work.
#
# Usage:
#   pull-update-work-branches.sh [--branch NAME]...
set -euo pipefail

ROOT="$(git rev-parse --show-toplevel 2>/dev/null)" || {
  echo "FAIL: not a git repository" >&2
  exit 1
}
cd "$ROOT"
# shellcheck source=gitops/work-branch-allowlist.sh
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/gitops/work-branch-allowlist.sh"

ONLY_BRANCHES=()
while [ $# -gt 0 ]; do
  case "$1" in
    --branch) ONLY_BRANCHES+=("$2"); shift 2 ;;
    *) echo "Unknown arg: $1" >&2; exit 2 ;;
  esac
done

if git remote get-url origin >/dev/null 2>&1; then
  git fetch origin development
elif ! git show-ref --verify --quiet refs/remotes/origin/development; then
  echo "FAIL: no origin remote and no refs/remotes/origin/development" >&2
  exit 1
fi

is_frozen() {
  local branch="$1"
  python3 "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/gitops/detect_review_freeze.py" \
    --repo-root "$ROOT" \
    --branch "$branch"
}

update_branch() {
  local branch="$1"
  if ! is_allowed_work_branch "$branch"; then
    echo "SKIP $branch — not an allowed work branch"
    return 0
  fi
  if is_frozen "$branch"; then
    echo "SKIP $branch — review freeze active"
    return 0
  fi
  # Checkout local branch if exists
  if ! git show-ref --verify --quiet "refs/heads/${branch}"; then
    if git show-ref --verify --quiet "refs/remotes/origin/${branch}"; then
      git branch --track "$branch" "origin/${branch}" >/dev/null
    else
      echo "SKIP $branch — not found locally or on origin"
      return 0
    fi
  fi
  # Dirty?
  git checkout "$branch" >/dev/null
  if [ -n "$(git status --porcelain)" ]; then
    echo "SKIP $branch — dirty working tree (refusing to discard)"
    return 0
  fi
  if git merge-base --is-ancestor origin/development HEAD; then
    echo "OK $branch — already contains origin/development"
    return 0
  fi
  if git merge --no-edit origin/development; then
    echo "UPDATED $branch — merged origin/development"
  else
    git merge --abort 2>/dev/null || true
    echo "BLOCKED $branch — merge conflict with development (left unchanged)"
  fi
}

if [ "${#ONLY_BRANCHES[@]}" -gt 0 ]; then
  for b in "${ONLY_BRANCHES[@]}"; do
    update_branch "$b"
  done
else
  # Local work branches
  while IFS= read -r b || [ -n "$b" ]; do
    is_allowed_work_branch "$b" || continue
    update_branch "$b"
  done < <(git for-each-ref --format='%(refname:short)' refs/heads)
fi
