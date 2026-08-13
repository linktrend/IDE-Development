#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
TMP="$(mktemp -d "${TMPDIR:-/tmp}/linktrend-w2-p3-profile.XXXXXX")"
trap 'rm -rf "$TMP"' EXIT

make_consumer() {
  local target="$1"
  mkdir -p "$target/.github"
  cat >"$target/.github/linktrend-gitops-consumer.json" <<'JSON'
{
  "schemaVersion": 1,
  "fastWorkflowName": "Consumer Fast",
  "ciWorkflowName": "Consumer CI",
  "branchPolicyWorkflowName": "Branch Source Policy",
  "bugbotCheckName": "Cursor Bugbot",
  "runnerType": "github-hosted"
}
JSON
}

local_repo="$TMP/local"
compat_repo="$TMP/compat"
make_consumer "$local_repo"
make_consumer "$compat_repo"

bash "$ROOT/scripts/sync-managed-workflows.sh" "$local_repo" \
  --orchestration-mode local-coordinator >/dev/null
bash "$ROOT/scripts/sync-managed-workflows.sh" "$compat_repo" \
  --orchestration-mode github-actions >/dev/null

for workflow in \
  linktrend-review-packager.yml \
  linktrend-integrator-merge.yml \
  linktrend-repair-observer.yml \
  linktrend-development-to-staging.yml \
  linktrend-staging-to-main.yml; do
  python3 - "$local_repo/.github/workflows/$workflow" <<'PY'
import re
import sys
from pathlib import Path

path = Path(sys.argv[1])
text = path.read_text(encoding="utf-8")
events = text.split("\non:\n", 1)[1].split("\npermissions:", 1)[0]
for event in ("schedule", "check_run", "workflow_run", "pull_request_target"):
    assert not re.search(rf"^  {event}:", events, re.M), f"{path.name}: {event} remained"
assert re.search(r"^  workflow_dispatch:", events, re.M), f"{path.name}: manual recovery missing"
assert "Orchestration profile: local-coordinator" in text
for context in (
    "Linktrend Fast Gate", "Linktrend Full Suite", "Linktrend Phase Ready",
    "Linktrend Staging Gate", "Linktrend Release Gate", "Linktrend Coordinator",
    "Cursor Bugbot",
):
    assert context in text, f"{path.name}: missing frozen context {context}"
PY
done

grep -q '^  schedule:' "$compat_repo/.github/workflows/linktrend-review-packager.yml"
grep -q '^  workflow_run:' "$compat_repo/.github/workflows/linktrend-integrator-merge.yml"
grep -q '^  check_run:' "$compat_repo/.github/workflows/linktrend-staging-to-main.yml"

if grep -R -n -iE 'create-github-app-token|LINKTREND_(APP|GITHUB_APP)|installation[_-]token' \
  "$local_repo/.github/workflows" "$compat_repo/.github/workflows"; then
  echo "FAIL: former custom-App dependency rendered into workflow profiles" >&2
  exit 1
fi

echo "PASS: local-coordinator is thin/manual and github-actions compatibility preserves wakes"
