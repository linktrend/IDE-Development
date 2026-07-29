#!/usr/bin/env bash
# GitOps lifecycle invariants (Batches 2–8).
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"
fail() { echo "FAIL: $1" >&2; exit 1; }
pass() { echo "PASS: $1"; }

# ---- Job-level env context ban (${{ env.X }} invalid → zero-job runs) ----
# Negative fixture: must not appear at job env in managed/live promote workflows.
for f in core/github/managed-workflows/linktrend-staging-to-main.yml \
         .github/workflows/linktrend-staging-to-main.yml \
         core/github/managed-workflows/linktrend-development-to-staging.yml \
         .github/workflows/linktrend-development-to-staging.yml; do
  # Detect job-level env using env context (heuristic: under jobs: before steps:)
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
    if re.match(r'^[a-zA-Z0-9_]+:', line) and not line.startswith(' '):
        # top-level key after jobs ended? unlikely
        pass
    m = re.match(r'^(\s+)env:\s*$', line)
    if m and in_jobs:
        # job-level env is typically indent 4 spaces under job name (indent 2)
        indent = len(m.group(1))
        # look ahead: if next non-empty is steps at same/less, or we're before steps
        # Flag only when this env block is a sibling of runs-on/steps (indent==4)
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

cmp -s core/github/managed-workflows/linktrend-staging-to-main.yml \
  .github/workflows/linktrend-staging-to-main.yml || fail "staging-to-main managed!=live"
pass "managed==live for staging-to-main"

! grep -q 'Open or update PR' core/skills/agentcomply/SKILL.md \
  || fail "agentcomply still has Open or update PR"
pass "agentcomply has no Open or update PR"

grep -q 'Tue & Fri 10:00' .cursor/rules/01-git-branching.mdc \
  || fail "branching rule missing staging 10:00"
! grep -q 'Tue & Fri 08:00' .cursor/rules/01-git-branching.mdc \
  || fail "branching rule still has staging 08:00"
pass "branching rule has 10:00 not staging 08:00"

# Active promote docs must not instruct prefer-incoming (negation / forbidden phrasing OK)
if grep -n 'prefer-incoming' docs/AUTONOMOUS-GIT-OPERATIONS.md docs/contracts/REPAIR-DISPATCHER.md \
     scripts/gitops/promote_staging.sh scripts/gitops/promote_main.sh 2>/dev/null \
  | grep -viE 'No prefer-incoming|no prefer-incoming|Never.*prefer-incoming|Must not|do not|prefer-incoming merges'; then
  fail "active prefer-incoming instruction found"
fi
pass "no prefer-incoming in active promote docs"

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
  issue)
    shift
    case "${1:-}" in
      list)
        # idempotent: exact title match returns existing
        if [[ "$*" == *list* ]] || true; then
          echo '[{"number":42,"title":"Exact Title Match"}]'
          exit 0
        fi
        ;;
      view)
        echo '{"number":42,"title":"Exact Title Match","state":"OPEN"}'
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
# git repo stub
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
  # fake origin/development
  git update-ref refs/remotes/origin/development HEAD
)
export PATH="$TMP/bin:$PATH"
export GH_REPO="owner/repo"
out="$(python3 "$ROOT/scripts/gitops/create_issue_branch.py" --workdir "$TMP/repo" --prefer-worktree "Exact Title Match" || true)"
echo "$out" | grep -q 'ISSUE_NUMBER=42' || fail "idempotent create_issue_branch did not reuse #42: $out"
echo "$out" | grep -q 'BRANCH=issue/42-' || fail "branch missing: $out"
WT="$(echo "$out" | sed -n 's/^WORKTREE=//p')"
[ -n "$WT" ] && [ -d "$WT" ] || fail "WORKTREE missing: $out"
pass "create_issue_branch idempotent reuse"

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

# ---- completion_gate fail-closed without Ready status ----
export LINKTREND_STATUS_BACKEND=file
export LINKTREND_STATUS_DIR="$TMP/status"
mkdir -p "$LINKTREND_STATUS_DIR"
# Use the worktree created above (branch already checked out there)
(
  cd "$WT"
  git commit -q --allow-empty -m "wip" || true
  branch="$(git rev-parse --abbrev-ref HEAD)"
  git update-ref "refs/remotes/origin/${branch}" HEAD
)
set +e
COMPLETION_TESTS_OK=1 COMPLETION_EVIDENCE="proof" \
  python3 "$ROOT/scripts/gitops/completion_gate.py" review-ready --workdir "$WT" >/tmp/cg.out 2>/tmp/cg.err
ec=$?
set -e
[ "$ec" -eq 78 ] || fail "completion_gate expected exit 78 without Ready status, got $ec ($(cat /tmp/cg.out /tmp/cg.err))"
pass "completion_gate fail-closed without Ready status"

# ---- repair_task three-attempt escalation ----
export LINKTREND_CONFLICT_BACKEND=file
export LINKTREND_CONFLICT_DIR="$TMP/repair"
mkdir -p "$LINKTREND_CONFLICT_DIR"
python3 "$ROOT/scripts/gitops/repair_task.py" upsert --repo r --failure-type ci_failure \
  --branch b --head-sha a --increment-attempt >/dev/null
python3 "$ROOT/scripts/gitops/repair_task.py" upsert --repo r --failure-type ci_failure \
  --branch b --head-sha a --increment-attempt >/dev/null
out="$(python3 "$ROOT/scripts/gitops/repair_task.py" upsert --repo r --failure-type ci_failure \
  --branch b --head-sha a --increment-attempt)"
echo "$out" | grep -q 'Issues\|escalated' || fail "repair_task missing Issues escalation: $out"
pass "repair_task three-attempt escalation"

# ---- cleanup dry-run safe ----
bash "$ROOT/scripts/cleanup-merged-branches.sh" --remote --repo-root "$TMP/repo" >/tmp/cleanup.out 2>&1 || true
grep -q 'dry-run\|cleanup mode=dry-run' /tmp/cleanup.out || fail "cleanup dry-run marker missing"
pass "cleanup script dry-run safe"

# ---- Cursor/Codex/ChatGPT mention Review Ready / no implementer PR ----
bash "$ROOT/scripts/verify-platform-adoption.sh"
pass "platform adoption entrypoints"

echo "test-gitops-lifecycle: OK"
