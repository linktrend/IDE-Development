#!/usr/bin/env bash
# GitOps lifecycle invariants (Batches 2–8 + repair control / managed runtime).
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
export PYTHONPATH="${ROOT}${PYTHONPATH:+:${PYTHONPATH}}"
cd "$ROOT"
fail() { echo "FAIL: $1" >&2; exit 1; }
pass() { echo "PASS: $1"; }

# ---- Job-level env context ban (${{ env.X }} invalid → zero-job runs) ----
for f in core/github/managed-workflows/*.yml .github/workflows/*.yml; do
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
pass "No job-level env context in managed or live workflows"

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
        .replace("__LINKTREND_UNTRUSTED_RUNS_ON__", untrusted_runner)
        .replace("__LINKTREND_RUNS_ON__", privileged_runner)
    )

names = sorted(path.name for path in (root / "core/github/managed-workflows").glob("*.yml"))
assert names, "no managed workflow templates"
for name in names:
    managed = (root / "core/github/managed-workflows" / name).read_text()
    live = (root / ".github/workflows" / name).read_text()
    assert render(managed) == live, f"{name} live != rendered managed"
    assert "self-hosted" not in live and "ubuntu-latest" not in live, name
PY
pass "managed templates render to live IDE workflow names"

! grep -q 'Open or update PR' core/skills/agentcomply/SKILL.md \
  || fail "agentcomply still has Open or update PR"
pass "agentcomply has no Open or update PR"

grep -q 'promote/main/' .cursor/rules/01-git-branching.mdc \
  || fail "branching rule missing promote/main"
grep -q 'issue/<PREFIX>-<n>-<slug>' .cursor/rules/01-git-branching.mdc \
  || fail "branching rule missing ledger issue branches"
! grep -qi 'staging' .cursor/rules/01-git-branching.mdc \
  || fail "branching rule still mentions staging"
pass "branching rule is v3 development and main"

if grep -n 'prefer-incoming' docs/AUTONOMOUS-GIT-OPERATIONS.md 2>/dev/null \
  | grep -viE 'No prefer-incoming|no prefer-incoming|Never.*prefer-incoming|Must not|do not|prefer-incoming merges'; then
  fail "active prefer-incoming instruction found"
fi
pass "no prefer-incoming in active promote docs"

grep -q 'git add --' core/session/SESSION-END.md || fail "SESSION-END missing owned-path staging"
if grep -nE 'git add \.|git add -A|git add --all' core/session/SESSION-END.md \
  | grep -viE 'never|refuse|not |Do not|do not|Owned-path|broad add'; then
  fail "SESSION-END still instructs broad git add"
fi
pass "SESSION-END owned-path staging"

grep -q '^\.linktrend/' .gitignore || fail ".linktrend/ not gitignored"
pass ".linktrend/ gitignored"

# ---- create_issue_branch (Ledger ID; no GitHub Issue) ----
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT
mkdir -p "$TMP/bin" "$TMP/repo"
cat >"$TMP/bin/gh" <<'EOF'
#!/usr/bin/env bash
exit 1
EOF
chmod +x "$TMP/bin/gh"
(
  cd "$TMP/repo"
  git init -q -b development
  git config user.email t@example.com
  git config user.name t
  git config commit.gpgsign false
  echo x >f
  git add f
  git commit -q -m init
  git branch -M development
  git remote add origin "file://$TMP/repo"
  git update-ref refs/remotes/origin/development HEAD
)
export PATH="$TMP/bin:$PATH"
export GH_REPO="owner/repo"
if python3 "$ROOT/scripts/gitops/create_issue_branch.py" --workdir "$TMP/repo" "Should Fail" 2>"$TMP/noid.err"; then
  fail "create_issue_branch should fail without a Ledger ID"
fi
grep -q 'Project orchestrator' "$TMP/noid.err" || fail "missing orchestrator message: $(cat "$TMP/noid.err")"
pass "create_issue_branch refuses missing Ledger ID"
out="$(python3 "$ROOT/scripts/gitops/create_issue_branch.py" --workdir "$TMP/repo" --id IDE-42 --slug exact-title --worktree "$TMP/issue-wt" --no-push)"
WT="$(python3 -c 'import json,sys; print(json.loads(sys.argv[1])["worktree"])' "$out")"
echo "$out" | grep -q 'issue/IDE-42-exact-title' || fail "branch missing: $out"
[ -n "$WT" ] && [ -d "$WT" ] || fail "WORKTREE missing: $out"
pass "create_issue_branch creates issue/IDE-42-exact-title"

# ---- cleanup dry-run safe ----
bash "$ROOT/scripts/cleanup-merged-branches.sh" --remote --repo-root "$TMP/repo" >/tmp/cleanup.out 2>&1 || true
grep -q 'dry-run\|cleanup mode=dry-run' /tmp/cleanup.out || fail "cleanup dry-run marker missing"
pass "cleanup script dry-run safe"

# ---- candidate finalization (runtime exact baseline + working-tree gate) ----
# The caller supplies the exact target identity.  The resolver may materialize
# that named remote ref in a shallow checkout; it never invents a branch.
candidate_baseline_ref="${LINKTREND_TARGET_BASELINE_REF:-}"
candidate_baseline_sha="${LINKTREND_TARGET_BASELINE_SHA:-}"
if [ -z "$candidate_baseline_ref" ] && [ -z "$candidate_baseline_sha" ]; then
  # The default portable harness is itself a test fixture.  Give its final
  # invocation the same kind of exact named remote target that CI injects,
  # while leaving all partially supplied or invalid input fail-closed.
  candidate_head="$(git rev-parse --verify HEAD^{commit} 2>/dev/null || true)"
  while IFS=' ' read -r candidate_ref candidate_sha; do
    [ -n "$candidate_ref" ] || continue
    case "$candidate_ref" in
      refs/remotes/*/HEAD) continue ;;
    esac
    if [ "$candidate_sha" = "$candidate_head" ]; then
      continue
    fi
    if git merge-base --is-ancestor "$candidate_sha" "$candidate_head" 2>/dev/null; then
      candidate_baseline_ref="${candidate_ref#refs/remotes/}"
      candidate_baseline_sha="$candidate_sha"
      break
    fi
  done < <(
    {
      git for-each-ref --sort=refname \
        --format='%(refname) %(objectname)' refs/remotes/origin/phase/
      git for-each-ref --sort=refname \
        --format='%(refname) %(objectname)' refs/remotes/origin/development
      git for-each-ref --sort=refname \
        --format='%(refname) %(objectname)' refs/remotes/origin/staging
      git for-each-ref --sort=refname \
        --format='%(refname) %(objectname)' refs/remotes/origin/main
      git for-each-ref --sort=refname \
        --format='%(refname) %(objectname)' refs/remotes
    } | awk '!seen[$1]++'
  )
  if [ -z "$candidate_baseline_ref" ] || [ -z "$candidate_baseline_sha" ]; then
    fail "default harness could not resolve a distinct named remote target baseline"
  fi
  pass "default harness selected named remote target baseline ${candidate_baseline_ref}"
fi
if [ -z "$candidate_baseline_ref" ] || [ -z "$candidate_baseline_sha" ]; then
  fail "runtime target baseline ref and SHA are required"
fi
LINKTREND_TARGET_BASELINE_REF="$candidate_baseline_ref" \
LINKTREND_TARGET_BASELINE_SHA="$candidate_baseline_sha" \
  python3 "$ROOT/scripts/gitops/generated_output_closure.py" --finalize \
  >/tmp/candidate-finalization.out 2>/tmp/candidate-finalization.err \
  || {
    cat /tmp/candidate-finalization.out /tmp/candidate-finalization.err >&2
    fail "candidate finalization failed for runtime target baseline"
  }
pass "candidate finalization clean for runtime target baseline"

echo "test-gitops-lifecycle: OK"
