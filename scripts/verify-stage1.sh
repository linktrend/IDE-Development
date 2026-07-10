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

# --- Hybrid registry exists ---
[ -f "docs/HYBRID-SKILLS-REGISTRY.md" ] || fail "Missing docs/HYBRID-SKILLS-REGISTRY.md"
pass "Hybrid skills registry present"

# --- Sunset skills gone from core/skills/ ---
SUNSET_SKILLS=(
  release-readiness
  browser-qa
  retrospective-learning
  spec-driven-development
  plan-writing
  task-decomposition
  test-driven-development
  systematic-debugging
)
for skill in "${SUNSET_SKILLS[@]}"; do
  [ ! -d "core/skills/$skill" ] || fail "Sunset skill still present: core/skills/$skill"
done
pass "All 8 sunset skills removed from core/skills/"

# --- Hybrid command entrypoints ---
[ -f "core/commands/hybrid-spec.md" ] || fail "Missing core/commands/hybrid-spec.md"
[ -f "core/commands/hybrid-grill.md" ] || fail "Missing core/commands/hybrid-grill.md"
[ -f "core/commands/hybrid-tdd.md" ] || fail "Missing core/commands/hybrid-tdd.md"
pass "Hybrid command entrypoints present"

# --- No LiNKdev in operator guide (LiNKdeveloper is allowed) ---
linkdev_hits="$(grep -in 'linkdev' docs/LINKDEVELOPER-WORKSPACE-OPERATOR-GUIDE.md 2>/dev/null | grep -iv 'linkdeveloper' || true)"
if [ -n "$linkdev_hits" ]; then
  fail "LiNKdev mentioned in operator guide (forbidden): $linkdev_hits"
fi
pass "Operator guide has no LiNKdev references"

echo ""
echo "Stage 1 verification: ALL CHECKS PASSED"
exit 0
