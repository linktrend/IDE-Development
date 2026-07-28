#!/usr/bin/env bash
# Write .linktrend/review-ready.json with contentSha = current HEAD (functional tip).
# Does not commit. Does not open a PR. Does not request Bugbot.
set -euo pipefail

ROOT="$(git rev-parse --show-toplevel 2>/dev/null)" || {
  echo "FAIL: not a git repository" >&2
  exit 1
}
cd "$ROOT"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=gitops/work-branch-allowlist.sh
source "${SCRIPT_DIR}/gitops/work-branch-allowlist.sh"

ISSUE_ID="${1:-}"
NOTES="${2:-}"
BRANCH="$(git rev-parse --abbrev-ref HEAD)"
CONTENT_SHA="$(git rev-parse HEAD)"

case "$BRANCH" in
  development|staging|main)
    echo "FAIL: refuse to mark review_ready on protected branch $BRANCH" >&2
    exit 1
    ;;
esac

if ! is_allowed_work_branch "$BRANCH"; then
  echo "FAIL: branch '$BRANCH' is not an allowed work-branch form" >&2
  exit 1
fi

if [ -n "$(git status --porcelain --untracked-files=no)" ]; then
  echo "FAIL: tracked working tree must be clean before marking review-ready (commit functional work first)" >&2
  git status --porcelain --untracked-files=no >&2 || true
  exit 1
fi

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

RECORDED_AT="$(date -u +"%Y-%m-%dT%H:%M:%SZ")"
python3 - "$ROOT" "$ISSUE_ID" "$BRANCH" "$CONTENT_SHA" "$RECORDED_AT" "$NOTES" <<'PY'
import sys
from pathlib import Path
sys.path.insert(0, str(Path(sys.argv[1]) / "scripts" / "gitops"))
from validate_review_ready import write_record
write_record(
    Path(sys.argv[1]),
    issue_id=sys.argv[2],
    branch=sys.argv[3],
    content_sha=sys.argv[4],
    recorded_at=sys.argv[5],
    notes=sys.argv[6],
)
print(f"Wrote .linktrend/review-ready.json contentSha={sys.argv[4]}")
PY

echo "Next: run scripts/commit-review-ready.sh to create the marker-only commit, then push."
echo "Do not amend the functional commit. The marker commit's parent must remain contentSha."
