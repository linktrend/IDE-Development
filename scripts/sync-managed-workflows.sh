#!/usr/bin/env bash
# Sync managed GitHub workflow templates from IDE Development into a target repo.
# Does not overwrite consumer-specific ci.yml or unrelated workflows.
# Stdlib/bash only. Exit 0 on success; non-zero on failure.

set -euo pipefail

SYSTEM_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TEMPLATE_DIR="${SYSTEM_ROOT}/core/github/managed-workflows"

MANAGED_FILES=(
  "branch-source-policy.yml"
  "linktrend-review-packager.yml"
  "linktrend-development-to-staging.yml"
  "linktrend-staging-to-main.yml"
  "linktrend-integrator-merge.yml"
  "linktrend-cleanup-merged.yml"
  "linktrend-repair-observer.yml"
)

fail() {
  echo "FAIL: $1" >&2
  exit 1
}

info() {
  echo "$1"
}

usage() {
  cat <<EOF
Usage: $(basename "$0") <repo-path> [--dry-run]

Copy managed GitHub workflow templates into <repo-path>/.github/workflows/.
Never overwrites ci.yml. Idempotent when files already match.

Examples:
  $(basename "$0") /Users/you/Projects/SomeProductRepo
  $(basename "$0") . --dry-run
EOF
}

DRY_RUN=0
TARGET_INPUT=""

for arg in "$@"; do
  case "$arg" in
    -h|--help)
      usage
      exit 0
      ;;
    --dry-run)
      DRY_RUN=1
      ;;
    *)
      if [ -z "$TARGET_INPUT" ]; then
        TARGET_INPUT="$arg"
      else
        fail "Unexpected argument: $arg"
      fi
      ;;
  esac
done

if [ -z "$TARGET_INPUT" ]; then
  usage >&2
  exit 1
fi

[ -d "$TARGET_INPUT" ] || fail "Target path is not a directory: $TARGET_INPUT"
[ -d "$TEMPLATE_DIR" ] || fail "Template directory missing: $TEMPLATE_DIR"

TARGET_REPO="$(cd "$TARGET_INPUT" && pwd -P)"
DEST_DIR="${TARGET_REPO}/.github/workflows"

info "System repository: $SYSTEM_ROOT"
info "Target repository: $TARGET_REPO"
info "Template source: $TEMPLATE_DIR"

if [ "$DRY_RUN" -eq 0 ]; then
  mkdir -p "$DEST_DIR"
fi

copied=0
unchanged=0

for file in "${MANAGED_FILES[@]}"; do
  src="${TEMPLATE_DIR}/${file}"
  dest="${DEST_DIR}/${file}"
  [ -f "$src" ] || fail "Missing template: $src"

  if [ -f "$dest" ] && cmp -s "$src" "$dest"; then
    info "PASS: unchanged $file"
    unchanged=$((unchanged + 1))
    continue
  fi

  if [ "$DRY_RUN" -eq 1 ]; then
    if [ -f "$dest" ]; then
      info "DRY-RUN: would update $file"
    else
      info "DRY-RUN: would create $file"
    fi
    copied=$((copied + 1))
    continue
  fi

  cp "$src" "$dest"
  info "PASS: synced $file"
  copied=$((copied + 1))
done

info ""
info "Managed workflow sync: SUCCESS"
info "Target: $TARGET_REPO"
info "Synced/updated: $copied"
info "Already matched: $unchanged"
info "Next: complete core/checklists/BUGBOT-INHERITANCE.md for this repo"
info "Next: ensure Cursor Automations exist (docs/CURSOR-AUTOMATIONS-SETUP.md)"
exit 0
