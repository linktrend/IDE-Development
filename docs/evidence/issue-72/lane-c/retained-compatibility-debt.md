# Issue #72 Lane C — retained compatibility debt

Items intentionally **not** removed. Each has unresolved runtime/test/migration dependency or fails the HIGH BAR for Codex.

## Platform entrypoints

### `chatgpt/AGENTS.md`

- **Debt class:** parallel ChatGPT Work Agent entrypoint vs root `AGENTS.md` + `.agents/`
- **Blocker:** `scripts/verify-platform-adoption.sh` requires the file and asserts Review Ready / no implementer Open-PR language
- **Safe future path:** update verify to treat root `AGENTS.md` as the sole ChatGPT/Codex system-repo entry, then archive `chatgpt/` under `docs/archive/platform-entrypoints/`
- **Risk if removed now:** breaks `verify-platform-adoption`, `verify-ide-development`, portable integration, and gitops lifecycle suites

### `codex/AGENTS.md` + `codex/README.md`

- **Debt class:** historical Codex packaging folder vs native Codex (`.agents/`, root `AGENTS.md`, `core/managed-core/platforms/codex/`)
- **Blocker:** same hard verify require as `chatgpt/`; mission forbids weakening native Codex
- **Note:** `completion_gate.py` / `packager_logic.py` `codex/` strings are **branch prefixes**, not this folder
- **Safe future path:** same verify redesign as chatgpt; archive root `codex/` only after prove no other adapters/docs/tests depend on it; never touch `platforms/codex/`

## Wire / sync / backfill scripts

| Script | Debt rationale |
|--------|----------------|
| `scripts/wire-repo.sh` | Still executed by platform-adoption verify; documented pre-v2 GitOps compatibility path |
| `scripts/backfill-managed-workflows.sh` | Consumer migration/backfill history + wiring docs |
| `scripts/sync-managed-workflows.sh` | Live sync used by wire + verify unsafe-name tests |
| `scripts/sync-managed-runtime.sh` | Listed in verify required entrypoints |
| `scripts/sync-agents-managed-section.sh` | Listed in verify required entrypoints; AGENTS marker sync |

Do **not** delete merely because docs call them “legacy.” Removal requires a dedicated migration issue with substitute installer coverage.

## Packaging guardrails that remain

These are **not** debt to remove; they encode Claude exclusion:

- `scripts/ide_development/manifest.py` rejects `claude/` / `.claude/` MANIFEST sources
- `scripts/ide_development/release_candidate.py` excludes top-level `claude` from RC paths

They correctly continue to block reintroduction of Claude packaging surfaces.

## Temporary first-party code

No additional non-doc first-party temp/scratch code proven dead in this lane. Filesystem ignore/hygiene remains **Lane D**.
