#!/usr/bin/env bash
# GitOps lifecycle invariants (Batches 2–8 + repair control / managed runtime).
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
export PYTHONPATH="${ROOT}${PYTHONPATH:+:${PYTHONPATH}}"
cd "$ROOT"
fail() { echo "FAIL: $1" >&2; exit 1; }
pass() { echo "PASS: $1"; }

# ---- Job-level env context ban (${{ env.X }} invalid → zero-job runs) ----
for f in core/github/managed-workflows/linktrend-staging-to-main.yml \
         .github/workflows/linktrend-staging-to-main.yml \
         core/github/managed-workflows/linktrend-development-to-staging.yml \
         .github/workflows/linktrend-development-to-staging.yml; do
  if python3 - "$f" <<'PY'
import re, sys
text = open(sys.argv[1]).read().splitlines()
in_jobs = False
in_job_env = False
job_indent = None
for i, line in enumerate(text, 1):
    if re.match(r'^jobs:\s*$', line):
        in_jobs = True
        continue
    if not in_jobs:
        continue
    m = re.match(r'^(\s+)env:\s*$', line)
    if m and in_jobs:
        indent = len(m.group(1))
        if indent == 4:
            in_job_env = True
            job_indent = indent
            continue
    if in_job_env:
        if line.strip() == '' or line.startswith(' ' * (job_indent + 2)):
            if '${{ env.' in line or '${{env.' in line:
                print(f"{sys.argv[1]}:{i}: job-level env context forbidden: {line.strip()}")
                sys.exit(2)
            continue
        in_job_env = False
sys.exit(0)
PY
  then
    :
  else
    fail "job-level \${{ env.* }} found in $f"
  fi
done
pass "No job-level env context in promote workflows"

python3 - "$ROOT" <<'PY'
from pathlib import Path
import json, sys

root = Path(sys.argv[1])
runner_type = json.loads(
    (root / ".github/linktrend-gitops-consumer.json").read_text()
).get("runnerType", "github-hosted")
runner_types = {"github-hosted": ("ubuntu-24.04-arm", "ubuntu-24.04-arm")}
assert runner_type in runner_types, f"Unsupported runnerType: {runner_type}"
privileged_runner, untrusted_runner = runner_types[runner_type]

def render(text: str) -> str:
    return (
        text.replace("__LINKTREND_CI_WORKFLOW_NAME__", "CI")
        .replace("__LINKTREND_BRANCH_POLICY_WORKFLOW_NAME__", "Branch Source Policy")
        .replace("__LINKTREND_BUGBOT_PROVIDER_CHECK_NAME__", "Cursor Bugbot")
        .replace("__LINKTREND_REVIEW_GATE_CHECK_NAME__", "Linktrend Review Gate")
        .replace("__LINKTREND_BUGBOT_CHECK_NAME__", "Linktrend Review Gate")
        .replace("__LINKTREND_UNTRUSTED_RUNS_ON__", untrusted_runner)
        .replace("__LINKTREND_RUNS_ON__", privileged_runner)
    )

for name in (
    "linktrend-staging-to-main.yml",
    "linktrend-repair-observer.yml",
    "linktrend-review-packager.yml",
    "linktrend-integrator-merge.yml",
    "linktrend-development-to-staging.yml",
):
    managed = (root / "core/github/managed-workflows" / name).read_text()
    live = (root / ".github/workflows" / name).read_text()
    assert render(managed) == live, f"{name} live != rendered managed"
    assert "self-hosted" not in live and "ubuntu-latest" not in live, name
PY
pass "managed templates render to live IDE workflow names"

! grep -q 'Open or update PR' core/skills/agentcomply/SKILL.md \
  || fail "agentcomply still has Open or update PR"
pass "agentcomply has no Open or update PR"

grep -q 'Tue & Fri 10:00' .cursor/rules/01-git-branching.mdc \
  || fail "branching rule missing staging 10:00"
! grep -q 'Tue & Fri 08:00' .cursor/rules/01-git-branching.mdc \
  || fail "branching rule still has staging 08:00"
pass "branching rule has 10:00 not staging 08:00"

if grep -n 'prefer-incoming' docs/AUTONOMOUS-GIT-OPERATIONS.md docs/contracts/REPAIR-DISPATCHER.md \
     scripts/gitops/promote_staging.sh scripts/gitops/promote_main.sh 2>/dev/null \
  | grep -viE 'No prefer-incoming|no prefer-incoming|Never.*prefer-incoming|Must not|do not|prefer-incoming merges'; then
  fail "active prefer-incoming instruction found"
fi
pass "no prefer-incoming in active promote docs"

grep -q 'git add --' core/session/SESSION-END.md || fail "SESSION-END missing owned-path staging"
if grep -nE 'git add \.|git add -A|git add --all' core/session/SESSION-END.md \
  | grep -viE 'never|refuse|not |Do not|do not|Owned-path|broad add'; then
  fail "SESSION-END still instructs broad git add"
fi
grep -q 'completion_gate.py review-ready' core/session/SESSION-END.md \
  || fail "SESSION-END missing authoritative review-ready gate"
grep -qi 'validates first\|only then' core/session/SESSION-END.md \
  || fail "SESSION-END missing validate-then-publish ordering"
if grep -niE 'Ready status is set|already be set|already set before' core/session/SESSION-END.md \
  | grep -viE 'do \*\*not\*\*|do not|not require'; then
  fail "SESSION-END still requires Ready status before gate"
fi
pass "SESSION-END owned-path staging + review-ready ordering"

grep -q '^\.linktrend/' .gitignore || fail ".linktrend/ not gitignored"
pass ".linktrend/ gitignored"

# ---- create_issue_branch mocked gh ----
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT
mkdir -p "$TMP/bin" "$TMP/repo"
cat >"$TMP/bin/gh" <<'EOF'
#!/usr/bin/env bash
set -euo pipefail
case "${1:-}" in
  auth) exit 0 ;;
  api) echo "owner/repo"; exit 0 ;;
  label)
    case "${2:-}" in
      list) echo '[{"name":"linktrend-agentsetup"}]'; exit 0 ;;
      create) exit 0 ;;
    esac
    ;;
  issue)
    shift
    case "${1:-}" in
      list)
        # With --label linktrend-agentsetup + matching title → reuse #42
        echo '[{"number":42,"title":"Exact Title Match","labels":[{"name":"linktrend-agentsetup"}]}]'
        exit 0
        ;;
      view)
        # Default open; closed when CLOSED_ISSUE=1
        if [ "${CLOSED_ISSUE:-}" = "1" ]; then
          echo '{"number":42,"title":"Exact Title Match","state":"CLOSED"}'
        else
          echo '{"number":42,"title":"Exact Title Match","state":"OPEN"}'
        fi
        exit 0
        ;;
      create)
        echo "https://github.com/owner/repo/issues/99"
        exit 0
        ;;
    esac
    ;;
  repo) echo "owner/repo"; exit 0 ;;
esac
echo "unexpected gh $*" >&2
exit 1
EOF
chmod +x "$TMP/bin/gh"
(
  cd "$TMP/repo"
  git init -q -b development
  git config user.email t@example.com
  git config user.name t
  echo x >f
  git add f
  git commit -q -m init
  git branch -M development
  git remote add origin "file://$TMP/repo"
  git update-ref refs/remotes/origin/development HEAD
)
export PATH="$TMP/bin:$PATH"
export GH_REPO="owner/repo"
out="$(python3 "$ROOT/scripts/gitops/create_issue_branch.py" --workdir "$TMP/repo" --prefer-worktree "Exact Title Match" || true)"
echo "$out" | grep -q 'ISSUE_NUMBER=42' || fail "idempotent create_issue_branch did not reuse #42: $out"
echo "$out" | grep -q 'BRANCH=issue/42-' || fail "branch missing: $out"
WT="$(echo "$out" | sed -n 's/^WORKTREE=//p')"
[ -n "$WT" ] && [ -d "$WT" ] || fail "WORKTREE missing: $out"
pass "create_issue_branch idempotent reuse (title+label)"

# reject closed issue
export CLOSED_ISSUE=1
if python3 "$ROOT/scripts/gitops/create_issue_branch.py" --workdir "$TMP/repo" --issue-number 42 2>/dev/null; then
  fail "create_issue_branch should reject CLOSED issue"
fi
unset CLOSED_ISSUE
pass "create_issue_branch rejects closed issue"

# auth fail
cat >"$TMP/bin/gh" <<'EOF'
#!/usr/bin/env bash
exit 1
EOF
chmod +x "$TMP/bin/gh"
if python3 "$ROOT/scripts/gitops/create_issue_branch.py" --workdir "$TMP/repo" "Should Fail" 2>/dev/null; then
  fail "create_issue_branch should fail closed on auth failure"
fi
pass "create_issue_branch auth fail closed"

# ---- completion_gate authoritative review-ready publish ----
export LINKTREND_STATUS_BACKEND=file
export LINKTREND_STATUS_DIR="$TMP/status"
mkdir -p "$LINKTREND_STATUS_DIR"
(
  cd "$WT"
  printf '\n.linktrend/\n' >>"$(git rev-parse --git-path info/exclude)"
  git commit -q --allow-empty -m "wip" || true
  branch="$(git rev-parse --abbrev-ref HEAD)"
  git update-ref "refs/remotes/origin/${branch}" HEAD
)

status_file_for() {
  lower_sha="$(printf '%s' "$1" | tr '[:upper:]' '[:lower:]')"
  printf '%s/%s.json' "$LINKTREND_STATUS_DIR" "$lower_sha"
}

has_success_status() {
  f="$(status_file_for "$1")"
  [ -f "$f" ] || return 1
  python3 - "$f" <<'PY'
import json, sys
rows = json.load(open(sys.argv[1], encoding="utf-8"))
for row in rows:
    if row.get("context") == "Linktrend Review Ready" and row.get("state") == "success":
        raise SystemExit(0)
raise SystemExit(1)
PY
}

assert_no_success_status() {
  if has_success_status "$1"; then
    fail "unexpected success status for $1 ($(cat "$(status_file_for "$1")"))"
  fi
}

assert_success_status() {
  if ! has_success_status "$1"; then
    f="$(status_file_for "$1")"
    if [ -f "$f" ]; then
      fail "missing success status for $1 ($(cat "$f"))"
    fi
    fail "missing success status file for $1"
  fi
}

run_review_ready_expect() {
  expected="$1"
  evidence_file="$2"
  out="$TMP/cg-${expected}.out"
  err="$TMP/cg-${expected}.err"
  set +e
  python3 "$ROOT/scripts/gitops/completion_gate.py" review-ready \
    --workdir "$WT" \
    --evidence-file "$evidence_file" >"$out" 2>"$err"
  ec=$?
  set -e
  [ "$ec" -eq "$expected" ] || fail "completion_gate expected exit $expected, got $ec ($(cat "$out" "$err"))"
  if [ "$expected" -eq 0 ]; then
    python3 - "$out" <<'PY'
import json
import sys

payload = json.load(open(sys.argv[1], encoding="utf-8"))
assert payload.get("state") == "waived_legacy_gate", payload
assert payload.get("published") is False, payload
assert payload.get("classification") == "WAIVED_LEGACY_GATE", payload
PY
  fi
}

write_completion_evidence() {
  evidence_file="$1"
  exit_code="$2"
  python3 "$ROOT/scripts/gitops/completion_gate.py" write-evidence \
    --workdir "$WT" \
    --evidence-file "$evidence_file" \
    --classification tests \
    --acceptance "lifecycle test acceptance" \
    --command "${exit_code}|scripts/tests/test-gitops-lifecycle.sh" >"$TMP/cg-write.out"
}

current_sha="$(git -C "$WT" rev-parse HEAD)"
run_review_ready_expect 78 ".linktrend/missing-evidence.json"
assert_no_success_status "$current_sha"
pass "completion_gate missing evidence fails closed without success status"

write_completion_evidence ".linktrend/failed-evidence.json" 1
run_review_ready_expect 78 ".linktrend/failed-evidence.json"
assert_no_success_status "$current_sha"
pass "completion_gate failed evidence fails closed without success status"

write_completion_evidence ".linktrend/stale-evidence.json" 0
(
  cd "$WT"
  git commit -q --allow-empty -m "advance after stale evidence"
  branch="$(git rev-parse --abbrev-ref HEAD)"
  git update-ref "refs/remotes/origin/${branch}" HEAD
)
advanced_sha="$(git -C "$WT" rev-parse HEAD)"
run_review_ready_expect 78 ".linktrend/stale-evidence.json"
assert_no_success_status "$advanced_sha"
pass "completion_gate stale evidence fails closed without success status"

write_completion_evidence ".linktrend/valid-evidence.json" 0
run_review_ready_expect 0 ".linktrend/valid-evidence.json"
assert_no_success_status "$advanced_sha"
pass "completion_gate valid evidence waives legacy Review Ready for exact SHA"

(
  cd "$WT"
  git commit -q --allow-empty -m "advance after review ready"
  branch="$(git rev-parse --abbrev-ref HEAD)"
  git update-ref "refs/remotes/origin/${branch}" HEAD
)
new_sha="$(git -C "$WT" rev-parse HEAD)"
set +e
python3 "$ROOT/scripts/gitops/readiness_status.py" get "$new_sha" >/tmp/ready-new.out 2>/tmp/ready-new.err
ready_new_ec=$?
set -e
[ "$ready_new_ec" -ne 0 ] || fail "new SHA unexpectedly review-ready ($(cat /tmp/ready-new.out /tmp/ready-new.err))"
assert_no_success_status "$new_sha"
pass "later commit is unready until gate succeeds for new SHA"

write_completion_evidence ".linktrend/new-failed-evidence.json" 1
run_review_ready_expect 78 ".linktrend/new-failed-evidence.json"
assert_no_success_status "$new_sha"
pass "failed gate leaves branch ineligible"

# ---- fetch failure fail-closed ----
(
  cd "$WT"
  git remote remove origin 2>/dev/null || true
  git remote add origin "https://invalid.example.invalid/no-such-repo.git"
)
# STATUS_BACKEND=file but origin exists → fetch must be attempted and fail closed
write_completion_evidence ".linktrend/fetch-fail-evidence.json" 0
run_review_ready_expect 78 ".linktrend/fetch-fail-evidence.json"
assert_no_success_status "$(git -C "$WT" rev-parse HEAD)"
pass "completion_gate fails closed when git fetch origin fails"

# restore file-backend style origin tip for later tests
(
  cd "$WT"
  git remote remove origin 2>/dev/null || true
  git remote add origin "$TMP/repo"
  branch="$(git rev-parse --abbrev-ref HEAD)"
  git fetch -q origin "$branch" 2>/dev/null || true
  git update-ref "refs/remotes/origin/${branch}" HEAD
)

# ---- disallowed branch ----
(
  cd "$WT"
  git checkout -q -b "random/not-allowed"
  git commit -q --allow-empty -m "disallowed branch tip"
  git update-ref "refs/remotes/origin/random/not-allowed" HEAD
)
write_completion_evidence ".linktrend/disallowed-evidence.json" 0
run_review_ready_expect 78 ".linktrend/disallowed-evidence.json"
assert_no_success_status "$(git -C "$WT" rev-parse HEAD)"
pass "completion_gate rejects disallowed work branch"

# return to allowed branch for remaining tests
ALLOWED_BR="$(git -C "$WT" branch --list 'issue/*' | head -1 | tr -d ' *')"
[ -n "$ALLOWED_BR" ] || ALLOWED_BR="issue/42-exact-title-match"
git -C "$WT" checkout -q "$ALLOWED_BR"

# ---- durable blocked record ----
export LINKTREND_REPAIR_BACKEND=file
export LINKTREND_REPAIR_DIR="$TMP/repair-blocked"
mkdir -p "$LINKTREND_REPAIR_DIR"
# Env-backed durable write (GH_REPO still set from earlier fixtures)
set +e
python3 "$ROOT/scripts/gitops/completion_gate.py" blocked \
  --workdir "$WT" \
  --reason "fixture blocker for durable record" \
  --attempted-repairs 2 >/tmp/blocked.out 2>/tmp/blocked.err
bec=$?
set -e
[ "$bec" -eq 2 ] || fail "blocked expected exit 2, got $bec ($(cat /tmp/blocked.out /tmp/blocked.err))"
echo "$(cat /tmp/blocked.out)" | python3 -c 'import json,sys; d=json.load(sys.stdin); assert d.get("durableRecord") is True, d; assert d.get("durableFailureId"), d; assert "LOCAL_CACHE_ONLY" not in (d.get("warning") or ""), d'
[ -f "$WT/.linktrend/completion-blocker.json" ] || fail "local blocker cache missing"
pass "completion_gate blocked writes local cache and durable repair task"

# Restore gh mock for local checkout resolution (after earlier auth-fail mock)
cat >"$TMP/bin/gh" <<'EOF'
#!/usr/bin/env bash
set -euo pipefail
case "${1:-}" in
  repo)
    # gh repo view --json nameWithOwner -q .nameWithOwner
    if [ "${GH_REPO_VIEW_FAIL:-}" = "1" ]; then
      echo "gh repo view failed" >&2
      exit 1
    fi
    echo "${GH_REPO_VIEW_NAME:-fixture/from-gh}"
    exit 0
    ;;
esac
echo "unexpected gh $*" >&2
exit 1
EOF
chmod +x "$TMP/bin/gh"

# Normal local session: no env repo vars → resolve via authenticated gh repo view
unset GITHUB_REPOSITORY GH_REPO LINKTREND_REPAIR_REPO || true
export LINKTREND_REPAIR_DIR="$TMP/repair-blocked-gh"
mkdir -p "$LINKTREND_REPAIR_DIR"
export GH_REPO_VIEW_NAME="fixture/from-gh"
set +e
python3 "$ROOT/scripts/gitops/completion_gate.py" blocked \
  --workdir "$WT" \
  --reason "local session via gh repo view" >/tmp/blocked-gh.out 2>/tmp/blocked-gh.err
bec=$?
set -e
[ "$bec" -eq 2 ] || fail "gh-resolve blocked expected exit 2 ($(cat /tmp/blocked-gh.out /tmp/blocked-gh.err))"
python3 - <<'PY'
import json
d=json.load(open("/tmp/blocked-gh.out"))
assert d.get("durableRecord") is True, d
assert d.get("repository") == "fixture/from-gh", d
assert d.get("repositorySource") == "gh_repo_view", d
assert "token" not in json.dumps(d).lower()
assert "://" not in (d.get("repository") or "")
PY
pass "blocked resolves repository from gh repo view without env"

# Origin remote resolution when gh fails; strip credentials; never print secrets
export GH_REPO_VIEW_FAIL=1
git -C "$WT" remote remove origin 2>/dev/null || true
git -C "$WT" remote add origin "https://example:not-a-secret@github.com/fixture/from-origin.git"
export LINKTREND_REPAIR_DIR="$TMP/repair-blocked-origin"
mkdir -p "$LINKTREND_REPAIR_DIR"
set +e
python3 "$ROOT/scripts/gitops/completion_gate.py" blocked \
  --workdir "$WT" \
  --reason "local session via origin" >/tmp/blocked-origin.out 2>/tmp/blocked-origin.err
bec=$?
set -e
[ "$bec" -eq 2 ] || fail "origin-resolve blocked expected exit 2 ($(cat /tmp/blocked-origin.out /tmp/blocked-origin.err))"
python3 - <<'PY'
import json
raw=open("/tmp/blocked-origin.out").read()+open("/tmp/blocked-origin.err").read()
assert "ghs_NOT_A_REAL_SECRET" not in raw, raw
assert "x-access-token" not in raw, raw
d=json.loads(open("/tmp/blocked-origin.out").read())
assert d.get("durableRecord") is True, d
assert d.get("repository") == "fixture/from-origin", d
assert d.get("repositorySource") == "origin_remote", d
PY
pass "blocked resolves sanitized origin remote; credentials never printed"

# Non-GitHub SCP hosts and ambiguous path segments must never resolve to a
# durable GitHub repository target.
for bad_origin in \
  "git@evil.example:fixture/from-origin.git" \
  "git@evil-github.com:fixture/from-origin.git" \
  "https://evil-github.com/fixture/from-origin.git" \
  "git@github.com:fixture/../from-origin.git" \
  "git@github.com:fixture/from%20origin.git"; do
  git -C "$WT" remote set-url origin "$bad_origin"
  set +e
  python3 "$ROOT/scripts/gitops/completion_gate.py" blocked \
    --workdir "$WT" \
    --reason "reject unsafe origin" >/tmp/blocked-unsafe-origin.out 2>/tmp/blocked-unsafe-origin.err
  bec=$?
  set -e
  [ "$bec" -eq 2 ] || fail "unsafe-origin blocked expected exit 2"
  python3 - <<'PY'
import json
d=json.load(open("/tmp/blocked-unsafe-origin.out"))
assert d.get("durableRecord") is False, d
assert d.get("localCacheOnly") is True, d
assert not d.get("repository"), d
PY
done
git -C "$WT" remote set-url origin "https://github.com/fixture/from-origin.git"
pass "blocked rejects non-GitHub and ambiguous origin remotes"

git -C "$WT" remote set-url origin "org-123@github.com:fixture/from-origin.git"
python3 "$ROOT/scripts/gitops/completion_gate.py" blocked \
  --workdir "$WT" \
  --reason "accept GitHub certificate-authority SSH origin" >/tmp/blocked-ca-origin.out 2>/tmp/blocked-ca-origin.err || true
python3 - <<'PY'
import json
d=json.load(open("/tmp/blocked-ca-origin.out"))
assert d.get("durableRecord") is True, d
assert d.get("repository") == "fixture/from-origin", d
assert d.get("repositorySource") == "origin_remote", d
PY
git -C "$WT" remote set-url origin "https://github.com/fixture/from-origin.git"
pass "blocked accepts exact GitHub certificate-authority SSH origin"

# Ambiguous origin+upstream → local cache only
git -C "$WT" remote add upstream "https://github.com/other/upstream.git"
export LINKTREND_REPAIR_DIR="$TMP/repair-blocked-ambiguous"
mkdir -p "$LINKTREND_REPAIR_DIR"
set +e
python3 "$ROOT/scripts/gitops/completion_gate.py" blocked \
  --workdir "$WT" \
  --reason "ambiguous remotes" >/tmp/blocked-amb.out 2>/tmp/blocked-amb.err
bec=$?
set -e
[ "$bec" -eq 2 ] || fail "ambiguous blocked expected exit 2"
python3 - <<'PY'
import json
d=json.load(open("/tmp/blocked-amb.out"))
assert d.get("durableRecord") is False, d
assert "LOCAL_CACHE_ONLY" in (d.get("warning") or ""), d
assert "ambiguous" in (d.get("repositorySource") or d.get("durableError") or ""), d
PY
git -C "$WT" remote remove upstream
pass "blocked rejects ambiguous origin+upstream (local cache only)"

# Missing/unrecognized origin (file remote) + gh fail → local cache only
git -C "$WT" remote remove origin
git -C "$WT" remote add origin "file://$TMP/repo"
export LINKTREND_REPAIR_DIR="$TMP/repair-blocked-missing"
mkdir -p "$LINKTREND_REPAIR_DIR"
set +e
python3 "$ROOT/scripts/gitops/completion_gate.py" blocked \
  --workdir "$WT" \
  --reason "missing github origin" >/tmp/blocked-miss.out 2>/tmp/blocked-miss.err
bec=$?
set -e
[ "$bec" -eq 2 ] || fail "missing-repo blocked expected exit 2"
python3 - <<'PY'
import json
d=json.load(open("/tmp/blocked-miss.out"))
assert d.get("durableRecord") is False, d
assert "LOCAL_CACHE_ONLY" in (d.get("warning") or ""), d
assert d.get("localCacheOnly") is True, d
PY
pass "blocked reports LOCAL_CACHE_ONLY when repository unresolved"

# Durable write failure with resolved repo → still local cache only warning
unset GH_REPO_VIEW_FAIL
export GH_REPO_VIEW_NAME="fixture/write-fail"
export LINKTREND_REPAIR_BACKEND=github
unset GH_TOKEN GITHUB_TOKEN || true
set +e
python3 "$ROOT/scripts/gitops/completion_gate.py" blocked \
  --workdir "$WT" \
  --reason "durable write should fail" >/tmp/blocked-dwf.out 2>/tmp/blocked-dwf.err
bec=$?
set -e
[ "$bec" -eq 2 ] || fail "durable-write-fail blocked expected exit 2"
python3 - <<'PY'
import json
d=json.load(open("/tmp/blocked-dwf.out"))
assert d.get("repository") == "fixture/write-fail", d
assert d.get("durableRecord") is False, d
assert "LOCAL_CACHE_ONLY" in (d.get("warning") or ""), d
assert d.get("durableError"), d
assert "ghs_" not in json.dumps(d).lower()
PY
# Restore file backend for remaining tests
export LINKTREND_REPAIR_BACKEND=file
pass "blocked durable-write failure keeps local cache and warns LOCAL_CACHE_ONLY"

# ---- repair_task: re-upsert does not increment; dispatch-attempt does; 3rd → Issues ----
export LINKTREND_REPAIR_BACKEND=file
export LINKTREND_REPAIR_DIR="$TMP/repair"
mkdir -p "$LINKTREND_REPAIR_DIR"
# Also set legacy aliases
export LINKTREND_CONFLICT_BACKEND=file
export LINKTREND_CONFLICT_DIR="$TMP/repair"

u1="$(python3 "$ROOT/scripts/gitops/repair_task.py" upsert --repo r --failure-type ci_failure \
  --branch b --check c --head-sha aaa)"
echo "$u1" | python3 -c 'import json,sys; t=json.load(sys.stdin); assert t["attemptCount"]==0, t'
u2="$(python3 "$ROOT/scripts/gitops/repair_task.py" upsert --repo r --failure-type ci_failure \
  --branch b --check c --head-sha bbb)"
echo "$u2" | python3 -c 'import json,sys; t=json.load(sys.stdin); assert t["attemptCount"]==0, t; assert t["headSha"]=="bbb", t; assert t["failureId"]'
FID="$(echo "$u2" | python3 -c 'import json,sys; print(json.load(sys.stdin)["failureId"])')"
# Same identity despite headSha change
echo "$u1" | python3 -c 'import json,sys; print(json.load(sys.stdin)["failureId"])' | grep -qx "$FID" \
  || fail "failureId changed when headSha changed"

d1="$(python3 "$ROOT/scripts/gitops/repair_task.py" dispatch-attempt --repo r --id "$FID")"
echo "$d1" | python3 -c 'import json,sys; t=json.load(sys.stdin); assert t["attemptCount"]==1, t; assert t["repairStatus"]=="dispatched", t'
d2="$(python3 "$ROOT/scripts/gitops/repair_task.py" dispatch-attempt --repo r --id "$FID")"
echo "$d2" | python3 -c 'import json,sys; t=json.load(sys.stdin); assert t["attemptCount"]==2, t'
# Re-upsert must NOT bump
u3="$(python3 "$ROOT/scripts/gitops/repair_task.py" upsert --repo r --failure-type ci_failure \
  --branch b --check c --head-sha ccc)"
echo "$u3" | python3 -c 'import json,sys; t=json.load(sys.stdin); assert t["attemptCount"]==2, t'
d3="$(python3 "$ROOT/scripts/gitops/repair_task.py" dispatch-attempt --repo r --id "$FID")"
echo "$d3" | python3 -c 'import json,sys; t=json.load(sys.stdin); assert t["attemptCount"]==3, t; assert t["resolutionState"]=="Issues", t; assert t["lisaDispatchState"]=="exhausted", t'
# Further dispatch blocked
set +e
python3 "$ROOT/scripts/gitops/repair_task.py" dispatch-attempt --repo r --id "$FID" >/tmp/d4.out 2>/tmp/d4.err
d4ec=$?
set -e
[ "$d4ec" -ne 0 ] || fail "dispatch after exhausted should fail"
pass "repair_task dispatch-attempt increments; re-upsert does not; 3rd → Issues"

# ---- cleanup dry-run safe ----
bash "$ROOT/scripts/cleanup-merged-branches.sh" --remote --repo-root "$TMP/repo" >/tmp/cleanup.out 2>&1 || true
grep -q 'dry-run\|cleanup mode=dry-run' /tmp/cleanup.out || fail "cleanup dry-run marker missing"
pass "cleanup script dry-run safe"

# ---- verify-platform-adoption (temp consumer path) ----
bash "$ROOT/scripts/verify-platform-adoption.sh"
pass "platform adoption entrypoints + temp consumer"

# ---- candidate finalization (generated closure, then exact-baseline diff check) ----
PKT08_EXACT_BASELINE=239dc35bbdaa33824e951f86911ef2bb29d20d80
if ! git cat-file -e "${PKT08_EXACT_BASELINE}^{commit}" 2>/dev/null; then
  fail "exact PKT-08 baseline missing — cannot finalize candidate"
fi
if ! python3 scripts/gitops/generated_output_closure.py \
  --finalize --baseline "$PKT08_EXACT_BASELINE" \
  >/tmp/candidate-finalization.out 2>/tmp/candidate-finalization.err; then
  cat /tmp/candidate-finalization.out /tmp/candidate-finalization.err >&2
  fail "candidate finalization failed"
fi
pass "candidate finalization clean against exact PKT-08 baseline"

# ---- Main Approve package/store interface (Lisa) ----
grep -q 'github_promote_pr_marker\|Package store' docs/contracts/LISA-MAIN-APPROVE-DISPATCH.md \
  || fail "LISA-MAIN-APPROVE-DISPATCH missing package store declaration"
grep -q 'expected_main_sha' docs/contracts/LISA-MAIN-APPROVE-DISPATCH.md \
  || fail "LISA-MAIN-APPROVE-DISPATCH missing expected_main_sha"
grep -q 'schemaVersion' docs/contracts/LISA-MAIN-APPROVE-DISPATCH.md \
  || fail "LISA-MAIN-APPROVE-DISPATCH missing marker schemaVersion"
grep -q 'main_approve_package_discover.py' docs/contracts/LISA-MAIN-APPROVE-DISPATCH.md \
  || fail "LISA-MAIN-APPROVE-DISPATCH missing discover CLI"
grep -q 'claimExpiresAt' docs/contracts/LISA-MAIN-APPROVE-DISPATCH.md \
  || fail "LISA-MAIN-APPROVE-DISPATCH missing claimExpiresAt / expiry policy"
grep -q 'requiresRepackage' docs/contracts/LISA-MAIN-APPROVE-DISPATCH.md \
  || fail "LISA-MAIN-APPROVE-DISPATCH missing freshness/repackage rules"
grep -q 'Do not use JSON/Markdown OpenClaw sidecar\|No JSON/Markdown OpenClaw sidecar' docs/contracts/LISA-MAIN-APPROVE-DISPATCH.md \
  || fail "LISA-MAIN-APPROVE-DISPATCH missing no-sidecar rule"
[ -f scripts/gitops/main_approve_package_discover.py ] || fail "missing main_approve_package_discover.py"
[ -f scripts/gitops/main_approve_package_reuse.py ] || fail "missing main_approve_package_reuse.py"
[ -f docs/contracts/fixtures/lisa-main-approve-package.schema.json ] \
  || fail "missing Lisa package schema fixture"
grep -q 'main_approve_package_discover.py' core/github/managed-runtime/MANIFEST.json \
  || fail "MANIFEST missing main_approve_package_discover.py"
grep -q 'main_approve_package_reuse.py' core/github/managed-runtime/MANIFEST.json \
  || fail "MANIFEST missing main_approve_package_reuse.py"
grep -q 'resolve_bugbot_user_token.sh' core/github/managed-runtime/MANIFEST.json \
  || fail "MANIFEST missing resolve_bugbot_user_token.sh"
grep -q 'bugbot_user_credentials.py' core/github/managed-runtime/MANIFEST.json \
  || fail "MANIFEST missing bugbot_user_credentials.py"

BODY="$TMP/main-approve-body.md"
cat >"$BODY" <<'EOF'
## Main promote package (awaiting Principal Approve)

Approve must bind:
- expected_sha (staging source) = `aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa`
- expected_main_sha (prior main target) = `bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb`
- expected_promote_head = `cccccccccccccccccccccccccccccccccccccccc`

<!-- linktrend-promote: {"schemaVersion":1,"stage":"main","sourceBranch":"staging","targetBranch":"main","sourceSha":"aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa","targetSha":"bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb","candidateHead":"cccccccccccccccccccccccccccccccccccccccc","promoteBranch":"promote/main/aaaaaaaaaaaa"} -->
EOF
CHECKS="$TMP/main-approve-checks.json"
cat >"$CHECKS" <<'EOF'
[
  {"name":"Verify IDE Development","state":"SUCCESS"},
  {"name":"Linktrend Branch Source Policy","state":"SUCCESS"}
]
EOF
disc="$(python3 "$ROOT/scripts/gitops/main_approve_package_discover.py" \
  --from-body-file "$BODY" \
  --repository linktrend/IDE-Development \
  --pr-number 99 \
  --head-sha cccccccccccccccccccccccccccccccccccccccc \
  --head-branch promote/main/aaaaaaaaaaaa \
  --staging-tip aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa \
  --main-tip bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb \
  --checks-json "$CHECKS" \
  --now 2026-08-03T10:00:00+08:00 \
  --created-at 2026-08-03T02:00:00Z)"
echo "$disc" | python3 -c '
import json,sys,re
from pathlib import Path
d=json.load(sys.stdin)
assert d.get("available") is True, d
assert d.get("store")=="github_promote_pr_marker", d
assert d.get("contract","").endswith("LISA-MAIN-APPROVE-DISPATCH.md"), d
assert d.get("itemCount")==1, d
pkg=d["package"]
assert pkg["packageId"].startswith("main-approve-2026-08-03-"), pkg
assert pkg["mondayDate"]=="2026-08-03", pkg
assert pkg["claimExpiresAt"].startswith("2026-08-03T23:59:59"), pkg
assert "+08:00" in pkg["claimExpiresAt"] or pkg["claimExpiresAt"].endswith("+08:00"), pkg
assert pkg["createdAt"], pkg
assert pkg.get("expired") is False, pkg
it=d["items"][0]
assert it["repository"]=="linktrend/IDE-Development"
assert it["promotionPrNumber"]==99
assert it["stagingSha"]=="aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
assert it["priorMainSha"]=="bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb"
assert it["promotionHeadSha"]=="cccccccccccccccccccccccccccccccccccccccc"
assert it["gateResult"]=="Clear"
assert it["gateEvidence"]["requiredChecks"]
assert "aaaaaaaa" not in it["plainDescription"]
assert it["workflowInputs"]["expected_main_sha"].startswith("bbb")
assert re.search(r"\b[0-9a-f]{7,40}\b", it["plainDescription"], re.I) is None
# Lisa-compatible package.items shape
lit=pkg["items"][0]
for k in ("index","plainDescription","repository","promotionPrNumber","stagingSha","priorMainSha","promotionHeadSha","gateResult"):
    assert k in lit, lit
# Schema fixture structural check (stdlib only)
schema=json.loads(Path("docs/contracts/fixtures/lisa-main-approve-package.schema.json").read_text())
assert set(schema["required"]) <= set(pkg.keys())
assert set(schema["properties"]["items"]["items"]["required"]) <= set(lit.keys())
assert lit["gateResult"] in ("Clear","Issues")
'
# Drifted head must be omitted (stale package)
set +e
python3 "$ROOT/scripts/gitops/main_approve_package_discover.py" \
  --from-body-file "$BODY" \
  --repository linktrend/IDE-Development \
  --pr-number 99 \
  --head-sha dddddddddddddddddddddddddddddddddddddddd \
  --head-branch promote/main/aaaaaaaaaaaa \
  --staging-tip aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa \
  --main-tip bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb \
  --checks-json "$CHECKS" \
  --now 2026-08-03T10:00:00+08:00 >/tmp/main-approve-drift.out 2>/tmp/main-approve-drift.err
dec=$?
set -e
[ "$dec" -ne 0 ] || fail "drifted head should not yield a sealed item"
pass "Main Approve package/store contract + discover CLI"

echo "test-gitops-lifecycle: OK"
