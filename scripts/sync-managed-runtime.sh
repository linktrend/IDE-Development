#!/usr/bin/env bash
# Sync managed runtime files + Cursor entrypoints into a target repo.
# Never deletes consumer files outside the managed set. Idempotent.
# Bash 3.2+ / macOS compatible (no mapfile).
set -euo pipefail

SYSTEM_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
MANIFEST="${SYSTEM_ROOT}/core/github/managed-runtime/MANIFEST.json"

fail() { echo "FAIL: $1" >&2; exit 1; }
info() { echo "$1"; }

usage() {
  cat <<EOF
Usage: $(basename "$0") <repo-path> [--dry-run]

Copy MANIFEST.json scripts + cursorEntrypoints into <repo-path>.
Does not delete consumer files. Idempotent when bytes match.
Preserves unrelated consumer .cursor commands/skills/rules.
EOF
}

DRY_RUN=0
TARGET_INPUT=""
for arg in "$@"; do
  case "$arg" in
    -h|--help) usage; exit 0 ;;
    --dry-run) DRY_RUN=1 ;;
    *)
      if [ -z "$TARGET_INPUT" ]; then TARGET_INPUT="$arg"
      else fail "Unexpected argument: $arg"; fi
      ;;
  esac
done
[ -n "$TARGET_INPUT" ] || { usage >&2; exit 1; }
[ -d "$TARGET_INPUT" ] || fail "Target path is not a directory: $TARGET_INPUT"
[ -f "$MANIFEST" ] || fail "Missing manifest: $MANIFEST"

TARGET_REPO="$(cd "$TARGET_INPUT" && pwd -P)"
info "System: $SYSTEM_ROOT"
info "Target: $TARGET_REPO"

sync_one() {
  local src="$1"
  local dest="$2"
  local rel_label="$3"
  [ -f "$src" ] || fail "Missing source: $src"
  if [ -e "$dest" ] && [ ! -f "$dest" ]; then
    fail "Ambiguous collision (not a regular file): $dest"
  fi
  if [ -f "$dest" ] && cmp -s "$src" "$dest"; then
    info "PASS: unchanged $rel_label"
    unchanged=$((unchanged + 1))
    return 0
  fi
  if [ "$DRY_RUN" -eq 1 ]; then
    info "DRY-RUN: would sync $rel_label"
    copied=$((copied + 1))
    return 0
  fi
  if [ -f "$dest" ]; then
    timestamp="$(date +%Y%m%d-%H%M%S)"
    cp "$dest" "${dest}.bak-${timestamp}"
  fi
  mkdir -p "$(dirname "$dest")"
  cp "$src" "$dest"
  if [ -x "$src" ]; then chmod +x "$dest"; fi
  info "PASS: synced $rel_label"
  copied=$((copied + 1))
}

copied=0
unchanged=0

while IFS= read -r rel; do
  [ -n "$rel" ] || continue
  sync_one "${SYSTEM_ROOT}/${rel}" "${TARGET_REPO}/${rel}" "$rel"
done < <(python3 -c 'import json,sys; m=json.load(open(sys.argv[1])); print("\n".join(m.get("files") or []))' "$MANIFEST")

while IFS= read -r line; do
  [ -n "$line" ] || continue
  src_rel="${line%%|*}"
  dest_rel="${line#*|}"
  sync_one "${SYSTEM_ROOT}/${src_rel}" "${TARGET_REPO}/${dest_rel}" "$dest_rel"
done < <(python3 -c '
import json,sys
m=json.load(open(sys.argv[1]))
# legacy cursorRules list support
for p in m.get("cursorRules") or []:
    dest=".cursor/rules/"+p.split("/")[-1]
    print(p+"|"+dest)
for row in m.get("cursorEntrypoints") or []:
    print(row["src"]+"|"+row["dest"])
' "$MANIFEST")

info ""
info "Managed runtime sync: SUCCESS"
info "Synced/updated: $copied"
info "Already matched: $unchanged"
exit 0
