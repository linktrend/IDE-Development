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

echo "OK: $PASS assertions passed"
