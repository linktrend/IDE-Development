#!/usr/bin/env bash
# Sync managed runtime files (scripts referenced by linktrend-*.yml) into a target repo.
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

Copy MANIFEST.json files into <repo-path>, preserving relative paths.
Does not delete consumer files. Idempotent when bytes match.
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

copied=0
unchanged=0
while IFS= read -r rel; do
  [ -n "$rel" ] || continue
  src="${SYSTEM_ROOT}/${rel}"
  dest="${TARGET_REPO}/${rel}"
  [ -f "$src" ] || fail "Missing source: $src"
  if [ -f "$dest" ] && cmp -s "$src" "$dest"; then
    info "PASS: unchanged $rel"
    unchanged=$((unchanged + 1))
    continue
  fi
  if [ "$DRY_RUN" -eq 1 ]; then
    info "DRY-RUN: would sync $rel"
    copied=$((copied + 1))
    continue
  fi
  mkdir -p "$(dirname "$dest")"
  cp "$src" "$dest"
  if [ -x "$src" ]; then chmod +x "$dest"; fi
  info "PASS: synced $rel"
  copied=$((copied + 1))
done < <(python3 -c 'import json,sys; m=json.load(open(sys.argv[1])); print("\n".join(m.get("files") or []))' "$MANIFEST")

info ""
info "Managed runtime sync: SUCCESS"
info "Synced/updated: $copied"
info "Already matched: $unchanged"
exit 0
