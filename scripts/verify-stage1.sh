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

# --- Operations manual and archive index ---
[ -f "docs/LINKDEVELOPER-OPERATIONS-MANUAL.md" ] || fail "Missing docs/LINKDEVELOPER-OPERATIONS-MANUAL.md"
pass "Operations manual present"

[ ! -f "docs/LINKDEVELOPER-WORKSPACE-OPERATOR-GUIDE.md" ] || fail "Retired doc must be removed: docs/LINKDEVELOPER-WORKSPACE-OPERATOR-GUIDE.md"
pass "Workspace operator guide retired (file absent)"

# --- No layer terminology in active docs (excluding docs/archive/) ---
while IFS= read -r -d '' file; do
  case "$file" in
    docs/archive/*|docs/adoption-backups/*) continue ;;
  esac
  if grep -qiE 'Layer [123]|three\.layer' "$file" 2>/dev/null; then
    fail "Forbidden layer terminology in active doc $file (Layer [123] or three.layer)"
  fi
done < <(find docs -type f -name '*.md' -print0 2>/dev/null)
pass "Active docs free of Layer 1/2/3 and three.layer terminology"

# --- No legacy linkdev commands at core/commands/ root ---
shopt -s nullglob
linkdev_cmds=(core/commands/linkdev-*.md)
shopt -u nullglob
if [ "${#linkdev_cmds[@]}" -gt 0 ]; then
  fail "Legacy linkdev command(s) at core/commands root (use compatibility-archive/): ${linkdev_cmds[*]}"
fi
pass "No linkdev-*.md at core/commands/ root"

[ -f "docs/ARCHIVE-INDEX.md" ] || fail "Missing docs/ARCHIVE-INDEX.md"
pass "Archive index present"

# --- Archived local snapshots (off-repo) ---
ARCHIVE_STAGE2="/Users/linktrend/Projects/Archive/LiNKdeveloper-Stage2-Runtime-20260710"
ARCHIVE_LINKDEV="/Users/linktrend/Projects/Archive/LiNKdev-legacy-20260710"
[ -d "$ARCHIVE_STAGE2" ] || fail "Missing archive directory: $ARCHIVE_STAGE2"
[ -d "$ARCHIVE_LINKDEV" ] || fail "Missing archive directory: $ARCHIVE_LINKDEV"
pass "Local archive snapshot directories present"

# --- No LiNKdev in active docs (LiNKdeveloper allowed; ARCHIVE-INDEX documents retirement) ---
while IFS= read -r -d '' file; do
  case "$file" in
    docs/archive/*|docs/adoption-backups/*|docs/ARCHIVE-INDEX.md) continue ;;
  esac
  linkdev_hits="$(grep -in 'linkdev' "$file" 2>/dev/null | grep -iv 'linkdeveloper' || true)"
  if [ -n "$linkdev_hits" ]; then
    fail "LiNKdev mentioned in active doc $file (forbidden): $linkdev_hits"
  fi
done < <(find docs -type f -name '*.md' -print0 2>/dev/null)
pass "Active docs have no LiNKdev references (excluding docs/archive, adoption-backups, ARCHIVE-INDEX)"

# --- No stale bootstrap in active prompts (core/ and .cursor/) ---
for prompt_root in core/prompts .cursor/prompts; do
  [ -d "$prompt_root" ] || continue
  while IFS= read -r -d '' file; do
    case "$file" in
      *adoption-backups*) continue ;;
    esac
    if grep -q '00-linkdev-bootstrap' "$file" 2>/dev/null; then
      fail "Stale bootstrap path in $file (expected 00-bootstrap.mdc)"
    fi
  done < <(find "$prompt_root" -type f \( -name '*.md' -o -name '*.mdc' \) -print0 2>/dev/null)
done
pass "No 00-linkdev-bootstrap in core/prompts/ or .cursor/prompts/ (excluding adoption-backups)"

# --- No dangling references to paths archived out of core/pilots ---
while IFS= read -r -d '' file; do
  case "$file" in
    docs/archive/*|docs/adoption-backups/*) continue ;;
  esac
  if grep -q 'core/pilots/hybrid-smoke' "$file" 2>/dev/null; then
    fail "Stale path in $file: core/pilots/hybrid-smoke was archived to docs/archive/pilots/hybrid-smoke"
  fi
done < <(find docs -type f -name '*.md' -print0 2>/dev/null)
pass "No dangling core/pilots/hybrid-smoke references in active docs"

# --- SKILLS_CATALOG.md path list matches skills on disk (both directions) ---
CATALOG="core/skills/SKILLS_CATALOG.md"
missing_from_disk=()
while IFS= read -r rel; do
  skill_dir="core/${rel%/SKILL.md}"
  [ -d "$skill_dir" ] || missing_from_disk+=("$rel")
done < <(grep -oE '`skills/[a-zA-Z0-9_-]+/SKILL\.md`' "$CATALOG" | tr -d '`')
if [ "${#missing_from_disk[@]}" -gt 0 ]; then
  fail "SKILLS_CATALOG.md lists skill(s) missing on disk: ${missing_from_disk[*]}"
fi

missing_from_catalog=()
for dir in core/skills/*/; do
  name="$(basename "$dir")"
  [ -f "${dir}SKILL.md" ] || continue
  grep -q "skills/${name}/SKILL.md" "$CATALOG" || missing_from_catalog+=("$name")
done
if [ "${#missing_from_catalog[@]}" -gt 0 ]; then
  fail "Skill folder(s) on disk missing from SKILLS_CATALOG.md path list: ${missing_from_catalog[*]}"
fi
pass "SKILLS_CATALOG.md path list matches core/skills/ on disk"

echo ""
echo "Stage 1 verification: ALL CHECKS PASSED"
exit 0
