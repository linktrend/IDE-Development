# Issue #72 Lane C — commands run

Worktree:

```text
/Users/linktrend/Projects/IDE Development/.git/linktrend-worktrees/issue-72-pre-launch-ide-development-codebase-cleanup-arch
```

Branch: `issue/72-pre-launch-ide-development-codebase-cleanup-arch`
No commit / no push.

## Discovery / reference proof

```bash
git branch --show-current
git status -sb
ls -la claude chatgpt codex

rg -n --glob '!**/gstack/**' --glob '!**/.cursor/runtime/**' --glob '!**/core/runtime/**' \
  'claude/CLAUDE\.md|(^|[^/.])claude/'

rg -n 'chatgpt/AGENTS|codex/AGENTS\.md|codex/README'
rg -n 'chatgpt|codex/|claude' scripts/wire-repo.sh scripts/backfill-managed-workflows.sh scripts/sync-managed-workflows.sh
rg -n 'claude/|chatgpt/|codex/AGENTS' scripts/verify-ide-development.sh

python3 - <<'PY'
# MANIFEST scan for root claude/chatgpt/codex (not platforms/codex)
...
PY

gh issue view 72 --json title,body
```

## Archive action

```bash
mkdir -p docs/archive/platform-entrypoints/claude
git mv claude/CLAUDE.md docs/archive/platform-entrypoints/claude/CLAUDE.md
rmdir claude 2>/dev/null || true
```

## Manifest / retention checks (no regen)

```bash
env PYTHONPATH=scripts python3 -m ide_development.build_manifest --verify
# → MANIFEST verify OK

python3 - <<'PY'
# assert chatgpt/AGENTS.md + codex/AGENTS.md exist
# assert claude/CLAUDE.md absent
# assert archive path present
PY
```

## Manifest regeneration

**Not run.** Root `claude/` was not a MANIFEST source; archive does not change `core/managed-core/MANIFEST.json`. Hand-edit of generated manifests forbidden and unnecessary.
