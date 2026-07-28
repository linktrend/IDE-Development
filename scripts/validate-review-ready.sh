#!/usr/bin/env bash
# Validate .linktrend/review-ready.json (contentSha + marker-commit design).
set -euo pipefail

ROOT="$(git rev-parse --show-toplevel 2>/dev/null)" || {
  echo "FAIL: not a git repository" >&2
  exit 1
}
RECORD_PATH="${1-}"
if [ -n "$RECORD_PATH" ]; then
  exec python3 "${ROOT}/scripts/gitops/validate_review_ready.py" "$ROOT" "$RECORD_PATH"
fi
exec python3 "${ROOT}/scripts/gitops/validate_review_ready.py" "$ROOT"
