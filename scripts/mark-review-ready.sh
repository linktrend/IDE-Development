#!/usr/bin/env bash
# Publish Linktrend Review Ready commit status for the current branch tip.
# Does not modify the feature diff. Does not open a PR. Does not request Bugbot.
set -euo pipefail

ROOT="$(git rev-parse --show-toplevel 2>/dev/null)" || {
  echo "FAIL: not a git repository" >&2
  exit 1
}
cd "$ROOT"
# shellcheck source=gitops/work-branch-allowlist.sh
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/gitops/work-branch-allowlist.sh"

ISSUE_ID="${1:-}"
NOTES="${2:-}"
BRANCH="$(git rev-parse --abbrev-ref HEAD)"
SHA="$(git rev-parse HEAD)"

case "$BRANCH" in
  development|staging|main|HEAD)
    echo "FAIL: refuse to mark review_ready on protected/detached ref $BRANCH" >&2
    exit 1
    ;;
esac

if ! is_allowed_work_branch "$BRANCH"; then
  echo "FAIL: branch '$BRANCH' is not an allowed work-branch form" >&2
  exit 1
fi

if [ -n "$(git status --porcelain)" ]; then
  echo "FAIL: working tree must be fully clean before marking review-ready" >&2
  git status --porcelain >&2 || true
  exit 1
fi

# Local HEAD must equal remote branch tip (when remote tracking exists / origin present)
if git rev-parse --verify "refs/remotes/origin/${BRANCH}" >/dev/null 2>&1; then
  REMOTE="$(git rev-parse "refs/remotes/origin/${BRANCH}")"
  if [ "$SHA" != "$REMOTE" ]; then
    echo "FAIL: local HEAD ($SHA) != origin/${BRANCH} ($REMOTE). Push first." >&2
    exit 1
  fi
elif git remote get-url origin >/dev/null 2>&1; then
  echo "FAIL: origin/${BRANCH} missing — push the branch before marking review-ready" >&2
  exit 1
fi
# File backend tests may have no origin; allowed when LINKTREND_STATUS_BACKEND=file

if [ -z "$ISSUE_ID" ]; then
  if [[ "$BRANCH" =~ ^issue/([A-Za-z0-9._-]+)- ]]; then
    ISSUE_ID="${BASH_REMATCH[1]}"
  elif [[ "$BRANCH" =~ ^cursor/ ]]; then
    ISSUE_ID="cursor"
  else
    echo "FAIL: provide issue id: $0 <issue-id> [notes]" >&2
    exit 1
  fi
fi

python3 "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/gitops/readiness_status.py" mark "$SHA" "$ISSUE_ID" "$NOTES"
echo "PASS: Linktrend Review Ready status published for ${SHA}"
echo "Next: push is already required; Review Packager will open a draft PR (no Bugbot until fast-gate)."
