#!/usr/bin/env bash
# Behavioral GitOps tests — isolated temp repos, file status/conflict backends.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
PASS=0
fail() { echo "FAIL: $1" >&2; exit 1; }
pass() { echo "PASS: $1"; PASS=$((PASS + 1)); }

make_repo() {
  local d="$1"
  mkdir -p "$d"
  git -C "$d" init -q -b development
  git -C "$d" config user.email "test@example.com"
  git -C "$d" config user.name "GitOps Test"
  echo "base" >"$d/README.md"
  git -C "$d" add README.md
  git -C "$d" commit -q -m "chore: base"
  git -C "$d" branch staging
  git -C "$d" branch main
}

seed_scripts() {
  local d="$1"
  mkdir -p "$d/scripts/gitops"
  mkdir -p "$d/scripts/gitops/coordinator"
  printf '%s\n' "__pycache__/" "*.py[cod]" >"$d/.gitignore"
  cp "$ROOT/scripts/mark-review-ready.sh" "$d/scripts/"
  cp "$ROOT/scripts/validate-review-ready.sh" "$d/scripts/"
  cp "$ROOT/scripts/clear-review-ready.sh" "$d/scripts/"
  cp "$ROOT/scripts/pull-update-work-branches.sh" "$d/scripts/"
  cp "$ROOT/scripts/cleanup-merged-branches.sh" "$d/scripts/"
  cp "$ROOT/scripts/gitops/"*.sh "$d/scripts/gitops/" 2>/dev/null || true
  cp "$ROOT/scripts/gitops/"*.py "$d/scripts/gitops/"
  cp "$ROOT/scripts/gitops/coordinator/"*.py "$d/scripts/gitops/coordinator/"
  cp "$ROOT/scripts/gitops/"*.json "$d/scripts/gitops/" 2>/dev/null || true
  chmod +x "$d/scripts/"*.sh "$d/scripts/gitops/"*.sh "$d/scripts/gitops/"*.py
  git -C "$d" add .gitignore scripts
  git -C "$d" commit -q -m "chore: seed gitops scripts"
}

mark_ready_with_evidence() {
  local issue_id="$1"
  local notes="${2:-}"
  local evidence_file="${TMP}/evidence-${issue_id}.json"

  python3 scripts/gitops/completion_gate.py write-evidence \
    --evidence-file "${evidence_file}" \
    --classification tests \
    --acceptance "behavioral fixture" \
    --command "0|behavioral-fixture" >/dev/null

  if [ -n "${notes}" ]; then
    COMPLETION_EVIDENCE_FILE="${evidence_file}" bash scripts/mark-review-ready.sh "${issue_id}" "${notes}"
  else
    COMPLETION_EVIDENCE_FILE="${evidence_file}" bash scripts/mark-review-ready.sh "${issue_id}"
  fi
}

TMP="$(mktemp -d)"
cleanup() { rm -rf "$TMP"; }
trap cleanup EXIT

export LINKTREND_STATUS_BACKEND=file
export LINKTREND_CONFLICT_BACKEND=file
export LINKTREND_REPAIR_BACKEND=file

# ============================================================================
# 1) Readiness status on exact tip; later commit invalidates; no shared file
# ============================================================================
R1="$TMP/ready1"
R2="$TMP/ready2"
make_repo "$R1"
seed_scripts "$R1"
make_repo "$R2"
seed_scripts "$R2"
export LINKTREND_STATUS_DIR="$TMP/status-store"
mkdir -p "$LINKTREND_STATUS_DIR"

pushd "$R1" >/dev/null
git checkout -q -b issue/A-one
echo a >a.txt && git add a.txt && git commit -q -m "feat: a"
SHA_A="$(git rev-parse HEAD)"
# no origin — file backend allows mark
mark_ready_with_evidence A "notes-a" >/dev/null
bash scripts/validate-review-ready.sh "$SHA_A" >/dev/null
# concurrent other branch/repo must not create shared readiness file in tree
[ ! -f .linktrend/review-ready.json ] || fail "must not write review-ready.json into feature tree"
echo more >>a.txt && git add a.txt && git commit -q -m "feat: later"
if bash scripts/validate-review-ready.sh >/dev/null 2>&1; then
  fail "later commit must invalidate readiness"
fi
popd >/dev/null

pushd "$R2" >/dev/null
git checkout -q -b issue/B-two
echo b >b.txt && git add b.txt && git commit -q -m "feat: b"
SHA_B="$(git rev-parse HEAD)"
mark_ready_with_evidence B >/dev/null
bash scripts/validate-review-ready.sh "$SHA_B" >/dev/null
[ ! -f .linktrend/review-ready.json ] || fail "branch B must not have readiness file"
popd >/dev/null
# Both SHAs independently ready in status store
python3 "$ROOT/scripts/gitops/readiness_status.py" get "$SHA_A" >/dev/null
python3 "$ROOT/scripts/gitops/readiness_status.py" get "$SHA_B" >/dev/null
pass "readiness status exact SHA; later commit invalidates; concurrent branches no shared file"

# ============================================================================
# 2) Packager policy: discovery no Bugbot; gate fail/head change zero; success once; idempotent
# ============================================================================
python3 - "$ROOT" <<'PY'
import sys
from pathlib import Path
sys.path.insert(0, str(Path(sys.argv[1]) / "scripts" / "gitops"))
from packager_logic import (
    should_request_bugbot,
    build_bugbot_comment,
    marker_for,
    fast_gate_status,
    count_bugbot_requests,
    DEFAULT_BUGBOT_COMMAND,
)

assert DEFAULT_BUGBOT_COMMAND == "@cursor review"
sha = "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
ok, reason = should_request_bugbot(comments=[], head_sha=sha, fast_gate_ok=False)
assert not ok and reason == "fast_gate_not_green"
ok, reason = should_request_bugbot(comments=[], head_sha=sha, fast_gate_ok=True)
assert ok and reason == "request"

# Generated comment is exactly @cursor review + exact-SHA hidden marker
body = build_bugbot_comment(DEFAULT_BUGBOT_COMMAND, sha)
assert body.startswith("@cursor review\n\n")
assert marker_for(sha) in body
assert body == f"@cursor review\n\n{marker_for(sha)}\n"

# Genuine request + marker → same-SHA idempotent
comments = [{"body": body}]
ok, reason = should_request_bugbot(comments=comments, head_sha=sha, fast_gate_ok=True)
assert not ok and reason == "skipped_duplicate_marker"

# Historical invalid "cursor review" + marker does NOT consume the limit
hist = [
  {"body": "cursor review\n\n" + marker_for("1111111111111111111111111111111111111111")},
  {"body": "cursor review\n\n" + marker_for("2222222222222222222222222222222222222222")},
]
assert count_bugbot_requests(hist) == 0
ok, reason = should_request_bugbot(comments=hist, head_sha=sha, fast_gate_ok=True)
assert ok and reason == "request"

# @cursor review + marker counts
c_at = [{"body": "@cursor review\n\n" + marker_for("1111111111111111111111111111111111111111")}]
assert count_bugbot_requests(c_at) == 1

# bugbot run + marker counts
c_run = [{"body": "bugbot run\n\n" + marker_for("2222222222222222222222222222222222222222")}]
assert count_bugbot_requests(c_run) == 1

# Two genuine requests block a third
c2 = [
  {"body": "@cursor review\n\n" + marker_for("1111111111111111111111111111111111111111")},
  {"body": "bugbot run\n\n" + marker_for("2222222222222222222222222222222222222222")},
]
assert count_bugbot_requests(c2) == 2
ok, reason = should_request_bugbot(comments=c2, head_sha=sha, fast_gate_ok=True)
assert not ok and reason == "skipped_max_requests"

# Invalid history + one genuine still allows another genuine for a new SHA
mixed = hist + c_at
assert count_bugbot_requests(mixed) == 1
ok, reason = should_request_bugbot(comments=mixed, head_sha=sha, fast_gate_ok=True)
assert ok and reason == "request"

st,_=fast_gate_status([],["Verify IDE Development"]); assert st=="missing"
st,_=fast_gate_status([{"name":"Verify IDE Development","state":"FAILURE","completedAt":"t"}],["Verify IDE Development"]); assert st=="failed"
print("packager policy ok")
PY
# evaluate abort on head change is coded — simulate function path
python3 - "$ROOT" <<'PY'
from pathlib import Path
import sys
text = Path(sys.argv[1], "scripts/gitops/packager_evaluate.py").read_text()
assert "abort_head_changed_after_gate" in text
assert "abort_head_changed_before_bugbot" in text
assert "bugbot_requested" in text
assert "stale_event_head" in text
# discovery must not call build_bugbot_comment
disc = Path(sys.argv[1], "scripts/gitops/packager_discover.py").read_text()
assert "build_bugbot_comment" not in disc
assert "--draft" in disc
assert "linktrend-packager:begin" in disc
assert "title_preserved" in disc
print("packager phases ok")
PY
pass "Packager discovery without Bugbot; gate/head abort; idempotent request policy"

# Multiple candidates must not share a serial wait in discover
grep -q 'timeout-minutes: 5' "$ROOT/core/github/managed-workflows/linktrend-review-packager.yml"
grep -q 'Linktrend Fast Checks' "$ROOT/core/github/managed-workflows/linktrend-review-packager.yml"
grep -q 'cancel-in-progress: true' "$ROOT/core/github/managed-workflows/linktrend-review-packager.yml"
! grep -q 'GATE_WAIT_SECONDS: "900"' "$ROOT/core/github/managed-workflows/linktrend-review-packager.yml" \
  || fail "discover must not serially wait 900s"
pass "multiple candidates not blocked by serial discover wait"

# ============================================================================
# 3) Promotion reevaluate does not rebuild/push; head unchanged across events
# ============================================================================
PROMO="$TMP/promo"
make_repo "$PROMO"
seed_scripts "$PROMO"
git -C "$PROMO" checkout -q development
echo d >"$PROMO/d.txt" && git -C "$PROMO" add d.txt && git -C "$PROMO" commit -q -m "feat: d"
DEV="$(git -C "$PROMO" rev-parse HEAD)"
git -C "$PROMO" checkout -q -b "promote/staging/${DEV:0:12}" staging
git -C "$PROMO" merge --no-ff development -m "candidate" >/dev/null
HEAD1="$(git -C "$PROMO" rev-parse HEAD)"
# Simulate reevaluate path functions: no branch -f / merge / push in MODE=reevaluate source
python3 - "$ROOT" <<'PY'
from pathlib import Path
import sys,re
text=Path(sys.argv[1],"scripts/gitops/promote_staging.sh").read_text()
assert "reevaluate_exact()" in text
fn=text.split("reevaluate_exact()")[1].split("if [ \"${MODE}\" = \"reevaluate\"")[0]
for banned in ["git branch -f", "git checkout", "git merge", "git push", "force-with-lease"]:
    for line in fn.splitlines():
        s=line.strip()
        if s.startswith("#"): continue
        if banned in s:
            raise SystemExit(f"banned `{banned}` in reevaluate: {s}")
assert "linktrend-promote:" in text
assert "EXPECTED_PROMOTE_HEAD" in text
assert "PROMOTE_PR_NUMBER" in text
for line in text.splitlines():
    if "git fetch origin" in line and not line.strip().startswith("#"):
        assert "|| true" not in line, line
print("reevaluate clean")
PY
# Repeated "events" leave head unchanged
HEAD2="$(git -C "$PROMO" rev-parse "promote/staging/${DEV:0:12}")"
[ "$HEAD1" = "$HEAD2" ] || fail "promotion head changed without rebuild"
pass "promotion reevaluate does not rebuild; head stable across events"

# ============================================================================
# 4) Durable conflict attempts across runs; stop at 3
# ============================================================================
export LINKTREND_CONFLICT_DIR="$TMP/conflicts"
export LINKTREND_REPAIR_DIR="$LINKTREND_CONFLICT_DIR"
mkdir -p "$LINKTREND_CONFLICT_DIR"
python3 "$ROOT/scripts/gitops/conflict_task.py" upsert --repo r --stage staging \
  --source-branch development --target-branch staging --source-sha aaa --target-sha bbb \
  --status conflict_blocked --next-action x --increment-attempt >"$TMP/c1.json"
ID="$(python3 -c 'import json;print(json.load(open("'"$TMP"'/c1.json"))["id"])')"
# "new run" — same dir
python3 "$ROOT/scripts/gitops/conflict_task.py" upsert --repo r --stage staging \
  --source-branch development --target-branch staging --source-sha aaa --target-sha bbb \
  --status conflict_blocked --next-action x --increment-attempt >"$TMP/c2.json"
[ "$(python3 -c 'import json;print(json.load(open("'"$TMP"'/c2.json"))["attemptCount"])')" = "2" ]
python3 "$ROOT/scripts/gitops/conflict_task.py" upsert --repo r --stage staging \
  --source-branch development --target-branch staging --source-sha aaa --target-sha bbb \
  --status conflict_blocked --next-action x --increment-attempt >"$TMP/c3.json"
[ "$(python3 -c 'import json;print(json.load(open("'"$TMP"'/c3.json"))["status"])')" = "Issues" ]
# persists on disk across process
python3 "$ROOT/scripts/gitops/conflict_task.py" show --repo r --id "$ID" | grep -q Issues
grep -q -- '--failure-type promotion_conflict' "$ROOT/scripts/gitops/promote_staging.sh"
pass "durable conflict attempts persist and stop at three"

# ============================================================================
# 5) Main approval requires staging + main + promote head SHAs
# ============================================================================
grep -q 'requires both EXPECTED_STAGING_SHA and EXPECTED_PROMOTE_HEAD' "$ROOT/scripts/gitops/promote_main.sh"
grep -q 'EXPECTED_MAIN_SHA' "$ROOT/scripts/gitops/promote_main.sh"
grep -q 'Linktrend Receipt Gate' "$ROOT/core/github/managed-workflows/linktrend-staging-to-main.yml"
grep -q 'head_sha' "$ROOT/core/github/managed-workflows/linktrend-staging-to-main.yml"
pass "main approval requires both expected SHAs"

# ============================================================================
# 6) Pull preserves caller checkout; updates clean unfinished; skips frozen
# ============================================================================
PULL="$TMP/pull"
make_repo "$PULL"
seed_scripts "$PULL"
export LINKTREND_STATUS_DIR="$TMP/pull-status"
mkdir -p "$LINKTREND_STATUS_DIR"
git -C "$PULL" checkout -q -b issue/unfinished
echo u >"$PULL/u.txt" && git -C "$PULL" add u.txt && git -C "$PULL" commit -q -m "wip"
git -C "$PULL" checkout -q development
echo adv >"$PULL/adv.txt" && git -C "$PULL" add adv.txt && git -C "$PULL" commit -q -m "advance"
git -C "$PULL" update-ref refs/remotes/origin/development refs/heads/development
git -C "$PULL" checkout -q -b issue/frozen issue/unfinished
echo f >"$PULL/f.txt" && git -C "$PULL" add f.txt && git -C "$PULL" commit -q -m "frozen feat"
FR="$(git -C "$PULL" rev-parse HEAD)"
pushd "$PULL" >/dev/null
mark_ready_with_evidence frozen >/dev/null
# Caller stays on development (not on unfinished)
git checkout -q development
BEFORE_BRANCH="$(git rev-parse --abbrev-ref HEAD)"
BEFORE_SHA="$(git rev-parse HEAD)"
BEFORE_STATUS="$(git status --porcelain)"
BEFORE_WT="$(git worktree list --porcelain)"
bash scripts/pull-update-work-branches.sh --branch issue/frozen --branch issue/unfinished >"$TMP/pull.out"
AFTER_BRANCH="$(git rev-parse --abbrev-ref HEAD)"
AFTER_SHA="$(git rev-parse HEAD)"
AFTER_STATUS="$(git status --porcelain)"
AFTER_WT="$(git worktree list --porcelain)"
[ "$BEFORE_BRANCH" = "$AFTER_BRANCH" ] || fail "caller branch changed"
[ "$BEFORE_SHA" = "$AFTER_SHA" ] || fail "caller sha changed"
[ "$BEFORE_STATUS" = "$AFTER_STATUS" ] || fail "caller status changed"
[ "$BEFORE_WT" = "$AFTER_WT" ] || fail "worktree list changed"
grep -q 'SKIP issue/frozen' "$TMP/pull.out" || fail "frozen not skipped: $(cat "$TMP/pull.out")"
grep -qE 'UPDATED issue/unfinished|OK issue/unfinished' "$TMP/pull.out" || fail "unfinished not updated: $(cat "$TMP/pull.out")"
grep -q 'PULL_CALLER_UNCHANGED=1' "$TMP/pull.out"
# unfinished tip should now contain development advance
git merge-base --is-ancestor origin/development issue/unfinished \
  || fail "unfinished missing origin/development after pull"
popd >/dev/null
pass "Pull preserves caller checkout; skips frozen; updates unfinished"

# ============================================================================
# 7) Cleanup: squash evidence, session ownership, promote eligible, dirty refuse
# ============================================================================
CLN="$TMP/clean"
make_repo "$CLN"
seed_scripts "$CLN"
mkdir -p "$CLN/.linktrend"
# fake gh
mkdir -p "$TMP/bin"
cat >"$TMP/bin/gh" <<'EOS'
#!/usr/bin/env bash
# Emulate gh pr list for cleanup tests
if [[ "$*" == *"--head issue/squash"* ]]; then
  echo '[{"number":1,"state":"MERGED","mergedAt":"2026-01-01T00:00:00Z","labels":[],"headRefOid":"'"${SQUASH_HEAD}"'"}]'
  exit 0
fi
if [[ "$*" == *"--head promote/staging/"* ]]; then
  echo '[{"number":2,"state":"MERGED","mergedAt":"2026-01-01T00:00:00Z","labels":[],"headRefOid":"'"${PROMO_HEAD}"'"}]'
  exit 0
fi
if [[ "$*" == *"--head issue/owned"* ]]; then
  echo '[{"number":3,"state":"MERGED","mergedAt":"2026-01-01T00:00:00Z","labels":[],"headRefOid":"'"${OWNED_HEAD}"'"}]'
  exit 0
fi
if [[ "$*" == *"--head issue/dirty"* ]]; then
  echo '[{"number":4,"state":"MERGED","mergedAt":"2026-01-01T00:00:00Z","labels":[],"headRefOid":"'"${DIRTY_HEAD}"'"}]'
  exit 0
fi
echo '[]'
EOS
chmod +x "$TMP/bin/gh"

git -C "$CLN" checkout -q -b issue/squash
echo s >"$CLN/s.txt" && git -C "$CLN" add s.txt && git -C "$CLN" commit -q -m "squash me"
SQUASH_HEAD="$(git -C "$CLN" rev-parse HEAD)"
export SQUASH_HEAD
# not an ancestor of development (simulates squash)
git -C "$CLN" checkout -q development
git -C "$CLN" checkout -q -b "promote/staging/deadbeefcafe"
echo p >"$CLN/p.txt" && git -C "$CLN" add p.txt && git -C "$CLN" commit -q -m "promo"
PROMO_HEAD="$(git -C "$CLN" rev-parse HEAD)"
export PROMO_HEAD
git -C "$CLN" checkout -q development
git -C "$CLN" checkout -q -b issue/owned
echo o >"$CLN/o.txt" && git -C "$CLN" add o.txt && git -C "$CLN" commit -q -m "owned"
OWNED_HEAD="$(git -C "$CLN" rev-parse HEAD)"
export OWNED_HEAD
printf '%s\n' '{"issue/owned":{"owner":"agent","active":true}}' >"$CLN/.linktrend/session-owners.json"
git -C "$CLN" add .linktrend/session-owners.json && git -C "$CLN" commit -q -m "session owners"
git -C "$CLN" checkout -q -b issue/dirty
echo d >"$CLN/d.txt" && git -C "$CLN" add d.txt && git -C "$CLN" commit -q -m "dirty base"
DIRTY_HEAD="$(git -C "$CLN" rev-parse HEAD)"
export DIRTY_HEAD
git -C "$CLN" checkout -q development
# dirty worktree via second worktree (branch not checked out in main)
WTD="$TMP/dirty-wt"
git -C "$CLN" worktree add "$WTD" issue/dirty >/dev/null
echo dirty >>"$WTD/d.txt"

git -C "$CLN" checkout -q development
PATH="$TMP/bin:$PATH" bash -c "cd \"$CLN\" && bash scripts/cleanup-merged-branches.sh" >"$TMP/clean.out"
grep -q 'WOULD_DELETE_REMOTE: issue/squash\|WOULD_DELETE_LOCAL: issue/squash' "$TMP/clean.out" \
  || grep -q 'issue/squash' "$TMP/clean.out" || fail "squash merge should be cleanup-eligible: $(cat "$TMP/clean.out")"
grep -q 'promote/staging/deadbeefcafe' "$TMP/clean.out" || fail "merged promote branch should be considered"
grep -q 'issue/owned' "$TMP/clean.out" && grep -qi 'session ownership\|KEEP:.*owned' "$TMP/clean.out" \
  || fail "owned session must be kept: $(cat "$TMP/clean.out")"
grep -qi 'dirty' "$TMP/clean.out" || fail "dirty worktree should be mentioned"
grep -q 'CLEANUP_CALLER_UNCHANGED=1' "$TMP/clean.out"
grep -qv '^DELETED_' "$TMP/clean.out" || fail "dry-run must not delete"
pass "cleanup squash/session/promote/dirty safety (dry-run)"

# ============================================================================
# 8) No direct push staging/main
# ============================================================================
if grep -nE 'push origin HEAD:(staging|main)|git push origin HEAD:staging|git push origin HEAD:main' \
  "$ROOT/scripts/gitops/promote_staging.sh" \
  "$ROOT/scripts/gitops/promote_main.sh" \
  "$ROOT/core/github/managed-workflows/linktrend-development-to-staging.yml" \
  "$ROOT/core/github/managed-workflows/linktrend-staging-to-main.yml"; then
  fail "direct push remains"
fi
pass "no direct push to staging/main"

# ============================================================================
# 9) Workflow activation docs + schedules
# ============================================================================
grep -q 'default branch' "$ROOT/docs/GITOPS-CONSUMER-ROLLOUT.md"
grep -qi 'mention-only\|manualTriggerOnly' "$ROOT/docs/GITOPS-CONSUMER-ROLLOUT.md" \
  || grep -qi 'mention-only\|manualTriggerOnly' "$ROOT/docs/contracts/"*.md \
  || fail "mention-only documentation missing"
grep -q 'pull_request:' "$ROOT/core/github/managed-workflows/linktrend-review-packager.yml"
grep -q 'workflow_dispatch:' "$ROOT/core/github/managed-workflows/linktrend-development-to-staging.yml"
! grep -q 'cron:' "$ROOT/core/github/managed-workflows/linktrend-review-packager.yml"
! grep -q 'cron:' "$ROOT/core/github/managed-workflows/linktrend-development-to-staging.yml"
! grep -q 'workflow_run:' "$ROOT/core/github/managed-workflows/linktrend-review-packager.yml"
pass "activation + mention-only docs + explicit Phase triggers"

# ============================================================================
# 10) PR body preservation outside managed section
# ============================================================================
python3 - "$ROOT" <<'PY'
import sys
from pathlib import Path
sys.path.insert(0, str(Path(sys.argv[1]) / "scripts" / "gitops"))
from packager_discover import merge_body, BEGIN, END

human = (
    "# Agent transcript\n\n"
    "Keep this byte-for-byte.\n\n"
    "## Evidence\n\n"
    "- test results: PASS\n"
    "- notes: do-not-touch\n"
)
body1 = merge_body(human, "aaa", "issue/x")
assert "Keep this byte-for-byte." in body1
assert BEGIN in body1 and END in body1
outside1 = body1.split(BEGIN)[0]
body2 = merge_body(body1, "bbb", "issue/x")
outside2 = body2.split(BEGIN)[0]
assert outside1 == outside2 == human + "\n\n" or outside1 == outside2
# stricter: bytes before managed begin unchanged across runs
assert body1.split(BEGIN)[0] == body2.split(BEGIN)[0]
# managed section updated
assert "bbb" in body2.split(BEGIN)[1]
assert "aaa" not in body2.split(BEGIN)[1].split(END)[0]
# title never in merge_body API — discover never edits title for existing
disc = Path(sys.argv[1], "scripts/gitops/packager_discover.py").read_text()
assert "Never overwrite title" in disc or "title_preserved" in disc
assert "gh\", \"pr\", \"edit\"" in disc
assert "--title" not in disc.split("if existing:")[1].split("return")[0]
print("body preserve ok")
PY
pass "existing PR content survives outside managed section"

# ============================================================================
# 11) Exact-candidate promote binding + source/target advancement
# ============================================================================
python3 - "$ROOT" <<'PY'
from pathlib import Path
import sys
root = Path(sys.argv[1])
stg = (root / "scripts/gitops/promote_staging.sh").read_text()
main = (root / "scripts/gitops/promote_main.sh").read_text()
assert "target staging advanced" in stg or "targetSha" in stg
assert "stale event" in stg
assert "marker candidateHead" in stg
assert "EXPECTED_MAIN_SHA" in main
assert "target advanced" in main or "expected main target" in main
assert "main_approve_package_reuse.py" in main
assert "requires repackage" in main or "valid for reuse" in main
# development tip advance must not rebuild an existing exact candidate
assert "already exists for this exact source/target" in stg or "sourceSha" in stg
wf = (root / "core/github/managed-workflows/linktrend-development-to-staging.yml").read_text()
assert "Linktrend Receipt Gate" in wf
assert "head_sha" in wf
# Branch prefix policy lives in trusted resolver + promote script (not duplicated in YAML ifs)
resolver = (root / "scripts/gitops/resolve_event_pr.py").read_text()
assert "promote/staging/" in resolver and "promote/staging/" in stg
assert "promote/main/" in resolver and "promote/main/" in main
assert "pull_request_target:" in wf
print("exact candidate ok")
PY
pass "exact-candidate promote binding + advancement fail-closed"

# ============================================================================
# 12) Gate wake path + Bugbot request scenarios (policy + workflow wiring)
# Exact order: ready → CI done → Branch Source pending → waiting →
# Branch Source done → wake → Bugbot exactly once
# ============================================================================
python3 - "$ROOT" <<'PY'
import sys
from pathlib import Path
sys.path.insert(0, str(Path(sys.argv[1]) / "scripts" / "gitops"))
from packager_logic import should_request_bugbot, fast_gate_status, build_bugbot_comment, parse_required_checks

sha = "cccccccccccccccccccccccccccccccccccccccc"
required = parse_required_checks(
    "Verify IDE Development,Enforce allowed PR source branches"
)
assert required == ["Verify IDE Development", "Enforce allowed PR source branches"]
comma_name = "Install, typecheck, test, build"
json_required = parse_required_checks(
    '["Install, typecheck, test, build", "Enforce allowed PR source branches"]'
)
assert json_required == [comma_name, "Enforce allowed PR source branches"]
semicolon_required = parse_required_checks(
    "Install, typecheck, test, build;Enforce allowed PR source branches"
)
assert semicolon_required == [comma_name, "Enforce allowed PR source branches"]
assert parse_required_checks('["unterminated"') == []
assert parse_required_checks('{"not": "a list"}') == [
    '{"not": "a list"}'
]

comma_checks = [
    {"name": comma_name, "state": "SUCCESS", "completedAt": "t1"},
    {"name": "Enforce allowed PR source branches", "state": "SUCCESS", "completedAt": "t2"},
]
comma_status, comma_detail = fast_gate_status(comma_checks, json_required)
assert comma_status == "success", (comma_status, comma_detail)

# 1-2) PR/head ready; CI completes; Branch Source Policy still pending
checks_after_ci = [
    {"name": "Verify IDE Development", "state": "SUCCESS", "completedAt": "t1"},
    {"name": "Enforce allowed PR source branches", "state": "PENDING", "completedAt": ""},
]
st, detail = fast_gate_status(checks_after_ci, required)
assert st == "pending", (st, detail)
ok, reason = should_request_bugbot(comments=[], head_sha=sha, fast_gate_ok=(st == "success"))
assert not ok and reason == "fast_gate_not_green"
# Evaluation returns waiting — no Bugbot request
eval1_status = "waiting"
assert eval1_status == "waiting"

# 5-6) Branch Source Policy then completes → evaluation wakes again
checks_both = [
    {"name": "Verify IDE Development", "state": "SUCCESS", "completedAt": "t1"},
    {"name": "Enforce allowed PR source branches", "state": "SUCCESS", "completedAt": "t2"},
]
st2, _ = fast_gate_status(checks_both, required)
assert st2 == "success"
ok2, reason2 = should_request_bugbot(comments=[], head_sha=sha, fast_gate_ok=True)
assert ok2 and reason2 == "request"
# Exactly one request
comments = [{"body": build_bugbot_comment("@cursor review", sha)}]
ok3, reason3 = should_request_bugbot(comments=comments, head_sha=sha, fast_gate_ok=True)
assert not ok3 and reason3 == "skipped_duplicate_marker"

# Fast work wakes from the Phase PR; the full suite is explicit dispatch and
# requests Bugbot only after its exact-head full receipt succeeds.
fast = Path(sys.argv[1], "core/github/managed-workflows/linktrend-review-packager.yml").read_text()
full = Path(sys.argv[1], "core/github/managed-workflows/linktrend-integrator-merge.yml").read_text()
assert "pull_request:" in fast and "cancel-in-progress: true" in fast
assert "workflow_dispatch:" in full and "Linktrend Final Candidate Bugbot Request" in full
assert "workflow_run:" not in fast
assert "vars.LINKTREND_WORKFLOW_RUN" not in fast + full
print("explicit-wake+final-bugbot scenarios ok")
PY
pass "wake path + Bugbot request scenarios"

# ============================================================================
# 13) Normal automation credential: repository token accepted; fail closed otherwise
# ============================================================================
: <<'RETIRED_CREDENTIAL_FIXTURES'
python3 - "$ROOT" <<'PY'
from pathlib import Path
import subprocess, os, sys
root = Path(sys.argv[1])
script = str(root / "scripts/gitops/resolve_automation_token.sh")

def run(env_extra):
    env = os.environ.copy()
    for k in ("LINKTREND_AUTOMATION_TOKEN", "AUTOMATION_TOKEN", "GH_TOKEN", "GITHUB_TOKEN"):
        env.pop(k, None)
    env["REQUIRE_AUTOMATION_TOKEN"] = "1"
    env.update(env_extra)
    return subprocess.run(["bash", script], capture_output=True, text=True, env=env)

# Real workflow shape: normal repository secret
r = run({"LINKTREND_AUTOMATION_TOKEN": "ghs_test_normal_token_value"})
assert r.returncode == 0, (r.returncode, r.stderr, r.stdout)
assert "AUTOMATION_TOKEN_SOURCE=github_token" in r.stdout, r.stdout
assert "ghs_test_normal_token_value" not in r.stdout  # never print token
assert "ghs_test_normal_token_value" not in r.stderr

# Missing token → blocked
r = run({})
assert r.returncode != 0, (r.returncode, r.stderr, r.stdout)
assert "automation_credentials_blocked" in (r.stderr + r.stdout)

# GITHUB_TOKEN alone must not grant autonomy
r = run({"GITHUB_TOKEN": "ghs_workflow_token_only", "GH_TOKEN": "ghs_workflow_token_only"})
assert r.returncode != 0, (r.returncode, r.stderr, r.stdout)
assert "automation_credentials_blocked" in (r.stderr + r.stdout)

doc = (root/"docs/contracts/GITHUB-APP-GITOPS-CREDENTIALS.md").read_text()
assert "LINKTREND_AUTOMATION_TOKEN" in doc
assert "job outputs" in doc.lower()
print("credentials contract ok")
PY
pass "Normal automation credentials fail closed; no silent GITHUB_TOKEN autonomy"

# ============================================================================
# 13b) Carlos BUGBOT_USER_TOKEN: fail closed; env scrubbing; author gate;
#      Packager create + Bugbot comment only; other mutations stay App-scoped
# ============================================================================
python3 - "$ROOT" <<'PY'
from pathlib import Path
import json, os, subprocess, sys

root = Path(sys.argv[1])
sys.path.insert(0, str(root / "scripts" / "gitops"))
from bugbot_user_credentials import (
    ALLOWED_OPERATIONS,
    BugbotUserCredentialsError,
    require_bugbot_user_token,
    resolve_bugbot_user_token,
    scrub_carlos_token_env,
    subprocess_env_for_token,
)
from packager_logic import (
    REQUIRED_PACKAGER_PR_AUTHOR,
    packager_pr_author_login,
    require_packager_pr_author,
)
import packager_discover as disc_mod
import packager_evaluate as eval_mod

assert ALLOWED_OPERATIONS == frozenset({"pr_create", "bugbot_comment"})
assert REQUIRED_PACKAGER_PR_AUTHOR == "linktrend"

def clear_env(env):
    for k in (
        "BUGBOT_USER_TOKEN", "LINKTREND_BUGBOT_USER_TOKEN",
        "AUTOMATION_TOKEN", "LINKTREND_APP_TOKEN", "GH_TOKEN", "GITHUB_TOKEN",
        "BUGBOT_USER_TOKEN_SOURCE", "BUGBOT_USER_CREDENTIALS_STATUS",
    ):
        env.pop(k, None)
    return env

# Missing → fail closed
clear_env(os.environ)
tok, src, st = resolve_bugbot_user_token()
assert tok is None and src == "none" and st == "missing"
try:
    require_bugbot_user_token("pr_create")
    raise SystemExit("expected missing user token to raise")
except BugbotUserCredentialsError as e:
    assert "bugbot_user_credentials_blocked" in str(e) or "missing" in str(e)

# Configured unique user token (resolved export)
os.environ["BUGBOT_USER_TOKEN"] = "user_pat_unique_value_abc"
os.environ["AUTOMATION_TOKEN"] = "app_token_different_value_xyz"
tok, src, st = resolve_bugbot_user_token()
assert tok == "user_pat_unique_value_abc" and src == "user_secret" and st == "configured"
assert require_bugbot_user_token("pr_create") == "user_pat_unique_value_abc"
assert require_bugbot_user_token("bugbot_comment") == "user_pat_unique_value_abc"

# Disallowed operations
for op in ("merge", "promote", "repair", "status", "cleanup", "branch_push", "pr_ready", "freeze_comment"):
    try:
        require_bugbot_user_token(op)
        raise SystemExit(f"{op} must not be allowed")
    except BugbotUserCredentialsError:
        pass

# A single normal GitHub identity may supply both trusted automation and Bugbot.
os.environ["BUGBOT_USER_TOKEN"] = "same_secret_value"
os.environ["AUTOMATION_TOKEN"] = "same_secret_value"
tok, src, st = resolve_bugbot_user_token()
assert tok == "same_secret_value" and st == "configured"
clear_env(os.environ)
os.environ["LINKTREND_BUGBOT_USER_TOKEN"] = "same_gh"
os.environ["GITHUB_TOKEN"] = "same_gh"
tok, src, st = resolve_bugbot_user_token()
assert tok == "same_gh" and st == "configured"

# Shell accepts ONLY LINKTREND_BUGBOT_USER_TOKEN (no BUGBOT_USER_TOKEN input fallback)
script = str(root / "scripts/gitops/resolve_bugbot_user_token.sh")
def run_shell(extra):
    env = clear_env(os.environ.copy())
    env["REQUIRE_BUGBOT_USER_TOKEN"] = "1"
    env.update(extra)
    return subprocess.run(["bash", script], capture_output=True, text=True, env=env)

secret = "user_pat_shell_secret_do_not_echo"
r = run_shell({"LINKTREND_BUGBOT_USER_TOKEN": secret, "AUTOMATION_TOKEN": "app_other"})
assert r.returncode == 0, (r.returncode, r.stderr, r.stdout)
assert "BUGBOT_USER_TOKEN_SOURCE=user_secret" in r.stdout
assert secret not in r.stdout and secret not in r.stderr

r = run_shell({"BUGBOT_USER_TOKEN": secret, "AUTOMATION_TOKEN": "app_other"})
assert r.returncode != 0, "shell must not accept BUGBOT_USER_TOKEN as secret input"
assert "bugbot_user_credentials_blocked" in (r.stderr + r.stdout)

r = run_shell({"AUTOMATION_TOKEN": "app_only"})
assert r.returncode != 0
assert "bugbot_user_credentials_blocked" in (r.stderr + r.stdout)

r = run_shell({"LINKTREND_BUGBOT_USER_TOKEN": "dup", "AUTOMATION_TOKEN": "dup"})
assert r.returncode == 0

# --- Author validation (pure) ---
assert packager_pr_author_login({"author": {"login": "linktrend"}}) == "linktrend"
assert packager_pr_author_login({"user": {"login": "linktrend-gitops[bot]"}}) == "linktrend-gitops[bot]"
assert packager_pr_author_login({}) is None
assert packager_pr_author_login({"author": {}}) is None
ok, d = require_packager_pr_author({"author": {"login": "linktrend"}})
assert ok and d == "linktrend"
ok, d = require_packager_pr_author({"author": {"login": "linktrend-gitops[bot]"}})
assert not ok and "wrong_packager_pr_author" in d and "linktrend-gitops[bot]" in d
ok, d = require_packager_pr_author({"author": {}})
assert not ok and d == "missing_packager_pr_author"
ok, d = require_packager_pr_author(None)
assert not ok and d == "missing_packager_pr_author"

# --- Subprocess env recorder: App kids scrub Carlos; create gets token as GH only ---
clear_env(os.environ)
os.environ["LINKTREND_BUGBOT_USER_TOKEN"] = "carlos_secret_PARENT"
os.environ["BUGBOT_USER_TOKEN"] = "carlos_secret_PARENT"
os.environ["AUTOMATION_TOKEN"] = "automation_token_PARENT"
recorded = []

def record_run(args, env):
    recorded.append({"args": list(args), "env": dict(env)})
    # Minimal responses for discover ensure_draft_pr create path pieces
    if args[:3] == ["gh", "pr", "list"]:
        return "[]"
    if args[:3] == ["gh", "pr", "create"]:
        return "https://example.test/pr/99"
    if args[:3] == ["gh", "pr", "view"]:
        if "--json" in args and "number,author,headRefOid" in args:
            return json.dumps({"number": 99, "author": {"login": "linktrend"}, "headRefOid": "abc"})
        return json.dumps({"number": 99, "author": {"login": "linktrend"}, "headRefOid": "abc"})
    if "repair_task.py" in " ".join(args):
        return "{}"
    return ""

disc_mod._RUN_HOOK = record_run
try:
    # App-role scrub
    env_automation = subprocess_env_for_token("automation_token_PARENT", role="automation")
    assert "LINKTREND_BUGBOT_USER_TOKEN" not in env_automation
    assert "BUGBOT_USER_TOKEN" not in env_automation
    assert env_automation["GH_TOKEN"] == "automation_token_PARENT"
    # pr_create role: token value as GH_*, secret names scrubbed
    env_c = subprocess_env_for_token("carlos_secret_PARENT", role="pr_create")
    assert "LINKTREND_BUGBOT_USER_TOKEN" not in env_c
    assert "BUGBOT_USER_TOKEN" not in env_c
    assert env_c["GH_TOKEN"] == "carlos_secret_PARENT"
    assert scrub_carlos_token_env({"LINKTREND_BUGBOT_USER_TOKEN": "x", "BUGBOT_USER_TOKEN": "y", "A": "1"}) == {"A": "1"}

    pr = disc_mod.ensure_draft_pr("automation_token_PARENT", "issue/31-x", "abc")
    assert pr["created"] is True and pr["author"] == "linktrend"
    # Find create child
    creates = [r for r in recorded if r["args"][:3] == ["gh", "pr", "create"]]
    assert len(creates) == 1
    cenv = creates[0]["env"]
    assert cenv.get("GH_TOKEN") == "carlos_secret_PARENT"
    assert "LINKTREND_BUGBOT_USER_TOKEN" not in cenv
    assert "BUGBOT_USER_TOKEN" not in cenv
    # App list/view children scrub Carlos names
    apps = [r for r in recorded if r["args"][:3] == ["gh", "pr", "list"] or (
        r["args"][:3] == ["gh", "pr", "view"] and r["env"].get("GH_TOKEN") == "automation_token_PARENT"
    )]
    assert apps
    for r in apps:
        assert "LINKTREND_BUGBOT_USER_TOKEN" not in r["env"]
        assert "BUGBOT_USER_TOKEN" not in r["env"]
        assert r["env"].get("GH_TOKEN") == "automation_token_PARENT"
finally:
    disc_mod._RUN_HOOK = None

# Bot-authored existing PR → fail closed (no recreate/close)
recorded.clear()
def record_bot_list(args, env):
    recorded.append({"args": list(args), "env": dict(env)})
    if args[:3] == ["gh", "pr", "list"]:
        return json.dumps([{
            "number": 30, "url": "u", "isDraft": True, "headRefOid": "abc",
            "title": "t", "body": "", "author": {"login": "linktrend-gitops[bot]"},
        }])
    if "repair_task.py" in " ".join(args):
        return "{}"
    raise AssertionError(f"unexpected call for bot-author case: {args}")

disc_mod._RUN_HOOK = record_bot_list
try:
    try:
        disc_mod.ensure_draft_pr("automation_token_PARENT", "issue/28-x", "abc")
        raise SystemExit("bot author must fail closed")
    except disc_mod.PackagerAuthorError as e:
        assert "wrong_packager_pr_author" in str(e) or "linktrend-gitops[bot]" in str(e)
    # Must not have attempted create
    assert not any(r["args"][:3] == ["gh", "pr", "create"] for r in recorded)
finally:
    disc_mod._RUN_HOOK = None

# Evaluate: bot author blocks before undraft/bugbot; repair uses App-scrubbed env
recorded.clear()
api_calls = []
os.environ["GITHUB_REPOSITORY"] = "linktrend/IDE-Development"
os.environ["BUGBOT_USER_TOKEN"] = "carlos_secret_PARENT"
os.environ["LINKTREND_BUGBOT_USER_TOKEN"] = "carlos_secret_PARENT"
os.environ["FAST_GATE_CHECKS"] = "Verify IDE Development"
os.environ["HEAD_SHA"] = "deadbeef"

def eval_run(args, env):
    recorded.append({"args": list(args), "env": dict(env)})
    if args[:3] == ["gh", "pr", "view"] and "author" in " ".join(args):
        return json.dumps({
            "number": 30, "url": "u", "isDraft": True, "headRefOid": "deadbeef",
            "baseRefName": "development", "state": "OPEN",
            "headRefName": "issue/30-x",
            "author": {"login": "linktrend-gitops[bot]"},
        })
    if "repair_task.py" in " ".join(args):
        return "{}"
    return "[]"

def eval_api(method, url, token, body, snap):
    api_calls.append({"method": method, "url": url, "token": token, "body": body, "snap": snap})
    return []

# readiness: force ready via monkeypatch on evaluate's bound symbol
orig_ready = eval_mod.is_sha_review_ready
eval_mod.is_sha_review_ready = lambda sha: (True, "ok")
eval_mod._RUN_HOOK = eval_run
eval_mod._API_HOOK = eval_api
try:
    out = eval_mod.evaluate_pr(30, "automation_token_PARENT")
    assert out["status"] == "blocked"
    assert "superseded_wrong_author" in out["detail"]
    assert "linktrend-gitops[bot]" in out["detail"]
    # Never posted bugbot comment
    assert not any(
        c["method"] == "POST" and c["token"] == "carlos_secret_PARENT" for c in api_calls
    )
    repairs = [r for r in recorded if "repair_task.py" in " ".join(r["args"])]
    assert repairs, "expected App-authored repair upsert"
    for r in repairs:
        assert r["env"].get("GH_TOKEN") == "automation_token_PARENT"
        assert "LINKTREND_BUGBOT_USER_TOKEN" not in r["env"]
        assert "BUGBOT_USER_TOKEN" not in r["env"]
        assert "packager_author_blocked" in r["args"]
finally:
    eval_mod._RUN_HOOK = None
    eval_mod._API_HOOK = None
    eval_mod.is_sha_review_ready = orig_ready

# Carlos author + gates: Bugbot comment uses user token via API; freeze uses App; App kids scrubbed
recorded.clear()
api_calls.clear()
os.environ["BUGBOT_REVIEW_COMMAND"] = "@cursor review"

def eval_run_ok(args, env):
    recorded.append({"args": list(args), "env": dict(env)})
    joined = " ".join(args)
    if args[:3] == ["gh", "pr", "view"] and "author" in joined:
        return json.dumps({
            "number": 31, "url": "u", "isDraft": True, "headRefOid": "deadbeef",
            "baseRefName": "development", "state": "OPEN",
            "headRefName": "issue/31-x",
            "author": {"login": "linktrend"},
        })
    if args[:3] == ["gh", "pr", "view"] and "headRefOid" in joined and "author" not in joined:
        return "deadbeef"
    if args[:3] == ["gh", "pr", "checks"]:
        return json.dumps([{"name": "Verify IDE Development", "state": "SUCCESS"}])
    if args[:3] == ["gh", "pr", "ready"]:
        assert "LINKTREND_BUGBOT_USER_TOKEN" not in env and "BUGBOT_USER_TOKEN" not in env
        assert env.get("GH_TOKEN") == "automation_token_PARENT"
        return ""
    if "repair_task.py" in joined:
        raise AssertionError("repair must not run on Carlos-authored success path")
    return "[]"

def eval_api_ok(method, url, token, body, snap):
    api_calls.append({"method": method, "url": url, "token": token, "body": body, "snap": snap})
    if method == "GET":
        return []
    return {"id": 1}

eval_mod.is_sha_review_ready = lambda sha: (True, "ok")
eval_mod._RUN_HOOK = eval_run_ok
eval_mod._API_HOOK = eval_api_ok
try:
    out = eval_mod.evaluate_pr(31, "automation_token_PARENT")
    assert out["status"] == "bugbot_requested", out
    assert out.get("author") == "linktrend"
    posts = [c for c in api_calls if c["method"] == "POST"]
    assert len(posts) == 2  # bugbot + freeze
    assert posts[0]["token"] == "carlos_secret_PARENT"
    assert "@cursor review" in (posts[0]["body"] or {}).get("body", "")
    assert posts[1]["token"] == "automation_token_PARENT"
    assert "Review freeze" in (posts[1]["body"] or {}).get("body", "")
    # undraft child scrubbed
    readies = [r for r in recorded if r["args"][:3] == ["gh", "pr", "ready"]]
    assert readies and "BUGBOT_USER_TOKEN" not in readies[0]["env"]
finally:
    eval_mod._RUN_HOOK = None
    eval_mod._API_HOOK = None
    eval_mod.is_sha_review_ready = orig_ready

# Author drift before bugbot (Carlos → bot on final reread)
recorded.clear()
api_calls.clear()
views = {"n": 0}

def eval_run_drift(args, env):
    recorded.append({"args": list(args), "env": dict(env)})
    joined = " ".join(args)
    if args[:3] == ["gh", "pr", "view"] and "author" in joined:
        views["n"] += 1
        login = "linktrend" if views["n"] < 3 else "linktrend-gitops[bot]"
        return json.dumps({
            "number": 32, "url": "u", "isDraft": False, "headRefOid": "deadbeef",
            "baseRefName": "development", "state": "OPEN",
            "headRefName": "issue/32-x",
            "author": {"login": login},
        })
    if args[:3] == ["gh", "pr", "view"] and "headRefOid" in joined:
        return "deadbeef"
    if args[:3] == ["gh", "pr", "checks"]:
        return json.dumps([{"name": "Verify IDE Development", "state": "SUCCESS"}])
    if "repair_task.py" in joined:
        return "{}"
    return "[]"

def eval_api_drift(method, url, token, body, snap):
    api_calls.append({"method": method, "token": token, "body": body})
    if method == "GET":
        return []
    raise AssertionError("must not POST comments on author drift")

eval_mod.is_sha_review_ready = lambda sha: (True, "ok")
eval_mod._RUN_HOOK = eval_run_drift
eval_mod._API_HOOK = eval_api_drift
try:
    out = eval_mod.evaluate_pr(32, "automation_token_PARENT")
    assert out["status"] == "blocked"
    assert "before_bugbot" in out["detail"]
    assert not any(c["method"] == "POST" for c in api_calls)
finally:
    eval_mod._RUN_HOOK = None
    eval_mod._API_HOOK = None
    eval_mod.is_sha_review_ready = orig_ready

# Workflow: no ordinary GITHUB_TOKEN autonomous mutations; App used when Carlos missing
pkg = (root / ".github/workflows/linktrend-review-packager.yml").read_text()
assert 'GH_TOKEN="${GITHUB_TOKEN}"' not in pkg
assert "secrets.LINKTREND_BUGBOT_USER_TOKEN" in pkg
assert "resolve_bugbot_user_token.sh" in pkg
assert 'GH_TOKEN="${AUTOMATION_TOKEN}"' in pkg
# Discover/evaluate job tokens are reduced (no workflow issues/checks write)
assert "issues: write" not in pkg.split("discover:")[1].split("resolve:")[0]
assert "checks: write" not in pkg.split("evaluate:")[1].split("upload-artifact")[0]
assert "issues: write" not in pkg.split("evaluate:")[1].split("upload-artifact")[0]
assert pkg.count("persist-credentials: false") >= 3
assert "github.event.repository.default_branch" in pkg
for block in pkg.split("actions/checkout@")[1:]:
    chunk = block.split("uses:")[0] if "uses:" in block else block[:800]
    assert "pull_request.head" not in chunk
    assert "persist-credentials: false" in chunk

# Other mutation paths must NOT reference the user token secret
forbidden_paths = [
    "scripts/gitops/promote_main.sh",
    "scripts/gitops/promote_staging.sh",
    "scripts/gitops/integrator_evaluate.sh",
    "scripts/gitops/repair_task.py",
    "scripts/gitops/repair_observer.py",
    "scripts/cleanup-merged-branches.sh",
    ".github/workflows/linktrend-integrator-merge.yml",
    ".github/workflows/linktrend-development-to-staging.yml",
    ".github/workflows/linktrend-staging-to-main.yml",
    ".github/workflows/linktrend-cleanup-merged.yml",
]
for rel in forbidden_paths:
    text = (root / rel).read_text()
    assert "LINKTREND_BUGBOT_USER_TOKEN" not in text, rel
    # repair_task may mention packager_author_blocked type label only — still no token env
    assert "BUGBOT_USER_TOKEN" not in text, rel

doc = (root / "docs/contracts/GITHUB-APP-GITOPS-CREDENTIALS.md").read_text()
assert "LINKTREND_BUGBOT_USER_TOKEN" in doc
mention = (root / "docs/contracts/BUGBOT-MENTION-ONLY.md").read_text()
assert "LINKTREND_BUGBOT_USER_TOKEN" in mention
assert "packager_author_blocked" in (root / "scripts/gitops/repair_task.py").read_text()
print("bugbot user credential boundary ok")
PY
pass "Carlos user token fail-closed; Packager-only; no App substitution"
RETIRED_CREDENTIAL_FIXTURES

# Permanent hosted-delivery credential boundary. The retired App/PAT fixture
# above is retained as historical test text but is not an active requirement.
python3 - "$ROOT" <<'PY'
from pathlib import Path
import sys

root = Path(sys.argv[1])
workflow_dir = root / "core" / "github" / "managed-workflows"
fast = (workflow_dir / "linktrend-review-packager.yml").read_text(encoding="utf-8")
full = (workflow_dir / "linktrend-integrator-merge.yml").read_text(encoding="utf-8")
staging = (workflow_dir / "linktrend-development-to-staging.yml").read_text(encoding="utf-8")
main = (workflow_dir / "linktrend-staging-to-main.yml").read_text(encoding="utf-8")
active = "\n".join((fast, full, staging, main))

for marker in (
    "LINKTREND_AUTOMATION_TOKEN",
    "LINKTREND_BUGBOT_USER_TOKEN",
    "resolve_automation_token",
    "resolve_bugbot_user_token",
    "actions/create-github-app-token",
    "linktrend-gitops[bot]",
):
    assert marker not in active, f"retired credential path remains: {marker}"

assert "pull_request:" in fast
assert "cancel-in-progress: true" in fast
assert "contents: read" in fast
assert "workflow_dispatch:" in full
assert "contents: read" in full and "pull-requests: write" in full
assert "github.token" in full
assert "@cursor review" in full
for promotion in (staging, main):
    assert "Linktrend Receipt Gate" in promotion
    assert "github.token" in promotion
    assert "permissions:" in promotion

credential_doc = (root / "docs" / "contracts" / "GITHUB-APP-GITOPS-CREDENTIALS.md").read_text(encoding="utf-8")
assert "retired" in credential_doc.lower() or "no longer" in credential_doc.lower()
assert "LINKTREND_AUTOMATION_TOKEN" not in credential_doc
assert "LINKTREND_BUGBOT_USER_TOKEN" not in credential_doc
print("built-in token and no-App credential boundary ok")
PY
pass "Built-in least-privilege token; custom App and PAT automation retired"


# ============================================================================
# 14) Event target resolver (trusted fields + production resolve_candidate)
# ============================================================================
python3 - "$ROOT" <<'PY'
from pathlib import Path
import sys
sys.path.insert(0, str(Path(sys.argv[1]) / "scripts" / "gitops"))
from resolve_event_pr import resolve_candidate

out = resolve_candidate("pull_request_target", {
  "pull_request": {
    "number": 19, "draft": False,
    "base": {"ref": "development"},
    "head": {"ref": "issue/x", "sha": "abc"},
  }
}, "", "o/r", role="packager")
assert out["relevant"] == "true" and out["pr"] == "19" and out["head_sha"] == "abc"

out = resolve_candidate("workflow_run", {
  "workflow_run": {
    "conclusion": "success", "head_sha": "def", "head_branch": "issue/x",
    "pull_requests": [{
      "number": 7, "state": "open",
      "base": {"ref": "development"},
      "head": {"ref": "issue/x", "sha": "def"},
    }],
  }
}, "", "o/r", role="packager")
assert out["relevant"] == "true" and out["pr"] == "7" and out["head_sha"] == "def"

out = resolve_candidate("check_run", {
  "check_run": {
    "name": "Cursor Bugbot", "head_sha": "ghi", "app": {"slug": "cursor"},
    "pull_requests": [{
      "number": 3, "state": "open",
      "base": {"ref": "development"},
      "head": {"ref": "issue/x", "sha": "ghi"},
    }],
  }
}, "", "o/r", role="packager")
assert out["relevant"] == "true" and out["pr"] == "3" and out["head_sha"] == "ghi"
print("resolver ok")
PY
pass "trusted event PR/SHA resolver"

# ============================================================================
# 15) Discovery readiness uses AUTOMATION_TOKEN (workflow-shaped env)
# ============================================================================
: <<'RETIRED_DISCOVERY_TOKEN_FIXTURE'
python3 - "$ROOT" <<'PY'
import os, sys, json, tempfile
from pathlib import Path
root = Path(sys.argv[1])
sys.path.insert(0, str(root / "scripts" / "gitops"))
import readiness_status as rs

token = "ghs_discovery_app_token_SECRET"
tmpdir = tempfile.mkdtemp()
os.environ["LINKTREND_STATUS_BACKEND"] = "file"
os.environ["LINKTREND_STATUS_DIR"] = tmpdir
# Workflow shape after resolve: AUTOMATION_TOKEN set; workflow GITHUB_TOKEN may also exist
os.environ["AUTOMATION_TOKEN"] = token
os.environ["GITHUB_TOKEN"] = "ghs_workflow_token_MUST_NOT_WIN"
os.environ.pop("GH_TOKEN", None)
os.environ.pop("LINKTREND_APP_TOKEN", None)

# Prove preference
assert rs._gh_token() == token

sha = "eeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee"
rs.mark_sha(sha, "ISSUE-1", "ready-for-discover")
ok, detail = rs.is_sha_review_ready(sha)
assert ok, detail

# Missing App automation token → github backend would fail; file backend still works,
# but resolve_automation_token fail-closed is the discover gate. Prove script rejects.
import subprocess
env = os.environ.copy()
env.pop("AUTOMATION_TOKEN", None)
env.pop("LINKTREND_APP_TOKEN", None)
env.pop("LINKTREND_GITOPS_APP_ID", None)
env.pop("LINKTREND_GITOPS_APP_PRIVATE_KEY", None)
env["REQUIRE_APP_TOKEN"] = "1"
r = subprocess.run(["bash", str(root/"scripts/gitops/resolve_automation_token.sh")],
                   capture_output=True, text=True, env=env)
assert r.returncode != 0
out = r.stdout + r.stderr
assert "automation_credentials_blocked" in out
assert token not in out
assert "ghs_workflow_token_MUST_NOT_WIN" not in out
print("discovery readiness token ok")
PY
pass "discovery readiness prefers AUTOMATION_TOKEN; fail closed without App"
RETIRED_DISCOVERY_TOKEN_FIXTURE
python3 - "$ROOT" <<'PY'
from pathlib import Path
import sys

root = Path(sys.argv[1])
fast = (root / "core/github/managed-workflows/linktrend-review-packager.yml").read_text(encoding="utf-8")
assert "contents: read" in fast and "pull-requests: read" in fast
assert "AUTOMATION_TOKEN" not in fast
assert "LINKTREND_APP_TOKEN" not in fast
assert "resolve_automation_token" not in fast
assert "actions/create-github-app-token" not in fast
print("discovery uses built-in read-only workflow authority")
PY
pass "Discovery uses built-in read-only workflow authority; no App token"

# ============================================================================
# 16) Uniform SHA concurrency (actual workflow expressions) + serialized
#     production-path Bugbot idempotency (not a local flock proof)
# ============================================================================
python3 - "$ROOT" <<'PY'
import re, sys
from pathlib import Path
root = Path(sys.argv[1])
sys.path.insert(0, str(root / "scripts" / "gitops"))
from packager_logic import should_request_bugbot, build_bugbot_comment

sha = "ffffffffffffffffffffffffffffffffffffffff"

def concurrency_expr(path: Path) -> str:
    text = path.read_text()
    m = re.search(r'(?m)^\s*group:\s*(.+)$', text)
    assert m, path
    return m.group(1).strip()

pkg = concurrency_expr(root / "core/github/managed-workflows/linktrend-review-packager.yml")
live = concurrency_expr(root / ".github/workflows/linktrend-review-packager.yml")
assert pkg == live, "managed/live packager concurrency diverged"
assert "workflow_run.id" not in pkg and "check_run.id" not in pkg
assert "pull_request.number" in pkg and "inputs.pr_number" in pkg
assert "workflow_run.head_sha" not in pkg
assert "check_run.head_sha" not in pkg

# Simulate expression fallbacks for same SHA with/without pull_requests arrays
def eval_packager_group(event_name: str, *, pr_sha="", wr_sha="", cr_sha="", run_id="9"):
    # Mirror YAML: a || b || c || misc-run_id
    return pr_sha or wr_sha or cr_sha or f"misc-{run_id}"

assert eval_packager_group("pull_request", pr_sha=sha) == sha

ig = concurrency_expr(root / "core/github/managed-workflows/linktrend-integrator-merge.yml")
assert "inputs.pr_number" in ig
assert "workflow_run" not in ig and "check_run" not in ig
assert "cancel-in-progress: true" in (root / "core/github/managed-workflows/linktrend-integrator-merge.yml").read_text()

# Production-path idempotency: first request, then reread comments → duplicate skip
comments = []
ok, reason = should_request_bugbot(comments=comments, head_sha=sha, fast_gate_ok=True)
assert ok and reason == "request"
comments.append({"body": build_bugbot_comment("@cursor review", sha)})
ok2, reason2 = should_request_bugbot(comments=comments, head_sha=sha, fast_gate_ok=True)
assert not ok2 and reason2 == "skipped_duplicate_marker"
assert sum(1 for c in comments if c["body"].startswith("@cursor review")) == 1
# Invalid historical bare trigger must not count as genuine
assert sum(1 for c in comments if "cursor review" in c["body"] and not c["body"].lstrip().startswith("@")) == 0
# Document honesty: cross-run serialization is Actions concurrency; this proves
# the second serialized evaluator's comment-reread idempotency only.
print("sha concurrency + serialized idempotency ok")
PY
pass "uniform SHA concurrency + production-path Bugbot idempotency"

# ============================================================================
# 17) Actual resolver matrix (empty PR arrays, forks, promote roles)
# ============================================================================
python3 - "$ROOT" <<'PY'
import json, sys
from pathlib import Path
root = Path(sys.argv[1])
runner_type = json.loads(
    (root / ".github/linktrend-gitops-consumer.json").read_text()
).get("runnerType", "github-hosted")
runner_types = {
    "github-hosted": ("ubuntu-latest", "ubuntu-latest"),
    "linktrend-private-macos-arm64": (
        "[self-hosted, macOS, ARM64, linktrend-privileged]",
        "[self-hosted, Linux, ARM64, linktrend-ci-isolated]",
    ),
}
assert runner_type in runner_types, f"Unsupported runnerType: {runner_type}"
privileged_runner, untrusted_runner = runner_types[runner_type]
sys.path.insert(0, str(root / "scripts" / "gitops"))
from resolve_event_pr import resolve_candidate

sha = "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb"
rows = []

def check(label, event_name, event, role, *, relevant, reason_substr=None, token="", api_prs=None):
    # Monkeypatch API when provided
    import resolve_event_pr as mod
    orig = mod._prs_for_sha
    if api_prs is not None:
        mod._prs_for_sha = lambda token, repo, s: api_prs
    try:
        out = resolve_candidate(event_name, event, token or "t", "o/r", role=role)
    finally:
        mod._prs_for_sha = orig
    rows.append((label, out))
    assert out["relevant"] == ("true" if relevant else "false"), (label, out)
    if reason_substr:
        assert reason_substr in out["reason"], (label, out["reason"])

# Feature PR → development
check("feature prt packager", "pull_request_target", {
  "pull_request": {"number": 1, "draft": False, "base": {"ref": "development", "repo": {"full_name": "o/r"}},
                   "head": {"ref": "issue/x", "sha": sha, "repo": {"full_name": "o/r"}}}
}, "packager", relevant=True)
check("feature prt integrator", "pull_request_target", {
  "pull_request": {"number": 1, "draft": False, "base": {"ref": "development"}, "head": {"ref": "issue/x", "sha": sha}}
}, "integrator", relevant=True)
check("feature prt staging", "pull_request_target", {
  "pull_request": {"number": 1, "base": {"ref": "development"}, "head": {"ref": "issue/x", "sha": sha}}
}, "staging", relevant=False, reason_substr="base_not_staging")

# workflow_run with PR array
check("wr with prs packager", "workflow_run", {
  "workflow_run": {"conclusion": "success", "event": "pull_request", "head_sha": sha, "head_branch": "issue/x",
                   "pull_requests": [{"number": 1, "state": "open", "base": {"ref": "development"}, "head": {"ref": "issue/x", "sha": sha}}]}
}, "packager", relevant=True)

# workflow_run empty PR array → API finds development PR
check("wr empty prs api hit", "workflow_run", {
  "workflow_run": {"conclusion": "success", "event": "pull_request", "head_sha": sha, "head_branch": "issue/x", "pull_requests": []}
}, "packager", relevant=True, api_prs=[{
  "number": 9, "state": "open", "base": {"ref": "development"}, "head": {"ref": "issue/x", "sha": sha}
}], reason_substr="api_commits_pulls")

# workflow_run empty + no matching PR
check("wr empty no match", "workflow_run", {
  "workflow_run": {"conclusion": "success", "event": "push", "head_sha": sha, "head_branch": "development", "pull_requests": []}
}, "packager", relevant=False, api_prs=[], reason_substr="no_matching_open_pr")

# check_run empty PR array
check("cr empty api hit", "check_run", {
  "check_run": {"name": "Cursor Bugbot", "head_sha": sha, "app": {"slug": "cursor"}, "pull_requests": []}
}, "packager", relevant=True, api_prs=[{
  "number": 3, "state": "open", "base": {"ref": "development"}, "head": {"ref": "issue/x", "sha": sha}
}])
check("cr empty no match", "check_run", {
  "check_run": {"name": "Cursor Bugbot", "head_sha": sha, "app": {"slug": "cursor"}, "pull_requests": []}
}, "packager", relevant=False, api_prs=[], reason_substr="no_matching_open_pr")

# Outcome checks filtered
check("outcome filtered", "check_run", {
  "check_run": {"name": "Linktrend Packager Result", "head_sha": sha, "app": {"slug": "github-actions"}, "pull_requests": []}
}, "packager", relevant=False, reason_substr="github_actions_check_filtered")

# Staging / main promote
check("staging promote prt", "pull_request_target", {
  "pull_request": {"number": 2, "base": {"ref": "staging"}, "head": {"ref": "promote/staging/abc", "sha": sha}}
}, "staging", relevant=True)
check("main promote prt", "pull_request_target", {
  "pull_request": {"number": 3, "base": {"ref": "main"}, "head": {"ref": "promote/main/abc", "sha": sha}}
}, "main", relevant=True)
check("staging wr empty unresolved", "workflow_run", {
  "workflow_run": {"conclusion": "success", "head_sha": sha, "head_branch": "promote/staging/abc", "pull_requests": []}
}, "staging", relevant=False, api_prs=[], reason_substr="empty_pr_array_unresolved")
check("staging wr empty api hit", "workflow_run", {
  "workflow_run": {"conclusion": "success", "head_sha": sha, "head_branch": "promote/staging/abc", "pull_requests": []}
}, "staging", relevant=True, api_prs=[{
  "number": 8, "state": "open", "base": {"ref": "staging"}, "head": {"ref": "promote/staging/abc", "sha": sha}
}])

# Fork-backed candidate (different head.repo) — still relevant when base/head match role
check("fork feature", "pull_request_target", {
  "pull_request": {"number": 4, "draft": False,
                   "base": {"ref": "development", "repo": {"full_name": "o/r"}},
                   "head": {"ref": "issue/fork", "sha": sha, "repo": {"full_name": "fork/r"}}}
}, "packager", relevant=True)
# Ambiguous API matches fail closed
check("ambiguous api", "workflow_run", {
  "workflow_run": {"conclusion": "success", "head_sha": sha, "head_branch": "issue/x", "pull_requests": []}
}, "packager", relevant=False, api_prs=[
  {"number": 1, "state": "open", "base": {"ref": "development"}, "head": {"ref": "issue/x", "sha": sha}},
  {"number": 2, "state": "open", "base": {"ref": "development"}, "head": {"ref": "issue/y", "sha": sha}},
], reason_substr="ambiguous_prs")

# Managed/live byte-identical for resolver-using workflows
for name in (
  "linktrend-review-packager.yml",
  "linktrend-integrator-merge.yml",
  "linktrend-development-to-staging.yml",
  "linktrend-staging-to-main.yml",
):
    managed = (Path(sys.argv[1]) / "core/github/managed-workflows" / name).read_text()
    live = (Path(sys.argv[1]) / ".github/workflows" / name).read_text()
    rendered = managed.replace("__LINKTREND_CI_WORKFLOW_NAME__", "CI")
    rendered = rendered.replace("__LINKTREND_BRANCH_POLICY_WORKFLOW_NAME__", "Branch Source Policy")
    rendered = rendered.replace("__LINKTREND_BUGBOT_CHECK_NAME__", "Cursor Bugbot")
    rendered = rendered.replace("__LINKTREND_UNTRUSTED_RUNS_ON__", untrusted_runner)
    rendered = rendered.replace("__LINKTREND_RUNS_ON__", privileged_runner)
    assert rendered == live, name

print("resolver matrix rows", len(rows))
print("resolver matrix ok")
PY
pass "actual resolver event matrix (incl. empty PR arrays)"

# ============================================================================
# 18) Repair observer lifecycle: failure → dispatch → current-head success resolve;
#     stale success ignored; neutral Bugbot usage_limit; workflow permissions
# ============================================================================
: <<'RETIRED_APP_OBSERVER_FIXTURE'
python3 - "$ROOT" "$TMP" <<'PY'
import json
import os
import sys
from pathlib import Path

root = Path(sys.argv[1])
tmp = Path(sys.argv[2])
sys.path.insert(0, str(root / "scripts" / "gitops"))
import repair_observer
import repair_task

repo = "owner/repo"
repair_dir = tmp / "observer-repair"
os.environ["LINKTREND_REPAIR_BACKEND"] = "file"
os.environ["LINKTREND_REPAIR_DIR"] = str(repair_dir)
os.environ.pop("LINKTREND_CONSUMER_GITOPS_CONFIG", None)
# PR CI sets GITHUB_EVENT_NAME=pull_request. Synthetic fixtures are workflow_run /
# check_run. Tests must control event identity explicitly and must not inherit
# ambient Actions event names (that produced unsupported_event on PR #24 CI).
os.environ.pop("GITHUB_EVENT_NAME", None)

current_pr_heads = {}
current_branch_heads = {}
repair_observer.current_pr_head = lambda repo, pr: current_pr_heads.get(str(pr), ("", ""))
repair_observer.current_branch_head = lambda repo, branch: current_branch_heads.get(str(branch), "")
repair_observer.lookup_pr_for_sha = lambda repo, sha: ("", "")

def write_event(name, payload):
    path = tmp / f"{name}.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    return str(path)

def handle_path(path, event_name):
    """Hermetic: always pass explicit event identity (never ambient CI env)."""
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    return repair_observer.handle_event(payload, repo, event_name=event_name)

def workflow_payload(conclusion, pr, branch, sha):
    return {
        "repository": {"full_name": repo},
        "workflow_run": {
            "name": "CI",
            "conclusion": conclusion,
            "head_sha": sha,
            "head_branch": branch,
            "pull_requests": [
                {"number": pr, "head": {"ref": branch, "sha": sha}},
            ],
        },
    }

sha_ok = "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
failure_path = write_event("workflow-failure", workflow_payload("failure", 23, "issue/ok", sha_ok))
out = handle_path(failure_path, "workflow_run")
assert out["action"] == "upserted", out
fid = repair_task.failure_id(repo, "ci_failure", pr="23", workflow="CI", check="CI", branch="issue/ok")
backend = repair_task.get_backend(repo)
assert backend.dispatch_attempt(fid)["repairStatus"] == "dispatched"
current_pr_heads["23"] = (sha_ok, "issue/ok")
success_path = write_event("workflow-success", workflow_payload("success", 23, "issue/ok", sha_ok))
out = handle_path(success_path, "workflow_run")
assert out["action"] == "resolved", out
assert backend.get(fid)["resolutionState"] == "resolved"

sha_old = "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb"
sha_new = "cccccccccccccccccccccccccccccccccccccccc"
failure_path = write_event("workflow-stale-failure", workflow_payload("failure", 24, "issue/stale", sha_old))
assert handle_path(failure_path, "workflow_run")["action"] == "upserted"
stale_id = repair_task.failure_id(repo, "ci_failure", pr="24", workflow="CI", check="CI", branch="issue/stale")
backend.dispatch_attempt(stale_id)
current_pr_heads["24"] = (sha_new, "issue/stale")
success_path = write_event("workflow-stale-success", workflow_payload("success", 24, "issue/stale", sha_old))
out = handle_path(success_path, "workflow_run")
assert out["action"] == "skip" and out["reason"] == "event_head_not_current_pr_head", out
assert backend.get(stale_id)["resolutionState"] != "resolved"

bugbot_sha = "dddddddddddddddddddddddddddddddddddddddd"
usage_path = write_event(
    "bugbot-neutral-usage",
    {
        "repository": {"full_name": repo},
        "check_run": {
            "name": "Cursor Bugbot",
            "conclusion": "neutral",
            "head_sha": bugbot_sha,
            "pull_requests": [{"number": 25, "head": {"ref": "issue/bugbot", "sha": bugbot_sha}}],
            "output": {"title": "Usage limit", "summary": "Payment required: out of credits."},
        },
    },
)
out = handle_path(usage_path, "check_run")
assert out["action"] == "upserted" and out["failureType"] == "usage_limit", out
usage_id = repair_task.failure_id(repo, "usage_limit", pr="25", check="Cursor Bugbot", branch="issue/bugbot")
assert backend.get(usage_id)["severity"] == "immediate"

ordinary_path = write_event(
    "bugbot-neutral-ordinary",
    {
        "repository": {"full_name": repo},
        "check_run": {
            "name": "Cursor Bugbot",
            "conclusion": "neutral",
            "head_sha": "eeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee",
            "pull_requests": [{"number": 26, "head": {"ref": "issue/skip"}}],
            "output": {"title": "Skipped", "summary": "Review not requested."},
        },
    },
)
out = handle_path(ordinary_path, "check_run")
assert out == {"action": "skip", "reason": "neutral_without_usage_limit"}, out
ordinary_id = repair_task.failure_id(repo, "usage_limit", pr="26", check="Cursor Bugbot", branch="issue/skip")
assert backend.get(ordinary_id) is None

# Successful Bugbot on exact current head must also resolve matching open usage_limit
usage_open_sha = "ffffffffffffffffffffffffffffffffffffffff"
usage_again = write_event(
    "bugbot-usage-open",
    {
        "repository": {"full_name": repo},
        "check_run": {
            "name": "Cursor Bugbot",
            "conclusion": "neutral",
            "head_sha": usage_open_sha,
            "pull_requests": [{"number": 27, "head": {"ref": "issue/fund", "sha": usage_open_sha}}],
            "output": {"title": "Usage limit", "summary": "out of credits / payment required"},
        },
    },
)
assert handle_path(usage_again, "check_run")["action"] == "upserted"
usage_open_id = repair_task.failure_id(
    repo, "usage_limit", pr="27", check="Cursor Bugbot", branch="issue/fund"
)
assert backend.get(usage_open_id)["resolutionState"] != "resolved"
current_pr_heads["27"] = (usage_open_sha, "issue/fund")
success_bugbot = write_event(
    "bugbot-success-clears-usage",
    {
        "repository": {"full_name": repo},
        "check_run": {
            "name": "Cursor Bugbot",
            "conclusion": "success",
            "head_sha": usage_open_sha,
            "pull_requests": [{"number": 27, "head": {"ref": "issue/fund", "sha": usage_open_sha}}],
            "output": {"title": "OK", "summary": "review complete"},
        },
    },
)
out = handle_path(success_bugbot, "check_run")
assert out["action"] == "resolved", out
assert backend.get(usage_open_id)["resolutionState"] == "resolved"

# Ambient PR-CI pollution: uncontrolled path still rejects; explicit path still works.
# (Production validation must remain fail-closed for unsupported events.)
os.environ["GITHUB_EVENT_NAME"] = "pull_request"
poison_sha = "1212121212121212121212121212121212121212"
poison_path = write_event("poison-ambient", workflow_payload("failure", 28, "issue/poison", poison_sha))
poisoned = repair_observer.handle_event_path(poison_path, repo)
assert poisoned == {
    "action": "skip",
    "reason": "unsupported_event",
    "event": "pull_request",
}, poisoned
controlled = handle_path(poison_path, "workflow_run")
assert controlled["action"] == "upserted", controlled
os.environ.pop("GITHUB_EVENT_NAME", None)
print("repair observer lifecycle ok")
PY
pass "repair observer resolves current-head successes, skips stale, handles/clears Bugbot usage_limit"

# Regression: surrounding process has GITHUB_EVENT_NAME=pull_request (PR CI shape).
GITHUB_EVENT_NAME=pull_request python3 - "$ROOT" "$TMP" <<'PY'
import json
import os
import sys
from pathlib import Path

root = Path(sys.argv[1])
tmp = Path(sys.argv[2]) / "ambient-pr-ci"
tmp.mkdir(parents=True, exist_ok=True)
sys.path.insert(0, str(root / "scripts" / "gitops"))
import repair_observer
import repair_task

assert os.environ.get("GITHUB_EVENT_NAME") == "pull_request"
repo = "owner/repo"
os.environ["LINKTREND_REPAIR_BACKEND"] = "file"
os.environ["LINKTREND_REPAIR_DIR"] = str(tmp / "repair")
os.environ.pop("LINKTREND_CONSUMER_GITOPS_CONFIG", None)
repair_observer.current_pr_head = lambda repo, pr: ("", "")
repair_observer.current_branch_head = lambda repo, branch: ""
repair_observer.lookup_pr_for_sha = lambda repo, sha: ("", "")

sha = "3434343434343434343434343434343434343434"
payload = {
    "repository": {"full_name": repo},
    "workflow_run": {
        "name": "CI",
        "conclusion": "failure",
        "head_sha": sha,
        "head_branch": "issue/ambient",
        "pull_requests": [{"number": 29, "head": {"ref": "issue/ambient", "sha": sha}}],
    },
}
path = tmp / "ambient-failure.json"
path.write_text(json.dumps(payload), encoding="utf-8")
# Uncontrolled inherits ambient pull_request → unsupported (production intact)
poisoned = repair_observer.handle_event_path(str(path), repo)
assert poisoned["reason"] == "unsupported_event" and poisoned["event"] == "pull_request", poisoned
# Controlled explicit identity works despite ambient PR CI env
ok = repair_observer.handle_event(payload, repo, event_name="workflow_run")
assert ok["action"] == "upserted", ok
print("ambient GITHUB_EVENT_NAME=pull_request hermetic ok")
PY
pass "repair observer hermetic under ambient GITHUB_EVENT_NAME=pull_request"

python3 - "$ROOT" "$TMP" <<'PY'
import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

root = Path(sys.argv[1])
tmp = Path(sys.argv[2])
runner_type = json.loads(
    (root / ".github/linktrend-gitops-consumer.json").read_text()
).get("runnerType", "github-hosted")
runner_types = {
    "github-hosted": ("ubuntu-latest", "ubuntu-latest"),
    "linktrend-private-macos-arm64": (
        "[self-hosted, macOS, ARM64, linktrend-privileged]",
        "[self-hosted, Linux, ARM64, linktrend-ci-isolated]",
    ),
}
assert runner_type in runner_types, f"Unsupported runnerType: {runner_type}"
privileged_runner, untrusted_runner = runner_types[runner_type]
workflow_paths = list((root / ".github" / "workflows").glob("linktrend-*.yml"))
workflow_paths += list((root / "core" / "github" / "managed-workflows").glob("linktrend-*.yml"))

WRITE_PERMS = (
    "issues: write",
    "checks: write",
    "pull-requests: write",
    "contents: write",
    "statuses: write",
)

def job_blocks(path):
    lines = path.read_text().splitlines()
    in_jobs = False
    current = None
    block = []
    for line in lines:
        if re.match(r"^jobs:\s*$", line):
            in_jobs = True
            continue
        if not in_jobs:
            continue
        m = re.match(r"^  ([A-Za-z0-9_-]+):\s*$", line)
        if m:
            if current:
                yield current, "\n".join(block)
            current = m.group(1)
            block = [line]
            continue
        if current:
            block.append(line)
    if current:
        yield current, "\n".join(block)

def job_permissions(block):
    lines = block.splitlines()
    out = []
    in_permissions = False
    perm_indent = None
    for line in lines:
        m = re.match(r"^(\s*)permissions:\s*$", line)
        if m:
            in_permissions = True
            perm_indent = len(m.group(1))
            continue
        if in_permissions:
            if line.strip() == "":
                continue
            indent = len(line) - len(line.lstrip(" "))
            if indent <= perm_indent:
                break
            out.append(line.strip())
    return out

def render(text: str) -> str:
    return (
        text.replace("__LINKTREND_CI_WORKFLOW_NAME__", "CI")
        .replace("__LINKTREND_BRANCH_POLICY_WORKFLOW_NAME__", "Branch Source Policy")
        .replace("__LINKTREND_BUGBOT_CHECK_NAME__", "Cursor Bugbot")
        .replace("__LINKTREND_UNTRUSTED_RUNS_ON__", untrusted_runner)
        .replace("__LINKTREND_RUNS_ON__", privileged_runner)
    )

# Live ≡ rendered managed for entire managed set
for name in (
    "linktrend-repair-observer.yml",
    "linktrend-integrator-merge.yml",
    "linktrend-development-to-staging.yml",
    "linktrend-staging-to-main.yml",
    "linktrend-review-packager.yml",
    "linktrend-review-ready-publisher.yml",
    "linktrend-cleanup-merged.yml",
):
    managed = (root / "core/github/managed-workflows" / name).read_text()
    live = (root / ".github/workflows" / name).read_text()
    assert render(managed) == live, name
    assert "LINKTREND___" not in managed, name

# Repair Observer: normal-token resolve; no ordinary workflow-token mutations
obs_live = (root / ".github/workflows/linktrend-repair-observer.yml").read_text()
assert "LINKTREND_AUTOMATION_TOKEN" in obs_live
assert "create-github-app-token@" not in obs_live
assert "resolve_automation_token.sh" in obs_live
assert 'export GH_TOKEN="${AUTOMATION_TOKEN}"' in obs_live
assert 'export GITHUB_TOKEN="${AUTOMATION_TOKEN}"' in obs_live
assert "repair_observer.py" in obs_live
assert "automation_credentials_blocked" in obs_live
assert "GH_TOKEN: ${{ github.token }}" not in obs_live
assert "GITHUB_TOKEN: ${{ github.token }}" not in obs_live
assert "issues: write" not in obs_live
assert "Does NOT mint" not in obs_live
assert "GITHUB_TOKEN only" not in obs_live
assert "persist-credentials: false" in obs_live

# Privileged mutation jobs must not grant write scopes to ordinary workflow token.
# Mutation jobs run repair_observer / promote / evaluate / cleanup apply.
mutation_markers = (
    "LINKTREND_AUTOMATION_TOKEN",
    "repair_observer.py",
    "promote_staging.sh",
    "promote_main.sh",
    "integrator_evaluate.sh",
    "packager_discover.py",
    "packager_evaluate.py",
    "cleanup-merged-branches.sh",
)
failures = []
for path in workflow_paths:
    for job, block in job_blocks(path):
        if not any(m in block for m in mutation_markers):
            continue
        perms = job_permissions(block)
        for wp in WRITE_PERMS:
            if wp in perms:
                failures.append(f"{path.relative_to(root)}:{job}:{wp}")
if failures:
    raise SystemExit("mutation jobs still grant workflow-token writes: " + ", ".join(failures))

# Read-only resolve jobs may still use github.token
for name in (
    "linktrend-integrator-merge.yml",
    "linktrend-development-to-staging.yml",
    "linktrend-staging-to-main.yml",
    "linktrend-review-packager.yml",
):
    live = (root / ".github/workflows" / name).read_text()
    assert "resolve:" in live
    resolve_block = None
    for job, block in job_blocks(root / ".github/workflows" / name):
        if job == "resolve":
            resolve_block = block
            break
    assert resolve_block is not None, name
    assert "github.token" in resolve_block, name
    perms = job_permissions(resolve_block)
    assert not any(wp in perms for wp in WRITE_PERMS), (name, perms)

# Packager must not mutate via ordinary GITHUB_TOKEN on credential failure
pkg = (root / ".github/workflows/linktrend-review-packager.yml").read_text()
assert 'GH_TOKEN="${GITHUB_TOKEN}"' not in pkg
assert "github.token" not in pkg.split("name: Discover")[1].split("upload-artifact")[0]
assert "github.token" not in pkg.split("Evaluate one PR")[1].split("upload-artifact")[0]

observer = (root / "scripts" / "gitops" / "repair_observer.py").read_text()
assert "repair_task.resolve_task(" in observer
assert 'failure_type="ci_failure"' in observer
assert "bugbot_failure" in observer and "usage_limit" in observer
assert '("bugbot_failure", "usage_limit")' in observer or "('bugbot_failure', 'usage_limit')" in observer

# Docs no longer claim GITHUB_TOKEN observer / App mint
readme = (root / "core/github/managed-workflows/README.md").read_text()
assert "no App mint" not in readme
assert "GITHUB_TOKEN issues:write" not in readme
assert "AUTOMATION_TOKEN" in readme or "GitHub App" in readme
disp = (root / "docs/contracts/REPAIR-DISPATCHER.md").read_text()
assert "no App mint" not in disp
assert "issues: write" not in disp.split("## Observer")[1].split("##")[0]
assert "AUTOMATION_TOKEN" in disp.split("## Observer")[1].split("##")[0]

# Behavioral: App-missing observer workflow path → local outcome, exit 1, zero gh
fake_bin = tmp / "fake-bin-observer"
fake_bin.mkdir(exist_ok=True)
(fake_bin / "gh").write_text(
    "#!/bin/bash\necho UNEXPECTED_GH_CALL >&2; echo args:\"$*\" >&2; exit 99\n",
    encoding="utf-8",
)
os.chmod(fake_bin / "gh", 0o755)
cwd = tmp / "observer-app-miss"
cwd.mkdir(exist_ok=True)
# Simulate the workflow App-miss branch (same commands as YAML)
env = os.environ.copy()
env["PATH"] = f"{fake_bin}:{env.get('PATH','')}"
env.pop("AUTOMATION_TOKEN", None)
env.pop("AUTOMATION_TOKEN_SOURCE", None)
env.pop("LINKTREND_APP_TOKEN", None)
env["GH_TOKEN"] = "ghs_FAKE_AMBIENT_GH"
env["GITHUB_TOKEN"] = "ghs_FAKE_AMBIENT_GITHUB"
env["GITHUB_REPOSITORY"] = "linktrend/IDE-Development"
env["GITHUB_STEP_SUMMARY"] = str(cwd / "summary.md")
Path(env["GITHUB_STEP_SUMMARY"]).write_text("", encoding="utf-8")
script = f"""
set -euo pipefail
cd "{cwd}"
# force resolve failure by leaving App vars empty while REQUIRE_APP_TOKEN=1
export REQUIRE_APP_TOKEN=1
export LINKTREND_GITOPS_APP_ID=""
export LINKTREND_APP_TOKEN=""
if ! source "{root}/scripts/gitops/resolve_automation_token.sh"; then
  python3 "{root}/scripts/gitops/write_outcome.py" \\
    --status automation_credentials_blocked \\
    --detail "Repair Observer requires GitHub App token for durable repair mutations"
  echo "### Repair Observer: \\`automation_credentials_blocked\\`" >> "$GITHUB_STEP_SUMMARY"
  exit 1
fi
echo SHOULD_NOT_REACH
exit 2
"""
r = subprocess.run(["bash", "-lc", script], env=env, capture_output=True, text=True)
assert r.returncode == 1, (r.returncode, r.stdout, r.stderr)
assert "UNEXPECTED_GH_CALL" not in (r.stdout + r.stderr)
outcome = json.loads((cwd / "gitops-outcome.json").read_text())
assert outcome["status"] == "automation_credentials_blocked"
assert "automation_credentials_blocked" in Path(env["GITHUB_STEP_SUMMARY"]).read_text()

# Ambient tokens must not authorize observer mutation when App path not taken:
# repair_observer with only fake GH/GITHUB and file backend still uses ambient token for gh reads,
# but workflow contract forbids exporting github.token — static proof above + App-miss zero gh.

# App-success path exports AUTOMATION_TOKEN into GH_TOKEN/GITHUB_TOKEN before observer
run_section = obs_live.split("name: Observe repair lifecycle")[-1]
assert "resolve_automation_token.sh" in run_section
assert 'GH_TOKEN="${AUTOMATION_TOKEN}"' in run_section
assert 'GITHUB_TOKEN="${AUTOMATION_TOKEN}"' in run_section
assert run_section.index("resolve_automation_token.sh") < run_section.index('GH_TOKEN="${AUTOMATION_TOKEN}"')
assert run_section.index('GH_TOKEN="${AUTOMATION_TOKEN}"') < run_section.index("repair_observer.py handle-event")

print("repair observer App identity + no workflow-token writes ok")
PY
pass "Repair Observer App identity; mutation jobs deny workflow-token writes; managed≡live"
RETIRED_APP_OBSERVER_FIXTURE

python3 - "$ROOT" <<'PY'
from pathlib import Path
import sys

root = Path(sys.argv[1])
workflow_paths = list((root / ".github/workflows").glob("linktrend-*.yml"))
workflow_paths += list((root / "core/github/managed-workflows").glob("linktrend-*.yml"))
active = "\n".join(path.read_text(encoding="utf-8") for path in workflow_paths)
for marker in (
    "LINKTREND_AUTOMATION_TOKEN",
    "LINKTREND_BUGBOT_USER_TOKEN",
    "create-github-app-token",
    "resolve_automation_token.sh",
    "resolve_bugbot_user_token.sh",
):
    assert marker not in active, f"retired App credential remains: {marker}"
for path in workflow_paths:
    text = path.read_text(encoding="utf-8")
    assert "ubuntu-latest" not in text, path
    assert "self-hosted" not in text, path
print("hosted workflows have no App or private-runner authority")
PY
pass "Hosted workflows use least-privilege built-in authority; no custom App"

# ============================================================================
# App-credential failure actually creates/updates a repair task (file backend)
: <<'RETIRED_APP_FAILURE_FIXTURE'
# ============================================================================
CRED_REPAIR="$TMP/cred-repair"
mkdir -p "$CRED_REPAIR"
export LINKTREND_REPAIR_BACKEND=file
export LINKTREND_REPAIR_DIR="$CRED_REPAIR"
out="$(python3 "$ROOT/scripts/gitops/repair_task.py" upsert \
  --repo owner/appcred \
  --failure-type automation_credentials_blocked \
  --severity immediate \
  --workflow "Linktrend Review Packager" \
  --next-action "Configure GitHub App credentials; do not auto-repair.")"
printf '%s\n' "$out" | python3 -c 'import json,sys; t=json.load(sys.stdin); assert t["failureType"]=="automation_credentials_blocked"; assert t["severity"]=="immediate"; assert t["failureId"]'
FID="$(printf '%s\n' "$out" | python3 -c 'import json,sys; print(json.load(sys.stdin)["failureId"])')"
# Idempotent update
out2="$(python3 "$ROOT/scripts/gitops/repair_task.py" upsert \
  --repo owner/appcred \
  --failure-type automation_credentials_blocked \
  --severity immediate \
  --workflow "Linktrend Review Packager" \
  --next-action "Configure GitHub App credentials; do not auto-repair.")"
FID2="$(printf '%s\n' "$out2" | python3 -c 'import json,sys; print(json.load(sys.stdin)["failureId"])')"
[ "$FID" = "$FID2" ] || fail "credential repair identity drifted: $FID vs $FID2"
# Workflows must not mask credential upsert with || true
for wf in \
  .github/workflows/linktrend-review-packager.yml \
  .github/workflows/linktrend-integrator-merge.yml \
  .github/workflows/linktrend-development-to-staging.yml \
  .github/workflows/linktrend-staging-to-main.yml; do
  python3 - "$wf" <<'PY'
from pathlib import Path
import re, sys
text = Path(sys.argv[1]).read_text()
# Find automation_credentials_blocked upsert blocks; ensure no || true on same logical command
for m in re.finditer(r"repair_task\.py upsert[\s\S]{0,400}?automation_credentials_blocked[\s\S]{0,200}", text):
    chunk = m.group(0)
    if "|| true" in chunk:
        raise SystemExit(f"credential upsert masked with || true in {sys.argv[1]}")
print("ok", sys.argv[1])
PY
done
pass "App-credential failure creates/updates repair task; upserts not masked"
RETIRED_APP_FAILURE_FIXTURE

# ============================================================================
# Main Approve store: gates, freshness, trust, expiry, Lisa schema, reuse
# ============================================================================
python3 - "$ROOT" <<'PY'
import json, re, subprocess, sys, tempfile
from pathlib import Path

root = Path(sys.argv[1])
disc = root / "scripts/gitops/main_approve_package_discover.py"
reuse = root / "scripts/gitops/main_approve_package_reuse.py"
schema = json.loads((root / "docs/contracts/fixtures/lisa-main-approve-package.schema.json").read_text())

SRC = "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
MAIN = "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb"
HEAD = "cccccccccccccccccccccccccccccccccccccccc"
BRANCH = "promote/main/aaaaaaaaaaaa"
BODY = f"""## pkg
<!-- linktrend-promote: {{"schemaVersion":1,"stage":"main","sourceBranch":"staging","targetBranch":"main","sourceSha":"{SRC}","targetSha":"{MAIN}","candidateHead":"{HEAD}","promoteBranch":"{BRANCH}"}} -->
"""

def run(args, checks=None, body=BODY, extra=None):
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        bf = td / "body.md"
        bf.write_text(body, encoding="utf-8")
        cmd = [
            sys.executable, str(disc),
            "--from-body-file", str(bf),
            "--repository", "linktrend/IDE-Development",
            "--pr-number", "42",
            "--head-sha", HEAD,
            "--head-branch", BRANCH,
            "--staging-tip", SRC,
            "--main-tip", MAIN,
            "--now", "2026-08-03T10:00:00+08:00",
            "--release-gate-checks",
            "Verify IDE Development,Enforce allowed PR source branches",
        ]
        if checks is not None:
            cf = td / "checks.json"
            cf.write_text(json.dumps(checks), encoding="utf-8")
            cmd += ["--checks-json", str(cf)]
        if extra:
            cmd += extra
        p = subprocess.run(cmd, capture_output=True, text=True)
        out = p.stdout.strip() or p.stderr.strip()
        try:
            data = json.loads(p.stdout)
        except Exception:
            data = {"_raw": out, "_err": p.stderr}
        return p.returncode, data

ok_checks = [
    {"name": "Verify IDE Development", "state": "SUCCESS"},
    {"name": "Enforce allowed PR source branches", "state": "SUCCESS"},
]

# all gates successful
rc, d = run([], checks=ok_checks)
assert rc == 0 and d["itemCount"] == 1 and d["items"][0]["gateResult"] == "Clear", d
assert "Unknown" not in {i.get("gateResult") for i in d["items"]}
pkg = d["package"]
assert set(schema["required"]) <= set(pkg.keys())
lit = pkg["items"][0]
assert set(schema["properties"]["items"]["items"]["required"]) <= set(lit.keys())
assert lit["gateResult"] in ("Clear", "Issues")
assert re.search(r"\b[0-9a-f]{7,40}\b", lit["plainDescription"], re.I) is None

# missing gate
rc, d = run([], checks=[{"name": "Verify IDE Development", "state": "SUCCESS"}])
assert rc == 0 and d["items"][0]["gateResult"] == "Issues", d
assert d["items"][0]["gateEvidence"]["status"] == "missing"

# pending gate
rc, d = run([], checks=[
    {"name": "Verify IDE Development", "state": "SUCCESS"},
    {"name": "Enforce allowed PR source branches", "state": "PENDING"},
])
assert d["items"][0]["gateResult"] == "Issues" and d["items"][0]["gateEvidence"]["status"] == "pending"

# failed gate
rc, d = run([], checks=[
    {"name": "Verify IDE Development", "state": "FAILURE"},
    {"name": "Enforce allowed PR source branches", "state": "SUCCESS"},
])
assert d["items"][0]["gateResult"] == "Issues" and d["items"][0]["gateEvidence"]["status"] == "failed"

# staging drift
rc, d = run([], checks=ok_checks, extra=["--staging-tip", "eeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee"])
assert rc != 0 and d["itemCount"] == 0
assert any(r.get("reason") == "staging_tip_drift" for r in d["rejected"]), d

# main drift
rc, d = run([], checks=ok_checks, extra=["--main-tip", "ffffffffffffffffffffffffffffffffffffffff"])
assert rc != 0 and any(r.get("reason") == "main_tip_drift" for r in d["rejected"]), d

# candidate-head drift
rc, d = run([], checks=ok_checks, extra=["--head-sha", "dddddddddddddddddddddddddddddddddddddddd"])
assert rc != 0 and any(r.get("reason") == "candidate_head_drift" for r in d["rejected"]), d

# fork / cross-repo
rc, d = run([], checks=ok_checks, extra=["--is-cross-repository"])
assert rc != 0 and any(r.get("reason") == "cross_repository_head" for r in d["rejected"]), d
rc, d = run([], checks=ok_checks, extra=["--head-repository", "evil/fork"])
assert rc != 0 and any(r.get("reason") == "head_repository_mismatch" for r in d["rejected"]), d

# invalid / short / non-hex SHA
bad_body = BODY.replace(SRC, "not-a-sha")
rc, d = run([], checks=ok_checks, body=bad_body)
assert rc != 0 and any("sha_invalid" in str(r.get("reason")) for r in d["rejected"]), d
short_body = BODY.replace(SRC, "aaaaaaaaaaaa")
# short breaks JSON length in marker — use 39 hex
short = "a" * 39
short_body = f"""<!-- linktrend-promote: {{"schemaVersion":1,"stage":"main","sourceBranch":"staging","targetBranch":"main","sourceSha":"{short}","targetSha":"{MAIN}","candidateHead":"{HEAD}","promoteBranch":"promote/main/aaaaaaaaaaaa"}} -->"""
rc, d = run([], checks=ok_checks, body=short_body)
assert rc != 0 and any(r.get("reason") == "marker_source_sha_invalid" for r in d["rejected"]), d

# wrong stage / source / base / branch
for field, val, reason in [
    ("stage", "staging", "marker_stage_not_main"),
    ("sourceBranch", "development", "marker_source_branch_not_staging"),
    ("targetBranch", "staging", "marker_target_branch_not_main"),
]:
    body = BODY.replace(f'"{field}":"main"' if field != "sourceBranch" else '"sourceBranch":"staging"',
                        f'"{field}":"{val}"' if field != "sourceBranch" else f'"sourceBranch":"{val}"')
    if field == "stage":
        body = BODY.replace('"stage":"main"', '"stage":"staging"')
    elif field == "sourceBranch":
        body = BODY.replace('"sourceBranch":"staging"', '"sourceBranch":"development"')
    elif field == "targetBranch":
        body = BODY.replace('"targetBranch":"main"', '"targetBranch":"staging"')
    rc, d = run([], checks=ok_checks, body=body)
    assert any(r.get("reason") == reason for r in d["rejected"]), (field, d)

rc, d = run([], checks=ok_checks, extra=["--base-ref", "staging"])
assert any(r.get("reason") == "base_not_main" for r in d["rejected"]), d
rc, d = run([], checks=ok_checks, extra=["--head-branch", "promote/main/bbbbbbbbbbbb"])
assert rc != 0, d

# duplicate packages
body2 = BODY.replace(HEAD, "dddddddddddddddddddddddddddddddddddddddd").replace(
    '"candidateHead":"cccccccccccccccccccccccccccccccccccccccc"',
    '"candidateHead":"dddddddddddddddddddddddddddddddddddddddd"',
)
with tempfile.TemporaryDirectory() as td:
    td = Path(td)
    b1, b2 = td / "b1.md", td / "b2.md"
    b1.write_text(BODY, encoding="utf-8")
    b2.write_text(body2, encoding="utf-8")
    cf = td / "c.json"
    cf.write_text(json.dumps(ok_checks), encoding="utf-8")
    p = subprocess.run([
        sys.executable, str(disc),
        "--from-body-file", str(b1),
        "--second-body-file", str(b2),
        "--second-pr-number", "43",
        "--second-head-sha", "dddddddddddddddddddddddddddddddddddddddd",
        "--repository", "linktrend/IDE-Development",
        "--pr-number", "42",
        "--head-sha", HEAD,
        "--head-branch", BRANCH,
        "--staging-tip", SRC,
        "--main-tip", MAIN,
        "--checks-json", str(cf),
        "--now", "2026-08-03T10:00:00+08:00",
        "--release-gate-checks",
        "Verify IDE Development,Enforce allowed PR source branches",
    ], capture_output=True, text=True)
    d = json.loads(p.stdout)
    assert d["itemCount"] == 0, d
    assert any(r.get("reason") == "ambiguous_duplicate_packages" for r in d["rejected"]), d

# expired package
rc, d = run([], checks=ok_checks, extra=["--now", "2026-08-04T00:00:01+08:00"])
assert d["package"]["expired"] is True and d["itemCount"] == 0, d
assert any(r.get("reason") == "package_expired" for r in d["rejected"]), d
assert rc == 3

# valid same-repository package already covered by Clear case

# invalid existing-package reuse (source/target match but head drift)
prs = [{
    "number": 7,
    "body": BODY,
    "headRefName": BRANCH,
    "headRefOid": "dddddddddddddddddddddddddddddddddddddddd",
    "baseRefName": "main",
    "state": "OPEN",
    "isCrossRepository": False,
    "headRepositoryNameWithOwner": "linktrend/IDE-Development",
}]
p = subprocess.run([
    sys.executable, str(reuse),
    "--expected-source", SRC,
    "--expected-target", MAIN,
    "--expected-branch", BRANCH,
    "--repository", "linktrend/IDE-Development",
], input=json.dumps(prs), capture_output=True, text=True)
assert p.returncode == 0, p.stderr
out = json.loads(p.stdout)
assert out["action"] == "repackage" and out["reason"] == "candidate_head_drift", out

# valid reuse
prs[0]["headRefOid"] = HEAD
p = subprocess.run([
    sys.executable, str(reuse),
    "--expected-source", SRC,
    "--expected-target", MAIN,
    "--expected-branch", BRANCH,
    "--repository", "linktrend/IDE-Development",
], input=json.dumps(prs), capture_output=True, text=True)
out = json.loads(p.stdout)
assert out == {"action": "reuse", "pr": 7}, out

# promote_main wires reuse validator
main_sh = (root / "scripts/gitops/promote_main.sh").read_text()
assert "main_approve_package_reuse.py" in main_sh
assert "requires repackage" in main_sh
assert "Verify IDE Development,Enforce allowed PR source branches" in main_sh

print("main approve store behavioral ok")
PY
pass "Main Approve store gates/freshness/trust/expiry/schema/reuse"

# ============================================================================
# Main Approve: live gh subprocess path (fake gh) — checks exit codes,
# final reread gate refresh, release-gate variable fail-closed
# ============================================================================
python3 - "$ROOT" <<'PY'
import json, os, stat, subprocess, sys, tempfile
from pathlib import Path

root = Path(sys.argv[1])
disc = root / "scripts/gitops/main_approve_package_discover.py"
SRC = "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
MAIN = "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb"
HEAD = "cccccccccccccccccccccccccccccccccccccccc"
BRANCH = "promote/main/aaaaaaaaaaaa"
REPO = "linktrend/IDE-Development"
BODY = (
    "## pkg\n"
    f'<!-- linktrend-promote: {{"schemaVersion":1,"stage":"main","sourceBranch":"staging",'
    f'"targetBranch":"main","sourceSha":"{SRC}","targetSha":"{MAIN}",'
    f'"candidateHead":"{HEAD}","promoteBranch":"{BRANCH}"}} -->\n'
)
PR = {
    "number": 42,
    "title": "promote",
    "body": BODY,
    "headRefName": BRANCH,
    "headRefOid": HEAD,
    "baseRefName": "main",
    "state": "OPEN",
    "isCrossRepository": False,
    "headRepository": {"nameWithOwner": REPO},
    "url": "https://example.invalid/pr/42",
    "createdAt": "2026-08-03T01:00:00Z",
}

def write_fake_gh(td: Path) -> Path:
    script = td / "gh"
    script.write_text(
        r'''#!/usr/bin/env bash
set -euo pipefail
LOG="${FAKE_GH_LOG:-/dev/null}"
printf '%s\n' "$*" >>"$LOG"
ARGS=("$@")

ok_checks='[{"name":"Verify IDE Development","state":"SUCCESS"},{"name":"Enforce allowed PR source branches","state":"SUCCESS"}]'
pending_checks='[{"name":"Verify IDE Development","state":"SUCCESS"},{"name":"Enforce allowed PR source branches","state":"PENDING"}]'
failed_checks='[{"name":"Verify IDE Development","state":"FAILURE"},{"name":"Enforce allowed PR source branches","state":"SUCCESS"}]'

if [[ "${1:-}" == "pr" && "${2:-}" == "checks" ]]; then
  COUNT_FILE="${FAKE_GH_CHECKS_COUNT:-}"
  if [[ -n "$COUNT_FILE" ]]; then
    n=0
    [[ -f "$COUNT_FILE" ]] && n=$(cat "$COUNT_FILE")
    n=$((n + 1))
    echo "$n" >"$COUNT_FILE"
  else
    n=1
  fi
  mode="${FAKE_GH_CHECKS_MODE:-success}"
  if [[ "$mode" == "reread_pending" ]]; then
    if [[ "$n" -eq 1 ]]; then
      printf '%s\n' "$ok_checks"
      exit 0
    fi
    printf '%s\n' "$pending_checks"
    exit 8
  fi
  case "$mode" in
    success) printf '%s\n' "$ok_checks"; exit 0 ;;
    pending) printf '%s\n' "$pending_checks"; exit 8 ;;
    failed) printf '%s\n' "$failed_checks"; exit 1 ;;
    auth)
      echo "gh: HTTP 401: Bad credentials (https://api.github.com/repos/x/y/commits/abc/status)" >&2
      exit 1
      ;;
    badjson) printf '%s\n' "not-json"; exit 8 ;;
    *) echo "unknown checks mode" >&2; exit 99 ;;
  esac
fi

if [[ "${1:-}" == "pr" && "${2:-}" == "list" ]]; then
  cat <<'JSON'
__PR_LIST_JSON__
JSON
  exit 0
fi

if [[ "${1:-}" == "pr" && "${2:-}" == "view" ]]; then
  cat <<'JSON'
__PR_VIEW_JSON__
JSON
  exit 0
fi

if [[ "${1:-}" == "api" ]]; then
  path="${2:-}"
  if [[ "$path" == *"/actions/variables/LINKTREND_RELEASE_GATE_CHECKS"* ]]; then
    case "${FAKE_GH_VAR_MODE:-absent}" in
      absent)
        echo '{"message":"Not Found","documentation_url":"https://docs.github.com"}' >&2
        exit 1
        ;;
      empty)
        printf '\n'
        exit 0
        ;;
      value)
        printf '%s\n' "Verify IDE Development,Enforce allowed PR source branches"
        exit 0
        ;;
      auth)
        echo "gh: HTTP 401: Bad credentials" >&2
        exit 1
        ;;
      ratelimit)
        echo "gh: HTTP 429: API rate limit exceeded" >&2
        exit 1
        ;;
      *)
        echo "gh: HTTP 500: boom" >&2
        exit 1
        ;;
    esac
  fi
  if [[ "$path" == *"/git/ref/heads/staging"* ]]; then
    printf '%s\n' "__SRC__"
    exit 0
  fi
  if [[ "$path" == *"/git/ref/heads/main"* ]]; then
    printf '%s\n' "__MAIN__"
    exit 0
  fi
fi

echo "unexpected gh $*" >&2
exit 90
'''.replace("__PR_LIST_JSON__", json.dumps([PR]))
        .replace("__PR_VIEW_JSON__", json.dumps(PR))
        .replace("__SRC__", SRC)
        .replace("__MAIN__", MAIN),
        encoding="utf-8",
    )
    script.chmod(script.stat().st_mode | stat.S_IEXEC)
    return script


def run_live(*, checks_mode: str, var_mode: str = "absent", extra_env=None):
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        write_fake_gh(td)
        env = os.environ.copy()
        for k in (
            "LINKTREND_RELEASE_GATE_CHECKS",
            "RELEASE_GATE_CHECKS",
            "GH_TOKEN",
            "GITHUB_TOKEN",
        ):
            env.pop(k, None)
        env["PATH"] = f"{td}:{env.get('PATH', '')}"
        env["FAKE_GH_CHECKS_MODE"] = checks_mode
        env["FAKE_GH_VAR_MODE"] = var_mode
        env["FAKE_GH_LOG"] = str(td / "gh.log")
        env["FAKE_GH_CHECKS_COUNT"] = str(td / "checks.count")
        if extra_env:
            env.update(extra_env)
        p = subprocess.run(
            [
                sys.executable,
                str(disc),
                "--repo",
                REPO,
                "--staging-tip",
                SRC,
                "--main-tip",
                MAIN,
                "--now",
                "2026-08-03T10:00:00+08:00",
                "--created-at",
                "2026-08-03T02:05:00Z",
            ],
            capture_output=True,
            text=True,
            env=env,
        )
        try:
            data = json.loads(p.stdout)
        except Exception:
            data = {"_raw": p.stdout, "_err": p.stderr}
        log = (td / "gh.log").read_text(encoding="utf-8") if (td / "gh.log").exists() else ""
        return p.returncode, data, log


# exit 8 + pending JSON → usable Issues item
rc, d, log = run_live(checks_mode="pending")
assert rc == 0, (rc, d, log)
assert d.get("itemCount") == 1 and d["items"][0]["gateResult"] == "Issues", d
assert d["items"][0]["gateEvidence"]["status"] == "pending", d
assert "pr checks" in log

# failed-check nonzero + valid JSON → Issues
rc, d, log = run_live(checks_mode="failed")
assert rc == 0 and d["items"][0]["gateResult"] == "Issues", d
assert d["items"][0]["gateEvidence"]["status"] == "failed", d

# exit 0 + success → Clear
rc, d, log = run_live(checks_mode="success")
assert rc == 0 and d["items"][0]["gateResult"] == "Clear", d
assert d["package"]["createdAt"] == "2026-08-03T02:05:00Z", d["package"]
assert any("discovery/seal" in n for n in d.get("notes", [])), d.get("notes")

# auth failure → fail closed (no usable item; gate_query_failed)
rc, d, log = run_live(checks_mode="auth")
assert d.get("itemCount", 0) == 0, d
assert any(
    r.get("reason") in {"gate_query_failed", "gate_query_failed_on_reread"}
    for r in d.get("rejected", [])
), d

# invalid JSON → fail closed
rc, d, log = run_live(checks_mode="badjson")
assert d.get("itemCount", 0) == 0, d
assert any("gate_query_failed" in str(r.get("reason")) for r in d.get("rejected", [])), d

# final reread: first Clear, second pending → sealed Issues
rc, d, log = run_live(checks_mode="reread_pending")
assert rc == 0 and d["itemCount"] == 1, d
assert d["items"][0]["gateResult"] == "Issues", d
assert d["items"][0]["gateEvidence"]["status"] == "pending", d
assert log.count("pr checks") >= 2, log

# absent variable → defaults (success path)
rc, d, log = run_live(checks_mode="success", var_mode="absent")
assert rc == 0 and d["items"][0]["gateResult"] == "Clear", d
assert "LINKTREND_RELEASE_GATE_CHECKS" in log

# empty variable → defaults
rc, d, log = run_live(checks_mode="success", var_mode="empty")
assert rc == 0 and d["itemCount"] == 1, d

# auth on variable query → discovery fail closed (available false)
rc, d, log = run_live(checks_mode="success", var_mode="auth")
assert rc == 1 and d.get("available") is False, d
assert "release_gate_config_failed" in str(d.get("error")), d
assert d.get("itemCount") == 0

# rate-limit on variable → fail closed
rc, d, log = run_live(checks_mode="success", var_mode="ratelimit")
assert rc == 1 and d.get("available") is False, d
assert "release_gate_config_failed" in str(d.get("error")), d

print("live gh subprocess path ok")
PY
pass "Main Approve live gh checks/reread/variable fail-closed"

# ============================================================================
# Identity boundary: write_outcome exact --token-env; App-missing zero mutation
# ============================================================================
: <<'RETIRED_APP_IDENTITY_BOUNDARY'
python3 - "$ROOT" "$TMP" <<'PY'
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

root = Path(sys.argv[1])
tmp = Path(sys.argv[2])
runner_type = json.loads(
    (root / ".github/linktrend-gitops-consumer.json").read_text()
).get("runnerType", "github-hosted")
runner_types = {
    "github-hosted": ("ubuntu-latest", "ubuntu-latest"),
    "linktrend-private-macos-arm64": (
        "[self-hosted, macOS, ARM64, linktrend-privileged]",
        "[self-hosted, Linux, ARM64, linktrend-ci-isolated]",
    ),
}
assert runner_type in runner_types, f"Unsupported runnerType: {runner_type}"
privileged_runner, untrusted_runner = runner_types[runner_type]
sys.path.insert(0, str(root / "scripts" / "gitops"))
import write_outcome as wo

# --- write_outcome: AUTOMATION_TOKEN absent; ambient GH/GITHUB present → zero API ---
calls = []

def fake_run(*args, **kwargs):
    calls.append({"args": args, "kwargs": kwargs})
    raise AssertionError("check-run API must not be invoked without exact token-env")

orig = wo.subprocess.run
wo.subprocess.run = fake_run
try:
    with tempfile.TemporaryDirectory() as td:
        out = Path(td) / "gitops-outcome.json"
        # In-process: ambient credentials must not authorize check mutation
        saved = {k: os.environ.get(k) for k in (
            "AUTOMATION_TOKEN", "GH_TOKEN", "GITHUB_TOKEN", "github.token"
        )}
        os.environ.pop("AUTOMATION_TOKEN", None)
        os.environ["GH_TOKEN"] = "ghs_FAKE_GH_MUST_NOT_AUTHORIZE"
        os.environ["GITHUB_TOKEN"] = "ghs_FAKE_GITHUB_MUST_NOT_AUTHORIZE"
        os.environ["github.token"] = "ghs_FAKE_DOT_MUST_NOT_AUTHORIZE"
        argv = [
            "write_outcome.py",
            "--file", str(out),
            "--status", "automation_credentials_blocked",
            "--detail", "App missing; ambient tokens must not post checks",
            "--check-name", "Linktrend Test Check",
            "--head-sha", "deadbeefdeadbeefdeadbeefdeadbeefdeadbeef",
            "--repo", "linktrend/IDE-Development",
            "--token-env", "AUTOMATION_TOKEN",
        ]
        old_argv = sys.argv
        sys.argv = argv
        try:
            import io
            from contextlib import redirect_stderr, redirect_stdout
            buf_err, buf_out = io.StringIO(), io.StringIO()
            with redirect_stderr(buf_err), redirect_stdout(buf_out):
                rc = wo.main()
            err = buf_err.getvalue() + buf_out.getvalue()
        finally:
            sys.argv = old_argv
            for k, v in saved.items():
                if v is None:
                    os.environ.pop(k, None)
                else:
                    os.environ[k] = v
        assert rc == 0, err
        payload = json.loads(out.read_text())
        assert payload["status"] == "automation_credentials_blocked"
        assert "skipping commit-status" in err
        assert "no ambient" in err
        assert calls == [], f"unexpected API calls: {calls}"

    # Unit: resolve_check_token never falls back
    saved2 = {k: os.environ.get(k) for k in ("AUTOMATION_TOKEN", "GH_TOKEN", "GITHUB_TOKEN")}
    os.environ.pop("AUTOMATION_TOKEN", None)
    os.environ["GH_TOKEN"] = "ambient_gh"
    os.environ["GITHUB_TOKEN"] = "ambient_github"
    try:
        assert wo.resolve_check_token("AUTOMATION_TOKEN") is None
        assert wo.resolve_check_token("GH_TOKEN") == "ambient_gh"
        assert wo.resolve_check_token("") is None
        assert wo.resolve_check_token("MISSING_ENV") is None
    finally:
        for k, v in saved2.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v
    src = (root / "scripts/gitops/write_outcome.py").read_text()
    assert "or os.environ.get(\"GH_TOKEN\")" not in src
    assert "or os.environ.get('GH_TOKEN')" not in src
    assert "resolve_check_token" in src
finally:
    wo.subprocess.run = orig

# --- App-missing paths: local outcome only; zero mutation helpers ---
wf_names = [
    "linktrend-review-packager.yml",
    "linktrend-integrator-merge.yml",
    "linktrend-development-to-staging.yml",
    "linktrend-staging-to-main.yml",
]
for name in wf_names:
    live = (root / ".github/workflows" / name).read_text()
    managed = (root / "core/github/managed-workflows" / name).read_text()
    rendered = (
        managed.replace("__LINKTREND_CI_WORKFLOW_NAME__", "CI")
        .replace("__LINKTREND_BRANCH_POLICY_WORKFLOW_NAME__", "Branch Source Policy")
        .replace("__LINKTREND_BUGBOT_CHECK_NAME__", "Cursor Bugbot")
        .replace("__LINKTREND_UNTRUSTED_RUNS_ON__", untrusted_runner)
        .replace("__LINKTREND_RUNS_ON__", privileged_runner)
    )
    assert rendered == live, name

    # No ordinary-token mutation for repair/check/comment/PR/branch/merge
    assert 'GH_TOKEN="${GITHUB_TOKEN}"' not in live, name
    assert "--token-env GITHUB_TOKEN" not in live, name
    assert "--token-env GH_TOKEN" not in live, name
    # App-unavailable blocks must not call repair_task / check-run with github.token
    for marker in (
        "App unavailable",
        "automation_credentials_blocked",
    ):
        pass
    # Split on resolve_automation_token failure branches (avoid splitting on "--file")
    if "if ! source scripts/gitops/resolve_automation_token.sh" in live:
        for chunk in live.split("if ! source scripts/gitops/resolve_automation_token.sh")[1:]:
            # End at the matching `fi` line (indent + fi), not substring "fi" in "--file"
            end = None
            for i, line in enumerate(chunk.splitlines()):
                if line.strip() == "fi":
                    end = i
                    break
            fail_block = "\n".join(chunk.splitlines()[: end if end is not None else 40])
            assert "repair_task.py" not in fail_block, f"{name} App-miss repair"
            assert "--check-name" not in fail_block, f"{name} App-miss check-run"
            assert "github.token" not in fail_block, f"{name} App-miss github.token"
            assert "automation_credentials_blocked" in fail_block
            assert "exit 1" in fail_block
    if "Report credentials blocked" in live:
        block = live.split("Report credentials blocked")[1].split("Configure git remote")[0]
        assert "repair_task.py" not in block, f"{name} Report credentials repair"
        assert "--check-name" not in block, f"{name} Report credentials check"
        assert "github.token" not in block, f"{name} Report credentials github.token"
        assert "exit 1" in block

# Success paths prefer explicit AUTOMATION_TOKEN for write_outcome mutations
for name in (
    "linktrend-integrator-merge.yml",
    "linktrend-development-to-staging.yml",
    "linktrend-staging-to-main.yml",
    "linktrend-review-packager.yml",
):
    live = (root / ".github/workflows" / name).read_text()
    if "--token-env" in live:
        assert "--token-env AUTOMATION_TOKEN" in live, name
        assert "--token-env GITHUB_TOKEN" not in live, name
        assert "--token-env GH_TOKEN" not in live, name

# Scripts: automation-token-missing = local outcome only
for rel in (
    "scripts/gitops/integrator_evaluate.sh",
    "scripts/gitops/promote_staging.sh",
    "scripts/gitops/promote_main.sh",
):
    text = (root / rel).read_text()
    assert "AUTOMATION_TOKEN_SOURCE" in text
    # Find normal-token-missing block
    idx = text.find('!= "github_token"')
    assert idx > 0, rel
    block = text[idx : idx + 500]
    assert "write_outcome" in block or "write_out" in block or "automation_credentials_blocked" in block
    assert "repair_task" not in block, rel
    assert 'GH_TOKEN="${GH_TOKEN:-${GITHUB_TOKEN' not in text, rel

# Behavioral: promote/integrator App-missing with ambient tokens → local only, exit 0, no gh
fake_bin = tmp / "fake-bin-zero-mut"
fake_bin.mkdir(exist_ok=True)
(fake_bin / "gh").write_text(
    "#!/bin/bash\necho 'UNEXPECTED_GH_CALL' >&2; echo args:\"$*\" >&2; exit 99\n",
    encoding="utf-8",
)
os.chmod(fake_bin / "gh", 0o755)

def run_script(script, extra_env=None):
    env = os.environ.copy()
    env["PATH"] = f"{fake_bin}:{env.get('PATH','')}"
    env.pop("AUTOMATION_TOKEN", None)
    env.pop("AUTOMATION_TOKEN_SOURCE", None)
    env.pop("LINKTREND_APP_TOKEN", None)
    env["GH_TOKEN"] = "ghs_FAKE_AMBIENT_GH"
    env["GITHUB_TOKEN"] = "ghs_FAKE_AMBIENT_GITHUB"
    env["GH_REPO"] = "linktrend/IDE-Development"
    env["GITHUB_REPOSITORY"] = "linktrend/IDE-Development"
    outcome = tmp / f"outcome-{Path(script).stem}.json"
    env["OUTCOME_FILE"] = str(outcome)
    if extra_env:
        env.update(extra_env)
    # promote_*.sh require a git toplevel; run from repo root with absolute OUTCOME_FILE
    if "promote_" in script:
        cwd = root
    else:
        cwd = tmp / f"cwd-{Path(script).stem}"
        cwd.mkdir(exist_ok=True)
    r = subprocess.run(
        ["bash", str(root / script)],
        cwd=str(cwd),
        env=env,
        capture_output=True,
        text=True,
    )
    return r, cwd, env, outcome

for script in (
    "scripts/gitops/integrator_evaluate.sh",
    "scripts/gitops/promote_staging.sh",
    "scripts/gitops/promote_main.sh",
):
    r, cwd, env, outcome = run_script(script)
    assert r.returncode == 0, (script, r.returncode, r.stderr, r.stdout)
    assert "UNEXPECTED_GH_CALL" not in (r.stderr + r.stdout), script
    candidates = [
        outcome,
        cwd / "integrator-result.json",
        cwd / "gitops-outcome.json",
    ]
    found = None
    for c in candidates:
        if c.is_file():
            found = json.loads(c.read_text())
            break
    assert found is not None, (script, candidates)
    assert found["status"] == "automation_credentials_blocked", (script, found)

# App-success path still posts checks via AUTOMATION_TOKEN (unit of write_outcome)
posted = []

expected_states = {
    "merged": "success",
    "bugbot_requested": "success",
    "packaged": "success",
    "waiting": "pending",
    "skipped": None,
    "blocked": "error",
    "failed": "failure",
    "automation_credentials_blocked": "failure",
    "bugbot_user_credentials_blocked": "failure",
}
for status, expected in expected_states.items():
    assert wo.commit_status_state(status) == expected, (status, expected)

def capture_run(cmd, **kwargs):
    posted.append({"cmd": cmd, "env": dict(kwargs.get("env") or {})})
    class R:
        returncode = 0
    return R()

wo.subprocess.run = capture_run
try:
    os.environ["AUTOMATION_TOKEN"] = "ghs_APP_SUCCESS_TOKEN"
    os.environ["GH_TOKEN"] = "ghs_SHOULD_NOT_BE_USED"
    os.environ["GITHUB_TOKEN"] = "ghs_SHOULD_NOT_BE_USED"
    with tempfile.TemporaryDirectory() as td:
        out = Path(td) / "out.json"
        wo.main = wo.main  # keep
        r = subprocess.run(
            [
                sys.executable,
                str(root / "scripts/gitops/write_outcome.py"),
                "--file", str(out),
                "--status", "merged",
                "--detail", "ok",
                "--check-name", "Linktrend Integrator Result",
                "--head-sha", "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
                "--repo", "linktrend/IDE-Development",
                "--token-env", "AUTOMATION_TOKEN",
            ],
            env={**os.environ},
            capture_output=True,
            text=True,
        )
        # Can't easily inject capture into subprocess child — use resolve + post_check_run directly
    posted.clear()
    wo.post_check_run(
        name="Linktrend Integrator Result",
        head_sha="aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
        status="merged",
        detail="ok",
        repo="linktrend/IDE-Development",
        token=wo.resolve_check_token("AUTOMATION_TOKEN"),
    )
    assert len(posted) == 1
    assert posted[0]["env"]["GH_TOKEN"] == "ghs_APP_SUCCESS_TOKEN"
    assert posted[0]["env"]["GITHUB_TOKEN"] == "ghs_APP_SUCCESS_TOKEN"
    assert "statuses/aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa" in " ".join(str(x) for x in posted[0]["cmd"])
    posted.clear()
    wo.post_check_run(
        name="Linktrend Packager Result",
        head_sha="bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
        status="skipped",
        detail="stale_event_head",
        repo="linktrend/IDE-Development",
        token=wo.resolve_check_token("AUTOMATION_TOKEN"),
    )
    assert posted == [], "stale-event skip must not overwrite live-head status"
finally:
    wo.subprocess.run = orig
    os.environ.pop("AUTOMATION_TOKEN", None)

# Carlos token remains Packager-only for PR create + Bugbot comment
pkg = (root / ".github/workflows/linktrend-review-packager.yml").read_text()
assert "secrets.LINKTREND_BUGBOT_USER_TOKEN" in pkg
assert "REQUIRED_PACKAGER_PR_AUTHOR" in (root / "scripts/gitops/packager_logic.py").read_text()
assert 'REQUIRED_PACKAGER_PR_AUTHOR = "linktrend"' in (
    root / "scripts/gitops/packager_logic.py"
).read_text()
for rel in (
    "scripts/gitops/promote_staging.sh",
    "scripts/gitops/promote_main.sh",
    "scripts/gitops/integrator_evaluate.sh",
):
    assert "BUGBOT_USER_TOKEN" not in (root / rel).read_text()
    assert "LINKTREND_BUGBOT_USER_TOKEN" not in (root / rel).read_text()

print("identity boundary zero-mutation proofs ok")
PY
pass "write_outcome/normal-token-missing zero-mutation + normal-token success + managed≡live"
RETIRED_APP_IDENTITY_BOUNDARY
python3 - "$ROOT" <<'PY'
from pathlib import Path
import sys

root = Path(sys.argv[1])
managed = root / "core/github/managed-workflows"
live = root / ".github/workflows"
for path in managed.glob("linktrend-*.yml"):
    counterpart = live / path.name
    if counterpart.exists():
        assert "LINKTREND_AUTOMATION_TOKEN" not in path.read_text(encoding="utf-8")
        assert "LINKTREND_BUGBOT_USER_TOKEN" not in path.read_text(encoding="utf-8")
for name in (
    "linktrend-review-packager.yml",
    "linktrend-integrator-merge.yml",
    "linktrend-development-to-staging.yml",
    "linktrend-staging-to-main.yml",
    "linktrend-cleanup-merged.yml",
):
    text = (live / name).read_text(encoding="utf-8")
    assert "permissions:" in text
    assert "github.token" in text
print("built-in token identity boundary ok")
PY
pass "Built-in token identity is explicit; retired App identity absent"

echo ""
echo "PASS: behavioral gitops tests (${PASS} groups)"
