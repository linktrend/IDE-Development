#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
TMP="$(mktemp -d "${TMPDIR:-/tmp}/managed-runner-routing.XXXXXX")"
cleanup() { rm -rf "$TMP"; }
trap cleanup EXIT

make_consumer() {
  local target="$1"
  local runner_type="$2"
  mkdir -p "$target/.github"
  python3 - "$target/.github/linktrend-gitops-consumer.json" "$runner_type" <<'PY'
import json
import sys
from pathlib import Path

Path(sys.argv[1]).write_text(json.dumps({
    "schemaVersion": 1,
    "ciWorkflowName": "Consumer CI",
    "branchPolicyWorkflowName": "Branch Source Policy",
    "bugbotCheckName": "Cursor Bugbot",
    "runnerType": sys.argv[2],
}, indent=2) + "\n", encoding="utf-8")
PY
}

hosted="$TMP/hosted"
private="$TMP/private"
make_consumer "$hosted" github-hosted
make_consumer "$private" linktrend-private-macos-arm64

bash "$ROOT/scripts/sync-managed-workflows.sh" "$hosted" >/dev/null
bash "$ROOT/scripts/sync-managed-workflows.sh" "$private" >/dev/null

if grep -R -q '__LINKTREND_RUNS_ON__' "$hosted/.github/workflows" "$private/.github/workflows"; then
  echo "FAIL: runner placeholder remained after render" >&2
  exit 1
fi

hosted_count="$(grep -R -h -c 'runs-on: ubuntu-latest' "$hosted/.github/workflows" | awk '{s += $1} END {print s + 0}')"
private_count="$(grep -R -h -c 'runs-on: \[self-hosted, macOS, ARM64, linktrend-privileged\]' "$private/.github/workflows" | awk '{s += $1} END {print s + 0}')"
[ "$hosted_count" -eq 14 ] || { echo "FAIL: expected 14 hosted jobs, got $hosted_count" >&2; exit 1; }
[ "$private_count" -eq 14 ] || { echo "FAIL: expected 14 private jobs, got $private_count" >&2; exit 1; }

make_consumer "$TMP/bad" arbitrary-runner
if bash "$ROOT/scripts/sync-managed-workflows.sh" "$TMP/bad" >"$TMP/bad.out" 2>&1; then
  echo "FAIL: unsupported runnerType was accepted" >&2
  exit 1
fi
grep -q 'unsupported consumer config runnerType' "$TMP/bad.out"

echo "PASS: managed runner routing is explicit, deterministic, and fail closed"
