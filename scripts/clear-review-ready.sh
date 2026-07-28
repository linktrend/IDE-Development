#!/usr/bin/env bash
# Withdraw review-ready status for the current tip (or given SHA).
set -euo pipefail

ROOT="$(git rev-parse --show-toplevel 2>/dev/null)" || {
  echo "FAIL: not a git repository" >&2
  exit 1
}
cd "$ROOT"
SHA="${1:-$(git rev-parse HEAD)}"
REASON="${2:-withdrawn}"
python3 "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/gitops/readiness_status.py" withdraw "$SHA" "$REASON"
echo "PASS: withdrew Linktrend Review Ready for ${SHA}"
