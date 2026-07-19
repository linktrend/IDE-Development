#!/usr/bin/env bash
# CI / operator equivalent of .githooks/pre-push pipeline-state consistency checks.
# Validates every tracked PIPELINE-STATE.json with --check-consistency.
# Exit 0 when none are tracked or all pass; non-zero on first failure.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

VALIDATOR=""
for candidate in \
  "$ROOT/core/runtime/validate-application-pipeline.mjs" \
  "$ROOT/.cursor/runtime/validate-application-pipeline.mjs"
do
  if [[ -f "$candidate" ]]; then
    VALIDATOR="$candidate"
    break
  fi
done

STATE_LIST="$(git ls-files | grep -E '(^|/)PIPELINE-STATE\.json$' || true)"

if [[ -z "$STATE_LIST" ]]; then
  echo "PASS: no tracked PIPELINE-STATE.json files"
  exit 0
fi

if [[ -z "$VALIDATOR" ]]; then
  echo "FAIL: PIPELINE-STATE.json is tracked but no application-pipeline validator" >&2
  echo "  expected core/runtime/validate-application-pipeline.mjs or .cursor/runtime/validate-application-pipeline.mjs" >&2
  exit 1
fi

FAILED=0
while IFS= read -r rel; do
  [[ -z "$rel" ]] && continue
  if [[ ! -f "$ROOT/$rel" ]]; then
    continue
  fi
  if ! node "$VALIDATOR" --state "$ROOT/$rel" --check-consistency; then
    echo "FAIL: invalid pipeline state in $rel" >&2
    FAILED=1
  fi
done <<< "$STATE_LIST"

if [[ "$FAILED" -ne 0 ]]; then
  exit 1
fi

echo "PASS: all tracked PIPELINE-STATE.json files are consistent"
exit 0
