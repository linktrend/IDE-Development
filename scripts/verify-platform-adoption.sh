#!/usr/bin/env bash
# Verify Cursor / Codex / ChatGPT GitOps entrypoints + key contracts exist.
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

echo "verify-platform-adoption: OK"
