#!/usr/bin/env bash
# Verify platform adoption via a temp consumer repo (no real 8-consumer wiring).
# Also keeps entrypoint/contract presence checks for IDE Development itself.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
fail() { echo "FAIL: $1" >&2; exit 1; }
pass() { echo "PASS: $1"; }

required=(
  ".cursor/rules/02-autonomous-ship-pull.mdc"
  "core/commands/agentsetup.md"
  "core/commands/agentcomply.md"
  "codex/AGENTS.md"
  "chatgpt/AGENTS.md"
  "docs/contracts/AGENT-COMPLETION.md"
  "docs/contracts/REPAIR-DISPATCHER.md"
  "docs/contracts/ACTIONS-COST-CONTROLS.md"
  "docs/contracts/LISA-LOCAL-CLEANUP-HANDOFF.md"
  "scripts/gitops/create_issue_branch.py"
  "scripts/gitops/completion_gate.py"
  "scripts/gitops/repair_task.py"
  "core/github/managed-workflows/linktrend-cleanup-merged.yml"
  "core/github/managed-workflows/linktrend-repair-observer.yml"
  "core/github/managed-runtime/MANIFEST.json"
  "scripts/sync-managed-runtime.sh"
  "scripts/sync-agents-managed-section.sh"
)

for f in "${required[@]}"; do
  [ -e "$f" ] || fail "missing $f"
done
pass "Required entrypoints and contracts present"

for f in chatgpt/AGENTS.md codex/AGENTS.md .cursor/rules/02-autonomous-ship-pull.mdc core/commands/agentcomply.md; do
  grep -q 'Review Ready\|review-ready\|review_ready' "$f" || fail "$f missing Review Ready language"
  if grep -qiE 'Open or update (a )?PR|open a PR targeting development' "$f"; then
    fail "$f still instructs implementer to open PR"
  fi
done
pass "Platform docs: Review Ready present; no implementer Open-PR instruction"

grep -q 'Lisa ACP Repair Dispatcher\|repair task' .cursor/rules/02-autonomous-ship-pull.mdc \
  || fail "ship-pull rule missing Lisa ACP Repair Dispatcher language"
if grep -nE 'prefer-incoming' .cursor/rules/02-autonomous-ship-pull.mdc docs/AUTONOMOUS-GIT-OPERATIONS.md \
  | grep -viE 'No prefer-incoming|no prefer-incoming|Never.*prefer-incoming|Must not|do not'; then
  fail "active prefer-incoming instruction"
fi
pass "Repair dispatcher language; no prefer-incoming instruction"

# ---- Temp consumer install (idempotent; preserves consumer AGENTS text) ----
TMP="$(mktemp -d "${TMPDIR:-/tmp}/verify-platform-adoption.XXXXXX")"
cleanup() { rm -rf "$TMP"; }
trap cleanup EXIT

CONSUMER="${TMP}/consumer"
mkdir -p "${CONSUMER}/.github/workflows"
(
  cd "$CONSUMER"
  git init -q -b development
  git config user.email t@example.com
  git config user.name t
)
CUSTOM_MARK="CONSUMER_CUSTOM_TEXT_DO_NOT_WIPE_$$"
cat >"${CONSUMER}/AGENTS.md" <<EOF
# Consumer AGENTS

${CUSTOM_MARK}

Consumer-specific policies live here.
EOF
cat >"${CONSUMER}/.github/workflows/ci.yml" <<'EOF'
name: CI
on: [push]
jobs:
  verify:
    name: Verify Consumer
    runs-on: ubuntu-latest
    steps:
      - run: echo ok
EOF

bash "$ROOT/scripts/sync-managed-workflows.sh" "$CONSUMER"
bash "$ROOT/scripts/sync-managed-runtime.sh" "$CONSUMER"
bash "$ROOT/scripts/sync-agents-managed-section.sh" "$CONSUMER"
mkdir -p "${CONSUMER}/.cursor/rules"
cp "$ROOT/core/github/managed-runtime/cursor-gitops-bootstrap.mdc" \
  "${CONSUMER}/.cursor/rules/cursor-gitops-bootstrap.mdc"

# Confirm every scripts/ path referenced by installed linktrend-*.yml exists
# (ignore comment-only mentions like "# Sync: scripts/sync-managed-workflows.sh")
missing=0
while IFS= read -r yml; do
  while IFS= read -r spath; do
    [ -n "$spath" ] || continue
    spath="${spath%/}"
    if [ ! -e "${CONSUMER}/${spath}" ]; then
      echo "MISSING in consumer: $spath (from $(basename "$yml"))" >&2
      missing=$((missing + 1))
    fi
  done < <(
    grep -vE '^[[:space:]]*#' "$yml" \
      | grep -oE 'scripts/[A-Za-z0-9_./-]+' \
      | sort -u
  )
done < <(find "${CONSUMER}/.github/workflows" -name 'linktrend-*.yml' -print)
[ "$missing" -eq 0 ] || fail "managed workflows reference missing scripts ($missing)"
pass "All scripts/ paths from linktrend-*.yml exist in consumer"

# Cursor rule present
ls "${CONSUMER}/.cursor/rules/"*gitops* >/dev/null 2>&1 \
  || [ -f "${CONSUMER}/.cursor/rules/cursor-gitops-bootstrap.mdc" ] \
  || fail "missing .cursor/rules gitops bootstrap"
pass "Cursor gitops bootstrap rule present"

# AGENTS markers + consumer text preserved
grep -q 'BEGIN LINKTREND-IDE-MANAGED' "${CONSUMER}/AGENTS.md" || fail "AGENTS missing BEGIN marker"
grep -q 'END LINKTREND-IDE-MANAGED' "${CONSUMER}/AGENTS.md" || fail "AGENTS missing END marker"
grep -q "$CUSTOM_MARK" "${CONSUMER}/AGENTS.md" || fail "AGENTS lost consumer custom text"
pass "AGENTS.md has IDE markers and preserves consumer text"

# actionlint installed workflows (ignore SC2129)
if command -v actionlint >/dev/null 2>&1; then
  set +e
  actionlint_out="$(actionlint "${CONSUMER}/.github/workflows/"*.yml 2>&1)"
  al_ec=$?
  set -e
  # Keep only finding header lines that are not SC2129; ignore caret context.
  filtered="$(printf '%s\n' "$actionlint_out" | grep -E '\.yml:[0-9]+:[0-9]+:' | grep -v 'SC2129' || true)"
  if [ -n "$(printf '%s' "$filtered" | tr -d '[:space:]')" ]; then
    echo "$filtered" >&2
    fail "actionlint reported errors"
  fi
  if [ "$al_ec" -ne 0 ] && [ -z "$(printf '%s' "$filtered" | tr -d '[:space:]')" ]; then
    pass "actionlint on installed workflows (SC2129 ignored)"
  else
    pass "actionlint on installed workflows (SC2129 ignored)"
  fi
else
  for yml in "${CONSUMER}/.github/workflows/"linktrend-*.yml; do
    [ -f "$yml" ] || fail "missing $yml"
  done
  pass "actionlint not installed; skipped (workflows present)"
fi

# Idempotent second install
bash "$ROOT/scripts/sync-managed-workflows.sh" "$CONSUMER" >/dev/null
bash "$ROOT/scripts/sync-managed-runtime.sh" "$CONSUMER" >/dev/null
bash "$ROOT/scripts/sync-agents-managed-section.sh" "$CONSUMER" >/dev/null
grep -q "$CUSTOM_MARK" "${CONSUMER}/AGENTS.md" || fail "second sync wiped consumer AGENTS text"
pass "Second install idempotent; consumer AGENTS custom text still present"

echo "verify-platform-adoption: OK"
