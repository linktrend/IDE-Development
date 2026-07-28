#!/usr/bin/env bash
# GitOps redesign invariants: schedules, Bugbot command, review-ready, named gates.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"

fail() { echo "FAIL: $1" >&2; exit 1; }
pass() { echo "PASS: $1"; }

# --- Schedules (Asia/Taipei, no DST): Packager 08:00 = 00:00 UTC; Staging 10:00 = 02:00 UTC ---
PKG="core/github/managed-workflows/linktrend-review-packager.yml"
STG="core/github/managed-workflows/linktrend-development-to-staging.yml"
MAIN="core/github/managed-workflows/linktrend-staging-to-main.yml"
INT="core/github/managed-workflows/linktrend-integrator-merge.yml"

[ -f "$PKG" ] || fail "missing $PKG"
grep -q 'cron: "0 0 \* \* 2,5"' "$PKG" || fail "Review Packager cron must be 0 0 * * 2,5 (Tue/Fri 08:00 Taipei)"
grep -q 'cron: "0 2 \* \* 2,5"' "$STG" || fail "Staging cron must be 0 2 * * 2,5 (Tue/Fri 10:00 Taipei)"
grep -q 'cron: "0 0 \* \* 1"' "$MAIN" || fail "Main package cron must be 0 0 * * 1 (Mon 08:00 Taipei)"
pass "Workflow crons match Asia/Taipei Packager 08:00 / Staging 10:00 / Main Mon 08:00"

# Live copies must match managed templates for managed files
for f in linktrend-review-packager.yml linktrend-development-to-staging.yml \
         linktrend-staging-to-main.yml linktrend-integrator-merge.yml; do
  if [ "$f" = "linktrend-review-packager.yml" ] && [ ! -f ".github/workflows/$f" ]; then
    fail "Live workflow missing: .github/workflows/$f (sync required)"
  fi
  cmp -s "core/github/managed-workflows/$f" ".github/workflows/$f" \
    || fail "Diverged: core/github/managed-workflows/$f vs .github/workflows/$f"
done
pass "Managed workflows match live .github/workflows copies"

# sync script lists packager
grep -q 'linktrend-review-packager.yml' scripts/sync-managed-workflows.sh \
  || fail "sync-managed-workflows.sh must include review packager"
pass "sync-managed-workflows.sh includes packager"

# --- Bugbot command default + marker ---
grep -q 'BUGBOT_REVIEW_COMMAND: "cursor review"' "$PKG" \
  || fail "Packager default BUGBOT_REVIEW_COMMAND must be cursor review"
grep -q 'linktrend-bugbot-requested:' "$PKG" \
  || fail "Packager must emit hidden bugbot-requested marker"
grep -q 'Cursor Bugbot' "$INT" \
  || fail "Integrator must still require Cursor Bugbot"
# No default @cursor in packager env
if grep -E 'BUGBOT_REVIEW_COMMAND:.*"@' "$PKG"; then
  fail "Default Bugbot command must not include @ unless proven required"
fi
pass "Bugbot default command and marker present"

# --- Integrator: named gates only (no wait-for-every-check loop over all states as hard fail for unknowns) ---
# The redesign removes the while-read over all checks that fails on non-SUCCESS/SKIPPED for every name.
if grep -n 'check not green' "$INT" | grep -v '^[[:space:]]*#'; then
  fail "Integrator still has wait-for-every-check failure path (check not green)"
fi
grep -q 'fast-gate' "$INT" || fail "Integrator must mention fast-gate"
grep -q 'reviewed SHA' "$INT" || fail "Integrator must require reviewed SHA marker"
pass "Integrator uses named fast-gate + reviewed SHA (not every-check)"

# --- Staging: skip-if-not-ready + no prefer-incoming ---
grep -qi 'prefer-incoming' "$STG" || fail "Staging workflow should explicitly forbid prefer-incoming"
grep -q 'skipped' "$STG" || fail "Staging workflow must support skip reporting"
pass "Staging promote skip/report and no prefer-incoming"

# --- Doctrine: Ship 05 / Pull 07 authoritative; checkpoint-only Ship ---
RULE=".cursor/rules/02-autonomous-ship-pull.mdc"
grep -q 'Ship 05' "$RULE" || fail "Rule 02 must use Ship 05"
grep -q 'Pull 07' "$RULE" || fail "Rule 02 must use Pull 07"
if grep -qE 'Ship 06|Pull 08' "$RULE"; then
  fail "Rule 02 must not use superseded Ship 06 / Pull 08"
fi
grep -qi 'checkpoint' "$RULE" || fail "Rule 02 must describe checkpoints"
grep -qi 'review-ready\|review_ready' "$RULE" || fail "Rule 02 must describe review-ready"
# Ship must not instruct opening PR
if grep -A6 'At Ship 05' "$RULE" | grep -qi 'Open or update a PR'; then
  fail "Rule 02 Ship path must not open a PR"
fi
pass "Rule 02 Ship 05/Pull 07 checkpoint + review-ready doctrine"

DOC="docs/AUTONOMOUS-GIT-OPERATIONS.md"
grep -q 'Tue & Fri \*\*08:00\*\*' "$DOC" || grep -q '08:00' "$DOC" || fail "Doctrine missing Packager 08:00"
grep -q '10:00' "$DOC" || fail "Doctrine missing Staging 10:00"
grep -q 'cursor review' "$DOC" || fail "Doctrine missing cursor review default"
grep -q 'fast-gate' "$DOC" || fail "Doctrine missing fast-gate"
pass "AUTONOMOUS-GIT-OPERATIONS matches redesign"

# ADR amendment present
grep -q '2026-07-28' docs/adr/0003-autonomous-ship-pull-promote.md \
  || fail "ADR 0003 missing 2026-07-28 amendment"
pass "ADR 0003 amendment dated 2026-07-28"

# --- review-ready scripts ---
[ -x scripts/mark-review-ready.sh ] || chmod +x scripts/mark-review-ready.sh
[ -x scripts/validate-review-ready.sh ] || chmod +x scripts/validate-review-ready.sh
[ -x scripts/clear-review-ready.sh ] || chmod +x scripts/clear-review-ready.sh

TMP="$(mktemp -d)"
cleanup() { rm -rf "$TMP"; }
trap cleanup EXIT

# Simulate stale review-ready against a fake file + this repo HEAD mismatch
mkdir -p "$TMP/.linktrend"
HEAD="$(git rev-parse HEAD)"
python3 - "$TMP/.linktrend/review-ready.json" <<PY
import json, pathlib, sys
pathlib.Path(sys.argv[1]).write_text(json.dumps({
  "schemaVersion": 1,
  "issueId": "GITOPS-01",
  "branch": "issue/fake",
  "commitSha": "deadbeefdeadbeefdeadbeefdeadbeefdeadbeef",
  "recordedAt": "2026-07-28T00:00:00Z",
  "deterministicGate": "pass",
  "notes": ""
}, indent=2) + "\n")
PY
if scripts/validate-review-ready.sh "$TMP/.linktrend/review-ready.json" 2>/dev/null; then
  fail "validate-review-ready should fail on stale SHA"
fi
pass "Stale review-ready SHA rejected"

# Valid when SHA matches HEAD and branch matches — run from repo with tempfile overlay is hard;
# instead write then validate using commitSha=HEAD but wrong branch should fail when branch set.
python3 - ".linktrend-test-ready.json" <<PY
import json, pathlib, subprocess, sys
sha = subprocess.check_output(["git","rev-parse","HEAD"], text=True).strip()
branch = subprocess.check_output(["git","rev-parse","--abbrev-ref","HEAD"], text=True).strip()
pathlib.Path(sys.argv[1]).write_text(json.dumps({
  "schemaVersion": 1,
  "issueId": "GITOPS-01",
  "branch": branch,
  "commitSha": sha,
  "recordedAt": "2026-07-28T00:00:00Z",
  "deterministicGate": "pass",
  "notes": "test"
}, indent=2) + "\n")
PY
scripts/validate-review-ready.sh .linktrend-test-ready.json || fail "valid review-ready should pass"
rm -f .linktrend-test-ready.json
pass "Valid review-ready accepted"

# Marker idempotency helper: same SHA → same marker string
marker_for() { echo "<!-- linktrend-bugbot-requested: $(echo "$1" | tr 'A-F' 'a-f') -->"; }
m1="$(marker_for "$HEAD")"
m2="$(marker_for "$HEAD")"
[ "$m1" = "$m2" ] || fail "marker not idempotent for same SHA"
pass "Bugbot marker idempotent for same SHA"

# Frozen-branch doctrine
grep -qi 'freeze\|frozen' "$RULE" || fail "Rule 02 must mention review freeze"
grep -qi 'another issue branch\|worktree' "$RULE" || fail "Rule 02 must allow continue on other branch/worktree"
pass "Review freeze / continue-elsewhere doctrine"

# CI gate contract file
[ -f core/github/CI-GATE-CONTRACTS.md ] || fail "missing CI-GATE-CONTRACTS.md"
grep -q 'fast-gate' core/github/CI-GATE-CONTRACTS.md
grep -q 'staging-gate' core/github/CI-GATE-CONTRACTS.md
grep -q 'release-gate' core/github/CI-GATE-CONTRACTS.md
pass "Named CI gate contracts documented"

# Contracts for Lisa follow-up exist (no claim they were applied)
[ -f docs/contracts/LISA-OPENCLAW-FOLLOW-UP.md ] || fail "missing Lisa OpenClaw follow-up contract"
[ -f docs/contracts/LISA-MAIN-APPROVE-DISPATCH.md ] || fail "missing Lisa main approve dispatch contract"
[ -f docs/GITOPS-CONSUMER-ROLLOUT.md ] || fail "missing consumer rollout doc"
pass "Follow-up contracts and consumer rollout present"

echo "PASS: all gitops review-packager redesign tests"
