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
    "fastWorkflowName": "Consumer Fast",
    "ciWorkflowName": "Consumer CI",
    "branchPolicyWorkflowName": "Branch Source Policy",
    "bugbotCheckName": "Cursor Bugbot",
    "runnerType": sys.argv[2],
}, indent=2) + "\n", encoding="utf-8")
PY
}

hosted="$TMP/hosted"
make_consumer "$hosted" github-hosted

bash "$ROOT/scripts/sync-managed-workflows.sh" "$hosted" >/dev/null

python3 - "$hosted/.github/workflows" <<'PY'
import re
import sys
from pathlib import Path

unpinned = []
for root_arg in sys.argv[1:]:
    for workflow in sorted(Path(root_arg).glob("*.yml")):
        for line_number, line in enumerate(workflow.read_text(encoding="utf-8").splitlines(), 1):
            match = re.search(r"\buses:\s+([^./\s][^@\s]*)@([^\s#]+)", line)
            if match and not re.fullmatch(r"[0-9a-f]{40}", match.group(2)):
                unpinned.append(f"{workflow.name}:{line_number}: {match.group(0)}")
if unpinned:
    raise SystemExit("FAIL: unpinned external actions:\n" + "\n".join(unpinned))
PY

if grep -R -q '__LINKTREND_.*RUNS_ON__' "$hosted/.github/workflows"; then
  echo "FAIL: runner placeholder remained after render" >&2
  exit 1
fi

hosted_count="$(grep -R -h -c 'runs-on: ubuntu-24.04-arm' "$hosted/.github/workflows" | awk '{s += $1} END {print s + 0}')"
[ "$hosted_count" -gt 0 ] || { echo "FAIL: expected hosted ARM64 jobs, got $hosted_count" >&2; exit 1; }
if grep -R -E -q 'self-hosted|macOS|linktrend-privileged|linktrend-ci-isolated|ubuntu-latest' "$hosted/.github/workflows"; then
  echo "FAIL: legacy/private runner profile remained" >&2
  exit 1
fi

make_consumer "$TMP/bad" arbitrary-runner
if bash "$ROOT/scripts/sync-managed-workflows.sh" "$TMP/bad" >"$TMP/bad.out" 2>&1; then
  echo "FAIL: unsupported runnerType was accepted" >&2
  exit 1
fi
grep -q 'unsupported consumer config runnerType' "$TMP/bad.out"

make_consumer "$TMP/private" linktrend-private-macos-arm64
if bash "$ROOT/scripts/sync-managed-workflows.sh" "$TMP/private" >"$TMP/private.out" 2>&1; then
  echo "FAIL: retired private runner profile was accepted" >&2
  exit 1
fi
grep -q 'unsupported consumer config runnerType' "$TMP/private.out"

echo "PASS: managed runner routing is explicit, deterministic, and fail closed"
