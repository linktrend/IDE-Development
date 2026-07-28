#!/usr/bin/env bash
# Clear local review-ready marker after merge or intentional withdrawal.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
MARKER="${ROOT}/.linktrend/review-ready.json"

if [[ -f "${MARKER}" ]]; then
  rm -f "${MARKER}"
  echo "Cleared ${MARKER}"
else
  echo "No review-ready marker present."
fi
