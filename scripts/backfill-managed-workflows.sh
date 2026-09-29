#!/usr/bin/env bash
# Backfill managed GitHub workflows for IDE Development + all currently wired consumers.
# Discovers consumer repos whose .cursor symlink resolves to this system's .cursor.

set -euo pipefail

SYSTEM_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SYNC="${SYSTEM_ROOT}/scripts/sync-managed-workflows.sh"
EXPECTED_CURSOR="$(cd "${SYSTEM_ROOT}/.cursor" && pwd -P)"

fail() {
  echo "FAIL: $1" >&2
  exit 1
}

info() {
  echo "$1"
}

[ -x "$SYNC" ] || chmod +x "$SYNC"
[ -f "$SYNC" ] || fail "Missing $SYNC"

resolve_symlink() {
  local path="$1"
  local link dir
  while [ -L "$path" ]; do
    link="$(readlink "$path")"
    if [[ "$link" != /* ]]; then
      dir="$(cd "$(dirname "$path")" && pwd -P)"
      path="${dir}/${link}"
    else
      path="$link"
    fi
    path="$(cd "$(dirname "$path")" && pwd -P)/$(basename "$path")"
  done
  if [ -d "$path" ]; then
    (cd "$path" && pwd -P)
  else
    echo "$path"
  fi
}

conflicts=()
sync_repo() {
  local repo="$1"
  local status=0
  "$SYNC" "$repo" || status=$?
  case "$status" in
    0) ;;
    11) conflicts+=("$repo") ;;
    *) fail "sync failed for $repo (exit $status)" ;;
  esac
}

info "=== Backfill IDE Development (system repo) ==="
sync_repo "$SYSTEM_ROOT"

PROJECTS_PARENT="$(cd "${SYSTEM_ROOT}/.." && pwd -P)"
info ""
info "=== Scanning ${PROJECTS_PARENT} for wired consumers ==="

found=0
for candidate in "${PROJECTS_PARENT}"/*; do
  [ -d "$candidate" ] || continue
  cursor_path="${candidate}/.cursor"
  [ -L "$cursor_path" ] || continue
  resolved="$(resolve_symlink "$cursor_path")"
  if [ "$resolved" != "$EXPECTED_CURSOR" ]; then
    continue
  fi
  # Skip if candidate is the system repo
  if [ "$(cd "$candidate" && pwd -P)" = "$(cd "$SYSTEM_ROOT" && pwd -P)" ]; then
    continue
  fi
  found=$((found + 1))
  info ""
  info "=== Backfill consumer: $candidate ==="
  sync_repo "$candidate"
done

info ""
info "Backfill complete. Wired consumers synced: $found"
if [ "${#conflicts[@]}" -gt 0 ]; then
  info "Retired workflows kept because they were modified locally (review, then delete deliberately):"
  for repo in "${conflicts[@]}"; do
    info "  - $repo"
  done
  exit 11
fi
info "Bugbot: complete core/checklists/BUGBOT-INHERITANCE.md per repo (dashboard step)."
info "Orchestrator: docs/AUTONOMOUS-GIT-OPERATIONS.md (Cursor Project step)."
exit 0
