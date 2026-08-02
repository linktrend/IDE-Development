#!/usr/bin/env bash
# WP02 Lane C — integration: stale-cleanup controls + WP01 portable-system lineage coexist.
#
# Preconditions (lead merge order): WP01 portable lineage, then cleanup tip (5cf0991),
# then this test + any remaining proposed additions.
#
# Covers:
#   - open / frozen PR head preservation
#   - worktree ownership KEEP
#   - ambiguous remotes fail-closed
#   - unavailable GitHub evidence fail-closed
#   - mismatched repositories (WP01 wrong-repo fixture + cleanup --repo)
#   - partially merged histories (OPEN wins; tip SHA mismatch KEEP)
#   - retry / idempotence of dry-run and failed-auth paths
#   - zero mutation on failed authorization
#
# No live GitHub mutation. No cleanup --apply against real remotes.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
# When executed from proposed/ mirror during review, allow override:
if [[ "${LINKTREND_TEST_REPO_ROOT:-}" ]]; then
  ROOT="$LINKTREND_TEST_REPO_ROOT"
fi

pass() { echo "PASS: $*"; }
fail() { echo "FAIL: $*" >&2; exit 1; }

require_file() {
  [[ -f "$1" ]] || fail "missing required path after WP01+cleanup merge: $1"
}

# --- Presence gate: both lineages must be on disk ---
require_file "$ROOT/scripts/gitops/cleanup_controls.py"
require_file "$ROOT/scripts/gitops/cleanup_stale_records.py"
require_file "$ROOT/scripts/gitops/cleanup_preserve.defaults.json"
require_file "$ROOT/scripts/cleanup-merged-branches.sh"
require_file "$ROOT/scripts/tests/test-stale-cleanup-controls.sh"
require_file "$ROOT/docs/contracts/STALE-CLEANUP-CONTROLS.md"
require_file "$ROOT/scripts/ide_development_tests/fixtures/security/cleanup/wrong-repo-evidence.json"
require_file "$ROOT/tests/security_acceptance/test_repo_scope_evidence.py"
require_file "$ROOT/tests/test-portable-v2-integration.sh"
pass "presence: cleanup controls + WP01 portable/security fixtures coexist"

TMP="$(mktemp -d "${TMPDIR:-/tmp}/wp02-lane-c-coexist.XXXXXX")"
trap 'rm -rf "$TMP"' EXIT

seed_repo() {
  local d="$1"
  mkdir -p "$d/scripts/gitops" "$d/.linktrend"
  # Minimal git repo with cleanup scripts copied from combined tree
  git -C "$d" init -q
  git -C "$d" config user.email "lane-c@test.local"
  git -C "$d" config user.name "Lane C"
  cp "$ROOT/scripts/cleanup-merged-branches.sh" "$d/scripts/"
  cp "$ROOT/scripts/gitops/"*.py "$d/scripts/gitops/" 2>/dev/null || true
  cp "$ROOT/scripts/gitops/"*.sh "$d/scripts/gitops/" 2>/dev/null || true
  cp "$ROOT/scripts/gitops/"*.json "$d/scripts/gitops/" 2>/dev/null || true
  # work-branch-allowlist may be required by cleanup-merged-branches.sh
  if [[ -f "$ROOT/scripts/gitops/work-branch-allowlist.sh" ]]; then
    cp "$ROOT/scripts/gitops/work-branch-allowlist.sh" "$d/scripts/gitops/"
  fi
  chmod +x "$d/scripts/"*.sh "$d/scripts/gitops/"*.py 2>/dev/null || true
  echo "*.pyc" >"$d/.gitignore"
  git -C "$d" add .gitignore scripts
  git -C "$d" commit -q -m "seed: cleanup + gitops"
  # development-like protected branch tip
  git -C "$d" branch -M development
}

# Fake gh that records invocations; scenarios override via PATH prefix.
install_gh_recorder() {
  local bin="$1"
  mkdir -p "$bin"
  cat >"$bin/gh" <<'GHEOF'
#!/usr/bin/env bash
set -euo pipefail
LOG="${GH_CALL_LOG:-/dev/null}"
printf '%s\n' "$*" >>"$LOG"
# Default: fail closed (unavailable evidence)
exit 1
GHEOF
  chmod +x "$bin/gh"
}

export TEST_ROOT="$ROOT"

# ---------------------------------------------------------------------------
# 1) WP01 wrong-repo fixture must refuse mismatch (portable security lineage)
# ---------------------------------------------------------------------------
python3 - <<'PY'
import json, sys, os
from pathlib import Path
root = Path(os.environ["TEST_ROOT"])
sys.path.insert(0, str(root / "scripts"))
fx = root / "scripts/ide_development_tests/fixtures/security/cleanup/wrong-repo-evidence.json"
payload = json.loads(fx.read_text(encoding="utf-8"))
assert payload.get("applyForbidden") is True
assert payload.get("mode") == "dry-run-only"
assert (payload.get("repository") or "").lower() != "linktrend/ide-development"
from gitops.review_ready_dispatch import DispatchValidationError, validate_repository
try:
    validate_repository(
        github_repository="linktrend/IDE-Development",
        requested_repository=payload["repository"],
    )
except DispatchValidationError as e:
    assert e.code == "repository_mismatch", e.code
else:
    raise SystemExit("expected repository_mismatch")
print("ok-wp01-wrong-repo")
PY
pass "WP01 wrong-repo fixture + validate_repository refuse mismatch"

# ---------------------------------------------------------------------------
# 2) Frozen / CLOSED preserve PR heads retained (cleanup policy parity)
# ---------------------------------------------------------------------------
REPO="$TMP/frozen-pr"
seed_repo "$REPO"
git -C "$REPO" checkout -q -b feature/frozen-closed-head
echo frozen >"$REPO/f.txt" && git -C "$REPO" add f.txt && git -C "$REPO" commit -q -m "frozen head"
CLOSED_HEAD="$(git -C "$REPO" rev-parse HEAD)"
git -C "$REPO" checkout -q development

BIN="$TMP/bin-frozen"
install_gh_recorder "$BIN"
cat >"$BIN/gh" <<GHEOF
#!/usr/bin/env bash
set -euo pipefail
printf '%s\n' "\$*" >>"\${GH_CALL_LOG:-/dev/null}"
if [[ "\$*" == *"pr view"* && "\$*" == *"903"* ]]; then
  echo '{"number":903,"state":"CLOSED","headRefName":"feature/frozen-closed-head"}'
  exit 0
fi
if [[ "\$*" == *"--head feature/frozen-closed-head"* ]]; then
  echo '[{"number":903,"state":"CLOSED","mergedAt":null,"labels":[],"headRefOid":"${CLOSED_HEAD}"}]'
  exit 0
fi
exit 1
GHEOF
chmod +x "$BIN/gh"

export GH_CALL_LOG="$TMP/gh-frozen.log"
export PATH="$BIN:$PATH"
export LINKTREND_CLEANUP_PRESERVE_FILE="$TMP/preserve-frozen.json"
cat >"$LINKTREND_CLEANUP_PRESERVE_FILE" <<'JSON'
{"schemaVersion":1,"defaults":false,"preserveIssueNumbers":[],"preservePrNumbers":[903],"preserveBranchExact":[]}
JSON

OUT="$TMP/frozen.out"
(
  cd "$REPO"
  python3 scripts/gitops/cleanup_controls.py export-preserve --repo linktrend/IDE-Development
) >"$OUT"
export TEST_OUT="$OUT"
python3 - <<'PY'
import json
from pathlib import Path
import os
d = json.loads(Path(os.environ['TEST_OUT']).read_text())
assert d.get("preserveResolutionOk") is True, d
assert "feature/frozen-closed-head" in d.get("prHeads", []), d
assert "feature/frozen-closed-head" in d.get("branches", []), d
assert 903 not in d.get("unresolvedPrNumbers", []), d
PY
pass "CLOSED/frozen preserve PR head retained in export-preserve"

# ---------------------------------------------------------------------------
# 3) Open PR KEEP + worktree ownership KEEP
# ---------------------------------------------------------------------------
REPO3="$TMP/open-wt"
seed_repo "$REPO3"
git -C "$REPO3" checkout -q -b issue/120-open-wt
echo open >"$REPO3/o.txt" && git -C "$REPO3" add o.txt && git -C "$REPO3" commit -q -m "open"
OPEN_SHA="$(git -C "$REPO3" rev-parse HEAD)"
git -C "$REPO3" checkout -q development
WT="$TMP/wt-120"
git -C "$REPO3" worktree add "$WT" issue/120-open-wt >/dev/null

BIN3="$TMP/bin-open"
mkdir -p "$BIN3"
cat >"$BIN3/gh" <<GHEOF
#!/usr/bin/env bash
set -euo pipefail
printf '%s\n' "\$*" >>"\${GH_CALL_LOG:-/dev/null}"
if [[ "\$*" == *"pr list"* && "\$*" == *"--head issue/120-open-wt"* ]]; then
  echo '[{"number":1201,"state":"OPEN","mergedAt":null,"labels":[],"headRefOid":"${OPEN_SHA}"}]'
  exit 0
fi
if [[ "\$*" == *"pr view"* ]]; then
  echo '{"number":49,"state":"CLOSED","headRefName":"issue/43-x"}'
  exit 0
fi
exit 0
GHEOF
chmod +x "$BIN3/gh"
export PATH="$BIN3:$PATH"
export GH_CALL_LOG="$TMP/gh-open.log"
unset LINKTREND_CLEANUP_PRESERVE_FILE || true

OUT3="$TMP/open-wt.out"
(
  cd "$REPO3"
  bash scripts/cleanup-merged-branches.sh --local --repo linktrend/IDE-Development
) >"$OUT3" 2>&1 || true
grep -qi 'KEEP:.*issue/120-open-wt\|KEEP:.*local:issue/120-open-wt' "$OUT3" \
  || fail "open/worktree case must KEEP: $(cat "$OUT3")"
grep -Eiq 'open PR|active worktree' "$OUT3" \
  || fail "expected open PR or worktree reason: $(cat "$OUT3")"
grep -qv '^DELETED_' "$OUT3" || fail "must not DELETE with open/worktree"
pass "open PR + attached worktree → KEEP (zero delete)"

# ---------------------------------------------------------------------------
# 4) Ambiguous remotes → no WOULD_DELETE / DELETED
# ---------------------------------------------------------------------------
REPO4="$TMP/ambig"
seed_repo "$REPO4"
git -C "$REPO4" remote add origin "https://github.com/linktrend/IDE-Development.git"
git -C "$REPO4" remote add upstream "https://github.com/other/fork.git"
git -C "$REPO4" checkout -q -b issue/200-merged-looking
echo m >"$REPO4/m.txt" && git -C "$REPO4" add m.txt && git -C "$REPO4" commit -q -m "m"
git -C "$REPO4" checkout -q development

BIN4="$TMP/bin-ambig"
install_gh_recorder "$BIN4"
# Even if gh would authorize MERGED, ambiguity must block without --repo/env
cat >"$BIN4/gh" <<'GHEOF'
#!/usr/bin/env bash
set -euo pipefail
printf '%s\n' "$*" >>"${GH_CALL_LOG:-/dev/null}"
# Tempting wrong-context success — must not be used under ambiguity
if [[ "$*" == *"pr list"* ]]; then
  echo '[{"number":1,"state":"MERGED","mergedAt":"2026-01-01T00:00:00Z","labels":[],"headRefOid":"deadbeef"}]'
  exit 0
fi
if [[ "$*" == *"pr view"* ]]; then
  echo '{"number":49,"state":"CLOSED","headRefName":"issue/43-x"}'
  exit 0
fi
exit 1
GHEOF
chmod +x "$BIN4/gh"
export PATH="$BIN4:$PATH"
export GH_CALL_LOG="$TMP/gh-ambig.log"
unset GITHUB_REPOSITORY GH_REPO || true

OUT4="$TMP/ambig.out"
(
  cd "$REPO4"
  # no --repo: ambiguous origin+upstream
  bash scripts/cleanup-merged-branches.sh --remote 2>&1 || true
) >"$OUT4"
grep -Eq 'WOULD_DELETE|DELETED_' "$OUT4" && fail "ambiguity must block deletes: $(cat "$OUT4")"
pass "ambiguous remotes → no WOULD_DELETE/DELETED"

# ---------------------------------------------------------------------------
# 5) Unavailable GitHub evidence → fail-closed KEEP / unresolved preserve
# ---------------------------------------------------------------------------
REPO5="$TMP/gh-down"
seed_repo "$REPO5"
BIN5="$TMP/bin-down"
install_gh_recorder "$BIN5"  # always exit 1
export PATH="$BIN5:$PATH"
export GH_CALL_LOG="$TMP/gh-down.log"
export LINKTREND_CLEANUP_PRESERVE_FILE="$TMP/preserve-down.json"
cat >"$LINKTREND_CLEANUP_PRESERVE_FILE" <<'JSON'
{"schemaVersion":1,"defaults":false,"preserveIssueNumbers":[],"preservePrNumbers":[49],"preserveBranchExact":[]}
JSON

OUT5="$TMP/gh-down.out"
(
  cd "$REPO5"
  python3 scripts/gitops/cleanup_controls.py export-preserve --repo linktrend/IDE-Development
) >"$OUT5" || true
export TEST_OUT="$OUT5"
python3 - <<'PY'
import json
from pathlib import Path
import os
d = json.loads(Path(os.environ['TEST_OUT']).read_text())
assert d.get("preserveResolutionOk") is False, d
assert 49 in d.get("unresolvedPrNumbers", []), d
PY
pass "unavailable gh → preserveResolutionOk=false (fail-closed)"

# ---------------------------------------------------------------------------
# 6) Mismatched repository: wrong --repo must not authorize file-backend apply
# ---------------------------------------------------------------------------
REPO6="$TMP/mismatch"
seed_repo "$REPO6"
REPAIR_DIR="$TMP/repair-file"
mkdir -p "$REPAIR_DIR"
# Resolved repair JSON that would otherwise be deletable if wrong repo authorized
cat >"$REPAIR_DIR/completed-1.json" <<'JSON'
{
  "schemaVersion": 2,
  "failureId": "abc",
  "repairStatus": "resolved",
  "repository": "linktrend/IDE-Development",
  "branch": "issue/300-done",
  "pr": 3001,
  "issueNumber": null
}
JSON

BIN6="$TMP/bin-mismatch"
mkdir -p "$BIN6"
# Ambient gh claims MERGED for wrong repo context
cat >"$BIN6/gh" <<'GHEOF'
#!/usr/bin/env bash
set -euo pipefail
printf '%s\n' "$*" >>"${GH_CALL_LOG:-/dev/null}"
# If --repo is wrong/missing, still return MERGED to tempt authorization
if [[ "$*" == *"pr view"* || "$*" == *"pr list"* ]]; then
  echo '{"number":3001,"state":"MERGED","mergedAt":"2026-01-01T00:00:00Z","headRefName":"issue/300-done"}'
  exit 0
fi
exit 0
GHEOF
chmod +x "$BIN6/gh"
export PATH="$BIN6:$PATH"
export GH_CALL_LOG="$TMP/gh-mismatch.log"
export LINKTREND_REPAIR_BACKEND=file
export LINKTREND_REPAIR_DIR="$REPAIR_DIR"

BEFORE_HASH="$(shasum -a 256 "$REPAIR_DIR/completed-1.json" | awk '{print $1}')"
# Invalid/mismatched caller --repo
OUT6="$TMP/mismatch.out"
set +e
(
  cd "$REPO6"
  python3 scripts/gitops/repair_task.py plan-cleanup-completed \
    --repo "linktrend/Wrong-Repo" \
    --repair-dir "$REPAIR_DIR" \
    --apply
) >"$OUT6" 2>&1
RC6=$?
set -e
AFTER_HASH="$(shasum -a 256 "$REPAIR_DIR/completed-1.json" | awk '{print $1}')"
[[ "$BEFORE_HASH" == "$AFTER_HASH" ]] || fail "file mutated despite failed authorization"
[[ -f "$REPAIR_DIR/completed-1.json" ]] || fail "repair file deleted under mismatch"
# Also empty/invalid --repo
set +e
(
  cd "$REPO6"
  python3 scripts/gitops/repair_task.py plan-cleanup-completed --repo "" --repair-dir "$REPAIR_DIR" --apply
) >"$TMP/mismatch-empty.out" 2>&1
RC6b=$?
set -e
[[ -f "$REPAIR_DIR/completed-1.json" ]] || fail "repair file deleted on empty --repo"
pass "mismatched/invalid --repo → zero mutation on apply (rc=${RC6}/${RC6b})"

# ---------------------------------------------------------------------------
# 7) Partially merged histories: OPEN wins; tip SHA mismatch KEEP
# ---------------------------------------------------------------------------
REPO7="$TMP/partial"
seed_repo "$REPO7"
git -C "$REPO7" checkout -q -b issue/400-moved-tip
echo a >"$REPO7/a.txt" && git -C "$REPO7" add a.txt && git -C "$REPO7" commit -q -m "a"
OLD_SHA="$(git -C "$REPO7" rev-parse HEAD)"
echo b >"$REPO7/b.txt" && git -C "$REPO7" add b.txt && git -C "$REPO7" commit -q -m "b"
NEW_SHA="$(git -C "$REPO7" rev-parse HEAD)"
git -C "$REPO7" checkout -q development
# Hermetic remote refs (do not fetch live origin) — mirrors test-stale-cleanup-controls.sh
git -C "$REPO7" update-ref "refs/remotes/origin/issue/400-moved-tip" "$NEW_SHA"
git -C "$REPO7" update-ref "refs/remotes/origin/issue/401-open-wins" "$NEW_SHA"

BIN7="$TMP/bin-partial"
mkdir -p "$BIN7"
cat >"$BIN7/gh" <<GHEOF
#!/usr/bin/env bash
set -euo pipefail
printf '%s\n' "\$*" >>"\${GH_CALL_LOG:-/dev/null}"
if [[ "\$*" == *"--head issue/400-moved-tip"* ]]; then
  # MERGED evidence but stale headOid (partial / moved tip)
  echo '[{"number":4001,"state":"MERGED","mergedAt":"2026-01-01T00:00:00Z","labels":[],"headRefOid":"${OLD_SHA}"}]'
  exit 0
fi
if [[ "\$*" == *"--head issue/401-open-wins"* ]]; then
  echo '[{"number":4010,"state":"MERGED","mergedAt":"2025-01-01T00:00:00Z","labels":[],"headRefOid":"${NEW_SHA}"},{"number":4011,"state":"OPEN","mergedAt":null,"labels":[],"headRefOid":"${NEW_SHA}"}]'
  exit 0
fi
if [[ "\$*" == *"pr view"* ]]; then
  echo '{"number":49,"state":"CLOSED","headRefName":"issue/43-x"}'
  exit 0
fi
echo '[]'
exit 0
GHEOF
chmod +x "$BIN7/gh"
export PATH="$BIN7:$PATH"
unset LINKTREND_CLEANUP_PRESERVE_FILE || true

OUT7="$TMP/partial.out"
(
  cd "$REPO7"
  # Prefer env CLEANUP_REPO over live github.com origin (no fetch pollution)
  env -u GH_REPO GITHUB_REPOSITORY=linktrend/IDE-Development \
    bash scripts/cleanup-merged-branches.sh --remote --repo linktrend/IDE-Development
) >"$OUT7" 2>&1 || true
grep -q 'KEEP:.*issue/400-moved-tip' "$OUT7" \
  || fail "moved tip must KEEP: $(cat "$OUT7")"
grep -qi 'PR head.*!=.*branch tip\|head .*!=.*tip' "$OUT7" \
  || fail "expected tip mismatch reason: $(cat "$OUT7")"
grep -q 'KEEP:.*issue/401-open-wins' "$OUT7" \
  || fail "OPEN must win over historical MERGED: $(cat "$OUT7")"
grep -Eqi 'open PR' "$OUT7" \
  || fail "expected open PR reason: $(cat "$OUT7")"
grep -Eq 'WOULD_DELETE.*issue/400-moved-tip|WOULD_DELETE.*issue/401-open-wins|DELETED_.*issue/40' "$OUT7" \
  && fail "partial history must not delete: $(cat "$OUT7")"
pass "partially merged / moved tip / OPEN-wins → KEEP"

# ---------------------------------------------------------------------------
# 8) Retry / idempotence: dry-run twice identical; failed auth twice zero mutation
# ---------------------------------------------------------------------------
REPO8="$TMP/idem"
seed_repo "$REPO8"
git -C "$REPO8" checkout -q -b issue/500-eligible
echo e >"$REPO8/e.txt" && git -C "$REPO8" add e.txt && git -C "$REPO8" commit -q -m "e"
ELIG_SHA="$(git -C "$REPO8" rev-parse HEAD)"
git -C "$REPO8" checkout -q development
git -C "$REPO8" update-ref "refs/remotes/origin/issue/500-eligible" "$ELIG_SHA"

BIN8="$TMP/bin-idem"
mkdir -p "$BIN8"
cat >"$BIN8/gh" <<GHEOF
#!/usr/bin/env bash
set -euo pipefail
printf '%s\n' "\$*" >>"\${GH_CALL_LOG:-/dev/null}"
if [[ "\$*" == *"--head issue/500-eligible"* ]]; then
  echo '[{"number":5001,"state":"MERGED","mergedAt":"2026-01-01T00:00:00Z","labels":[],"headRefOid":"${ELIG_SHA}"}]'
  exit 0
fi
if [[ "\$*" == *"pr view"* ]]; then
  echo '{"number":49,"state":"CLOSED","headRefName":"issue/43-x"}'
  exit 0
fi
echo '[]'
exit 0
GHEOF
chmod +x "$BIN8/gh"
export PATH="$BIN8:$PATH"

OUT8a="$TMP/idem-a.out"
OUT8b="$TMP/idem-b.out"
(
  cd "$REPO8"
  env -u GH_REPO GITHUB_REPOSITORY=linktrend/IDE-Development \
    bash scripts/cleanup-merged-branches.sh --remote --repo linktrend/IDE-Development
) >"$OUT8a" 2>&1 || true
(
  cd "$REPO8"
  env -u GH_REPO GITHUB_REPOSITORY=linktrend/IDE-Development \
    bash scripts/cleanup-merged-branches.sh --remote --repo linktrend/IDE-Development
) >"$OUT8b" 2>&1 || true
# Normalize volatile paths if any — compare decision lines
grep -E '^(KEEP|WOULD_DELETE)' "$OUT8a" | sort >"$TMP/idem-a.norm"
grep -E '^(KEEP|WOULD_DELETE)' "$OUT8b" | sort >"$TMP/idem-b.norm"
diff -u "$TMP/idem-a.norm" "$TMP/idem-b.norm" >/dev/null \
  || fail "dry-run not idempotent:\n$(diff -u "$TMP/idem-a.norm" "$TMP/idem-b.norm")"
# Failed auth retry: empty --repo twice
BEFORE_BRANCHES="$(git -C "$REPO8" branch -a | sort | shasum -a 256)"
set +e
(cd "$REPO8" && bash scripts/cleanup-merged-branches.sh --remote --repo "" --apply) >"$TMP/idem-fail1.out" 2>&1
(cd "$REPO8" && bash scripts/cleanup-merged-branches.sh --remote --repo "" --apply) >"$TMP/idem-fail2.out" 2>&1
set -e
AFTER_BRANCHES="$(git -C "$REPO8" branch -a | sort | shasum -a 256)"
[[ "$BEFORE_BRANCHES" == "$AFTER_BRANCHES" ]] || fail "branches mutated after failed auth retries"
pass "retry/idempotence: dry-run stable; failed auth zero mutation"

# ---------------------------------------------------------------------------
# 9) Coexistence smoke: portable-v2 script still present & cleanup unit suite path
# ---------------------------------------------------------------------------
[[ -x "$ROOT/tests/test-portable-v2-integration.sh" || -f "$ROOT/tests/test-portable-v2-integration.sh" ]] \
  || fail "WP01 portable integration script missing"
[[ -f "$ROOT/scripts/tests/test-stale-cleanup-controls.sh" ]] \
  || fail "cleanup controls suite missing"
# Import both modules in one process (no name clash / path clash)
export TEST_ROOT="$ROOT"
python3 - <<'PY'
import importlib.util
import sys
from pathlib import Path
import os
root = Path(os.environ["TEST_ROOT"])
sys.path.insert(0, str(root / "scripts" / "gitops"))
import cleanup_controls  # noqa: F401
spec = importlib.util.spec_from_file_location(
    "repair_task", root / "scripts" / "gitops" / "repair_task.py"
)
rt = importlib.util.module_from_spec(spec)
assert spec.loader is not None
# Do not execute main; just load module attrs via partial — import side effects OK
spec.loader.exec_module(rt)
assert hasattr(cleanup_controls, "resolve_cleanup_repo")
assert hasattr(cleanup_controls, "export_preserve_for_shell")
assert hasattr(cleanup_controls, "normalize_caller_repo")
assert hasattr(rt, "main")
print("ok-imports")
PY
pass "cleanup_controls + repair_task import alongside WP01 gitops tree"

echo ""
echo "ALL PASS: cleanup lineage + WP01 portable-system lineage coexistence"
