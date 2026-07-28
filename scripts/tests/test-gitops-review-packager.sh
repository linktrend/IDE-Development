#!/usr/bin/env bash
# Static GitOps invariants + trust-boundary proofs (companion to behavioral suite).
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"
fail() { echo "FAIL: $1" >&2; exit 1; }
pass() { echo "PASS: $1"; }

PKG="core/github/managed-workflows/linktrend-review-packager.yml"
STG="core/github/managed-workflows/linktrend-development-to-staging.yml"
MAIN="core/github/managed-workflows/linktrend-staging-to-main.yml"
INT="core/github/managed-workflows/linktrend-integrator-merge.yml"
CI=".github/workflows/ci.yml"

grep -q 'cron: "0 0 \* \* 2,5"' "$PKG" || fail "packager cron"
grep -q 'cron: "0 2 \* \* 2,5"' "$STG" || fail "staging cron"
grep -q 'packager_discover.py' "$PKG" || fail "discover phase missing"
grep -q 'packager_evaluate.py' "$PKG" || fail "evaluate phase missing"
grep -q 'workflow_run:' "$PKG" || fail "packager missing workflow_run wake"
grep -q 'workflows:' "$PKG" || fail "packager missing workflows list"
grep -q 'CI' "$PKG" || fail "packager must wake on CI workflow_run"
grep -q 'Branch Source Policy' "$PKG" || fail "packager must wake on Branch Source Policy"
grep -q 'Branch Source Policy' "$INT" || fail "integrator must wake on Branch Source Policy"
grep -q 'Enforce allowed PR source branches' "$PKG" || fail "packager FAST_GATE must include Branch Source check"
pass "Workflow phases + crons + workflow_run wake"

for f in linktrend-review-packager.yml linktrend-development-to-staging.yml \
         linktrend-staging-to-main.yml linktrend-integrator-merge.yml branch-source-policy.yml; do
  cmp -s "core/github/managed-workflows/$f" ".github/workflows/$f" || fail "Diverged: $f"
done
pass "Managed workflows match live copies"

grep -q 'Linktrend Review Ready' core/github/REVIEW-READY.md || fail "status context missing"
grep -q 'LINKTREND_BUGBOT_REVIEW_COMMAND' "$PKG" || fail "bugbot command var"
grep -q 'cursor review' "$PKG" || fail "default cursor review"
pass "Readiness status + Bugbot command"

if grep -nE 'push origin HEAD:(staging|main)' scripts/gitops/promote_*.sh "$STG" "$MAIN"; then
  fail "direct push remains"
fi
grep -q 'MODE: build\|mode=build\|MODE="build"\|options: \[build, reevaluate\]' "$STG" \
  || grep -q 'build' "$STG" || fail "staging build mode missing"
grep -q 'reevaluate' "$STG" || fail "staging reevaluate mode missing"
pass "No direct push; promote modes split"

# ---- Trust boundary: write-capable workflows ----
WRITE_WFS=("$PKG" "$STG" "$MAIN" "$INT")
for wf in "${WRITE_WFS[@]}"; do
  # Must not check out PR head/merge ref
  if grep -nE 'ref:\s*\$\{\{\s*github\.event\.pull_request\.(head\.sha|merge_commit_sha)' "$wf"; then
    fail "write workflow checks out PR head/merge: $wf"
  fi
  if grep -nE 'refs/pull/' "$wf"; then
    fail "write workflow references refs/pull: $wf"
  fi
  grep -q 'persist-credentials: false' "$wf" || fail "missing persist-credentials false: $wf"
  grep -q 'default_branch' "$wf" || fail "missing trusted default_branch checkout: $wf"
  # Prefer pull_request_target over privileged pull_request for PR events
  if grep -qE '^\s+pull_request:' "$wf" && ! grep -q 'pull_request_target' "$wf"; then
    fail "privileged pull_request without pull_request_target: $wf"
  fi
  # Must not interpolate untrusted title/body into shell run blocks via expression
  if grep -nE 'github\.event\.pull_request\.(title|body)' "$wf"; then
    fail "untrusted PR title/body interpolated: $wf"
  fi
  grep -q 'LINKTREND_GITOPS_APP' "$wf" || fail "missing App credential contract: $wf"
  grep -q 'automation_credentials_blocked\|resolve_automation_token' "$wf" \
    || fail "missing fail-closed credentials path: $wf"
done
# Unprivileged CI remains read-only and tests proposed code
grep -q 'permissions:' "$CI" || fail "ci missing permissions"
grep -q 'contents: read' "$CI" || fail "ci must be contents:read"
grep -q 'pull_request:' "$CI" || fail "ci must test PRs with pull_request"
! grep -q 'contents: write' "$CI" || fail "ci must not have contents:write"
pass "Trust boundary: trusted checkout + App fail-closed; CI unprivileged"

# Self-trigger guards
grep -q "github-actions" "$PKG" || fail "packager must filter Actions check_run"
grep -q "Linktrend Packager Result" "$PKG" || fail "packager must ignore own result check"
grep -q "Linktrend Integrator Result" "$INT" || fail "integrator must ignore own result check"
pass "No indefinite self-trigger via own check runs"

grep -q 'Ship 05' .cursor/rules/02-autonomous-ship-pull.mdc
grep -q 'Pull 07' .cursor/rules/02-autonomous-ship-pull.mdc
grep -q 'Linktrend Review Ready' .cursor/rules/02-autonomous-ship-pull.mdc
pass "Doctrine Ship 05/Pull 07 + status readiness"

grep -q 'default branch' docs/GITOPS-CONSUMER-ROLLOUT.md
grep -qi 'mention-only\|manualTriggerOnly' docs/contracts/BUGBOT-MENTION-ONLY.md
grep -q 'LINKTREND_GITOPS_APP' docs/contracts/GITHUB-APP-GITOPS-CREDENTIALS.md
pass "Activation + mention-only + App credential docs"

for s in scripts/mark-review-ready.sh scripts/validate-review-ready.sh \
         scripts/pull-update-work-branches.sh scripts/cleanup-merged-branches.sh \
         scripts/gitops/promote_staging.sh scripts/gitops/promote_main.sh \
         scripts/gitops/integrator_evaluate.sh scripts/tests/test-gitops-behavioral.sh \
         scripts/gitops/resolve_automation_token.sh; do
  [ -x "$s" ] || fail "not executable: $s"
done
[ ! -f scripts/commit-review-ready.sh ] || fail "commit-review-ready.sh must be removed"
[ ! -f core/templates/REVIEW-READY.json ] || fail "REVIEW-READY.json template must be removed"
pass "Executable modes + obsolete readiness file artifacts removed"

# Honest outcomes vocabulary
python3 - <<'PY'
from pathlib import Path
import sys
sys.path.insert(0, "scripts/gitops")
from write_outcome import VALID
need = {"packaged","waiting","skipped","blocked","failed","bugbot_requested","merged","automation_credentials_blocked"}
assert need <= VALID, need - VALID
text = Path("scripts/gitops/packager_evaluate.py").read_text()
for s in ("waiting","skipped","blocked","bugbot_requested","automation_credentials_blocked"):
    assert s in text
print("outcomes ok")
PY
pass "Honest outcome vocabulary present"

# ---- App token: same-job mint; never job-output secrets ----
PINNED="fee1f7d63c2ff003460e3d139729b119787bc349"
for wf in "${WRITE_WFS[@]}"; do
  grep -q "create-github-app-token@${PINNED}" "$wf" \
    || fail "App token action not pinned to reviewed SHA: $wf"
  if grep -nE 'outputs:\s*$' "$wf" >/dev/null; then
    # Any job-level outputs block must not expose app_token / token
    python3 - "$wf" <<'PY'
import re,sys
text=open(sys.argv[1],encoding="utf-8").read()
# Rough: between "jobs:" and end, find job outputs that mention token
for m in re.finditer(r'(?m)^  [A-Za-z0-9_-]+:\n(?:.*\n)*?(?=^  [A-Za-z0-9_-]+:|\Z)', text.split("jobs:\n",1)[-1] if "jobs:" in text else ""):
    block=m.group(0)
    if re.search(r'(?m)^\s+outputs:\s*$', block):
        if re.search(r'(?i)app_token|outputs\.token|token:', block.split("steps:",1)[0]):
            raise SystemExit(f"token-like job output in {sys.argv[1]}")
print("ok")
PY
  fi
  if grep -nE 'needs\.[A-Za-z0-9_-]+\.outputs\.(app_token|token)\b' "$wf"; then
    fail "consumes App token via needs.*.outputs: $wf"
  fi
  if grep -nE 'skip-token-revoke:\s*true' "$wf"; then
    fail "skip-token-revoke workaround forbidden: $wf"
  fi
done
# Consumer steps must not inject private key env
for wf in "${WRITE_WFS[@]}"; do
  # private-key: is allowed only under create-github-app-token with: block
  python3 - "$wf" <<'PY'
from pathlib import Path
import sys,re
text=Path(sys.argv[1]).read_text()
# Forbid LINKTREND_GITOPS_APP_PRIVATE_KEY in env: mappings for run steps
if re.search(r'(?m)^\s+LINKTREND_GITOPS_APP_PRIVATE_KEY:\s*', text):
    raise SystemExit(f"private key env injected into workflow steps: {sys.argv[1]}")
# Forbid job output named app_token
if re.search(r'(?m)^\s+app_token:\s*', text):
    raise SystemExit(f"app_token job output present: {sys.argv[1]}")
print("ok")
PY
done
pass "App token same-job only; no job-output secret transport"

# ---- Concurrency: PR/head key; never workflow_run.id / check_run.id ----
for wf in "$PKG" "$INT"; do
  grp="$(grep -E '^\s*group:' "$wf" | head -1)"
  echo "$grp" | grep -q 'workflow_run\.id\|check_run\.id' \
    && fail "concurrency must not use workflow_run.id/check_run.id: $wf :: $grp"
  echo "$grp" | grep -Eq 'pull_request\.number|pull_requests\[0\]\.number|head_sha' \
    || fail "concurrency must key on PR number or head SHA: $wf :: $grp"
  grep -q 'cancel-in-progress: false' "$wf" || fail "cancel-in-progress must be false: $wf"
done
grep -q 'cancel-in-progress: false' "$STG"
grep -q 'cancel-in-progress: false' "$MAIN"
# Event filters before mint: promote workflows require promote/* head
grep -q "startsWith(github.event.workflow_run.head_branch, 'promote/staging/')" "$STG" \
  || fail "staging must filter workflow_run head_branch before mint"
grep -q "startsWith(github.event.workflow_run.head_branch, 'promote/main/')" "$MAIN" \
  || fail "main must filter workflow_run head_branch before mint"
grep -q "Linktrend Main Outcome" "$STG" || fail "staging must exclude Linktrend Main Outcome"
grep -q "workflow_run.event == 'pull_request'" "$PKG" || fail "packager must ignore push CI"
grep -q "workflow_run.event == 'pull_request'" "$INT" || fail "integrator must ignore push CI"
grep -q "!startsWith(github.head_ref, 'promote/')" "$PKG" || fail "packager must exclude promote heads"
pass "Concurrency per PR/head + pre-mint event filters"

echo "PASS: gitops static redesign + trust-boundary checks"
