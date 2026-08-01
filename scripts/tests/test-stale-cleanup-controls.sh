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

PATH="$TMP/bin:$PATH" bash -c "cd \"$REPO1\" && bash scripts/cleanup-merged-branches.sh --remote" >"$TMP/open.out"
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

PATH="$TMP/bin:$PATH" bash -c "cd \"$REPO2\" && bash scripts/cleanup-merged-branches.sh --local" >"$TMP/wt.out"
grep -q 'KEEP: local:issue/99-merged-clean-wt' "$TMP/wt.out" \
  || fail "clean worktree must KEEP: $(cat "$TMP/wt.out")"
grep -qi 'active worktree attached' "$TMP/wt.out" \
  || fail "worktree KEEP reason missing: $(cat "$TMP/wt.out")"
grep -qv '^DELETED_' "$TMP/wt.out" || fail "dry-run must not DELETE worktree case"
pass "clean attached worktree → KEEP"

# ============================================================================
# 3) Preserve policy: issue/44-* KEEP even with MERGED evidence + no worktree
# ============================================================================
REPO3="$TMP/preserve"
make_repo "$REPO3"
seed_cleanup "$REPO3"
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

PATH="$TMP/bin:$PATH" bash -c "cd \"$REPO3\" && bash scripts/cleanup-merged-branches.sh --local" >"$TMP/pres.out"
grep -q 'KEEP:.*issue/44-add-app-backed-review-ready-publisher-and-produc' "$TMP/pres.out" \
  || fail "preserve issue/44 must KEEP: $(cat "$TMP/pres.out")"
grep -qi 'preserve' "$TMP/pres.out" \
  || fail "preserve reason missing: $(cat "$TMP/pres.out")"
grep -qv '^DELETED_' "$TMP/pres.out" || fail "dry-run must not DELETE preserve case"
pass "preserve issue/44-* → KEEP"

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

PATH="$TMP/bin:$PATH" bash -c "cd \"$REPO4\" && bash scripts/cleanup-merged-branches.sh --remote" >"$TMP/elig.out"
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
  python3 "$ROOT/scripts/gitops/cleanup_controls.py" plan-completed-repairs \
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
  python3 "$ROOT/scripts/gitops/cleanup_controls.py" plan-completed-repairs \
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

PATH="$TMP/bin:$PATH" bash -c "cd \"$REPO6\" && bash scripts/cleanup-merged-branches.sh --local" >"$TMP/df.out"
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

echo "OK: $PASS assertions passed"
