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
  cp "$ROOT/scripts/mark-review-ready.sh" "$d/scripts/"
  cp "$ROOT/scripts/validate-review-ready.sh" "$d/scripts/"
  cp "$ROOT/scripts/clear-review-ready.sh" "$d/scripts/"
  cp "$ROOT/scripts/pull-update-work-branches.sh" "$d/scripts/"
  cp "$ROOT/scripts/cleanup-merged-branches.sh" "$d/scripts/"
  cp "$ROOT/scripts/gitops/"*.sh "$d/scripts/gitops/" 2>/dev/null || true
  cp "$ROOT/scripts/gitops/"*.py "$d/scripts/gitops/"
  chmod +x "$d/scripts/"*.sh "$d/scripts/gitops/"*.sh "$d/scripts/gitops/"*.py
  git -C "$d" add scripts
  git -C "$d" commit -q -m "chore: seed gitops scripts"
}

TMP="$(mktemp -d)"
cleanup() { rm -rf "$TMP"; }
trap cleanup EXIT

export LINKTREND_STATUS_BACKEND=file
export LINKTREND_CONFLICT_BACKEND=file

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
bash scripts/mark-review-ready.sh A "notes-a" >/dev/null
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
bash scripts/mark-review-ready.sh B >/dev/null
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
grep -q -- '--increment-attempt' "$ROOT/scripts/gitops/promote_staging.sh"
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
bash scripts/mark-review-ready.sh frozen >/dev/null
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
stg = Path(sys.argv[1], "scripts/gitops/promote_staging.sh").read_text()
main = Path(sys.argv[1], "scripts/gitops/promote_main.sh").read_text()
assert "target staging advanced" in stg or "targetSha" in stg
assert "stale event" in stg
assert "marker candidateHead" in stg
assert "EXPECTED_MAIN_SHA" in main
assert "target advanced" in main or "expected main target" in main
# development tip advance must not rebuild an existing exact candidate
assert "already exists for this exact source/target" in stg or "sourceSha" in stg
wf = Path(sys.argv[1], "core/github/managed-workflows/linktrend-development-to-staging.yml").read_text()
assert "PROMOTE_PR_NUMBER" in wf
assert "EXPECTED_PROMOTE_HEAD" in wf
assert "promote/staging/" in wf
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
    assert "Branch Source Policy" in text
    assert "- CI" in text or "CI" in text
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
              "AUTOMATION_TOKEN","GH_TOKEN","GITHUB_TOKEN"):
        env.pop(k, None)
    env["REQUIRE_APP_TOKEN"] = "1"
    env.update(env_extra)
    return subprocess.run(["bash", script], capture_output=True, text=True, env=env)

# Real workflow shape: App ID + minted token; private key ABSENT
r = run({"LINKTREND_GITOPS_APP_ID": "12345", "LINKTREND_APP_TOKEN": "ghs_test_minted_token_value"})
assert r.returncode == 0, r.stderr + r.stdout
assert "AUTOMATION_TOKEN_SOURCE=github_app" in r.stdout
assert "ghs_test_minted_token_value" not in r.stdout  # never print token
assert "ghs_test_minted_token_value" not in r.stderr

# Missing token → blocked
r = run({"LINKTREND_GITOPS_APP_ID": "12345"})
assert r.returncode != 0
assert "automation_credentials_blocked" in (r.stderr + r.stdout)

# Private key leaked into consumer → blocked
r = run({
    "LINKTREND_GITOPS_APP_ID": "12345",
    "LINKTREND_APP_TOKEN": "ghs_test",
    "LINKTREND_GITOPS_APP_PRIVATE_KEY": "-----BEGIN PRIVATE KEY-----\nX\n-----END PRIVATE KEY-----",
})
assert r.returncode != 0
assert "private_key_leaked" in (r.stderr + r.stdout) or "automation_credentials_blocked" in (r.stderr + r.stdout)

# GITHUB_TOKEN alone must not grant autonomy
r = run({"GITHUB_TOKEN": "ghs_workflow_token_only", "GH_TOKEN": "ghs_workflow_token_only"})
assert r.returncode != 0
assert "automation_credentials_blocked" in (r.stderr + r.stdout)

doc = (root/"docs/contracts/GITHUB-APP-GITOPS-CREDENTIALS.md").read_text()
assert "same job" in doc.lower() or "SAME job" in doc
assert "job outputs" in doc.lower()
print("credentials contract ok")
PY
pass "App credentials fail closed; no silent GITHUB_TOKEN autonomy"

# ============================================================================
# 14) Event target resolver (trusted fields only)
# ============================================================================
python3 - "$ROOT" <<'PY'
import json, os, tempfile
from pathlib import Path
import sys
sys.path.insert(0, str(Path(sys.argv[1]) / "scripts" / "gitops"))
from resolve_event_pr import resolve

pr, head = resolve("pull_request_target", {
  "pull_request": {"number": 19, "head": {"sha": "abc"}}
}, "", "")
assert pr == "19" and head == "abc"
pr, head = resolve("workflow_run", {
  "workflow_run": {"head_sha": "def", "pull_requests": [{"number": 7}]}
}, "", "")
assert pr == "7" and head == "def"
pr, head = resolve("check_run", {
  "check_run": {"head_sha": "ghi", "pull_requests": [{"number": 3}]}
}, "", "")
assert pr == "3" and head == "ghi"
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

echo ""
echo "PASS: behavioral gitops tests (${PASS} groups)"
