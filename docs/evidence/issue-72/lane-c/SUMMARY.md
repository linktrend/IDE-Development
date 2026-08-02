# Issue #72 Lane C — SUMMARY

**Lane:** C (first-party dead-code / reference / manifest analysis)  
**Model:** Cursor Grok 4.5 High  
**Branch:** `issue/72-pre-launch-ide-development-codebase-cleanup-arch`  
**Commit/push:** none (per brief)

## Verdict

Conservative pass: **one archive**, **no deletes**, **no MANIFEST regen**, **native Codex untouched**.

## Archived

| Path | Destination | Proof strength |
|------|-------------|----------------|
| `claude/CLAUDE.md` | `docs/archive/platform-entrypoints/claude/CLAUDE.md` | **High** — Claude excluded; not in MANIFEST; RC excludes `claude/`; not required by `verify-platform-adoption.sh`; portable harness allows absence |

Also added `docs/archive/platform-entrypoints/README.md` (audit index).

## Deleted

None (prefer archive for audit).

## Retained (compatibility debt)

| Path | Why |
|------|-----|
| `chatgpt/AGENTS.md` | Hard required by `scripts/verify-platform-adoption.sh` (+ suites that call it) |
| `codex/AGENTS.md`, `codex/README.md` | Same verify hard-require; HIGH BAR vs weakening Codex surfaces |
| `scripts/wire-repo.sh`, `backfill-managed-workflows.sh`, `sync-managed-*.sh`, `sync-agents-managed-section.sh` | Active verify / migration / install dependencies — “legacy” name ≠ dead |

Native Codex kept intact: root `AGENTS.md`, `.agents/`, `core/managed-core/platforms/codex/`.

## Manifest

- Hand-edit: **no**
- Regenerate: **not needed** (archive path not a MANIFEST source)
- `env PYTHONPATH=scripts python3 -m ide_development.build_manifest --verify` → **OK**

## Risks

1. Active docs (Intent/PRD/README/SETUP) still say “historical `claude/` may remain” — accurate enough; Lane A/B may retarget to archive path.
2. Future removal of `chatgpt/` / root `codex/` requires redesigning `verify-platform-adoption.sh` first (not done here).
3. Branch-prefix `codex/` in gitops allowlists is unrelated; do not confuse with root folder.

## Out of scope (honored)

- No vendored gstack/mattpocock edits
- No broad Lane A/B doc rewrites
- No `.gitignore` edits (suggestion noted in inventory)
- No GitHub destructive ops / consumer mutation / commit / push
