#!/usr/bin/env bash
# Wire a consumer repository for LiNKtrend GitOps portability.
# Installs managed workflows (rendered from consumer config), runtime scripts,
# a physical Cursor bootstrap rule, and an AGENTS.md managed section.
#
# Does NOT symlink consumer .cursor to IDE Development (that is Mac-local and
# breaks Cursor Cloud / other machines).
set -euo pipefail

SYSTEM_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

fail() { echo "FAIL: $1" >&2; exit 1; }
info() { echo "$1"; }

canonicalize() {
  local path="$1"
  if command -v realpath >/dev/null 2>&1; then
    realpath "$path"
  else
    (cd "$path" && pwd -P)
  fi
}

usage() {
  cat <<EOF
Usage: $(basename "$0") <consumer-repo-path> [--ci-workflow-name NAME] [--branch-policy-workflow-name NAME] [--bugbot-check-name NAME] [--runner-type TYPE]

Wires managed GitOps into a consumer repository:
  - requires/creates .github/linktrend-gitops-consumer.json
  - syncs managed workflows (rendered names) + runtime scripts
  - installs physical .cursor/rules/cursor-gitops-bootstrap.mdc
  - upserts IDE-managed AGENTS.md section (never overwrites consumer text)

Examples:
  $(basename "$0") /path/to/LiNKsites --ci-workflow-name "Consumer CI"
  $(basename "$0") .
EOF
}

TARGET_INPUT=""
CI_NAME=""
BRANCH_POLICY_NAME=""
BUGBOT_NAME=""
RUNNER_TYPE="github-hosted"
RUNNER_TYPE_SET=0

while [ $# -gt 0 ]; do
  case "$1" in
    -h|--help) usage; exit 0 ;;
    --ci-workflow-name)
      [ $# -ge 2 ] || fail "--ci-workflow-name requires a value"
      CI_NAME="$2"; shift 2 ;;
    --branch-policy-workflow-name)
      [ $# -ge 2 ] || fail "--branch-policy-workflow-name requires a value"
      BRANCH_POLICY_NAME="$2"; shift 2 ;;
    --bugbot-check-name)
      [ $# -ge 2 ] || fail "--bugbot-check-name requires a value"
      BUGBOT_NAME="$2"; shift 2 ;;
    --runner-type)
      [ $# -ge 2 ] || fail "--runner-type requires a value"
      RUNNER_TYPE="$2"; RUNNER_TYPE_SET=1; shift 2 ;;
    *)
      if [ -z "$TARGET_INPUT" ]; then
        TARGET_INPUT="$1"; shift
      else
        fail "Unexpected argument: $1"
      fi
      ;;
  esac
done

[ -n "$TARGET_INPUT" ] || { usage >&2; exit 1; }
[ -d "$TARGET_INPUT" ] || fail "Target path is not a directory: $TARGET_INPUT"

TARGET_REPO="$(canonicalize "$TARGET_INPUT")"
info "System repository: $SYSTEM_ROOT"
info "Consumer repository: $TARGET_REPO"

if [ "$TARGET_REPO" = "$(canonicalize "$SYSTEM_ROOT")" ]; then
  fail "Refusing to wire the system repository to itself"
fi

CONFIG_PATH="${TARGET_REPO}/.github/linktrend-gitops-consumer.json"
mkdir -p "${TARGET_REPO}/.github"

if [ ! -f "$CONFIG_PATH" ]; then
  if [ -z "$CI_NAME" ] || [ -z "$BRANCH_POLICY_NAME" ]; then
    fail "Missing $CONFIG_PATH. Create it or pass --ci-workflow-name and --branch-policy-workflow-name (fail closed)."
  fi
  BUGBOT_NAME="${BUGBOT_NAME:-Cursor Bugbot}"
  python3 - "$CONFIG_PATH" "$CI_NAME" "$BRANCH_POLICY_NAME" "$BUGBOT_NAME" "$RUNNER_TYPE" <<'PY'
import json, sys
from pathlib import Path
path, ci, branch, bugbot, runner_type = sys.argv[1:6]
Path(path).write_text(json.dumps({
    "schemaVersion": 1,
    "ciWorkflowName": ci,
    "branchPolicyWorkflowName": branch,
    "bugbotCheckName": bugbot,
    "runnerType": runner_type,
}, indent=2) + "\n", encoding="utf-8")
print(f"PASS: wrote consumer config {path}")
PY
elif [ -n "$CI_NAME" ] || [ -n "$BRANCH_POLICY_NAME" ] || [ -n "$BUGBOT_NAME" ] || [ "$RUNNER_TYPE_SET" -eq 1 ]; then
  fail "Config already exists at $CONFIG_PATH; refuse to overwrite with CLI flags. Edit the JSON instead."
fi

[ -f "$CONFIG_PATH" ] || fail "Consumer config missing after setup: $CONFIG_PATH"

info ""
info "=== Layer A: physical .cursor tree (no IDE Development symlink) ==="
TARGET_CURSOR="${TARGET_REPO}/.cursor"
timestamp="$(date +%Y%m%d-%H%M%S)"
if [ -L "$TARGET_CURSOR" ]; then
  backup_path="${TARGET_REPO}/.cursor-symlink-backup-${timestamp}"
  info "Migrating symlink .cursor -> physical tree; backup: $backup_path"
  mv "$TARGET_CURSOR" "$backup_path"
elif [ -e "$TARGET_CURSOR" ] && [ ! -d "$TARGET_CURSOR" ]; then
  fail "Ambiguous .cursor path exists and is not a directory/symlink: $TARGET_CURSOR"
fi
mkdir -p "${TARGET_CURSOR}/rules" "${TARGET_CURSOR}/commands" "${TARGET_CURSOR}/skills"
[ ! -L "$TARGET_CURSOR" ] || fail "Consumer .cursor must not be a symlink after wire"

info ""
info "=== Layer B: sync managed GitHub workflows (rendered names) ==="
SYNC_SCRIPT="${SYSTEM_ROOT}/scripts/sync-managed-workflows.sh"
[ -f "$SYNC_SCRIPT" ] || fail "Missing sync script: $SYNC_SCRIPT"
bash "$SYNC_SCRIPT" "$TARGET_REPO" --config "$CONFIG_PATH"

info ""
info "=== Layer C: sync managed runtime scripts + Cursor entrypoints ==="
RUNTIME_SYNC="${SYSTEM_ROOT}/scripts/sync-managed-runtime.sh"
[ -f "$RUNTIME_SYNC" ] || fail "Missing runtime sync: $RUNTIME_SYNC"
bash "$RUNTIME_SYNC" "$TARGET_REPO"

# Prove managed Cursor entrypoints exist as regular files
for rel in \
  ".cursor/rules/cursor-gitops-bootstrap.mdc" \
  ".cursor/rules/linktrend-git-branching.mdc" \
  ".cursor/commands/agentsetup.md" \
  ".cursor/commands/agentcomply.md" \
  ".cursor/skills/agentsetup/SKILL.md" \
  ".cursor/skills/agentcomply/SKILL.md"; do
  [ -f "${TARGET_REPO}/${rel}" ] || fail "Missing managed entrypoint after sync: $rel"
  [ ! -L "${TARGET_REPO}/${rel}" ] || fail "Managed entrypoint must be a regular file: $rel"
done
info "PASS: managed agentsetup/agentcomply Cursor entrypoints installed"

info ""
info "=== Layer D: AGENTS.md managed section ==="
AGENTS_SYNC="${SYSTEM_ROOT}/scripts/sync-agents-managed-section.sh"
[ -f "$AGENTS_SYNC" ] || fail "Missing agents sync: $AGENTS_SYNC"
bash "$AGENTS_SYNC" "$TARGET_REPO"

info ""
info "Wire summary: SUCCESS"
info "Consumer: $TARGET_REPO"
info "Cursor: physical managed entrypoints under .cursor/ (not a symlink to IDE Development)"
info "Config: $CONFIG_PATH"
info "Managed workflows + runtime + agentsetup/agentcomply + AGENTS section: synced"
info "Next: complete Bugbot checklist — core/checklists/BUGBOT-INHERITANCE.md"
info "Next: Cursor Automations — docs/CURSOR-AUTOMATIONS-SETUP.md"
info "Next: commit .github/linktrend-gitops-consumer.json and managed .cursor entrypoints"
exit 0
