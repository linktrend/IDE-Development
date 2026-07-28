#!/usr/bin/env bash
# Write .linktrend/review-ready.json for the current HEAD (idempotent rewrite).
# Does not open a PR. Does not request Bugbot.
set -euo pipefail

ROOT="$(git rev-parse --show-toplevel 2>/dev/null)" || {
  echo "FAIL: not a git repository" >&2
  exit 1
}
cd "$ROOT"

ISSUE_ID="${1:-}"
NOTES="${2:-}"
BRANCH="$(git rev-parse --abbrev-ref HEAD)"
HEAD="$(git rev-parse HEAD)"

case "$BRANCH" in
  development|staging|main)
    echo "FAIL: refuse to mark review_ready on protected branch $BRANCH" >&2
    exit 1
    ;;
esac

if [ -z "$ISSUE_ID" ]; then
  # Derive from issue/<id>-slug when possible
  if [[ "$BRANCH" =~ ^issue/([A-Za-z0-9._-]+)- ]]; then
    ISSUE_ID="${BASH_REMATCH[1]}"
  else
    echo "FAIL: provide issue id: $0 <issue-id> [notes]" >&2
    exit 1
  fi
fi

mkdir -p .linktrend
RECORDED_AT="$(date -u +"%Y-%m-%dT%H:%M:%SZ")"
python3 - "$ISSUE_ID" "$BRANCH" "$HEAD" "$RECORDED_AT" "$NOTES" <<'PY'
import json, sys
from pathlib import Path
issue_id, branch, sha, recorded_at, notes = sys.argv[1:6]
payload = {
  "schemaVersion": 1,
  "issueId": issue_id,
  "branch": branch,
  "commitSha": sha,
  "recordedAt": recorded_at,
  "deterministicGate": "pass",
  "notes": notes or "",
}
Path(".linktrend/review-ready.json").write_text(json.dumps(payload, indent=2) + "\n")
print(f"Wrote .linktrend/review-ready.json for {sha}")
PY

echo "Next: commit this file on the task branch, then push. Do not open a PR until Review Packager (or urgent dispatch)."
