#!/usr/bin/env bash
# Static GitOps invariants (companion to test-gitops-behavioral.sh).
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"
fail() { echo "FAIL: $1" >&2; exit 1; }
pass() { echo "PASS: $1"; }

PKG="core/github/managed-workflows/linktrend-review-packager.yml"
STG="core/github/managed-workflows/linktrend-development-to-staging.yml"
MAIN="core/github/managed-workflows/linktrend-staging-to-main.yml"

grep -q 'cron: "0 0 \* \* 2,5"' "$PKG" || fail "packager cron"
grep -q 'cron: "0 2 \* \* 2,5"' "$STG" || fail "staging cron"
grep -q 'packager_discover.py' "$PKG" || fail "discover phase missing"
grep -q 'packager_evaluate.py' "$PKG" || fail "evaluate phase missing"
pass "Workflow phases + crons"

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
grep -q 'MODE: reevaluate' "$STG" || fail "staging reevaluate job missing"
grep -q 'MODE: build' "$STG" || fail "staging build job missing"
pass "No direct push; promote modes split"

grep -q 'Ship 05' .cursor/rules/02-autonomous-ship-pull.mdc
grep -q 'Pull 07' .cursor/rules/02-autonomous-ship-pull.mdc
grep -q 'Linktrend Review Ready' .cursor/rules/02-autonomous-ship-pull.mdc
pass "Doctrine Ship 05/Pull 07 + status readiness"

grep -q 'default branch' docs/GITOPS-CONSUMER-ROLLOUT.md
grep -qi 'mention-only\|manualTriggerOnly' docs/contracts/BUGBOT-MENTION-ONLY.md
pass "Activation + mention-only docs"

for s in scripts/mark-review-ready.sh scripts/validate-review-ready.sh \
         scripts/pull-update-work-branches.sh scripts/cleanup-merged-branches.sh \
         scripts/gitops/promote_staging.sh scripts/gitops/promote_main.sh \
         scripts/gitops/integrator_evaluate.sh scripts/tests/test-gitops-behavioral.sh; do
  [ -x "$s" ] || fail "not executable: $s"
done
[ ! -f scripts/commit-review-ready.sh ] || fail "commit-review-ready.sh must be removed"
[ ! -f core/templates/REVIEW-READY.json ] || fail "REVIEW-READY.json template must be removed"
pass "Executable modes + obsolete readiness file artifacts removed"

echo "PASS: gitops static redesign checks"
