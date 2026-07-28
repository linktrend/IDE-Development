#!/usr/bin/env bash
# Static + light behavioral invariants for GitOps redesign (companion to test-gitops-behavioral.sh).
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"

fail() { echo "FAIL: $1" >&2; exit 1; }
pass() { echo "PASS: $1"; }

PKG="core/github/managed-workflows/linktrend-review-packager.yml"
STG="core/github/managed-workflows/linktrend-development-to-staging.yml"
MAIN="core/github/managed-workflows/linktrend-staging-to-main.yml"
INT="core/github/managed-workflows/linktrend-integrator-merge.yml"

grep -q 'cron: "0 0 \* \* 2,5"' "$PKG" || fail "Review Packager cron"
grep -q 'cron: "0 2 \* \* 2,5"' "$STG" || fail "Staging cron"
grep -q 'cron: "0 0 \* \* 1"' "$MAIN" || fail "Main cron"
pass "Workflow crons Asia/Taipei"

for f in linktrend-review-packager.yml linktrend-development-to-staging.yml \
         linktrend-staging-to-main.yml linktrend-integrator-merge.yml branch-source-policy.yml; do
  cmp -s "core/github/managed-workflows/$f" ".github/workflows/$f" \
    || fail "Diverged: $f"
done
pass "Managed workflows match live copies"

grep -q 'LINKTREND_BUGBOT_REVIEW_COMMAND' "$PKG" || fail "Bugbot command must be repo-variable configurable"
grep -q "cursor review" "$PKG" || fail "default cursor review"
pass "Bugbot command configurable with safe default"

# No direct push fallbacks
if grep -nE 'push origin HEAD:(staging|main)|git push origin.*\bstaging\b|git push origin.*\bmain\b' \
  scripts/gitops/promote_staging.sh scripts/gitops/promote_main.sh "$STG" "$MAIN"; then
  fail "direct push to staging/main remains"
fi
pass "No direct staging/main push"

grep -q 'Ship 05' .cursor/rules/02-autonomous-ship-pull.mdc
grep -q 'Pull 07' .cursor/rules/02-autonomous-ship-pull.mdc
if grep -qE 'Ship 06|Pull 08' .cursor/rules/02-autonomous-ship-pull.mdc; then
  fail "superseded Ship 06/Pull 08 in rule 02"
fi
pass "Ship 05 / Pull 07 doctrine"

grep -q 'contentSha' core/github/REVIEW-READY.md || fail "REVIEW-READY must document contentSha"
grep -q 'default branch' docs/GITOPS-CONSUMER-ROLLOUT.md || fail "rollout must document default branch activation"
pass "Docs: contentSha + default-branch activation"

# Executable bits on key scripts (committed mode)
for s in scripts/mark-review-ready.sh scripts/commit-review-ready.sh scripts/validate-review-ready.sh \
         scripts/pull-update-work-branches.sh scripts/cleanup-merged-branches.sh \
         scripts/gitops/promote_staging.sh scripts/gitops/promote_main.sh \
         scripts/gitops/integrator_evaluate.sh scripts/tests/test-gitops-behavioral.sh; do
  [ -f "$s" ] || fail "missing $s"
  [ -x "$s" ] || fail "not executable (commit mode): $s"
done
pass "Key scripts are executable"

echo "PASS: gitops static redesign checks"
