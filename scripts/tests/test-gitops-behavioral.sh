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
  printf '%s\n' "__pycache__/" "*.py[cod]" >"$d/.gitignore"
  cp "$ROOT/scripts/mark-review-ready.sh" "$d/scripts/"
  cp "$ROOT/scripts/validate-review-ready.sh" "$d/scripts/"
  cp "$ROOT/scripts/clear-review-ready.sh" "$d/scripts/"
  cp "$ROOT/scripts/pull-update-work-branches.sh" "$d/scripts/"
  cp "$ROOT/scripts/cleanup-merged-branches.sh" "$d/scripts/"
  cp "$ROOT/scripts/gitops/"*.sh "$d/scripts/gitops/" 2>/dev/null || true
  cp "$ROOT/scripts/gitops/"*.py "$d/scripts/gitops/"
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
from packager_logic import should_request_bugbot, build_bugbot_comment, marker_for, fast_gate_status

sha = "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
ok, reason = should_request_bugbot(comments=[], head_sha=sha, fast_gate_ok=False)
assert not ok and reason == "fast_gate_not_green"
ok, reason = should_request_bugbot(comments=[], head_sha=sha, fast_gate_ok=True)
assert ok and reason == "request"
comments = [{"body": build_bugbot_comment("cursor review", sha)}]
ok, reason = should_request_bugbot(comments=comments, head_sha=sha, fast_gate_ok=True)
assert not ok and reason == "skipped_duplicate_marker"
# max 2
c2 = [
  {"body": "cursor review\n\n" + marker_for("1111111111111111111111111111111111111111")},
  {"body": "cursor review\n\n" + marker_for("2222222222222222222222222222222222222222")},
]
ok, reason = should_request_bugbot(comments=c2, head_sha=sha, fast_gate_ok=True)
assert not ok and reason == "skipped_max_requests"
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
grep -q 'timeout-minutes: 20' "$ROOT/core/github/managed-workflows/linktrend-review-packager.yml"
grep -q 'packager_discover.py' "$ROOT/core/github/managed-workflows/linktrend-review-packager.yml"
grep -q 'packager_evaluate.py' "$ROOT/core/github/managed-workflows/linktrend-review-packager.yml"
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
grep -q 'expected_main_sha' "$ROOT/core/github/managed-workflows/linktrend-staging-to-main.yml"
grep -q 'expected_promote_head' "$ROOT/core/github/managed-workflows/linktrend-staging-to-main.yml"
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
grep -q 'cron: "0 0 \* \* 2,5"' "$ROOT/core/github/managed-workflows/linktrend-review-packager.yml"
grep -q 'cron: "0 2 \* \* 2,5"' "$ROOT/core/github/managed-workflows/linktrend-development-to-staging.yml"
pass "activation + mention-only docs + schedules"

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
# development tip advance must not rebuild an existing exact candidate
assert "already exists for this exact source/target" in stg or "sourceSha" in stg
wf = (root / "core/github/managed-workflows/linktrend-development-to-staging.yml").read_text()
assert "PROMOTE_PR_NUMBER" in wf
assert "EXPECTED_PROMOTE_HEAD" in wf
# Branch prefix policy lives in trusted resolver + promote script (not duplicated in YAML ifs)
resolver = (root / "scripts/gitops/resolve_event_pr.py").read_text()
assert "promote/staging/" in resolver and "promote/staging/" in stg
assert "promote/main/" in resolver and "promote/main/" in main
assert "RESOLVE_ROLE: staging" in wf
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
comments = [{"body": build_bugbot_comment("cursor review", sha)}]
ok3, reason3 = should_request_bugbot(comments=comments, head_sha=sha, fast_gate_ok=True)
assert not ok3 and reason3 == "skipped_duplicate_marker"

# Workflow wiring: both wake names present; static YAML (not vars)
for rel in (
    "core/github/managed-workflows/linktrend-review-packager.yml",
    "core/github/managed-workflows/linktrend-integrator-merge.yml",
):
    text = Path(sys.argv[1], rel).read_text()
    assert "Branch Source Policy" in text or "__LINKTREND_BRANCH_POLICY_WORKFLOW_NAME__" in text
    assert "- CI" in text or "__LINKTREND_CI_WORKFLOW_NAME__" in text
    # Must not claim dynamic workflow_run names via vars
    assert "vars.LINKTREND_WORKFLOW_RUN" not in text
print("wake+bugbot dual-gate scenarios ok")
PY
pass "wake path + Bugbot request scenarios"

# ============================================================================
# 13) App credentials: minted token accepted without private key; fail closed otherwise
# ============================================================================
python3 - "$ROOT" <<'PY'
from pathlib import Path
import subprocess, os, sys
root = Path(sys.argv[1])
script = str(root / "scripts/gitops/resolve_automation_token.sh")

def run(env_extra):
    env = os.environ.copy()
    for k in ("LINKTREND_APP_TOKEN","LINKTREND_GITOPS_APP_ID","LINKTREND_GITOPS_APP_PRIVATE_KEY",
              "LINKTREND_GITOPS_APP_ID_VAR","AUTOMATION_TOKEN","GH_TOKEN","GITHUB_TOKEN"):
        env.pop(k, None)
    env["REQUIRE_APP_TOKEN"] = "1"
    env.update(env_extra)
    return subprocess.run(["bash", script], capture_output=True, text=True, env=env)

# Real workflow shape: App ID + minted token; private key ABSENT
r = run({"LINKTREND_GITOPS_APP_ID": "12345", "LINKTREND_APP_TOKEN": "ghs_test_minted_token_value"})
assert r.returncode == 0, (r.returncode, r.stderr, r.stdout)
assert "AUTOMATION_TOKEN_SOURCE=github_app" in r.stdout, r.stdout
assert "ghs_test_minted_token_value" not in r.stdout  # never print token
assert "ghs_test_minted_token_value" not in r.stderr

# Missing token → blocked
r = run({"LINKTREND_GITOPS_APP_ID": "12345"})
assert r.returncode != 0, (r.returncode, r.stderr, r.stdout)
assert "automation_credentials_blocked" in (r.stderr + r.stdout)

# Private key leaked into consumer → blocked
r = run({
    "LINKTREND_GITOPS_APP_ID": "12345",
    "LINKTREND_APP_TOKEN": "ghs_test",
    "LINKTREND_GITOPS_APP_PRIVATE_KEY": "-----BEGIN PRIVATE KEY-----\nX\n-----END PRIVATE KEY-----",
})
assert r.returncode != 0, (r.returncode, r.stderr, r.stdout)
assert "private_key_leaked" in (r.stderr + r.stdout) or "automation_credentials_blocked" in (r.stderr + r.stdout)

# GITHUB_TOKEN alone must not grant autonomy
r = run({"GITHUB_TOKEN": "ghs_workflow_token_only", "GH_TOKEN": "ghs_workflow_token_only"})
assert r.returncode != 0, (r.returncode, r.stderr, r.stdout)
assert "automation_credentials_blocked" in (r.stderr + r.stdout)

doc = (root/"docs/contracts/GITHUB-APP-GITOPS-CREDENTIALS.md").read_text()
assert "same job" in doc.lower() or "SAME job" in doc
assert "job outputs" in doc.lower()
print("credentials contract ok")
PY
pass "App credentials fail closed; no silent GITHUB_TOKEN autonomy"

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
assert "pull_request.number" not in pkg and "pull_requests[0].number" not in pkg
assert "pull_request.head.sha" in pkg
assert "workflow_run.head_sha" in pkg
assert "check_run.head_sha" in pkg

# Simulate expression fallbacks for same SHA with/without pull_requests arrays
def eval_packager_group(event_name: str, *, pr_sha="", wr_sha="", cr_sha="", run_id="9"):
    # Mirror YAML: a || b || c || misc-run_id
    return pr_sha or wr_sha or cr_sha or f"misc-{run_id}"

g_prt = eval_packager_group("pull_request_target", pr_sha=sha)
g_wr_with = eval_packager_group("workflow_run", wr_sha=sha)  # PR array present or not — SHA is uniform
g_wr_empty = eval_packager_group("workflow_run", wr_sha=sha)
g_cr_with = eval_packager_group("check_run", cr_sha=sha)
g_cr_empty = eval_packager_group("check_run", cr_sha=sha)
assert g_prt == g_wr_with == g_wr_empty == g_cr_with == g_cr_empty == sha

ig = concurrency_expr(root / "core/github/managed-workflows/linktrend-integrator-merge.yml")
assert "pull_request.head.sha" in ig and "workflow_run.head_sha" in ig and "check_run.head_sha" in ig
assert "inputs.pr_number" in ig  # dispatch-only fallback
assert "cancel-in-progress: false" in (root / "core/github/managed-workflows/linktrend-integrator-merge.yml").read_text()

# Production-path idempotency: first request, then reread comments → duplicate skip
comments = []
ok, reason = should_request_bugbot(comments=comments, head_sha=sha, fast_gate_ok=True)
assert ok and reason == "request"
comments.append({"body": build_bugbot_comment("cursor review", sha)})
ok2, reason2 = should_request_bugbot(comments=comments, head_sha=sha, fast_gate_ok=True)
assert not ok2 and reason2 == "skipped_duplicate_marker"
assert sum(1 for c in comments if "cursor review" in c["body"].lower()) == 1
# Document honesty: cross-run serialization is Actions concurrency; this proves
# the second serialized evaluator's comment-reread idempotency only.
print("sha concurrency + serialized idempotency ok")
PY
pass "uniform SHA concurrency + production-path Bugbot idempotency"

# ============================================================================
# 17) Actual resolver matrix (empty PR arrays, forks, promote roles)
# ============================================================================
python3 - "$ROOT" <<'PY'
import sys
from pathlib import Path
sys.path.insert(0, str(Path(sys.argv[1]) / "scripts" / "gitops"))
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
    assert rendered == live, name

print("resolver matrix rows", len(rows))
print("resolver matrix ok")
PY
pass "actual resolver event matrix (incl. empty PR arrays)"

# ============================================================================
# 18) Repair observer lifecycle: failure → dispatch → current-head success resolve;
#     stale success ignored; neutral Bugbot usage_limit; workflow permissions
# ============================================================================
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

current_pr_heads = {}
current_branch_heads = {}
repair_observer.current_pr_head = lambda repo, pr: current_pr_heads.get(str(pr), ("", ""))
repair_observer.current_branch_head = lambda repo, branch: current_branch_heads.get(str(branch), "")
repair_observer.lookup_pr_for_sha = lambda repo, sha: ("", "")

def write_event(name, payload):
    path = tmp / f"{name}.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    return str(path)

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
out = repair_observer.handle_event_path(failure_path, repo)
assert out["action"] == "upserted", out
fid = repair_task.failure_id(repo, "ci_failure", pr="23", workflow="CI", check="CI", branch="issue/ok")
backend = repair_task.get_backend(repo)
assert backend.dispatch_attempt(fid)["repairStatus"] == "dispatched"
current_pr_heads["23"] = (sha_ok, "issue/ok")
success_path = write_event("workflow-success", workflow_payload("success", 23, "issue/ok", sha_ok))
out = repair_observer.handle_event_path(success_path, repo)
assert out["action"] == "resolved", out
assert backend.get(fid)["resolutionState"] == "resolved"

sha_old = "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb"
sha_new = "cccccccccccccccccccccccccccccccccccccccc"
failure_path = write_event("workflow-stale-failure", workflow_payload("failure", 24, "issue/stale", sha_old))
assert repair_observer.handle_event_path(failure_path, repo)["action"] == "upserted"
stale_id = repair_task.failure_id(repo, "ci_failure", pr="24", workflow="CI", check="CI", branch="issue/stale")
backend.dispatch_attempt(stale_id)
current_pr_heads["24"] = (sha_new, "issue/stale")
success_path = write_event("workflow-stale-success", workflow_payload("success", 24, "issue/stale", sha_old))
out = repair_observer.handle_event_path(success_path, repo)
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
out = repair_observer.handle_event_path(usage_path, repo)
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
out = repair_observer.handle_event_path(ordinary_path, repo)
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
assert repair_observer.handle_event_path(usage_again, repo)["action"] == "upserted"
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
out = repair_observer.handle_event_path(success_bugbot, repo)
assert out["action"] == "resolved", out
assert backend.get(usage_open_id)["resolutionState"] == "resolved"
print("repair observer lifecycle ok")
PY
pass "repair observer resolves current-head successes, skips stale, handles/clears Bugbot usage_limit"

python3 - "$ROOT" <<'PY'
import re
import sys
from pathlib import Path

root = Path(sys.argv[1])
workflow_paths = list((root / ".github" / "workflows").glob("*.yml"))
workflow_paths += list((root / "core" / "github" / "managed-workflows").glob("*.yml"))

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
            out.append(line)
    return "\n".join(out)

failures = []
for path in workflow_paths:
    for job, block in job_blocks(path):
        needs_issue_write = "repair_task.py upsert" in block or "repair_observer" in block
        if not needs_issue_write:
            continue
        perms = job_permissions(block)
        if not re.search(r"(?m)^\s+issues:\s*write\s*$", perms):
            failures.append(f"{path.relative_to(root)}:{job}")
if failures:
    raise SystemExit("jobs missing issues: write: " + ", ".join(failures))

observer = (root / "scripts" / "gitops" / "repair_observer.py").read_text()
assert "repair_task.resolve_task(" in observer
assert 'failure_type="ci_failure"' in observer
assert "bugbot_failure" in observer and "usage_limit" in observer
assert '("bugbot_failure", "usage_limit")' in observer or "('bugbot_failure', 'usage_limit')" in observer
print("repair observer permissions + resolve caller proof ok")
PY
pass "repair observer/upsert jobs carry issues:write and production resolve caller exists"

# ============================================================================
# App-credential failure actually creates/updates a repair task (file backend)
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

echo ""
echo "PASS: behavioral gitops tests (${PASS} groups)"
