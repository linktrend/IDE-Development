#!/usr/bin/env bash
# Upsert the LiNKtrend IDE-managed section into a consumer AGENTS.md.
# Preserves all consumer content outside BEGIN/END markers. Creates AGENTS.md if missing.
set -euo pipefail

SYSTEM_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SECTION_SRC="${SYSTEM_ROOT}/core/github/managed-runtime/AGENTS.managed-section.md"
BEGIN="<!-- BEGIN LINKTREND-IDE-MANAGED -->"
END="<!-- END LINKTREND-IDE-MANAGED -->"

fail() { echo "FAIL: $1" >&2; exit 1; }
info() { echo "$1"; }

usage() {
  cat <<EOF
Usage: $(basename "$0") <repo-path> [--dry-run]

Upsert delimited IDE-managed section into <repo-path>/AGENTS.md.
Never wipes consumer content outside the markers.
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
[ -d "$TARGET_INPUT" ] || fail "not a directory: $TARGET_INPUT"
[ -f "$SECTION_SRC" ] || fail "missing section template: $SECTION_SRC"

TARGET_REPO="$(cd "$TARGET_INPUT" && pwd -P)"
DEST="${TARGET_REPO}/AGENTS.md"
SECTION="$(cat "$SECTION_SRC")"

python3 - "$DEST" "$SECTION" "$BEGIN" "$END" "$DRY_RUN" <<'PY'
import pathlib, sys
dest = pathlib.Path(sys.argv[1])
section = sys.argv[2]
begin, end = sys.argv[3], sys.argv[4]
dry = sys.argv[5] == "1"

if dest.is_file():
    text = dest.read_text(encoding="utf-8")
else:
    text = "# AGENTS.md\n\nConsumer repository agent guidance.\n"

if begin in text and end in text:
    pre = text.split(begin, 1)[0]
    post = text.split(end, 1)[1]
    # Drop leading blank lines of post for tidy join
    new = pre.rstrip() + "\n\n" + section.rstrip() + "\n" + (post if post.startswith("\n") else "\n" + post)
else:
    new = text.rstrip() + "\n\n" + section.rstrip() + "\n"

if dry:
    print("DRY-RUN: would write", dest)
    print("--- preview (first 20 lines of section) ---")
    print("\n".join(section.splitlines()[:20]))
    raise SystemExit(0)

dest.write_text(new, encoding="utf-8")
print(f"PASS: upserted managed section into {dest}")
PY

info "AGENTS managed section sync: SUCCESS"
exit 0
