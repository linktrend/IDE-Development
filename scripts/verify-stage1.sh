#!/usr/bin/env bash
# LiNKdeveloper Stage 1 verification — stdlib/shell only.
# Exit 0 on pass; non-zero with message on fail.

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

fail() {
  echo "FAIL: $1" >&2
  exit 1
}

pass() {
  echo "PASS: $1"
}

# --- Broken symlink check ---
broken="$(find .cursor -type l ! -exec test -e {} \; -print 2>/dev/null | wc -l | tr -d ' ')"
total="$(find .cursor -type l 2>/dev/null | wc -l | tr -d ' ')"
if [ "$broken" != "0" ]; then
  fail "Found $broken broken symlink(s) under .cursor/ (of $total total)"
fi
pass "Symlinks: $total total, 0 broken"

# --- Wire-checklist structure (file/dir existence) ---
required_files=(
  ".cursor/README.md"
  "core/checklists/wire-checklist.md"
  ".cursor/skills/SKILLS_CATALOG.md"
  ".cursor/rules/00-bootstrap.mdc"
  ".cursor/bootstrap/START-HERE.md"
  ".cursor/commands/INDEX.yaml"
  ".cursor/commands/small-change.md"
)

required_dirs=(
  ".cursor/rules"
  ".cursor/skills"
  ".cursor/prompts"
  ".cursor/agents"
  ".cursor/templates"
  ".cursor/commands"
  "core/workflows"
  "core/checklists"
)

for f in "${required_files[@]}"; do
  [ -f "$f" ] || fail "Missing required file: $f"
done
pass "Wire-checklist required files present"

for d in "${required_dirs[@]}"; do
  [ -d "$d" ] || fail "Missing required directory: $d"
done
pass "Wire-checklist required directories present"

# workflows/ and checklists/ resolve via .cursor symlink
for link in workflows checklists; do
  [ -L ".cursor/$link" ] || fail ".cursor/$link is not a symlink"
  [ -e ".cursor/$link" ] || fail ".cursor/$link symlink is broken"
done
pass "core/ → .cursor/ symlinks for workflows and checklists"

# --- No 00-linkdev-bootstrap in active execution prompts ---
PROMPT_DIR="core/prompts/execution"
if [ -d "$PROMPT_DIR" ]; then
  while IFS= read -r -d '' file; do
    case "$file" in
      *adoption-backups*) continue ;;
    esac
    if grep -q '00-linkdev-bootstrap' "$file" 2>/dev/null; then
      fail "Stale bootstrap path in $file (expected 00-bootstrap.mdc)"
    fi
  done < <(find "$PROMPT_DIR" -type f -name '*.md' -print0 2>/dev/null)
fi
pass "No 00-linkdev-bootstrap in core/prompts/execution/ (excluding adoption-backups)"

echo ""
echo "Stage 1 verification: ALL CHECKS PASSED"
exit 0
