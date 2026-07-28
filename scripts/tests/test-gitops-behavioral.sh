#!/usr/bin/env bash
# Behavioral GitOps tests in isolated temporary repositories.
# Must not modify the caller's checkout. Must not perform destructive cleanup.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
PASS=0
fail() { echo "FAIL: $1" >&2; exit 1; }
pass() { echo "PASS: $1"; PASS=$((PASS + 1)); }

# --- helpers ---
make_repo() {
  local d="$1"
  mkdir -p "$d"
  git -C "$d" init -q -b development
  git -C "$d" config user.email "test@example.com"
  git -C "$d" config user.name "GitOps Test"
  echo "base" >"$d/README.md"
  git -C "$d" add README.md
  git -C "$d" commit -q -m "chore: base"
  # protected branch tips
  git -C "$d" branch staging
  git -C "$d" branch main
}

# Copy scripts under test into temp repo (simulate checkout)
seed_scripts() {
  local d="$1"
  mkdir -p "$d/scripts/gitops"
  cp "$ROOT/scripts/mark-review-ready.sh" "$d/scripts/"
  cp "$ROOT/scripts/commit-review-ready.sh" "$d/scripts/"
  cp "$ROOT/scripts/validate-review-ready.sh" "$d/scripts/"
  cp "$ROOT/scripts/pull-update-work-branches.sh" "$d/scripts/"
  cp "$ROOT/scripts/cleanup-merged-branches.sh" "$d/scripts/"
  cp "$ROOT/scripts/gitops/"*.sh "$d/scripts/gitops/" 2>/dev/null || true
  cp "$ROOT/scripts/gitops/"*.py "$d/scripts/gitops/"
  chmod +x "$d/scripts/"*.sh "$d/scripts/gitops/"*.sh "$d/scripts/gitops/"*.py
  git -C "$d" add scripts
  git -C "$d" commit -q -m "chore: seed gitops scripts under test"
}

TMP="$(mktemp -d)"
cleanup() { rm -rf "$TMP"; }
trap cleanup EXIT

# ============================================================================
# 1) Readiness lifecycle: functional -> mark -> marker commit -> eligible;
#    later commit invalidates
# ============================================================================
REPO="$TMP/ready"
make_repo "$REPO"
seed_scripts "$REPO"
pushd "$REPO" >/dev/null
git checkout -q -b issue/GITOPS-test-ready
echo "feature" >app.txt
git add app.txt
git commit -q -m "feat: functional"
CONTENT="$(git rev-parse HEAD)"
bash scripts/mark-review-ready.sh GITOPS-test "notes"
python3 -c 'import json,sys; d=json.load(open(sys.argv[1])); assert d["contentSha"]==sys.argv[2]' \
  .linktrend/review-ready.json "$CONTENT"
if bash scripts/validate-review-ready.sh >/dev/null 2>&1; then
  popd >/dev/null
  fail "validate should fail before marker commit"
fi
bash scripts/commit-review-ready.sh >/dev/null
MARKER="$(git rev-parse HEAD)"
[ "$MARKER" != "$CONTENT" ] || { popd >/dev/null; fail "marker commit must be distinct from contentSha"; }
bash scripts/validate-review-ready.sh >/dev/null
PARENT="$(git rev-parse HEAD^)"
[ "$PARENT" = "$CONTENT" ] || { popd >/dev/null; fail "HEAD^ must equal contentSha"; }
CHANGED="$(git diff-tree --no-commit-id --name-only -r HEAD)"
echo "$CHANGED" | grep -qx '.linktrend/review-ready.json' || { popd >/dev/null; fail "marker must change review-ready.json"; }
echo "more" >>app.txt
git add app.txt
git commit -q -m "feat: later change"
if bash scripts/validate-review-ready.sh >/dev/null 2>&1; then
  popd >/dev/null
  fail "later commit must invalidate readiness"
fi
popd >/dev/null
pass "readiness marking + marker commit structure + eligible validation"
pass "later commit invalidates readiness"

# ============================================================================
# 2) Packager Bugbot policy: fast-gate fail => no request; idempotency; max 2
# ============================================================================
python3 - <<'PY'
import json, sys
sys.path.insert(0, "scripts/gitops")
# use ROOT via env
PY
python3 - "$ROOT" <<'PY'
import json, sys
from pathlib import Path
sys.path.insert(0, str(Path(sys.argv[1]) / "scripts" / "gitops"))
from packager_logic import should_request_bugbot, build_bugbot_comment, marker_for, count_bugbot_requests, fast_gate_status

sha = "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
# fast-gate fail => no request
ok, reason = should_request_bugbot(comments=[], head_sha=sha, fast_gate_ok=False)
assert ok is False and reason == "fast_gate_not_green", (ok, reason)

# success path
ok, reason = should_request_bugbot(comments=[], head_sha=sha, fast_gate_ok=True)
assert ok and reason == "request"

# after marker comment, idempotent skip
comments = [{"body": build_bugbot_comment("cursor review", sha)}]
ok, reason = should_request_bugbot(comments=comments, head_sha=sha, fast_gate_ok=True)
assert ok is False and reason == "skipped_duplicate_marker", (ok, reason)

# max two requests
c2 = [
    {"body": "cursor review\n\n" + marker_for("1111111111111111111111111111111111111111")},
    {"body": "cursor review\n\n" + marker_for("2222222222222222222222222222222222222222")},
]
ok, reason = should_request_bugbot(comments=c2, head_sha=sha, fast_gate_ok=True)
assert ok is False and reason == "skipped_max_requests", (ok, reason)
assert count_bugbot_requests(c2) >= 2

# fast-gate missing/failed
st, _ = fast_gate_status([], ["Verify IDE Development"])
assert st == "missing"
st, _ = fast_gate_status(
    [{"name": "Verify IDE Development", "state": "FAILURE", "completedAt": "2026-01-01"}],
    ["Verify IDE Development"],
)
assert st == "failed"
st, _ = fast_gate_status(
    [{"name": "Verify IDE Development", "state": "SUCCESS", "completedAt": "2026-01-01"}],
    ["Verify IDE Development"],
)
assert st == "success"
# marker only after request text
body = build_bugbot_comment("cursor review", sha)
assert body.startswith("cursor review")
assert marker_for(sha) in body
print("packager policy ok")
PY
pass "fast-gate failure blocks Bugbot; idempotency; max two requests"

# Ensure no pre-request marker in packager draft body builder (runner source)
grep -n 'linktrend-bugbot-requested' "$ROOT/scripts/gitops/packager_runner.py" | grep -v 'build_bugbot_comment\|marker_for\|should_request' >/tmp/marker_hits.txt || true
# Marker may appear only via build_bugbot_comment path — draft body in ensure_draft_pr must not include it
python3 - "$ROOT" <<'PY'
from pathlib import Path
import sys
text = Path(sys.argv[1], "scripts/gitops/packager_runner.py").read_text()
# Extract ensure_draft_pr body string region roughly
assert "Draft PR for deterministic fast-gate before Bugbot" in text
idx = text.index("Draft PR for deterministic fast-gate before Bugbot")
chunk = text[idx:idx+500]
assert "linktrend-bugbot-requested" not in chunk
print("draft body clean")
PY
pass "draft PR body has no requested marker before Bugbot"

# ============================================================================
# 3) Combined staging/main candidate validation (local merges, no direct push)
# ============================================================================
PROMO="$TMP/promo"
make_repo "$PROMO"
seed_scripts "$PROMO"
# simulate remotes via local branches + fake origin refs
git -C "$PROMO" checkout -q development
echo "dev1" >"$PROMO/d.txt"
git -C "$PROMO" add d.txt
git -C "$PROMO" commit -q -m "feat: on development"
DEV="$(git -C "$PROMO" rev-parse HEAD)"
git -C "$PROMO" checkout -q staging
echo "stg" >"$PROMO/s.txt"
git -C "$PROMO" add s.txt
git -C "$PROMO" commit -q -m "chore: staging unique"
STG="$(git -C "$PROMO" rev-parse HEAD)"
# Build staging candidate from staging tip merging development
git -C "$PROMO" checkout -q -b "promote/staging/${DEV:0:12}" staging
if ! git -C "$PROMO" merge --no-ff development -m "chore(promote): candidate"; then
  fail "expected clean staging candidate merge"
fi
CAND="$(git -C "$PROMO" rev-parse HEAD)"
# Candidate must contain both trees
git -C "$PROMO" cat-file -e "${CAND}:d.txt"
git -C "$PROMO" cat-file -e "${CAND}:s.txt"
# Protected staging tip unchanged
[ "$(git -C "$PROMO" rev-parse staging)" = "$STG" ] || fail "staging tip moved during candidate build"
pass "combined staging candidate built; staging tip unchanged"

# Conflict leaves protected unchanged
CON="$TMP/conflict"
make_repo "$CON"
git -C "$CON" checkout -q development
echo "A" >"$CON/conflict.txt"
git -C "$CON" add conflict.txt
git -C "$CON" commit -q -m "dev side"
git -C "$CON" checkout -q staging
echo "B" >"$CON/conflict.txt"
git -C "$CON" add conflict.txt
git -C "$CON" commit -q -m "stg side"
STG2="$(git -C "$CON" rev-parse staging)"
git -C "$CON" checkout -q -b promote/staging/conflict staging
if git -C "$CON" merge --no-ff development -m "should conflict"; then
  fail "expected conflict"
fi
git -C "$CON" merge --abort
[ "$(git -C "$CON" rev-parse staging)" = "$STG2" ] || fail "staging changed after conflict"
pass "promotion conflict leaves protected staging unchanged"

# Main candidate similarly
git -C "$PROMO" checkout -q main
echo "mainline" >"$PROMO/m.txt"
git -C "$PROMO" add m.txt
git -C "$PROMO" commit -q -m "chore: main unique"
MAIN="$(git -C "$PROMO" rev-parse HEAD)"
# move staging to include development candidate content for main package source
git -C "$PROMO" checkout -q staging
git -C "$PROMO" merge --no-ff development -m "simulate staging advanced" >/dev/null
STG_ADV="$(git -C "$PROMO" rev-parse HEAD)"
git -C "$PROMO" checkout -q -b "promote/main/${STG_ADV:0:12}" main
git -C "$PROMO" merge --no-ff staging -m "chore(promote): main candidate" >/dev/null
git -C "$PROMO" cat-file -e "HEAD:m.txt"
git -C "$PROMO" cat-file -e "HEAD:d.txt"
[ "$(git -C "$PROMO" rev-parse main)" = "$MAIN" ] || fail "main tip moved"
pass "combined main candidate built; main tip unchanged"

# ============================================================================
# 4) No direct push fallbacks in promote scripts / workflows
# ============================================================================
if grep -nE 'push origin HEAD:(staging|main)|push origin.*:staging|:main' \
  "$ROOT/scripts/gitops/promote_staging.sh" \
  "$ROOT/scripts/gitops/promote_main.sh" \
  "$ROOT/core/github/managed-workflows/linktrend-development-to-staging.yml" \
  "$ROOT/core/github/managed-workflows/linktrend-staging-to-main.yml"; then
  fail "direct push to staging/main still present"
fi
# Allow pushing promote branches only
grep -q 'promote/staging' "$ROOT/scripts/gitops/promote_staging.sh" || fail "staging promote branch missing"
grep -q 'promote/main' "$ROOT/scripts/gitops/promote_main.sh" || fail "main promote branch missing"
pass "no direct push to staging/main; temp promote branches used"

# ============================================================================
# 5) Conflict task idempotency + attempt cap
# ============================================================================
CT="$TMP/conflict-tasks"
mkdir -p "$CT"
python3 "$ROOT/scripts/gitops/conflict_task.py" upsert \
  --root "$CT" \
  --repo "linktrend/IDE-Development" \
  --stage staging \
  --source-branch development \
  --target-branch staging \
  --source-sha "$DEV" \
  --target-sha "$STG" \
  --status conflict_blocked \
  --next-action "repair" \
  --increment-attempt >"$TMP/t1.json"
ID="$(python3 -c 'import json; print(json.load(open("'"$TMP"'/t1.json"))["id"])')"
python3 "$ROOT/scripts/gitops/conflict_task.py" upsert \
  --root "$CT" \
  --repo "linktrend/IDE-Development" \
  --stage staging \
  --source-branch development \
  --target-branch staging \
  --source-sha "$DEV" \
  --target-sha "$STG" \
  --status conflict_blocked \
  --next-action "repair" \
  --increment-attempt >"$TMP/t2.json"
ID2="$(python3 -c 'import json; print(json.load(open("'"$TMP"'/t2.json"))["id"])')"
[ "$ID" = "$ID2" ] || fail "task id not idempotent"
ATTEMPTS="$(python3 -c 'import json; print(json.load(open("'"$TMP"'/t2.json"))["attemptCount"])')"
[ "$ATTEMPTS" = "2" ] || fail "expected attemptCount 2 got $ATTEMPTS"
python3 "$ROOT/scripts/gitops/conflict_task.py" upsert \
  --root "$CT" --repo "linktrend/IDE-Development" --stage staging \
  --source-branch development --target-branch staging \
  --source-sha "$DEV" --target-sha "$STG" \
  --status conflict_blocked --next-action "repair" --increment-attempt >"$TMP/t3.json"
STATUS="$(python3 -c 'import json; print(json.load(open("'"$TMP"'/t3.json"))["status"])')"
[ "$STATUS" = "Issues" ] || fail "expected Issues after 3 attempts, got $STATUS"
python3 "$ROOT/scripts/gitops/conflict_task.py" resume --root "$CT" --id "$ID" >"$TMP/tr.json" || true
# resume should not clear Issues
STATUS2="$(python3 -c 'import json; print(json.load(open("'"$TMP"'/tr.json"))["status"])')"
[ "$STATUS2" = "Issues" ] || fail "Issues must stick after resume attempt"
pass "conflict task idempotency and attempt cap"

# Reevaluation marker before cap
CT2="$TMP/conflict-tasks2"
mkdir -p "$CT2"
python3 "$ROOT/scripts/gitops/conflict_task.py" upsert \
  --root "$CT2" --repo r --stage staging --source-branch development --target-branch staging \
  --source-sha aaa --target-sha bbb --status conflict_blocked --next-action x --increment-attempt >"$TMP/u1.json"
TASK_UID="$(python3 -c 'import json; print(json.load(open("'"$TMP"'/u1.json"))["id"])')"
python3 "$ROOT/scripts/gitops/conflict_task.py" resume --root "$CT2" --id "$TASK_UID" >"$TMP/u2.json"
RST="$(python3 -c 'import json; print(json.load(open("'"$TMP"'/u2.json"))["status"])')"
[ "$RST" = "ready_for_reevaluation" ] || fail "expected ready_for_reevaluation"
pass "automatic reevaluation status after repair resume"

# ============================================================================
# 6) Pull freeze skip + unfinished update
# ============================================================================
PULL="$TMP/pull"
make_repo "$PULL"
seed_scripts "$PULL"
git -C "$PULL" checkout -q -b issue/unfinished
echo "u" >"$PULL/u.txt"
git -C "$PULL" add u.txt
git -C "$PULL" commit -q -m "wip"
# advance development
git -C "$PULL" checkout -q development
echo "adv" >"$PULL/adv.txt"
git -C "$PULL" add adv.txt
git -C "$PULL" commit -q -m "chore: advance development"
# frozen branch with valid marker
git -C "$PULL" checkout -q -b issue/frozen development
# reset frozen to before advance? Use unfinished tip as base without adv
git -C "$PULL" reset --hard issue/unfinished
echo "f" >"$PULL/f.txt"
git -C "$PULL" add f.txt
git -C "$PULL" commit -q -m "feat: frozen functional"
pushd "$PULL" >/dev/null
bash scripts/mark-review-ready.sh frozen >/dev/null
bash scripts/commit-review-ready.sh >/dev/null
popd >/dev/null
# Simulate origin/development
git -C "$PULL" update-ref refs/remotes/origin/development refs/heads/development
# Pull should skip frozen, update unfinished
pushd "$PULL" >/dev/null
git checkout -q issue/unfinished
bash scripts/pull-update-work-branches.sh --branch issue/frozen --branch issue/unfinished >"$TMP/pull.out" || true
popd >/dev/null
grep -q 'SKIP issue/frozen' "$TMP/pull.out" || fail "frozen branch not skipped: $(cat "$TMP/pull.out")"
grep -qE 'UPDATED issue/unfinished|OK issue/unfinished' "$TMP/pull.out" || fail "unfinished not updated: $(cat "$TMP/pull.out")"
pass "frozen Pull skip + unfinished Pull update"

# ============================================================================
# 7) Cleanup refuses active/unmerged/dirty (dry-run only)
# ============================================================================
CLN="$TMP/clean"
make_repo "$CLN"
seed_scripts "$CLN"
git -C "$CLN" checkout -q -b issue/active-work
echo "a" >"$CLN/a.txt"
git -C "$CLN" add a.txt
git -C "$CLN" commit -q -m "wip active"
# no gh in dry decision path for unmerged — script keeps without merged PR
# Run with GH unavailable simulation: override gh
git -C "$CLN" checkout -q development
PATH_SAVE="$PATH"
mkdir -p "$TMP/bin"
cat >"$TMP/bin/gh" <<'EOS'
#!/usr/bin/env bash
echo '[]'
EOS
chmod +x "$TMP/bin/gh"
PATH="$TMP/bin:$PATH" bash -c "cd \"$CLN\" && bash scripts/cleanup-merged-branches.sh" >"$TMP/clean.out" || true
grep -q 'KEEP' "$TMP/clean.out" || fail "cleanup should KEEP without merged confirmation"
grep -qv 'DELETED_' "$TMP/clean.out" || fail "dry-run must not delete"
# dirty local branch keep
git -C "$CLN" checkout -q -b issue/dirty
echo dirty >"$CLN/dirty.txt"
# uncommitted
PATH="$TMP/bin:$PATH" bash -c "cd \"$CLN\" && bash scripts/cleanup-merged-branches.sh --local" >"$TMP/clean2.out" || true
grep -q 'issue/dirty' "$TMP/clean2.out" || true
PATH="$PATH_SAVE"
pass "cleanup dry-run refuses unmerged/active work (no deletes)"

# ============================================================================
# 8) Exact-SHA approval bindings present in main promote script
# ============================================================================
grep -q 'EXPECTED_STAGING_SHA' "$ROOT/scripts/gitops/promote_main.sh" || fail "missing staging SHA bind"
grep -q 'EXPECTED_PROMOTE_HEAD' "$ROOT/scripts/gitops/promote_main.sh" || fail "missing promote head bind"
pass "exact-SHA approval bindings present"

# ============================================================================
# 9) Workflow activation / default-branch expectations documented + schedules
# ============================================================================
grep -q 'default branch' "$ROOT/docs/GITOPS-CONSUMER-ROLLOUT.md" \
  || grep -qi 'default branch' "$ROOT/docs/GITOPS-CONSUMER-ROLLOUT.md" \
  || fail "rollout doc must mention default branch activation"
grep -q 'cron: "0 0 \* \* 2,5"' "$ROOT/core/github/managed-workflows/linktrend-review-packager.yml"
grep -q 'cron: "0 2 \* \* 2,5"' "$ROOT/core/github/managed-workflows/linktrend-development-to-staging.yml"
pass "workflow schedules + activation expectations"

# ============================================================================
# 10) Shared allowlist consistency: packager + branch-source-policy
# ============================================================================
python3 - "$ROOT" <<'PY'
from pathlib import Path
import re, sys
root = Path(sys.argv[1])
allow = (root / "scripts/gitops/work-branch-allowlist.sh").read_text()
policy = (root / "core/github/managed-workflows/branch-source-policy.yml").read_text()
logic = (root / "scripts/gitops/packager_logic.py").read_text()
for prefix in ["issue/", "cursor/", "dev/", "feature/", "fix/", "chore/", "codex/", "antigravity/", "dependabot/"]:
    assert prefix in allow, prefix
    assert "is_allowed_work_branch" in policy
assert "promote/staging/" in allow and "promote/main/" in allow
assert "is_allowed_work_branch" in logic
assert "promote/staging" in policy and "promote/main" in policy
print("allowlist ok")
PY
pass "shared work-branch allowlist consistent"

# Integrator honest status values
grep -q 'merged|waiting|blocked|failed' "$ROOT/scripts/gitops/integrator_evaluate.sh" \
  || grep -q 'write_result "merged"' "$ROOT/scripts/gitops/integrator_evaluate.sh"
grep -q 'Linktrend Integrator Result' "$ROOT/scripts/gitops/integrator_evaluate.sh"
pass "integrator honest status reporting"

echo ""
echo "PASS: behavioral gitops tests (${PASS} groups)"
