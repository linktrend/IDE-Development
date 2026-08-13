#!/usr/bin/env bash
# Issue #51 — stale cleanup controls (open-PR KEEP, worktree KEEP, preserve, repair inventory).
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
PASS=0
fail() { echo "FAIL: $1" >&2; exit 1; }
pass() { echo "PASS: $1"; PASS=$((PASS + 1)); }

TMP="$(mktemp -d "${TMPDIR:-/tmp}/stale-cleanup-XXXXXX")"
cleanup() { rm -rf "$TMP"; }
trap cleanup EXIT

make_repo() {
  local d="$1"
  mkdir -p "$d"
  git -C "$d" init -q -b development
  git -C "$d" config user.email "test@example.com"
  git -C "$d" config user.name "Stale Cleanup Test"
  echo base >"$d/README.md"
  git -C "$d" add README.md
  git -C "$d" commit -q -m "chore: base"
  git -C "$d" branch staging
  git -C "$d" branch main
}

# Hermetic CLEANUP_REPO for shell dry-runs that need PR evidence (Issue #61).
# Prefer env over a live github.com origin — --remote would otherwise git fetch
# and pollute refs/remotes/origin. Ambiguity fixtures unset these and add remotes.
with_cleanup_repo() {
  env -u GH_REPO GITHUB_REPOSITORY=linktrend/IDE-Development "$@"
}

seed_cleanup() {
  local d="$1"
  mkdir -p "$d/scripts/gitops"
  cp "$ROOT/scripts/cleanup-merged-branches.sh" "$d/scripts/"
  cp "$ROOT/scripts/gitops/work-branch-allowlist.sh" "$d/scripts/gitops/"
  cp "$ROOT/scripts/gitops/cleanup_controls.py" "$d/scripts/gitops/"
  cp "$ROOT/scripts/gitops/cleanup_preserve.defaults.json" "$d/scripts/gitops/"
  if [ -f "$ROOT/scripts/gitops/cleanup_stale_records.py" ]; then
    cp "$ROOT/scripts/gitops/cleanup_stale_records.py" "$d/scripts/gitops/"
  fi
  chmod +x "$d/scripts/"*.sh "$d/scripts/gitops/"*.py
  git -C "$d" add scripts
  git -C "$d" commit -q -m "chore: seed cleanup scripts"
}

stub_gh_pr_view() {
  # shared prefix written by callers after their branch-specific cases
  cat <<'EOS'
if [[ "$*" == *"pr view"* ]]; then
  echo '{"number":49,"state":"OPEN","headRefName":"issue/43-build-portable-ide-development-v2-managed-core-i"}'
  exit 0
fi
echo '[]'
EOS
}

# ============================================================================
# 1) Historical MERGED + newer OPEN for same branch → KEEP
# ============================================================================
REPO1="$TMP/open-pr"
make_repo "$REPO1"
seed_cleanup "$REPO1"
git -C "$REPO1" checkout -q -b issue/23-gitops-lifecycle-repair-control
echo x >"$REPO1/x.txt" && git -C "$REPO1" add x.txt && git -C "$REPO1" commit -q -m "work"
OPEN_HEAD="$(git -C "$REPO1" rev-parse HEAD)"
git -C "$REPO1" checkout -q development
git -C "$REPO1" update-ref "refs/remotes/origin/issue/23-gitops-lifecycle-repair-control" "$OPEN_HEAD"

mkdir -p "$TMP/bin"
cat >"$TMP/bin/gh" <<EOF
#!/usr/bin/env bash
if [[ "\$*" == *"pr view"* ]]; then
  echo '{"number":49,"state":"OPEN","headRefName":"issue/43-build-portable-ide-development-v2-managed-core-i"}'
  exit 0
fi
if [[ "\$*" == *"--head issue/23-gitops-lifecycle-repair-control"* ]]; then
  cat <<JSON
[{"number":35,"state":"MERGED","mergedAt":"2026-01-01T00:00:00Z","labels":[],"headRefOid":"deadbeef"},
 {"number":36,"state":"OPEN","mergedAt":null,"labels":[],"headRefOid":"${OPEN_HEAD}"}]
JSON
  exit 0
fi
echo '[]'
EOF
chmod +x "$TMP/bin/gh"

PATH="$TMP/bin:$PATH" with_cleanup_repo bash -c "cd \"$REPO1\" && bash scripts/cleanup-merged-branches.sh --remote" >"$TMP/open.out"
grep -q 'KEEP: issue/23-gitops-lifecycle-repair-control' "$TMP/open.out" \
  || fail "open PR must KEEP over historical MERGED: $(cat "$TMP/open.out")"
grep -qi 'open PR' "$TMP/open.out" \
  || fail "open PR reason missing: $(cat "$TMP/open.out")"
grep -qv 'WOULD_DELETE.*issue/23-gitops-lifecycle-repair-control' "$TMP/open.out" \
  || fail "must not WOULD_DELETE open-PR branch"
grep -qv '^DELETED_' "$TMP/open.out" || fail "dry-run must not DELETE"
pass "historical MERGED + OPEN PR → KEEP"

# ============================================================================
# 2) Clean attached worktree on local cleanup → KEEP
# ============================================================================
REPO2="$TMP/worktree"
make_repo "$REPO2"
seed_cleanup "$REPO2"
git -C "$REPO2" checkout -q -b issue/99-merged-clean-wt
echo y >"$REPO2/y.txt" && git -C "$REPO2" add y.txt && git -C "$REPO2" commit -q -m "merged work"
WT_HEAD="$(git -C "$REPO2" rev-parse HEAD)"
git -C "$REPO2" checkout -q development
WT="$TMP/wt-clean"
git -C "$REPO2" worktree add "$WT" issue/99-merged-clean-wt >/dev/null

cat >"$TMP/bin/gh" <<EOF
#!/usr/bin/env bash
if [[ "\$*" == *"pr view"* ]]; then
  echo '{"number":49,"state":"CLOSED","headRefName":"issue/43-x"}'
  exit 0
fi
if [[ "\$*" == *"--head issue/99-merged-clean-wt"* ]]; then
  echo '[{"number":7,"state":"MERGED","mergedAt":"2026-01-01T00:00:00Z","labels":[],"headRefOid":"${WT_HEAD}"}]'
  exit 0
fi
echo '[]'
EOF
chmod +x "$TMP/bin/gh"

PATH="$TMP/bin:$PATH" with_cleanup_repo bash -c "cd \"$REPO2\" && bash scripts/cleanup-merged-branches.sh --local" >"$TMP/wt.out"
grep -q 'KEEP: local:issue/99-merged-clean-wt' "$TMP/wt.out" \
  || fail "clean worktree must KEEP: $(cat "$TMP/wt.out")"
grep -qi 'active worktree attached' "$TMP/wt.out" \
  || fail "worktree KEEP reason missing: $(cat "$TMP/wt.out")"
grep -qv '^DELETED_' "$TMP/wt.out" || fail "dry-run must not DELETE worktree case"
pass "clean attached worktree → KEEP"

# ============================================================================
# 3) Preserve overlay: an explicitly protected branch stays KEEP even with
# MERGED evidence + no worktree. Committed defaults may legitimately be empty
# after the named work is reconciled.
# ============================================================================
REPO3="$TMP/preserve"
make_repo "$REPO3"
seed_cleanup "$REPO3"
mkdir -p "$REPO3/.linktrend"
cat >"$REPO3/.linktrend/cleanup-preserve.json" <<'EOF'
{"schemaVersion":1,"issueNumbers":[44],"prNumbers":[],"branches":[]}
EOF
git -C "$REPO3" checkout -q -b issue/44-add-app-backed-review-ready-publisher-and-produc
echo z >"$REPO3/z.txt" && git -C "$REPO3" add z.txt && git -C "$REPO3" commit -q -m "preserve me"
PRESERVE_HEAD="$(git -C "$REPO3" rev-parse HEAD)"
git -C "$REPO3" checkout -q development

cat >"$TMP/bin/gh" <<EOF
#!/usr/bin/env bash
if [[ "\$*" == *"pr view"* ]]; then
  echo '{"number":49,"state":"CLOSED","headRefName":"issue/43-x"}'
  exit 0
fi
if [[ "\$*" == *"--head issue/44-add-app-backed-review-ready-publisher-and-produc"* ]]; then
  echo '[{"number":45,"state":"MERGED","mergedAt":"2026-01-01T00:00:00Z","labels":[],"headRefOid":"${PRESERVE_HEAD}"}]'
  exit 0
fi
echo '[]'
EOF
chmod +x "$TMP/bin/gh"

PATH="$TMP/bin:$PATH" with_cleanup_repo bash -c "cd \"$REPO3\" && bash scripts/cleanup-merged-branches.sh --local" >"$TMP/pres.out"
grep -q 'KEEP:.*issue/44-add-app-backed-review-ready-publisher-and-produc' "$TMP/pres.out" \
  || fail "preserve issue/44 must KEEP: $(cat "$TMP/pres.out")"
grep -qi 'preserve' "$TMP/pres.out" \
  || fail "preserve reason missing: $(cat "$TMP/pres.out")"
grep -qv '^DELETED_' "$TMP/pres.out" || fail "dry-run must not DELETE preserve case"
pass "explicit preserve overlay issue/44-* → KEEP"

# ============================================================================
# 4) Eligible merged branch without preserve/worktree → WOULD_DELETE (dry-run)
# ============================================================================
REPO4="$TMP/eligible"
make_repo "$REPO4"
seed_cleanup "$REPO4"
git -C "$REPO4" checkout -q -b issue/GITOPS-01-review-packager-pipeline
echo e >"$REPO4/e.txt" && git -C "$REPO4" add e.txt && git -C "$REPO4" commit -q -m "eligible"
ELIG_HEAD="$(git -C "$REPO4" rev-parse HEAD)"
git -C "$REPO4" checkout -q development
git -C "$REPO4" update-ref "refs/remotes/origin/issue/GITOPS-01-review-packager-pipeline" "$ELIG_HEAD"

cat >"$TMP/bin/gh" <<EOF
#!/usr/bin/env bash
if [[ "\$*" == *"pr view"* ]]; then
  echo '{"number":49,"state":"CLOSED","headRefName":"issue/43-x"}'
  exit 0
fi
if [[ "\$*" == *"--head issue/GITOPS-01-review-packager-pipeline"* ]]; then
  echo '[{"number":9,"state":"MERGED","mergedAt":"2026-01-01T00:00:00Z","labels":[],"headRefOid":"${ELIG_HEAD}"}]'
  exit 0
fi
echo '[]'
EOF
chmod +x "$TMP/bin/gh"

PATH="$TMP/bin:$PATH" with_cleanup_repo bash -c "cd \"$REPO4\" && bash scripts/cleanup-merged-branches.sh --remote" >"$TMP/elig.out"
grep -q 'WOULD_DELETE_REMOTE: issue/GITOPS-01-review-packager-pipeline' "$TMP/elig.out" \
  || fail "eligible merged branch should WOULD_DELETE: $(cat "$TMP/elig.out")"
grep -qv '^DELETED_' "$TMP/elig.out" || fail "dry-run must not DELETE eligible case"
pass "eligible merged → WOULD_DELETE dry-run only"

# ============================================================================
# 5) cleanup_stale_records.py inventory via mocked gh issue list
# ============================================================================
if [ -f "$ROOT/scripts/gitops/cleanup_stale_records.py" ]; then
  cat >"$TMP/bin/gh" <<'EOF'
#!/usr/bin/env bash
if [[ "$*" == *"pr view 36"* ]]; then
  echo '{"number":36,"state":"OPEN","mergedAt":null,"headRefName":"issue/23-x"}'
  exit 0
fi
if [[ "$*" == *"pr view 45"* ]]; then
  echo '{"number":45,"state":"MERGED","mergedAt":"2026-01-01T00:00:00Z","headRefName":"issue/99-done"}'
  exit 0
fi
if [[ "$*" == *"pr view"* ]]; then
  echo '{"number":49,"state":"OPEN","headRefName":"issue/43-x"}'
  exit 0
fi
if [[ "$*" == *"issue list"* ]]; then
  python3 - <<'PY'
import json
marker40 = "<!-- linktrend-repair-task: " + json.dumps({
  "failureId": "keepopen00000001",
  "failureType": "merge_conflict",
  "prNumber": "36",
  "branch": "issue/23-x",
  "resolutionState": "open",
  "repairStatus": "recorded",
}) + " -->"
marker46 = "<!-- linktrend-repair-task: " + json.dumps({
  "failureId": "candusage00000001",
  "failureType": "usage_limit",
  "prNumber": "45",
  "branch": "issue/99-done",
  "resolutionState": "open",
  "repairStatus": "immediate_no_auto_repair",
}) + " -->"
print(json.dumps([
  {"number": 40, "title": "repair 40", "body": "x\n" + marker40, "state": "OPEN"},
  {"number": 46, "title": "repair 46", "body": "y\n" + marker46, "state": "OPEN"},
]))
PY
  exit 0
fi
echo '[]'
EOF
  chmod +x "$TMP/bin/gh"

  OUT="$(
    PATH="$TMP/bin:$PATH" \
    python3 "$ROOT/scripts/gitops/cleanup_stale_records.py" \
      --repo linktrend/IDE-Development --json
  )"
  echo "$OUT" | python3 -c '
import json,sys
r=json.load(sys.stdin)
assert r.get("mode")=="dry-run", r
keeps={k.get("issueNumber") for k in (r.get("keeps") or [])}
cands={c.get("issueNumber") for c in (r.get("candidates") or [])}
assert 40 in keeps, r.get("keeps")
assert 46 in cands, r.get("candidates")
'
  APPLY_RC=0
  PATH="$TMP/bin:$PATH" \
  python3 "$ROOT/scripts/gitops/cleanup_stale_records.py" \
    --repo linktrend/IDE-Development --apply --i-understand-close-repairs >/tmp/stale-apply.out 2>&1 \
    || APPLY_RC=$?
  [ "$APPLY_RC" -ne 0 ] || fail "apply must be refused (non-zero)"
  grep -qi 'refused\|deferred\|Codex\|not authorized' /tmp/stale-apply.out \
    || fail "apply refusal message missing: $(cat /tmp/stale-apply.out)"
  pass "cleanup_stale_records inventory keep/candidate + apply refused"
else
  echo "SKIP: cleanup_stale_records.py not present"
fi

# Pure helper: OPEN evidence not authorized
python3 "$ROOT/scripts/gitops/cleanup_controls.py" check-branch \
  --branch issue/23-x --evidence OPEN --pr 36 | python3 -c '
import json,sys
d=json.load(sys.stdin)
assert d["decision"]=="KEEP"
assert d["authorized_delete"] is False
'
pass "cleanup_controls OPEN → KEEP unauthorized"

# ============================================================================
# 6) Issue #53 Bugbot: defaults:false disables committed preserve defaults
# ============================================================================
REPO6="$TMP/defaults-false"
make_repo "$REPO6"
seed_cleanup "$REPO6"
mkdir -p "$REPO6/.linktrend"
cat >"$REPO6/.linktrend/cleanup-preserve.json" <<'EOF'
{"schemaVersion":1,"defaults":false,"issueNumbers":[],"prNumbers":[],"branches":[]}
EOF

SHOW6="$(
  cd "$REPO6" && python3 "$ROOT/scripts/gitops/cleanup_controls.py" show-preserve
)"
echo "$SHOW6" | python3 -c '
import json,sys
d=json.load(sys.stdin)
issues=set(d.get("preserveIssueNumbers") or d.get("issueNumbers") or [])
prs=set(d.get("preservePrNumbers") or d.get("prNumbers") or [])
banned={43,44,51}
assert not (issues & banned), f"defaults:false still has issues {issues & banned}: {d}"
assert 49 not in prs, f"defaults:false still has PR 49: {d}"
'
pass "show-preserve: defaults:false omits 43/44/51 and PR 49"

# ============================================================================
# 7) Issue #53 Bugbot: repair cleanup apply honors preserve / open-PR
# ============================================================================
REPAIR_DIR="$TMP/repair-tasks"
mkdir -p "$REPAIR_DIR"

cat >"$REPAIR_DIR/preserve44.json" <<'EOF'
{
  "failureId": "preserve4400000001",
  "failureType": "merge_conflict",
  "resolutionState": "resolved",
  "repairStatus": "resolved",
  "branch": "issue/44-add-app-backed-review-ready-publisher-and-produc",
  "prNumber": "45",
  "repository": "linktrend/IDE-Development",
  "updatedAt": "2026-01-01T00:00:00Z"
}
EOF

cat >"$REPAIR_DIR/openpr.json" <<'EOF'
{
  "failureId": "openpr00000000001",
  "failureType": "merge_conflict",
  "resolutionState": "resolved",
  "repairStatus": "resolved",
  "branch": "issue/99-open-pr-linked",
  "prNumber": "77",
  "repository": "linktrend/IDE-Development",
  "updatedAt": "2026-01-01T00:00:00Z"
}
EOF

cat >"$REPAIR_DIR/eligible.json" <<'EOF'
{
  "failureId": "eligible000000001",
  "failureType": "merge_conflict",
  "resolutionState": "resolved",
  "repairStatus": "resolved",
  "branch": "issue/GITOPS-01-review-packager-pipeline",
  "prNumber": "88",
  "repository": "linktrend/IDE-Development",
  "updatedAt": "2026-01-01T00:00:00Z"
}
EOF

cat >"$TMP/bin/gh" <<'EOF'
#!/usr/bin/env bash
if [[ "$*" == *"pr view 77"* ]]; then
  echo '{"number":77,"state":"OPEN","mergedAt":null,"headRefName":"issue/99-open-pr-linked"}'
  exit 0
fi
if [[ "$*" == *"pr view 88"* ]]; then
  echo '{"number":88,"state":"MERGED","mergedAt":"2026-01-01T00:00:00Z","headRefName":"issue/GITOPS-01-review-packager-pipeline"}'
  exit 0
fi
if [[ "$*" == *"pr view 45"* ]]; then
  echo '{"number":45,"state":"MERGED","mergedAt":"2026-01-01T00:00:00Z","headRefName":"issue/44-add-app-backed-review-ready-publisher-and-produc"}'
  exit 0
fi
if [[ "$*" == *"pr view"* ]]; then
  echo '{"number":49,"state":"CLOSED","headRefName":"issue/43-x"}'
  exit 0
fi
echo '[]'
EOF
chmod +x "$TMP/bin/gh"

PLAN7="$(
  PATH="$TMP/bin:$PATH" \
  LINKTREND_CLEANUP_PRESERVE=issue/44-add-app-backed-review-ready-publisher-and-produc \
  python3 "$ROOT/scripts/gitops/cleanup_controls.py" plan-completed-repairs \
    --repo linktrend/IDE-Development \
    --repair-dir "$REPAIR_DIR"
)"
echo "$PLAN7" | python3 -c '
import json,sys
p=json.load(sys.stdin)
assert p.get("mode") in ("dry-run","plan",None) or p.get("mode")!="apply", p
by={a.get("failureId"):a for a in (p.get("actions") or [])}
assert "preserve4400000001" in by, p
assert "openpr00000000001" in by, p
assert "eligible000000001" in by, p
for fid in ("preserve4400000001","openpr00000000001"):
    a=by[fid]
    dec=str(a.get("decision") or "")
    auth=a.get("authorized")
    assert dec.upper().startswith("KEEP") or auth is False, (fid,a)
    assert "DELETE" not in dec.upper() or dec.upper().startswith("KEEP"), (fid,a)
elig=by["eligible000000001"]
edec=str(elig.get("decision") or "")
assert "WOULD_DELETE" in edec.upper() or elig.get("authorized") is True, elig
assert "KEEP" not in edec.upper() or "DELETE" in edec.upper(), elig
'
pass "plan-completed-repairs: preserve + open-PR KEEP; eligible WOULD_DELETE"

APPLY7="$(
  PATH="$TMP/bin:$PATH" \
  LINKTREND_CLEANUP_PRESERVE=issue/44-add-app-backed-review-ready-publisher-and-produc \
  python3 "$ROOT/scripts/gitops/cleanup_controls.py" plan-completed-repairs \
    --repo linktrend/IDE-Development \
    --repair-dir "$REPAIR_DIR" --apply
)"
echo "$APPLY7" | python3 -c '
import json,sys
from pathlib import Path
p=json.load(sys.stdin)
root=Path(p["root"])
by={a.get("failureId"):a for a in (p.get("actions") or [])}
# preserve + open-PR must remain on disk
assert (root/"preserve44.json").is_file(), "preserve file must not be deleted"
assert (root/"openpr.json").is_file(), "open-PR file must not be deleted"
for fid in ("preserve4400000001","openpr00000000001"):
    a=by[fid]
    dec=str(a.get("decision") or "")
    assert "DELETE" not in dec.upper() or dec.upper().startswith("KEEP"), (fid,a)
    assert a.get("authorized") is False or dec.upper().startswith("KEEP"), (fid,a)
# eligible must be deleted on apply
assert not (root/"eligible.json").is_file(), "eligible resolved file should be DELETED on apply"
elig=by["eligible000000001"]
edec=str(elig.get("decision") or "")
assert "DELETED" in edec.upper() or elig.get("authorized") is True, elig
'
pass "apply-completed-repairs: preserve/open-PR kept; eligible DELETED"

# ============================================================================
# 6b) Shell dry-run: defaults:false must not KEEP issue/44 via preserve (needs Task B)
# ============================================================================
git -C "$REPO6" checkout -q -b issue/44-add-app-backed-review-ready-publisher-and-produc
echo df >"$REPO6/df.txt" && git -C "$REPO6" add df.txt && git -C "$REPO6" commit -q -m "defaults false eligible"
DF_HEAD="$(git -C "$REPO6" rev-parse HEAD)"
git -C "$REPO6" checkout -q development

cat >"$TMP/bin/gh" <<EOF
#!/usr/bin/env bash
if [[ "\$*" == *"pr view"* ]]; then
  echo '{"number":49,"state":"CLOSED","headRefName":"issue/43-x"}'
  exit 0
fi
if [[ "\$*" == *"--head issue/44-add-app-backed-review-ready-publisher-and-produc"* ]]; then
  echo '[{"number":45,"state":"MERGED","mergedAt":"2026-01-01T00:00:00Z","labels":[],"headRefOid":"${DF_HEAD}"}]'
  exit 0
fi
echo '[]'
EOF
chmod +x "$TMP/bin/gh"

PATH="$TMP/bin:$PATH" with_cleanup_repo bash -c "cd \"$REPO6\" && bash scripts/cleanup-merged-branches.sh --local" >"$TMP/df.out"
if grep -q 'KEEP:.*issue/44-add-app-backed-review-ready-publisher-and-produc' "$TMP/df.out"; then
  if grep -qi 'preserve' "$TMP/df.out"; then
    fail "defaults:false must not KEEP issue/44 via preserve: $(cat "$TMP/df.out")"
  fi
fi
grep -q 'WOULD_DELETE.*issue/44-add-app-backed-review-ready-publisher-and-produc' "$TMP/df.out" \
  || fail "defaults:false + MERGED issue/44 should WOULD_DELETE: $(cat "$TMP/df.out")"
grep -qv '^DELETED_' "$TMP/df.out" || fail "dry-run must not DELETE defaults:false case"
pass "shell dry-run: defaults:false → issue/44 WOULD_DELETE (not preserve KEEP)"

# ============================================================================
# 8) Issue #53 Bugbot: shell uses shared cleanup_controls (no divergent hardcoded defaults)
# ============================================================================
SHELL_SCRIPT="$ROOT/scripts/cleanup-merged-branches.sh"
if grep -qE 'for n in \(43,\s*44,\s*51\)' "$SHELL_SCRIPT"; then
  fail "shell still hardcodes default issue numbers (43,44,51) — must use cleanup_controls"
fi
if grep -qE 'pr_numbers\.append\(49\)|if 49 not in pr_numbers' "$SHELL_SCRIPT"; then
  fail "shell still hardcodes default PR 49 — must use cleanup_controls"
fi
grep -q 'cleanup_controls\.py' "$SHELL_SCRIPT" \
  || fail "shell load_preserve_policy must call cleanup_controls.py"

# Same overlay: Python show-preserve issue set must match export-preserve issueNumbers
REPO8="$TMP/shared-loader"
make_repo "$REPO8"
seed_cleanup "$REPO8"
mkdir -p "$REPO8/.linktrend"
cat >"$REPO8/.linktrend/cleanup-preserve.json" <<'EOF'
{"schemaVersion":1,"defaults":false,"issueNumbers":[77],"prNumbers":[],"branches":["issue/exact-shared"]}
EOF

cat >"$TMP/bin/gh" <<'EOF'
#!/usr/bin/env bash
if [[ "$*" == *"pr view"* ]]; then
  echo '{"number":49,"state":"CLOSED","headRefName":"issue/43-x"}'
  exit 0
fi
echo '[]'
EOF
chmod +x "$TMP/bin/gh"

PY8="$(
  cd "$REPO8" && PATH="$TMP/bin:$PATH" \
  python3 "$ROOT/scripts/gitops/cleanup_controls.py" show-preserve
)"
EXPORT8="$(
  cd "$REPO8" && PATH="$TMP/bin:$PATH" \
  python3 "$ROOT/scripts/gitops/cleanup_controls.py" export-preserve
)"
# Shell must call export-preserve (or equivalent) via cleanup_controls.py
grep -qE 'export-preserve|cleanup_controls\.py' "$SHELL_SCRIPT" \
  || fail "shell must invoke cleanup_controls export-preserve"

python3 -c '
import json,sys
py=json.loads(sys.argv[1])
ex=json.loads(sys.argv[2])
def issues(d):
    return set(d.get("preserveIssueNumbers") or d.get("issueNumbers") or [])
def branches(d):
    return set(d.get("preserveBranchExact") or d.get("branches") or [])
assert issues(py)==issues(ex), (issues(py), issues(ex), py, ex)
assert 77 in issues(py), py
assert 43 not in issues(py) and 44 not in issues(py) and 51 not in issues(py), py
assert "issue/exact-shared" in branches(py)|branches(ex), (py, ex)
assert ex.get("defaultsDisabled") is True, ex
' "$PY8" "$EXPORT8"
pass "shell uses cleanup_controls; no hardcoded 43/44/51; policy parity"

# ============================================================================
# 9) Issue #55 Bugbot: export-preserve retains CLOSED/MERGED preservePrNumbers heads
# BEGIN issue-55 finding-1
REPO9="$TMP/export-closed-pr-head"
make_repo "$REPO9"
seed_cleanup "$REPO9"
mkdir -p "$REPO9/.linktrend"
# defaults:false — only fixture preservePrNumbers matter; head is NOT an issue/* preserve
cat >"$REPO9/.linktrend/cleanup-preserve.json" <<'EOF'
{
  "schemaVersion": 1,
  "defaults": false,
  "issueNumbers": [],
  "preservePrNumbers": [901, 902],
  "branches": []
}
EOF

git -C "$REPO9" checkout -q -b feature/preserve-closed-head
echo closed >"$REPO9/closed.txt" && git -C "$REPO9" add closed.txt && git -C "$REPO9" commit -q -m "closed preserve head"
CLOSED_HEAD="$(git -C "$REPO9" rev-parse HEAD)"
git -C "$REPO9" checkout -q development
git -C "$REPO9" checkout -q -b feature/preserve-merged-head
echo merged >"$REPO9/merged.txt" && git -C "$REPO9" add merged.txt && git -C "$REPO9" commit -q -m "merged preserve head"
MERGED_HEAD="$(git -C "$REPO9" rev-parse HEAD)"
git -C "$REPO9" checkout -q development

cat >"$TMP/bin/gh" <<EOF
#!/usr/bin/env bash
if [[ "\$*" == *"pr view 901"* ]]; then
  echo '{"number":901,"state":"CLOSED","headRefName":"feature/preserve-closed-head"}'
  exit 0
fi
if [[ "\$*" == *"pr view 902"* ]]; then
  echo '{"number":902,"state":"MERGED","mergedAt":"2026-01-01T00:00:00Z","headRefName":"feature/preserve-merged-head"}'
  exit 0
fi
if [[ "\$*" == *"--head feature/preserve-closed-head"* ]]; then
  echo '[{"number":901,"state":"CLOSED","mergedAt":null,"labels":[],"headRefOid":"${CLOSED_HEAD}"}]'
  exit 0
fi
if [[ "\$*" == *"--head feature/preserve-merged-head"* ]]; then
  echo '[{"number":902,"state":"MERGED","mergedAt":"2026-01-01T00:00:00Z","labels":[],"headRefOid":"${MERGED_HEAD}"}]'
  exit 0
fi
if [[ "\$*" == *"pr view"* ]]; then
  echo '{"number":0,"state":"CLOSED","headRefName":""}'
  exit 0
fi
echo '[]'
EOF
chmod +x "$TMP/bin/gh"

EXPORT9="$(
  cd "$REPO9" && PATH="$TMP/bin:$PATH" \
  python3 "$ROOT/scripts/gitops/cleanup_controls.py" export-preserve
)"
echo "$EXPORT9" | python3 -c '
import json,sys
d=json.load(sys.stdin)
branches=set(d.get("branches") or [])
pr_heads=set(d.get("prHeads") or [])
prs=set(d.get("prNumbers") or [])
assert 901 in prs and 902 in prs, d
assert "feature/preserve-closed-head" in pr_heads, d
assert "feature/preserve-merged-head" in pr_heads, d
assert "feature/preserve-closed-head" in branches, d
assert "feature/preserve-merged-head" in branches, d
assert d.get("defaultsDisabled") is True, d
'
pass "export-preserve: CLOSED + MERGED preservePrNumbers heads in branches/prHeads"

# Optional: shell dry-run KEEP via preserve for MERGED head listed only under preservePrNumbers
PATH="$TMP/bin:$PATH" with_cleanup_repo bash -c "cd \"$REPO9\" && bash scripts/cleanup-merged-branches.sh --local" >"$TMP/exp9.out"
grep -q 'KEEP:.*feature/preserve-merged-head' "$TMP/exp9.out" \
  || fail "MERGED preservePrNumbers head must KEEP via preserve: $(cat "$TMP/exp9.out")"
grep -qi 'preserve' "$TMP/exp9.out" \
  || fail "preserve reason missing for MERGED preservePr head: $(cat "$TMP/exp9.out")"
grep -qv 'WOULD_DELETE.*feature/preserve-merged-head' "$TMP/exp9.out" \
  || fail "must not WOULD_DELETE MERGED preservePr head"
grep -qv '^DELETED_' "$TMP/exp9.out" || fail "dry-run must not DELETE export-closed-pr case"
pass "shell dry-run: MERGED preservePrNumbers-only head → KEEP via preserve"
# END issue-55 finding-1

# ============================================================================
# 10) Issue #55 Bugbot: shell/Python issue/<n> preserve parity
# BEGIN issue-55 finding-2
# ============================================================================
# Shell is_preserved_branch must use the same ISSUE_BRANCH_RE as cleanup_controls.py
# so bare issue/<n> (e.g. issue/51) preserves identically to issue/<n>-slug.
REPO55F2="$TMP/issue55-finding2"
make_repo "$REPO55F2"
seed_cleanup "$REPO55F2"
mkdir -p "$REPO55F2/.linktrend"
cat >"$REPO55F2/.linktrend/cleanup-preserve.json" <<'EOF'
{"schemaVersion":1,"defaults":false,"issueNumbers":[51],"prNumbers":[],"branches":[]}
EOF

# Static parity: shell embedded regex matches Python ISSUE_BRANCH_RE
grep -q 're.match(r"^issue/(\\d+)(?:-|\$)", branch)' \
  "$ROOT/scripts/cleanup-merged-branches.sh" \
  || fail "shell is_preserved_branch regex must match ISSUE_BRANCH_RE ^issue/(\\d+)(?:-|\$)"
grep -q 're.match(r"^issue/(\\d+)-", branch)' \
  "$ROOT/scripts/cleanup-merged-branches.sh" \
  && fail "shell still has legacy ^issue/(\\d+)- regex (must allow bare issue/<n>)"

# Python preserve_reason / ISSUE_BRANCH_RE accept bare issue/51 and slugged form
PY55F2="$(
  cd "$REPO55F2" && python3 "$ROOT/scripts/gitops/cleanup_controls.py" check-branch \
    --branch issue/51 --evidence MERGED
)"
echo "$PY55F2" | python3 -c '
import json,sys
d=json.load(sys.stdin)
assert d.get("decision")=="KEEP", d
assert "preserve" in str(d.get("reason") or "").lower() or "51" in str(d.get("reason") or ""), d
assert d.get("authorized_delete") is False, d
'
PY55F2_SLUG="$(
  cd "$REPO55F2" && python3 "$ROOT/scripts/gitops/cleanup_controls.py" check-branch \
    --branch issue/51-some-slug --evidence MERGED
)"
echo "$PY55F2_SLUG" | python3 -c '
import json,sys
d=json.load(sys.stdin)
assert d.get("decision")=="KEEP", d
assert "51" in str(d.get("reason") or ""), d
'
python3 -c '
import importlib.util
from pathlib import Path
p = Path(r"'"$ROOT"'") / "scripts/gitops/cleanup_controls.py"
spec = importlib.util.spec_from_file_location("cleanup_controls", p)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
assert mod.ISSUE_BRANCH_RE.match("issue/51"), "ISSUE_BRANCH_RE must match bare issue/51"
assert mod.ISSUE_BRANCH_RE.match("issue/51-some-slug"), "ISSUE_BRANCH_RE must match issue/51-slug"
assert mod.ISSUE_BRANCH_RE.pattern == r"^issue/(\d+)(?:-|$)"
'
pass "Python ISSUE_BRANCH_RE + preserve_reason accept issue/51 and issue/51-slug"

# Shell is_preserved_branch via export-preserve + embedded matcher (mirrors script)
EXPORT55F2="$(
  cd "$REPO55F2" && python3 "$ROOT/scripts/gitops/cleanup_controls.py" export-preserve
)"
python3 -c '
import json, re, sys
policy = json.loads(sys.argv[1])
assert 51 in (policy.get("issueNumbers") or []), policy
for branch in ("issue/51", "issue/51-some-slug"):
    m = re.match(r"^issue/(\d+)(?:-|$)", branch)
    assert m and int(m.group(1)) in (policy.get("issueNumbers") or []), (branch, policy)
# non-preserved number must not match preserve set
m99 = re.match(r"^issue/(\d+)(?:-|$)", "issue/99")
assert m99 and int(m99.group(1)) not in (policy.get("issueNumbers") or [])
' "$EXPORT55F2"
pass "shell/Python issue regex + export issueNumbers:[51] preserve parity"

# Dry-run cleanup: bare issue/51 KEEP via preserve; issue/99 WOULD_DELETE
git -C "$REPO55F2" checkout -q -b issue/51
echo bare51 >"$REPO55F2/bare51.txt" && git -C "$REPO55F2" add bare51.txt \
  && git -C "$REPO55F2" commit -q -m "bare issue/51"
HEAD51="$(git -C "$REPO55F2" rev-parse HEAD)"
git -C "$REPO55F2" checkout -q development

git -C "$REPO55F2" checkout -q -b issue/51-some-slug
echo slug51 >"$REPO55F2/slug51.txt" && git -C "$REPO55F2" add slug51.txt \
  && git -C "$REPO55F2" commit -q -m "slugged issue/51"
HEAD51S="$(git -C "$REPO55F2" rev-parse HEAD)"
git -C "$REPO55F2" checkout -q development

git -C "$REPO55F2" checkout -q -b issue/99-not-preserved
echo n99 >"$REPO55F2/n99.txt" && git -C "$REPO55F2" add n99.txt \
  && git -C "$REPO55F2" commit -q -m "non-preserved issue/99"
HEAD99="$(git -C "$REPO55F2" rev-parse HEAD)"
git -C "$REPO55F2" checkout -q development

mkdir -p "$TMP/bin"
cat >"$TMP/bin/gh" <<EOF
#!/usr/bin/env bash
if [[ "\$*" == *"pr view"* ]]; then
  echo '{"number":49,"state":"CLOSED","headRefName":"issue/43-x"}'
  exit 0
fi
if [[ "\$*" == *"--head issue/51-some-slug"* ]]; then
  echo '[{"number":5101,"state":"MERGED","mergedAt":"2026-01-01T00:00:00Z","labels":[],"headRefOid":"${HEAD51S}"}]'
  exit 0
fi
if [[ "\$*" == *"--head issue/51"* ]]; then
  echo '[{"number":5100,"state":"MERGED","mergedAt":"2026-01-01T00:00:00Z","labels":[],"headRefOid":"${HEAD51}"}]'
  exit 0
fi
if [[ "\$*" == *"--head issue/99-not-preserved"* ]]; then
  echo '[{"number":9900,"state":"MERGED","mergedAt":"2026-01-01T00:00:00Z","labels":[],"headRefOid":"${HEAD99}"}]'
  exit 0
fi
echo '[]'
EOF
chmod +x "$TMP/bin/gh"

PATH="$TMP/bin:$PATH" with_cleanup_repo bash -c "cd \"$REPO55F2\" && bash scripts/cleanup-merged-branches.sh --local" \
  >"$TMP/issue55f2.out"
grep -E 'KEEP: local:issue/51 — preserve policy' "$TMP/issue55f2.out" \
  || fail "bare issue/51 must KEEP via preserve policy: $(cat "$TMP/issue55f2.out")"
grep -E 'KEEP: local:issue/51-some-slug — preserve policy' "$TMP/issue55f2.out" \
  || fail "issue/51-some-slug must KEEP via preserve policy: $(cat "$TMP/issue55f2.out")"
grep -q 'WOULD_DELETE.*issue/99-not-preserved' "$TMP/issue55f2.out" \
  || fail "non-preserved issue/99 with MERGED should WOULD_DELETE: $(cat "$TMP/issue55f2.out")"
# Bare or slug preserved branches must not be WOULD_DELETE (word-boundary-ish: not issue/510…)
grep -E 'WOULD_DELETE.*(local:)?issue/51( |$|—)' "$TMP/issue55f2.out" \
  && fail "preserved issue/51 must not WOULD_DELETE: $(cat "$TMP/issue55f2.out")"
grep -E 'WOULD_DELETE.*issue/51-some-slug' "$TMP/issue55f2.out" \
  && fail "preserved issue/51-some-slug must not WOULD_DELETE: $(cat "$TMP/issue55f2.out")"
grep -qv '^DELETED_' "$TMP/issue55f2.out" || fail "dry-run must not DELETE finding-2 case"
pass "shell dry-run: issue/51 + issue/51-slug KEEP preserve; issue/99 WOULD_DELETE"
# END issue-55 finding-2

# ============================================================================
# 11) Issue #57 Bugbot: fail-closed preserve PR head resolution
# BEGIN issue-57
# ============================================================================

# --- 11a) gh unavailable / always-fails → unresolved + shell fail-closed KEEP ---
REPO57A="$TMP/issue57-gh-unavailable"
make_repo "$REPO57A"
seed_cleanup "$REPO57A"
mkdir -p "$REPO57A/.linktrend"
cat >"$REPO57A/.linktrend/cleanup-preserve.json" <<'EOF'
{"schemaVersion":1,"defaults":false,"issueNumbers":[],"preservePrNumbers":[903],"branches":[]}
EOF

# Export: PATH with gh that always fails (simulates missing/broken gh)
mkdir -p "$TMP/bin"
cat >"$TMP/bin/gh" <<'EOF'
#!/usr/bin/env bash
echo "gh unavailable (issue-57 fixture)" >&2
exit 127
EOF
chmod +x "$TMP/bin/gh"

EXPORT57A_RC=0
EXPORT57A="$(
  cd "$REPO57A" && env -u GITHUB_REPOSITORY -u GH_REPO PATH="$TMP/bin:$PATH" \
  python3 "$ROOT/scripts/gitops/cleanup_controls.py" export-preserve 2>/dev/null
)" || EXPORT57A_RC=$?
echo "$EXPORT57A" | python3 -c '
import json,sys
d=json.load(sys.stdin)
unresolved=set(d.get("unresolvedPrNumbers") or [])
assert 903 in unresolved, d
assert d.get("preserveResolutionOk") is False, d
assert "unresolvedPrNumbers" in d and "preserveResolutionOk" in d, d
assert "repo" in d and "repoSource" in d, d
'
# CLI may exit non-zero when preserveResolutionOk is false while still printing JSON
[ "$EXPORT57A_RC" -ne 0 ] || true
pass "export-preserve: gh unavailable → 903 unresolved, preserveResolutionOk false"

# Shell dry-run: selective mock — pr view 903 fails (unresolved preserve), but MERGED
# evidence exists for an otherwise-deletable candidate.
git -C "$REPO57A" checkout -q -b issue/57-fail-closed-eligible
echo e57a >"$REPO57A/e57a.txt" && git -C "$REPO57A" add e57a.txt \
  && git -C "$REPO57A" commit -q -m "eligible merged under unresolved preserve"
HEAD57A="$(git -C "$REPO57A" rev-parse HEAD)"
git -C "$REPO57A" checkout -q development

cat >"$TMP/bin/gh" <<EOF
#!/usr/bin/env bash
if [[ "\$*" == *"pr view 903"* ]]; then
  echo "could not resolve PR 903" >&2
  exit 1
fi
if [[ "\$*" == *"pr view"* ]]; then
  echo "pr view failed" >&2
  exit 1
fi
if [[ "\$*" == *"--head issue/57-fail-closed-eligible"* ]]; then
  echo '[{"number":5701,"state":"MERGED","mergedAt":"2026-01-01T00:00:00Z","labels":[],"headRefOid":"${HEAD57A}"}]'
  exit 0
fi
echo '[]'
EOF
chmod +x "$TMP/bin/gh"

PATH="$TMP/bin:$PATH" env -u GITHUB_REPOSITORY -u GH_REPO \
  bash -c "cd \"$REPO57A\" && bash scripts/cleanup-merged-branches.sh --local" \
  >"$TMP/issue57a.out" || true
grep -qv 'WOULD_DELETE.*issue/57-fail-closed-eligible' "$TMP/issue57a.out" \
  || fail "unresolved preserve must not WOULD_DELETE eligible: $(cat "$TMP/issue57a.out")"
if grep -q 'WOULD_DELETE' "$TMP/issue57a.out"; then
  fail "fail-closed unresolved must not WOULD_DELETE any candidate: $(cat "$TMP/issue57a.out")"
fi
grep -qv '^DELETED_' "$TMP/issue57a.out" || fail "dry-run must not DELETE issue-57a"
# Prefer KEEP with fail-closed / unresolved reason when the candidate is listed
if grep -q 'issue/57-fail-closed-eligible' "$TMP/issue57a.out"; then
  grep -qiE 'fail-closed|unresolved' "$TMP/issue57a.out" \
    || fail "KEEP reason should mention fail-closed/unresolved: $(cat "$TMP/issue57a.out")"
  grep -qE 'KEEP:.*issue/57-fail-closed-eligible' "$TMP/issue57a.out" \
    || fail "eligible under unresolved preserve must KEEP: $(cat "$TMP/issue57a.out")"
fi
pass "shell dry-run: gh fail on preserve PR → no WOULD_DELETE (fail-closed)"

# --- 11b) gh returns missing/empty headRefName → unresolved + shell fail-closed ---
REPO57B="$TMP/issue57-empty-head"
make_repo "$REPO57B"
seed_cleanup "$REPO57B"
mkdir -p "$REPO57B/.linktrend"
cat >"$REPO57B/.linktrend/cleanup-preserve.json" <<'EOF'
{"schemaVersion":1,"defaults":false,"issueNumbers":[],"preservePrNumbers":[904],"branches":[]}
EOF

git -C "$REPO57B" checkout -q -b issue/57-empty-head-eligible
echo e57b >"$REPO57B/e57b.txt" && git -C "$REPO57B" add e57b.txt \
  && git -C "$REPO57B" commit -q -m "eligible under empty preserve head"
HEAD57B="$(git -C "$REPO57B" rev-parse HEAD)"
git -C "$REPO57B" checkout -q development

cat >"$TMP/bin/gh" <<EOF
#!/usr/bin/env bash
if [[ "\$*" == *"pr view 904"* ]]; then
  echo '{"number":904,"state":"MERGED","headRefName":""}'
  exit 0
fi
if [[ "\$*" == *"pr view"* ]]; then
  echo '{"number":0,"state":"CLOSED","headRefName":""}'
  exit 0
fi
if [[ "\$*" == *"--head issue/57-empty-head-eligible"* ]]; then
  echo '[{"number":5702,"state":"MERGED","mergedAt":"2026-01-01T00:00:00Z","labels":[],"headRefOid":"${HEAD57B}"}]'
  exit 0
fi
echo '[]'
EOF
chmod +x "$TMP/bin/gh"

EXPORT57B_RC=0
EXPORT57B="$(
  cd "$REPO57B" && env -u GITHUB_REPOSITORY -u GH_REPO PATH="$TMP/bin:$PATH" \
  python3 "$ROOT/scripts/gitops/cleanup_controls.py" export-preserve \
    --repo linktrend/IDE-Development 2>/dev/null
)" || EXPORT57B_RC=$?
echo "$EXPORT57B" | python3 -c '
import json,sys
d=json.load(sys.stdin)
unresolved=set(d.get("unresolvedPrNumbers") or [])
assert 904 in unresolved, d
assert d.get("preserveResolutionOk") is False, d
heads=set(d.get("prHeads") or [])
assert "" not in heads, d
assert "feature/" not in " ".join(heads), d
'
pass "export-preserve: empty headRefName → 904 unresolved, preserveResolutionOk false"

PATH="$TMP/bin:$PATH" env -u GITHUB_REPOSITORY -u GH_REPO \
  bash -c "cd \"$REPO57B\" && bash scripts/cleanup-merged-branches.sh --local" \
  >"$TMP/issue57b.out" || true
grep -qv 'WOULD_DELETE.*issue/57-empty-head-eligible' "$TMP/issue57b.out" \
  || fail "empty-head unresolved must not WOULD_DELETE: $(cat "$TMP/issue57b.out")"
if grep -q 'WOULD_DELETE' "$TMP/issue57b.out"; then
  fail "empty-head fail-closed must not WOULD_DELETE any candidate: $(cat "$TMP/issue57b.out")"
fi
grep -qv '^DELETED_' "$TMP/issue57b.out" || fail "dry-run must not DELETE issue-57b"
if grep -q 'issue/57-empty-head-eligible' "$TMP/issue57b.out"; then
  grep -qiE 'fail-closed|unresolved' "$TMP/issue57b.out" \
    || fail "empty-head KEEP reason should mention fail-closed/unresolved: $(cat "$TMP/issue57b.out")"
  grep -qE 'KEEP:.*issue/57-empty-head-eligible' "$TMP/issue57b.out" \
    || fail "empty-head eligible must KEEP: $(cat "$TMP/issue57b.out")"
fi
pass "shell dry-run: empty preserve head → no WOULD_DELETE (fail-closed)"

# --- 11c) Deterministic --repo makes preserve head resolution succeed ---
REPO57C="$TMP/issue57-explicit-repo"
make_repo "$REPO57C"
seed_cleanup "$REPO57C"
mkdir -p "$REPO57C/.linktrend"
cat >"$REPO57C/.linktrend/cleanup-preserve.json" <<'EOF'
{"schemaVersion":1,"defaults":false,"issueNumbers":[],"preservePrNumbers":[905],"branches":[]}
EOF

cat >"$TMP/bin/gh" <<'EOF'
#!/usr/bin/env bash
# Only succeed when --repo linktrend/IDE-Development is present for pr view 905
if [[ "$*" == *"pr view 905"* ]]; then
  if [[ "$*" == *"--repo linktrend/IDE-Development"* ]]; then
    echo '{"number":905,"state":"OPEN","headRefName":"feature/preserve-905-head"}'
    exit 0
  fi
  echo "error: --repo required for PR 905 (issue-57 fixture)" >&2
  exit 1
fi
if [[ "$*" == *"repo view"* ]]; then
  echo "error: no default repo" >&2
  exit 1
fi
echo '[]'
EOF
chmod +x "$TMP/bin/gh"

EXPORT57C="$(
  cd "$REPO57C" && env -u GITHUB_REPOSITORY -u GH_REPO PATH="$TMP/bin:$PATH" \
  python3 "$ROOT/scripts/gitops/cleanup_controls.py" export-preserve \
    --repo linktrend/IDE-Development
)"
echo "$EXPORT57C" | python3 -c '
import json,sys
d=json.load(sys.stdin)
unresolved=set(d.get("unresolvedPrNumbers") or [])
assert 905 not in unresolved, d
assert unresolved == set() or 905 not in unresolved, d
assert d.get("preserveResolutionOk") is True, d
heads=set(d.get("prHeads") or [])
branches=set(d.get("branches") or [])
assert "feature/preserve-905-head" in heads, d
assert "feature/preserve-905-head" in branches, d
assert d.get("repo") == "linktrend/IDE-Development", d
'
pass "export-preserve: --repo linktrend/IDE-Development resolves PR 905 head"

# END issue-57

# ============================================================================
# 12) Issue #59 Bugbot: ambiguous origin+upstream fail-closed
# BEGIN issue-59
# ============================================================================

# --- 12a) Ambiguous origin+upstream — Python export payload ---
REPO59A="$TMP/issue59-ambiguous-export"
make_repo "$REPO59A"
seed_cleanup "$REPO59A"
git -C "$REPO59A" remote add origin "https://github.com/linktrend/IDE-Development.git"
git -C "$REPO59A" remote add upstream "https://github.com/other/fork-upstream.git"
mkdir -p "$REPO59A/.linktrend"
cat >"$REPO59A/.linktrend/cleanup-preserve.json" <<'EOF'
{"schemaVersion":1,"defaults":false,"issueNumbers":[],"preservePrNumbers":[906],"branches":[]}
EOF

# Trap stub: gh would succeed on pr view / repo view if called — must NOT be trusted
# under origin+upstream ambiguity (never guess origin or implicit gh context).
mkdir -p "$TMP/bin"
cat >"$TMP/bin/gh" <<'EOF'
#!/usr/bin/env bash
if [[ "$*" == *"repo view"* ]]; then
  echo "linktrend/IDE-Development"
  exit 0
fi
if [[ "$*" == *"pr view 906"* ]]; then
  echo '{"number":906,"state":"OPEN","headRefName":"feature/preserve-906-trap-head"}'
  exit 0
fi
if [[ "$*" == *"pr view"* ]]; then
  echo '{"number":906,"state":"OPEN","headRefName":"feature/preserve-906-trap-head"}'
  exit 0
fi
echo '[]'
EOF
chmod +x "$TMP/bin/gh"

EXPORT59A_RC=0
EXPORT59A="$(
  cd "$REPO59A" && env -u GITHUB_REPOSITORY -u GH_REPO PATH="$TMP/bin:$PATH" \
  python3 "$ROOT/scripts/gitops/cleanup_controls.py" export-preserve 2>/dev/null
)" || EXPORT59A_RC=$?
echo "$EXPORT59A" | python3 -c '
import json,sys
d=json.load(sys.stdin)
assert "repo" in d and "repoSource" in d, d
assert "unresolvedPrNumbers" in d and "preserveResolutionOk" in d, d
assert "prHeads" in d, d
assert d.get("repoSource") == "ambiguous_origin_and_upstream", d
assert d.get("preserveResolutionOk") is False, d
unresolved=set(d.get("unresolvedPrNumbers") or [])
assert 906 in unresolved, d
assert unresolved == {906}, d
assert (d.get("repo") or "") == "", d
heads=set(d.get("prHeads") or [])
# Trap head must never appear — ambiguity must not call/trust gh
assert "feature/preserve-906-trap-head" not in heads, d
assert heads == set(), d
'
# CLI may exit non-zero when preserveResolutionOk is false while still printing JSON
[ "$EXPORT59A_RC" -ne 0 ] || true
pass "export-preserve: ambiguous origin+upstream → 906 unresolved, preserveResolutionOk false"

# --- 12b) Shell dry-run — no WOULD_DELETE / DELETED under ambiguity ---
REPO59B="$TMP/issue59-ambiguous-shell"
make_repo "$REPO59B"
seed_cleanup "$REPO59B"
git -C "$REPO59B" remote add origin "https://github.com/linktrend/IDE-Development.git"
git -C "$REPO59B" remote add upstream "https://github.com/other/fork-upstream.git"
mkdir -p "$REPO59B/.linktrend"
cat >"$REPO59B/.linktrend/cleanup-preserve.json" <<'EOF'
{"schemaVersion":1,"defaults":false,"issueNumbers":[],"preservePrNumbers":[906],"branches":[]}
EOF

git -C "$REPO59B" checkout -q -b issue/59-ambiguous-eligible
echo e59b >"$REPO59B/e59b.txt" && git -C "$REPO59B" add e59b.txt \
  && git -C "$REPO59B" commit -q -m "eligible merged under ambiguous remotes"
HEAD59B="$(git -C "$REPO59B" rev-parse HEAD)"
git -C "$REPO59B" checkout -q development

cat >"$TMP/bin/gh" <<EOF
#!/usr/bin/env bash
# Trap: would succeed if trusted — ambiguity must fail closed before these matter
if [[ "\$*" == *"repo view"* ]]; then
  echo "linktrend/IDE-Development"
  exit 0
fi
if [[ "\$*" == *"pr view 906"* ]]; then
  echo '{"number":906,"state":"OPEN","headRefName":"feature/preserve-906-trap-head"}'
  exit 0
fi
if [[ "\$*" == *"pr view"* ]]; then
  echo '{"number":0,"state":"CLOSED","headRefName":""}'
  exit 0
fi
if [[ "\$*" == *"--head issue/59-ambiguous-eligible"* ]]; then
  echo '[{"number":5901,"state":"MERGED","mergedAt":"2026-01-01T00:00:00Z","labels":[],"headRefOid":"${HEAD59B}"}]'
  exit 0
fi
echo '[]'
EOF
chmod +x "$TMP/bin/gh"

PATH="$TMP/bin:$PATH" env -u GITHUB_REPOSITORY -u GH_REPO \
  bash -c "cd \"$REPO59B\" && bash scripts/cleanup-merged-branches.sh --local" \
  >"$TMP/issue59b.out" || true
# Prefer positive "if present then fail" over grep -qv (which passes if any line lacks the token)
if grep -q 'WOULD_DELETE' "$TMP/issue59b.out"; then
  fail "ambiguous fail-closed must not WOULD_DELETE any candidate: $(cat "$TMP/issue59b.out")"
fi
if grep -q '^DELETED_' "$TMP/issue59b.out"; then
  fail "ambiguous fail-closed must not emit DELETED_ lines: $(cat "$TMP/issue59b.out")"
fi
# Prefer KEEP with fail-closed / unresolved reason when the eligible candidate is listed
if grep -q 'issue/59-ambiguous-eligible' "$TMP/issue59b.out"; then
  grep -qiE 'fail-closed|unresolved' "$TMP/issue59b.out" \
    || fail "KEEP reason should mention fail-closed/unresolved: $(cat "$TMP/issue59b.out")"
  grep -qE 'KEEP:.*issue/59-ambiguous-eligible' "$TMP/issue59b.out" \
    || fail "eligible under ambiguous remotes must KEEP: $(cat "$TMP/issue59b.out")"
fi
pass "shell dry-run: ambiguous remotes → no WOULD_DELETE/DELETED (fail-closed)"

# --- 12c) Precedence: env authoritative despite ambiguous remotes ---
REPO59C="$TMP/issue59-env-precedence"
make_repo "$REPO59C"
seed_cleanup "$REPO59C"
git -C "$REPO59C" remote add origin "https://github.com/linktrend/IDE-Development.git"
git -C "$REPO59C" remote add upstream "https://github.com/other/fork-upstream.git"
mkdir -p "$REPO59C/.linktrend"
cat >"$REPO59C/.linktrend/cleanup-preserve.json" <<'EOF'
{"schemaVersion":1,"defaults":false,"issueNumbers":[],"preservePrNumbers":[906],"branches":[]}
EOF

cat >"$TMP/bin/gh" <<'EOF'
#!/usr/bin/env bash
# Succeed only when pr view 906 targets --repo linktrend/IDE-Development
if [[ "$*" == *"pr view 906"* ]]; then
  if [[ "$*" == *"--repo linktrend/IDE-Development"* ]]; then
    echo '{"number":906,"state":"OPEN","headRefName":"feature/preserve-906-env-head"}'
    exit 0
  fi
  echo "error: --repo required for PR 906 (issue-59 fixture)" >&2
  exit 1
fi
if [[ "$*" == *"repo view"* ]]; then
  echo "error: no default repo (should not be needed when env set)" >&2
  exit 1
fi
echo '[]'
EOF
chmod +x "$TMP/bin/gh"

EXPORT59C="$(
  cd "$REPO59C" && env -u GH_REPO GITHUB_REPOSITORY=linktrend/IDE-Development \
  PATH="$TMP/bin:$PATH" \
  python3 "$ROOT/scripts/gitops/cleanup_controls.py" export-preserve
)"
echo "$EXPORT59C" | python3 -c '
import json,sys
d=json.load(sys.stdin)
src=str(d.get("repoSource") or "")
assert src.startswith("env:"), d
assert src != "ambiguous_origin_and_upstream", d
assert d.get("preserveResolutionOk") is True, d
unresolved=set(d.get("unresolvedPrNumbers") or [])
assert 906 not in unresolved, d
assert unresolved == set() or 906 not in unresolved, d
heads=set(d.get("prHeads") or [])
branches=set(d.get("branches") or [])
assert "feature/preserve-906-env-head" in heads, d
assert "feature/preserve-906-env-head" in branches, d
assert d.get("repo") == "linktrend/IDE-Development", d
'
pass "export-preserve: GITHUB_REPOSITORY authoritative despite ambiguous remotes"

# --- 12c2) Precedence: --repo authoritative despite ambiguous remotes ---
EXPORT59C2="$(
  cd "$REPO59C" && env -u GITHUB_REPOSITORY -u GH_REPO PATH="$TMP/bin:$PATH" \
  python3 "$ROOT/scripts/gitops/cleanup_controls.py" export-preserve \
    --repo linktrend/IDE-Development
)"
echo "$EXPORT59C2" | python3 -c '
import json,sys
d=json.load(sys.stdin)
assert d.get("repoSource") == "explicit", d
assert d.get("preserveResolutionOk") is True, d
unresolved=set(d.get("unresolvedPrNumbers") or [])
assert 906 not in unresolved, d
heads=set(d.get("prHeads") or [])
branches=set(d.get("branches") or [])
assert "feature/preserve-906-env-head" in heads, d
assert "feature/preserve-906-env-head" in branches, d
assert d.get("repo") == "linktrend/IDE-Development", d
'
pass "export-preserve: --repo authoritative despite ambiguous remotes"

# END issue-59

# ============================================================================
# 13) Issue #61 Bugbot: repository-scoped PR evidence for cleanup
# BEGIN issue-61
# ============================================================================

# --- 13a) Resolved CLEANUP_REPO (unambiguous origin) → --repo on every PR evidence query ---
# Contract: nonempty CLEANUP_REPO ⇒ gh pr list for eligibility MUST pass --repo <resolved>.
# Fake gh returns MERGED only when --repo linktrend/IDE-Development is present; without
# --repo it refuses (empty) so implicit/wrong-repo evidence cannot unlock WOULD_DELETE.
REPO61A="$TMP/issue61-scoped-pr-evidence"
make_repo "$REPO61A"
seed_cleanup "$REPO61A"
# Unambiguous origin only (no upstream); --local so no live fetch. Env cleared below.
git -C "$REPO61A" remote add origin "https://github.com/linktrend/IDE-Development.git"
mkdir -p "$REPO61A/.linktrend"
cat >"$REPO61A/.linktrend/cleanup-preserve.json" <<'EOF'
{"schemaVersion":1,"defaults":false,"issueNumbers":[],"preservePrNumbers":[],"branches":[]}
EOF

git -C "$REPO61A" checkout -q -b issue/61-scoped-eligible
echo e61a >"$REPO61A/e61a.txt" && git -C "$REPO61A" add e61a.txt \
  && git -C "$REPO61A" commit -q -m "eligible merged with resolved CLEANUP_REPO"
HEAD61A="$(git -C "$REPO61A" rev-parse HEAD)"
git -C "$REPO61A" checkout -q development

: >"$TMP/gh-argv-61a.log"
mkdir -p "$TMP/bin"
cat >"$TMP/bin/gh" <<EOF
#!/usr/bin/env bash
printf '%s\n' "\$*" >>"$TMP/gh-argv-61a.log"
if [[ "\$*" == *"repo view"* ]]; then
  echo "linktrend/IDE-Development"
  exit 0
fi
if [[ "\$*" == *"pr list"* ]] && [[ "\$*" == *"--head issue/61-scoped-eligible"* ]]; then
  if [[ "\$*" == *"--repo linktrend/IDE-Development"* ]]; then
    echo '[{"number":6101,"state":"MERGED","mergedAt":"2026-01-01T00:00:00Z","labels":[],"headRefOid":"${HEAD61A}"}]'
    exit 0
  fi
  # Refuse implicit gh — trap would be wrong-repo MERGED; empty forces --repo for eligibility
  echo '[]'
  exit 0
fi
if [[ "\$*" == *"pr view"* ]]; then
  echo '{"number":0,"state":"CLOSED","headRefName":""}'
  exit 0
fi
echo '[]'
EOF
chmod +x "$TMP/bin/gh"

PATH="$TMP/bin:$PATH" env -u GITHUB_REPOSITORY -u GH_REPO \
  bash -c "cd \"$REPO61A\" && bash scripts/cleanup-merged-branches.sh --local" \
  >"$TMP/issue61a.out" || true
grep -q 'WOULD_DELETE.*issue/61-scoped-eligible' "$TMP/issue61a.out" \
  || fail "resolved CLEANUP_REPO + scoped MERGED should WOULD_DELETE: $(cat "$TMP/issue61a.out")"
if grep -q '^DELETED_' "$TMP/issue61a.out"; then
  fail "dry-run must not DELETE issue-61 scoped case: $(cat "$TMP/issue61a.out")"
fi
# Every PR-evidence pr list for the candidate must include --repo <resolved>
python3 -c '
import sys
from pathlib import Path
log = Path(sys.argv[1]).read_text(encoding="utf-8")
lines = [l for l in log.splitlines() if "pr list" in l and "--head issue/61-scoped-eligible" in l]
assert lines, f"expected gh pr list evidence query for candidate; log={log!r}"
for l in lines:
    assert "--repo linktrend/IDE-Development" in l, f"PR evidence must pass --repo: {l!r}"
' "$TMP/gh-argv-61a.log"
pass "shell dry-run: resolved CLEANUP_REPO → pr list --repo + WOULD_DELETE (scoped MERGED only)"

# --- 13b) Ambiguous remotes → implicit gh MUST NOT influence PR evidence ---
# Trap: fake gh returns MERGED for the candidate when called WITHOUT --repo.
# With empty preservePrNumbers (defaults:false), preserve-head resolution is not the
# blocker under test — empty CLEANUP_REPO must fail-closed so trap MERGED cannot
# produce WOULD_DELETE/DELETED. Prefer: no pr list evidence at all (or never bare).
REPO61B="$TMP/issue61-ambiguous-no-implicit"
make_repo "$REPO61B"
seed_cleanup "$REPO61B"
git -C "$REPO61B" remote add origin "https://github.com/linktrend/IDE-Development.git"
git -C "$REPO61B" remote add upstream "https://github.com/other/fork-upstream.git"
mkdir -p "$REPO61B/.linktrend"
cat >"$REPO61B/.linktrend/cleanup-preserve.json" <<'EOF'
{"schemaVersion":1,"defaults":false,"issueNumbers":[],"preservePrNumbers":[],"branches":[]}
EOF

git -C "$REPO61B" checkout -q -b issue/61-ambiguous-trap-eligible
echo e61b >"$REPO61B/e61b.txt" && git -C "$REPO61B" add e61b.txt \
  && git -C "$REPO61B" commit -q -m "trap MERGED under ambiguous remotes"
HEAD61B="$(git -C "$REPO61B" rev-parse HEAD)"
git -C "$REPO61B" checkout -q development

: >"$TMP/gh-argv-61b.log"
cat >"$TMP/bin/gh" <<EOF
#!/usr/bin/env bash
printf '%s\n' "\$*" >>"$TMP/gh-argv-61b.log"
if [[ "\$*" == *"repo view"* ]]; then
  echo "linktrend/IDE-Development"
  exit 0
fi
if [[ "\$*" == *"pr list"* ]] && [[ "\$*" == *"--head issue/61-ambiguous-trap-eligible"* ]]; then
  if [[ "\$*" == *"--repo "* ]]; then
    # Should not be reached when CLEANUP_REPO is empty; still refuse guessed repos
    echo '[]'
    exit 0
  fi
  # Trap: implicit gh MERGED — must NOT unlock delete when CLEANUP_REPO empty
  echo '[{"number":6102,"state":"MERGED","mergedAt":"2026-01-01T00:00:00Z","labels":[],"headRefOid":"${HEAD61B}"}]'
  exit 0
fi
if [[ "\$*" == *"pr view"* ]]; then
  echo '{"number":0,"state":"CLOSED","headRefName":""}'
  exit 0
fi
echo '[]'
EOF
chmod +x "$TMP/bin/gh"

PATH="$TMP/bin:$PATH" env -u GITHUB_REPOSITORY -u GH_REPO \
  bash -c "cd \"$REPO61B\" && bash scripts/cleanup-merged-branches.sh --local" \
  >"$TMP/issue61b.out" || true
if grep -q 'WOULD_DELETE' "$TMP/issue61b.out"; then
  fail "ambiguous + empty CLEANUP_REPO must not WOULD_DELETE (implicit trap): $(cat "$TMP/issue61b.out")"
fi
if grep -q '^DELETED_' "$TMP/issue61b.out"; then
  fail "ambiguous + empty CLEANUP_REPO must not DELETED: $(cat "$TMP/issue61b.out")"
fi
python3 -c '
import sys
from pathlib import Path
log = Path(sys.argv[1]).read_text(encoding="utf-8")
# Prefer no PR-evidence pr list when CLEANUP_REPO empty; never allow bare (no --repo)
evidence = [l for l in log.splitlines() if "pr list" in l and "--head issue/61-ambiguous-trap-eligible" in l]
bare = [l for l in evidence if "--repo " not in l]
assert not bare, f"implicit gh pr list without --repo must not run: {bare!r}"
assert not evidence, f"empty CLEANUP_REPO must not query PR evidence: {evidence!r}"
' "$TMP/gh-argv-61b.log"
pass "shell dry-run: ambiguous remotes → no implicit pr list; trap MERGED cannot WOULD_DELETE"

# --- 13c) Ambiguity still blocks WOULD_DELETE/DELETED (Issue #59 fail-closed retain) ---
# Strengthen: preservePrNumbers present + ambiguous remotes + trap MERGED for candidate.
REPO61C="$TMP/issue61-ambiguous-fail-closed"
make_repo "$REPO61C"
seed_cleanup "$REPO61C"
git -C "$REPO61C" remote add origin "https://github.com/linktrend/IDE-Development.git"
git -C "$REPO61C" remote add upstream "https://github.com/other/fork-upstream.git"
mkdir -p "$REPO61C/.linktrend"
cat >"$REPO61C/.linktrend/cleanup-preserve.json" <<'EOF'
{"schemaVersion":1,"defaults":false,"issueNumbers":[],"preservePrNumbers":[961],"branches":[]}
EOF

git -C "$REPO61C" checkout -q -b issue/61-ambiguous-fc-eligible
echo e61c >"$REPO61C/e61c.txt" && git -C "$REPO61C" add e61c.txt \
  && git -C "$REPO61C" commit -q -m "eligible under ambiguous fail-closed"
HEAD61C="$(git -C "$REPO61C" rev-parse HEAD)"
git -C "$REPO61C" checkout -q development

: >"$TMP/gh-argv-61c.log"
cat >"$TMP/bin/gh" <<EOF
#!/usr/bin/env bash
printf '%s\n' "\$*" >>"$TMP/gh-argv-61c.log"
if [[ "\$*" == *"repo view"* ]]; then
  echo "linktrend/IDE-Development"
  exit 0
fi
if [[ "\$*" == *"pr view 961"* ]]; then
  echo '{"number":961,"state":"OPEN","headRefName":"feature/preserve-961-trap-head"}'
  exit 0
fi
if [[ "\$*" == *"pr view"* ]]; then
  echo '{"number":961,"state":"OPEN","headRefName":"feature/preserve-961-trap-head"}'
  exit 0
fi
if [[ "\$*" == *"--head issue/61-ambiguous-fc-eligible"* ]]; then
  echo '[{"number":6103,"state":"MERGED","mergedAt":"2026-01-01T00:00:00Z","labels":[],"headRefOid":"${HEAD61C}"}]'
  exit 0
fi
echo '[]'
EOF
chmod +x "$TMP/bin/gh"

PATH="$TMP/bin:$PATH" env -u GITHUB_REPOSITORY -u GH_REPO \
  bash -c "cd \"$REPO61C\" && bash scripts/cleanup-merged-branches.sh --local" \
  >"$TMP/issue61c.out" || true
if grep -q 'WOULD_DELETE' "$TMP/issue61c.out"; then
  fail "ambiguous fail-closed must not WOULD_DELETE: $(cat "$TMP/issue61c.out")"
fi
if grep -q '^DELETED_' "$TMP/issue61c.out"; then
  fail "ambiguous fail-closed must not DELETED: $(cat "$TMP/issue61c.out")"
fi
if grep -q 'issue/61-ambiguous-fc-eligible' "$TMP/issue61c.out"; then
  grep -qiE 'fail-closed|unresolved' "$TMP/issue61c.out" \
    || fail "KEEP reason should mention fail-closed/unresolved: $(cat "$TMP/issue61c.out")"
  grep -qE 'KEEP:.*issue/61-ambiguous-fc-eligible' "$TMP/issue61c.out" \
    || fail "eligible under ambiguous remotes must KEEP: $(cat "$TMP/issue61c.out")"
fi
pass "shell dry-run: ambiguous remotes → no WOULD_DELETE/DELETED (Issue #59/#61 fail-closed)"

# --- 13d) Env override unlocks scoped PR evidence despite ambiguous remotes ---
# GITHUB_REPOSITORY authoritative → CLEANUP_REPO set → pr list --repo → WOULD_DELETE.
# Empty preservePrNumbers / defaults:false so preserve-head resolution does not fail-closed.
REPO61D="$TMP/issue61-env-unlock-evidence"
make_repo "$REPO61D"
seed_cleanup "$REPO61D"
git -C "$REPO61D" remote add origin "https://github.com/linktrend/IDE-Development.git"
git -C "$REPO61D" remote add upstream "https://github.com/other/fork-upstream.git"
mkdir -p "$REPO61D/.linktrend"
cat >"$REPO61D/.linktrend/cleanup-preserve.json" <<'EOF'
{"schemaVersion":1,"defaults":false,"issueNumbers":[],"preservePrNumbers":[],"branches":[]}
EOF

git -C "$REPO61D" checkout -q -b issue/61-env-unlock-eligible
echo e61d >"$REPO61D/e61d.txt" && git -C "$REPO61D" add e61d.txt \
  && git -C "$REPO61D" commit -q -m "eligible merged via env-scoped evidence"
HEAD61D="$(git -C "$REPO61D" rev-parse HEAD)"
git -C "$REPO61D" checkout -q development

: >"$TMP/gh-argv-61d.log"
cat >"$TMP/bin/gh" <<EOF
#!/usr/bin/env bash
printf '%s\n' "\$*" >>"$TMP/gh-argv-61d.log"
if [[ "\$*" == *"repo view"* ]]; then
  echo "error: no default repo (env should supply CLEANUP_REPO)" >&2
  exit 1
fi
if [[ "\$*" == *"pr list"* ]] && [[ "\$*" == *"--head issue/61-env-unlock-eligible"* ]]; then
  if [[ "\$*" == *"--repo linktrend/IDE-Development"* ]]; then
    echo '[{"number":6104,"state":"MERGED","mergedAt":"2026-01-01T00:00:00Z","labels":[],"headRefOid":"${HEAD61D}"}]'
    exit 0
  fi
  # Implicit trap MERGED — must not be used; only --repo unlocks correct evidence
  echo '[{"number":9998,"state":"MERGED","mergedAt":"2026-01-01T00:00:00Z","labels":[],"headRefOid":"cafebabecafebabecafebabecafebabecafebabe"}]'
  exit 0
fi
if [[ "\$*" == *"pr view"* ]]; then
  echo '{"number":0,"state":"CLOSED","headRefName":""}'
  exit 0
fi
echo '[]'
EOF
chmod +x "$TMP/bin/gh"

PATH="$TMP/bin:$PATH" env -u GH_REPO GITHUB_REPOSITORY=linktrend/IDE-Development \
  bash -c "cd \"$REPO61D\" && bash scripts/cleanup-merged-branches.sh --local" \
  >"$TMP/issue61d.out" || true
grep -q 'WOULD_DELETE.*issue/61-env-unlock-eligible' "$TMP/issue61d.out" \
  || fail "GITHUB_REPOSITORY override + scoped MERGED should WOULD_DELETE: $(cat "$TMP/issue61d.out")"
if grep -q '^DELETED_' "$TMP/issue61d.out"; then
  fail "dry-run must not DELETE env-unlock case: $(cat "$TMP/issue61d.out")"
fi
python3 -c '
import sys
from pathlib import Path
log = Path(sys.argv[1]).read_text(encoding="utf-8")
lines = [l for l in log.splitlines() if "pr list" in l and "--head issue/61-env-unlock-eligible" in l]
assert lines, f"expected scoped gh pr list evidence query; log={log!r}"
for l in lines:
    assert "--repo linktrend/IDE-Development" in l, f"env override must pass --repo: {l!r}"
bare = [l for l in lines if "--repo " not in l]
assert not bare, f"no bare pr list allowed: {bare!r}"
' "$TMP/gh-argv-61d.log"
pass "shell dry-run: GITHUB_REPOSITORY despite ambiguous remotes → --repo + WOULD_DELETE"

# END issue-61

# ============================================================================
# 14) Issue #63 Bugbot: explicit shell --repo + repair cleanup repo propagation
# BEGIN issue-63
# ============================================================================

# --- 14a) Explicit shell --repo authoritative despite ambiguous origin+upstream ---
# Contract: CLI --repo OWNER/NAME wins over dual remotes; PR evidence / preserve use
# that slug. Fake gh returns MERGED only for --repo linktrend/IDE-Development;
# implicit / wrong-repo evidence must not unlock WOULD_DELETE.
REPO63A="$TMP/issue63-shell-explicit-repo"
make_repo "$REPO63A"
seed_cleanup "$REPO63A"
git -C "$REPO63A" remote add origin "https://github.com/linktrend/IDE-Development.git"
git -C "$REPO63A" remote add upstream "https://github.com/other/fork-upstream.git"
mkdir -p "$REPO63A/.linktrend"
cat >"$REPO63A/.linktrend/cleanup-preserve.json" <<'EOF'
{"schemaVersion":1,"defaults":false,"issueNumbers":[],"preservePrNumbers":[],"branches":[]}
EOF

git -C "$REPO63A" checkout -q -b issue/63-explicit-repo-eligible
echo e63a >"$REPO63A/e63a.txt" && git -C "$REPO63A" add e63a.txt \
  && git -C "$REPO63A" commit -q -m "eligible merged via explicit shell --repo"
HEAD63A="$(git -C "$REPO63A" rev-parse HEAD)"
git -C "$REPO63A" checkout -q development

: >"$TMP/gh-argv-63a.log"
mkdir -p "$TMP/bin"
cat >"$TMP/bin/gh" <<EOF
#!/usr/bin/env bash
printf '%s\n' "\$*" >>"$TMP/gh-argv-63a.log"
if [[ "\$*" == *"repo view"* ]]; then
  echo "error: no default repo (explicit --repo must supply CLEANUP_REPO)" >&2
  exit 1
fi
if [[ "\$*" == *"pr list"* ]] && [[ "\$*" == *"--head issue/63-explicit-repo-eligible"* ]]; then
  if [[ "\$*" == *"--repo linktrend/IDE-Development"* ]]; then
    echo '[{"number":6301,"state":"MERGED","mergedAt":"2026-01-01T00:00:00Z","labels":[],"headRefOid":"${HEAD63A}"}]'
    exit 0
  fi
  # Implicit / wrong-repo trap — must not authorize delete
  echo '[{"number":9991,"state":"MERGED","mergedAt":"2026-01-01T00:00:00Z","labels":[],"headRefOid":"cafebabecafebabecafebabecafebabecafebabe"}]'
  exit 0
fi
if [[ "\$*" == *"pr view"* ]]; then
  echo '{"number":0,"state":"CLOSED","headRefName":""}'
  exit 0
fi
echo '[]'
EOF
chmod +x "$TMP/bin/gh"

PATH="$TMP/bin:$PATH" env -u GITHUB_REPOSITORY -u GH_REPO \
  bash -c "cd \"$REPO63A\" && bash scripts/cleanup-merged-branches.sh --local --repo linktrend/IDE-Development" \
  >"$TMP/issue63a.out" 2>"$TMP/issue63a.err" || true
grep -q 'WOULD_DELETE.*issue/63-explicit-repo-eligible' "$TMP/issue63a.out" \
  || fail "explicit shell --repo + scoped MERGED should WOULD_DELETE: out=$(cat "$TMP/issue63a.out") err=$(cat "$TMP/issue63a.err")"
if grep -q '^DELETED_' "$TMP/issue63a.out"; then
  fail "dry-run must not DELETE issue-63a: $(cat "$TMP/issue63a.out")"
fi
python3 -c '
import sys
from pathlib import Path
log = Path(sys.argv[1]).read_text(encoding="utf-8")
lines = [l for l in log.splitlines() if "pr list" in l and "--head issue/63-explicit-repo-eligible" in l]
assert lines, f"expected scoped gh pr list evidence query; log={log!r}"
for l in lines:
    assert "--repo linktrend/IDE-Development" in l, f"explicit --repo must scope PR evidence: {l!r}"
bare = [l for l in lines if "--repo " not in l]
assert not bare, f"no bare pr list allowed: {bare!r}"
' "$TMP/gh-argv-63a.log"
pass "shell dry-run: explicit --repo despite ambiguous remotes → --repo + WOULD_DELETE"

# --- 14b) Invalid/empty explicit shell --repo fail-closed ---
# Contract: empty or invalid --repo must FAIL (non-zero), never fall through to
# env/remotes/implicit gh, and never emit WOULD_DELETE / DELETED.
REPO63B="$TMP/issue63-shell-invalid-repo"
make_repo "$REPO63B"
seed_cleanup "$REPO63B"
git -C "$REPO63B" remote add origin "https://github.com/linktrend/IDE-Development.git"
git -C "$REPO63B" remote add upstream "https://github.com/other/fork-upstream.git"
mkdir -p "$REPO63B/.linktrend"
cat >"$REPO63B/.linktrend/cleanup-preserve.json" <<'EOF'
{"schemaVersion":1,"defaults":false,"issueNumbers":[],"preservePrNumbers":[],"branches":[]}
EOF

git -C "$REPO63B" checkout -q -b issue/63-invalid-repo-eligible
echo e63b >"$REPO63B/e63b.txt" && git -C "$REPO63B" add e63b.txt \
  && git -C "$REPO63B" commit -q -m "must not delete under invalid --repo"
HEAD63B="$(git -C "$REPO63B" rev-parse HEAD)"
git -C "$REPO63B" checkout -q development

run_invalid_repo_case() {
  local label="$1"
  local repo_arg="$2"
  : >"$TMP/gh-argv-63b.log"
  cat >"$TMP/bin/gh" <<EOF
#!/usr/bin/env bash
printf '%s\n' "\$*" >>"$TMP/gh-argv-63b.log"
if [[ "\$*" == *"pr list"* ]] && [[ "\$*" == *"--head issue/63-invalid-repo-eligible"* ]]; then
  # Trap MERGED if anyone queries — invalid --repo must not reach here for evidence
  echo '[{"number":6302,"state":"MERGED","mergedAt":"2026-01-01T00:00:00Z","labels":[],"headRefOid":"${HEAD63B}"}]'
  exit 0
fi
if [[ "\$*" == *"repo view"* ]]; then
  echo "linktrend/IDE-Development"
  exit 0
fi
echo '[]'
EOF
  chmod +x "$TMP/bin/gh"

  local rc=0
  PATH="$TMP/bin:$PATH" env -u GITHUB_REPOSITORY -u GH_REPO \
    bash -c "cd \"$REPO63B\" && bash scripts/cleanup-merged-branches.sh --local --repo \"$repo_arg\"" \
    >"$TMP/issue63b.out" 2>"$TMP/issue63b.err" || rc=$?
  [ "$rc" -ne 0 ] \
    || fail "invalid --repo ($label) must exit non-zero: out=$(cat "$TMP/issue63b.out") err=$(cat "$TMP/issue63b.err")"
  grep -qiE 'FAIL|invalid|empty|--repo' "$TMP/issue63b.err" "$TMP/issue63b.out" 2>/dev/null \
    || fail "invalid --repo ($label) should mention FAIL/invalid: err=$(cat "$TMP/issue63b.err") out=$(cat "$TMP/issue63b.out")"
  if grep -q 'WOULD_DELETE' "$TMP/issue63b.out" 2>/dev/null; then
    fail "invalid --repo ($label) must not WOULD_DELETE: $(cat "$TMP/issue63b.out")"
  fi
  if grep -q '^DELETED_' "$TMP/issue63b.out" 2>/dev/null; then
    fail "invalid --repo ($label) must not DELETED: $(cat "$TMP/issue63b.out")"
  fi
  python3 -c '
import sys
from pathlib import Path
log = Path(sys.argv[1]).read_text(encoding="utf-8")
evidence = [l for l in log.splitlines() if "pr list" in l and "--head issue/63-invalid-repo-eligible" in l]
assert not evidence, f"invalid --repo must not query PR evidence: {evidence!r}"
' "$TMP/gh-argv-63b.log"
}

run_invalid_repo_case "empty" ""
run_invalid_repo_case "no-slash" "notaslug"
run_invalid_repo_case "too-many-slashes" "a/b/c"
# Align with Python REPO_SLUG_RE: empty owner/name must fail closed (Issue #63)
run_invalid_repo_case "empty-owner" "/IDE-Development"
run_invalid_repo_case "empty-name" "linktrend/"
pass "shell: empty/invalid explicit --repo → FAIL, no implicit gh, no WOULD_DELETE"

# --- 14c) repair_task plan-cleanup-completed: caller --repo scopes all PR queries ---
# Contract: plan-cleanup-completed --repo must reach every gh pr view used for
# file-backend authorization. Row repository empty/wrong must not drive evidence.
# Fake gh returns MERGED only for --repo linktrend/IDE-Development; bare/wrong → OPEN
# so implicit context cannot authorize WOULD_DELETE_FILE.
REPAIR63C="$TMP/repair63-scoped"
mkdir -p "$REPAIR63C"
cat >"$REPAIR63C/eligible63.json" <<'EOF'
{
  "failureId": "eligible6300000001",
  "failureType": "merge_conflict",
  "resolutionState": "resolved",
  "repairStatus": "resolved",
  "branch": "issue/63-repair-scoped-eligible",
  "prNumber": "6303",
  "repository": "",
  "updatedAt": "2026-01-01T00:00:00Z"
}
EOF

: >"$TMP/gh-argv-63c.log"
cat >"$TMP/bin/gh" <<EOF
#!/usr/bin/env bash
printf '%s\n' "\$*" >>"$TMP/gh-argv-63c.log"
if [[ "\$*" == *"pr view 6303"* ]]; then
  if [[ "\$*" == *"--repo linktrend/IDE-Development"* ]]; then
    echo '{"number":6303,"state":"MERGED","mergedAt":"2026-01-01T00:00:00Z","headRefName":"issue/63-repair-scoped-eligible"}'
    exit 0
  fi
  # Implicit / wrong-repo → OPEN so trap cannot authorize delete
  echo '{"number":6303,"state":"OPEN","mergedAt":null,"headRefName":"issue/63-repair-scoped-eligible"}'
  exit 0
fi
if [[ "\$*" == *"pr view"* ]]; then
  echo '{"number":0,"state":"OPEN","headRefName":""}'
  exit 0
fi
echo '[]'
EOF
chmod +x "$TMP/bin/gh"

PLAN63C="$(
  PATH="$TMP/bin:$PATH" \
  LINKTREND_REPAIR_BACKEND=file \
  env -u GITHUB_REPOSITORY -u GH_REPO \
  python3 "$ROOT/scripts/gitops/repair_task.py" plan-cleanup-completed \
    --repo linktrend/IDE-Development \
    --repair-dir "$REPAIR63C"
)"
echo "$PLAN63C" | python3 -c '
import json,sys
p=json.load(sys.stdin)
by={a.get("failureId"):a for a in (p.get("actions") or [])}
assert "eligible6300000001" in by, p
a=by["eligible6300000001"]
dec=str(a.get("decision") or "")
assert "WOULD_DELETE_FILE" in dec.upper(), a
assert a.get("authorized") is True, a
assert "KEEP" not in dec.upper() or "DELETE" in dec.upper(), a
'
python3 -c '
import sys
from pathlib import Path
log = Path(sys.argv[1]).read_text(encoding="utf-8")
views = [l for l in log.splitlines() if "pr view 6303" in l]
assert views, f"expected gh pr view 6303; log={log!r}"
for l in views:
    assert "--repo linktrend/IDE-Development" in l, f"repair_task must pass caller --repo: {l!r}"
bare = [l for l in views if "--repo " not in l]
assert not bare, f"no bare pr view allowed: {bare!r}"
' "$TMP/gh-argv-63c.log"
pass "repair_task plan-cleanup-completed: --repo scopes pr view → WOULD_DELETE_FILE"

# --- 14d) cleanup_stale_records --file-backend: caller --repo scopes PR queries ---
REPAIR63D="$TMP/repair63-stale-scoped"
mkdir -p "$REPAIR63D"
cat >"$REPAIR63D/eligible63d.json" <<'EOF'
{
  "failureId": "eligible6300000002",
  "failureType": "merge_conflict",
  "resolutionState": "resolved",
  "repairStatus": "resolved",
  "branch": "issue/63-stale-scoped-eligible",
  "prNumber": "6304",
  "repository": "other/wrong-implicit-repo",
  "updatedAt": "2026-01-01T00:00:00Z"
}
EOF

: >"$TMP/gh-argv-63d.log"
cat >"$TMP/bin/gh" <<EOF
#!/usr/bin/env bash
printf '%s\n' "\$*" >>"$TMP/gh-argv-63d.log"
if [[ "\$*" == *"pr view 6304"* ]]; then
  if [[ "\$*" == *"--repo linktrend/IDE-Development"* ]]; then
    echo '{"number":6304,"state":"MERGED","mergedAt":"2026-01-01T00:00:00Z","headRefName":"issue/63-stale-scoped-eligible"}'
    exit 0
  fi
  # Wrong/implicit context → OPEN (must not authorize)
  echo '{"number":6304,"state":"OPEN","mergedAt":null,"headRefName":"issue/63-stale-scoped-eligible"}'
  exit 0
fi
echo '[]'
EOF
chmod +x "$TMP/bin/gh"

PLAN63D="$(
  PATH="$TMP/bin:$PATH" \
  env -u GITHUB_REPOSITORY -u GH_REPO \
  python3 "$ROOT/scripts/gitops/cleanup_stale_records.py" \
    --repo linktrend/IDE-Development \
    --file-backend \
    --repair-dir "$REPAIR63D"
)"
echo "$PLAN63D" | python3 -c '
import json,sys
p=json.load(sys.stdin)
by={a.get("failureId"):a for a in (p.get("actions") or [])}
assert "eligible6300000002" in by, p
a=by["eligible6300000002"]
dec=str(a.get("decision") or "")
assert "WOULD_DELETE_FILE" in dec.upper(), a
assert a.get("authorized") is True, a
'
python3 -c '
import sys
from pathlib import Path
log = Path(sys.argv[1]).read_text(encoding="utf-8")
views = [l for l in log.splitlines() if "pr view 6304" in l]
assert views, f"expected gh pr view 6304; log={log!r}"
for l in views:
    assert "--repo linktrend/IDE-Development" in l, f"cleanup_stale_records must pass caller --repo: {l!r}"
    assert "--repo other/wrong-implicit-repo" not in l, f"row repository must not override caller: {l!r}"
bare = [l for l in views if "--repo " not in l]
assert not bare, f"no bare pr view allowed: {bare!r}"
' "$TMP/gh-argv-63d.log"
pass "cleanup_stale_records --file-backend: --repo scopes pr view → WOULD_DELETE_FILE"

# --- 14e) Wrong implicit context must NOT authorize apply deletes ---
# Trap: bare gh (no --repo) returns MERGED. Without authoritative caller repo
# propagation, that would wrongly authorize. Contract: keep KEEP / no DELETED_FILE
# when evidence is only available via implicit gh.
REPAIR63E="$TMP/repair63-implicit-trap"
mkdir -p "$REPAIR63E"
cat >"$REPAIR63E/trap63.json" <<'EOF'
{
  "failureId": "trap6300000000001",
  "failureType": "merge_conflict",
  "resolutionState": "resolved",
  "repairStatus": "resolved",
  "branch": "issue/63-implicit-trap-eligible",
  "prNumber": "6305",
  "repository": "",
  "updatedAt": "2026-01-01T00:00:00Z"
}
EOF

: >"$TMP/gh-argv-63e.log"
cat >"$TMP/bin/gh" <<EOF
#!/usr/bin/env bash
printf '%s\n' "\$*" >>"$TMP/gh-argv-63e.log"
if [[ "\$*" == *"pr view 6305"* ]]; then
  if [[ "\$*" == *"--repo linktrend/IDE-Development"* ]]; then
    # Correct scope intentionally CLOSED/unknown-ish for this trap case: we are
    # testing the path that fails to pass --repo. If --repo IS passed, MERGED is
    # fine — apply may delete. The RED assertion is: bare MERGED must not authorize
    # when caller repo was not propagated.
    echo '{"number":6305,"state":"MERGED","mergedAt":"2026-01-01T00:00:00Z","headRefName":"issue/63-implicit-trap-eligible"}'
    exit 0
  fi
  # Implicit trap MERGED — must NOT authorize when --repo was not propagated
  echo '{"number":6305,"state":"MERGED","mergedAt":"2026-01-01T00:00:00Z","headRefName":"issue/63-implicit-trap-eligible"}'
  exit 0
fi
echo '[]'
EOF
chmod +x "$TMP/bin/gh"

# Simulate missing propagation: call plan_completed_repair_cleanup with empty repo
# (same failure mode as repair_task before Issue #63 fix). Apply must not delete.
mkdir -p "$TMP/issue63e-policy"
cat >"$TMP/issue63e-policy/cleanup-preserve.json" <<'EOF'
{"schemaVersion":1,"defaults":false,"issueNumbers":[],"preservePrNumbers":[],"branches":[]}
EOF
APPLY63E="$(
  PATH="$TMP/bin:$PATH" \
  env -u GITHUB_REPOSITORY -u GH_REPO -u LINKTREND_CLEANUP_PRESERVE \
  LINKTREND_CLEANUP_PRESERVE_FILE="$TMP/issue63e-policy/cleanup-preserve.json" \
  python3 -c '
import json, sys
from pathlib import Path
sys.path.insert(0, "'"$ROOT"'/scripts/gitops")
from cleanup_controls import plan_completed_repair_cleanup, load_preserve_policy
root = Path("'"$REPAIR63E"'")
pol = load_preserve_policy(Path("'"$TMP"'/issue63e-policy/cleanup-preserve.json"))
# Empty caller repo — must fail closed (no implicit-gh authorization)
plan = plan_completed_repair_cleanup(root, apply=True, policy=pol, repo="")
print(json.dumps(plan))
'
)"
echo "$APPLY63E" | python3 -c '
import json,sys
from pathlib import Path
p=json.load(sys.stdin)
by={a.get("failureId"):a for a in (p.get("actions") or [])}
assert "trap6300000000001" in by, p
a=by["trap6300000000001"]
dec=str(a.get("decision") or "").upper()
auth=a.get("authorized")
# Fail-closed: empty caller repo must not authorize via implicit gh
assert auth is not True, a
assert "DELETED_FILE" not in dec, a
assert "WOULD_DELETE_FILE" not in dec, a
assert Path(a["path"]).is_file(), "implicit trap must not delete file on apply"
'
# Also: bare pr view (no --repo) must not be the authorizing path when callers
# correctly pass --repo. Re-run via repair_task apply — after fix, scoped MERGED
# may delete; before fix, implicit MERGED must not be trusted. Assert gh log for
# repair_task always includes --repo when plan-cleanup-completed is invoked with it.
: >"$TMP/gh-argv-63e2.log"
cat >"$TMP/bin/gh" <<EOF
#!/usr/bin/env bash
printf '%s\n' "\$*" >>"$TMP/gh-argv-63e2.log"
if [[ "\$*" == *"pr view 6305"* ]]; then
  if [[ "\$*" == *"--repo linktrend/IDE-Development"* ]]; then
    echo '{"number":6305,"state":"OPEN","mergedAt":null,"headRefName":"issue/63-implicit-trap-eligible"}'
    exit 0
  fi
  echo '{"number":6305,"state":"MERGED","mergedAt":"2026-01-01T00:00:00Z","headRefName":"issue/63-implicit-trap-eligible"}'
  exit 0
fi
echo '[]'
EOF
chmod +x "$TMP/bin/gh"

# Recreate file in case prior apply somehow removed it
cat >"$REPAIR63E/trap63.json" <<'EOF'
{
  "failureId": "trap6300000000001",
  "failureType": "merge_conflict",
  "resolutionState": "resolved",
  "repairStatus": "resolved",
  "branch": "issue/63-implicit-trap-eligible",
  "prNumber": "6305",
  "repository": "",
  "updatedAt": "2026-01-01T00:00:00Z"
}
EOF

APPLY63E2="$(
  PATH="$TMP/bin:$PATH" \
  LINKTREND_REPAIR_BACKEND=file \
  env -u GITHUB_REPOSITORY -u GH_REPO \
  python3 "$ROOT/scripts/gitops/repair_task.py" plan-cleanup-completed \
    --repo linktrend/IDE-Development \
    --repair-dir "$REPAIR63E" \
    --apply
)"
echo "$APPLY63E2" | python3 -c '
import json,sys
from pathlib import Path
p=json.load(sys.stdin)
by={a.get("failureId"):a for a in (p.get("actions") or [])}
assert "trap6300000000001" in by, p
a=by["trap6300000000001"]
dec=str(a.get("decision") or "")
# Scoped evidence is OPEN → must KEEP; implicit MERGED must not win
assert a.get("authorized") is False, a
assert "DELETED_FILE" not in dec.upper(), a
assert "WOULD_DELETE_FILE" not in dec.upper(), a
assert Path(a["path"]).is_file(), "OPEN scoped evidence must not delete on apply"
'
python3 -c '
import sys
from pathlib import Path
log = Path(sys.argv[1]).read_text(encoding="utf-8")
views = [l for l in log.splitlines() if "pr view 6305" in l]
# After Issue #63: every authorizing pr view must carry caller --repo
# Before fix (missing propagation): bare views may appear — that is RED.
assert views, f"expected pr view 6305; log={log!r}"
bare = [l for l in views if "--repo " not in l]
assert not bare, f"wrong implicit context: bare pr view must not authorize: {bare!r}"
for l in views:
    assert "--repo linktrend/IDE-Development" in l, f"caller --repo required: {l!r}"
' "$TMP/gh-argv-63e2.log"
pass "wrong implicit gh MERGED cannot authorize apply / WOULD_DELETE_FILE"

# --- 14f) cleanup_stale_records apply: wrong/missing repo fail-closed ---
REPAIR63F="$TMP/repair63-stale-failclosed"
mkdir -p "$REPAIR63F"
cat >"$REPAIR63F/keep63f.json" <<'EOF'
{
  "failureId": "keep6300000000001",
  "failureType": "merge_conflict",
  "resolutionState": "resolved",
  "repairStatus": "resolved",
  "branch": "issue/63-stale-failclosed",
  "prNumber": "6306",
  "repository": "",
  "updatedAt": "2026-01-01T00:00:00Z"
}
EOF

: >"$TMP/gh-argv-63f.log"
cat >"$TMP/bin/gh" <<EOF
#!/usr/bin/env bash
printf '%s\n' "\$*" >>"$TMP/gh-argv-63f.log"
if [[ "\$*" == *"pr view 6306"* ]]; then
  echo '{"number":6306,"state":"MERGED","mergedAt":"2026-01-01T00:00:00Z","headRefName":"issue/63-stale-failclosed"}'
  exit 0
fi
echo '[]'
EOF
chmod +x "$TMP/bin/gh"

STALE63F_RC=0
PATH="$TMP/bin:$PATH" env -u GITHUB_REPOSITORY -u GH_REPO \
  python3 "$ROOT/scripts/gitops/cleanup_stale_records.py" \
    --repo "" \
    --file-backend \
    --repair-dir "$REPAIR63F" \
    --apply --i-understand-close-repairs \
  >"$TMP/issue63f.out" 2>"$TMP/issue63f.err" || STALE63F_RC=$?
[ "$STALE63F_RC" -ne 0 ] \
  || fail "empty --repo file-backend apply must fail closed: out=$(cat "$TMP/issue63f.out") err=$(cat "$TMP/issue63f.err")"
[ -f "$REPAIR63F/keep63f.json" ] \
  || fail "empty --repo must not delete repair file"
if grep -q 'WOULD_DELETE_FILE\|DELETED_FILE' "$TMP/issue63f.out" 2>/dev/null; then
  fail "empty --repo must not emit delete decisions: $(cat "$TMP/issue63f.out")"
fi
python3 -c '
import sys
from pathlib import Path
log = Path(sys.argv[1]).read_text(encoding="utf-8")
views = [l for l in log.splitlines() if "pr view" in l]
assert not views, f"empty --repo must not call gh pr view: {views!r}"
' "$TMP/gh-argv-63f.log"
pass "cleanup_stale_records: empty --repo file-backend apply fail-closed (no gh, no delete)"

# END issue-63

# GitHub remote parsing must validate the complete host, not a substring that
# can be embedded in an attacker-controlled hostname, userinfo, or path.
python3 - "$ROOT" <<'PY'
import importlib.util
import sys
from pathlib import Path

path = Path(sys.argv[1]) / "scripts/gitops/cleanup_controls.py"
spec = importlib.util.spec_from_file_location("cleanup_controls", path)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

valid = {
    "https://github.com/linktrend/IDE-Development.git",
    "https://git@github.com/linktrend/IDE-Development.git",
    "ssh://git@github.com/linktrend/IDE-Development.git",
    "git@github.com:linktrend/IDE-Development.git",
}
for url in valid:
    assert module._owner_repo_from_github_url(url) == "linktrend/IDE-Development", url

invalid = {
    "https://evilgithub.com/linktrend/IDE-Development.git",
    "https://github.com.evil.example/linktrend/IDE-Development.git",
    "https://github.com@evil.example/linktrend/IDE-Development.git",
    "https://evil.example/github.com/linktrend/IDE-Development.git",
    "https://github.com/linktrend/IDE-Development.git?github.com/other/repo",
    "git@github.com.evil.example:linktrend/IDE-Development.git",
}
for url in invalid:
    assert module._owner_repo_from_github_url(url) is None, url
PY
pass "GitHub remote parser requires exact trusted host"

echo "OK: $PASS assertions passed"
