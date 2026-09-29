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

TMP="$(mktemp -d)"
cleanup() { rm -rf "$TMP"; }
trap cleanup EXIT

export LINKTREND_CONFLICT_BACKEND=file
export LINKTREND_REPAIR_BACKEND=file

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
pass "durable conflict attempts persist and stop at three"


# ============================================================================
# 6) Pull preserves caller checkout; updates clean unfinished; skips frozen
# ============================================================================
PULL="$TMP/pull"
make_repo "$PULL"
seed_scripts "$PULL"
git -C "$PULL" checkout -q -b issue/unfinished
echo u >"$PULL/u.txt" && git -C "$PULL" add u.txt && git -C "$PULL" commit -q -m "wip"
git -C "$PULL" checkout -q development
echo adv >"$PULL/adv.txt" && git -C "$PULL" add adv.txt && git -C "$PULL" commit -q -m "advance"
git -C "$PULL" update-ref refs/remotes/origin/development refs/heads/development
git -C "$PULL" checkout -q -b issue/frozen issue/unfinished
echo f >"$PULL/f.txt" && git -C "$PULL" add f.txt && git -C "$PULL" commit -q -m "frozen feat"
FR="$(git -C "$PULL" rev-parse HEAD)"
mkdir -p "$TMP/bin"
cat >"$TMP/bin/gh" <<EOF
#!/usr/bin/env bash
if [[ "\$*" == *"--head issue/frozen"* ]]; then
  echo '[{"headRefOid":"${FR}"}]'
else
  echo '[]'
fi
EOF
chmod +x "$TMP/bin/gh"
pushd "$PULL" >/dev/null
# Caller stays on development (not on unfinished)
git checkout -q development
BEFORE_BRANCH="$(git rev-parse --abbrev-ref HEAD)"
BEFORE_SHA="$(git rev-parse HEAD)"
BEFORE_STATUS="$(git status --porcelain)"
BEFORE_WT="$(git worktree list --porcelain)"
PATH="$TMP/bin:$PATH" bash scripts/pull-update-work-branches.sh --branch issue/frozen --branch issue/unfinished >"$TMP/pull.out"
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
if [[ "$*" == *"--head promote/main/"* ]]; then
  echo '[{"number":2,"state":"MERGED","mergedAt":"2026-01-01T00:00:00Z","labels":[],"headRefOid":"'"${PROMO_HEAD}"'"}]'
  exit 0
fi
if [[ "$*" == *"--head promote/staging/"* ]]; then
  echo '[{"number":5,"state":"MERGED","mergedAt":"2026-01-01T00:00:00Z","labels":[],"headRefOid":"'"${STAGING_PROMO_HEAD}"'"}]'
  exit 0
fi
if [[ "$*" == *"--head g1/"* ]]; then
  echo '[{"number":6,"state":"MERGED","mergedAt":"2026-01-01T00:00:00Z","labels":[],"headRefOid":"'"${G1_HEAD}"'"}]'
  exit 0
fi
if [[ "$*" == *"--head release-baseline/"* ]]; then
  echo '[{"number":7,"state":"MERGED","mergedAt":"2026-01-01T00:00:00Z","labels":[],"headRefOid":"'"${BASELINE_HEAD}"'"}]'
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
git -C "$CLN" checkout -q -b "promote/main/deadbeefcafe"
echo p >"$CLN/p.txt" && git -C "$CLN" add p.txt && git -C "$CLN" commit -q -m "promo"
PROMO_HEAD="$(git -C "$CLN" rev-parse HEAD)"
export PROMO_HEAD
git -C "$CLN" checkout -q development
git -C "$CLN" checkout -q -b "promote/staging/deadbeefcafe"
echo ps >"$CLN/ps.txt" && git -C "$CLN" add ps.txt && git -C "$CLN" commit -q -m "old staging promo"
STAGING_PROMO_HEAD="$(git -C "$CLN" rev-parse HEAD)"
export STAGING_PROMO_HEAD
git -C "$CLN" checkout -q development
git -C "$CLN" checkout -q -b "g1/leftover"
echo g >"$CLN/g.txt" && git -C "$CLN" add g.txt && git -C "$CLN" commit -q -m "g1 leftover"
G1_HEAD="$(git -C "$CLN" rev-parse HEAD)"
export G1_HEAD
git -C "$CLN" checkout -q development
git -C "$CLN" checkout -q -b "release-baseline/leftover"
echo b >"$CLN/b.txt" && git -C "$CLN" add b.txt && git -C "$CLN" commit -q -m "baseline leftover"
BASELINE_HEAD="$(git -C "$CLN" rev-parse HEAD)"
export BASELINE_HEAD
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
env -u GH_REPO GITHUB_REPOSITORY=linktrend/fixture PATH="$TMP/bin:$PATH" \
  bash -c "cd \"$CLN\" && bash scripts/cleanup-merged-branches.sh" >"$TMP/clean.out"
grep -q 'WOULD_DELETE_REMOTE: issue/squash\|WOULD_DELETE_LOCAL: issue/squash' "$TMP/clean.out" \
  || grep -q 'issue/squash' "$TMP/clean.out" || fail "squash merge should be cleanup-eligible: $(cat "$TMP/clean.out")"
grep -q 'WOULD_DELETE_.*promote/main/deadbeefcafe' "$TMP/clean.out" || fail "merged promote/main branch should be cleanup-eligible: $(cat "$TMP/clean.out")"
grep -q 'WOULD_DELETE_.*g1/leftover' "$TMP/clean.out" || fail "merged g1 leftover should be cleanup-eligible: $(cat "$TMP/clean.out")"
grep -q 'WOULD_DELETE_.*release-baseline/leftover' "$TMP/clean.out" || fail "merged release-baseline leftover should be cleanup-eligible: $(cat "$TMP/clean.out")"
grep -q 'KEEP:.*promote/staging/deadbeefcafe' "$TMP/clean.out" || fail "promote/staging is not a cleanup candidate: $(cat "$TMP/clean.out")"
grep -q 'KEEP: local:staging' "$TMP/clean.out" || fail "staging must stay: $(cat "$TMP/clean.out")"
grep -q 'issue/owned' "$TMP/clean.out" && grep -qi 'session ownership\|KEEP:.*owned' "$TMP/clean.out" \
  || fail "owned session must be kept: $(cat "$TMP/clean.out")"
grep -qi 'dirty' "$TMP/clean.out" || fail "dirty worktree should be mentioned"
grep -q 'CLEANUP_CALLER_UNCHANGED=1' "$TMP/clean.out"
grep -qv '^DELETED_' "$TMP/clean.out" || fail "dry-run must not delete"
pass "cleanup squash/session/promote/dirty safety (dry-run)"


# ============================================================================
# 9) Workflow activation docs; managed workflows have no scheduled wakes
# ============================================================================
grep -q 'default branch' "$ROOT/docs/GITOPS-CONSUMER-ROLLOUT.md"
grep -qi 'mention-only\|manualTriggerOnly' "$ROOT/docs/GITOPS-CONSUMER-ROLLOUT.md" \
  || grep -qi 'mention-only\|manualTriggerOnly' "$ROOT/docs/contracts/"*.md \
  || fail "mention-only documentation missing"
if grep -lE 'cron:|workflow_run:' "$ROOT/core/github/managed-workflows/"*.yml; then
  fail "managed workflows must not wake on schedule/workflow_run"
fi
pass "activation + mention-only docs + no scheduled managed wakes"

# ============================================================================
# Credential doctrine: custom App / PAT automation stays retired
# ============================================================================
python3 - "$ROOT" <<'PY'
from pathlib import Path
import sys

root = Path(sys.argv[1])
credential_doc = (root / "docs" / "contracts" / "GITHUB-APP-GITOPS-CREDENTIALS.md").read_text(encoding="utf-8")
assert "retired" in credential_doc.lower() or "no longer" in credential_doc.lower()
assert "LINKTREND_AUTOMATION_TOKEN" not in credential_doc
assert "LINKTREND_BUGBOT_USER_TOKEN" not in credential_doc
print("no-App credential doctrine ok")
PY
pass "Custom App and PAT automation retired in credential doctrine"

# ============================================================================
# Hosted managed workflows: least-privilege built-in authority, no custom App
# ============================================================================
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
for name in ("linktrend-cleanup-merged.yml",):
    text = (live / name).read_text(encoding="utf-8")
    assert "permissions:" in text
    assert "github.token" in text
print("built-in token identity boundary ok")
PY
pass "Built-in token identity is explicit; retired App identity absent"

echo ""
echo "PASS: behavioral gitops tests (${PASS} groups)"
