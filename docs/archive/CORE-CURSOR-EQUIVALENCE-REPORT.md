# Core ↔ Cursor Equivalence Report

**Date:** 2026-07-10  
**Mission:** LiNKdeveloper Stage 1b, Phase 1 (Decision 3)  
**Repository:** IDE Development only

## Verdict

**Equivalent for shared knowledge content — intentional adapter asymmetry, no content drift detected.**

The symlinked portions of `.cursor/` resolve to the same files as `core/`. Spot-checks on five paired paths were byte-identical. No broken symlinks were found.

This is **not** a claim that `core/` and `.cursor/` are identical directory trees. They are designed to differ: `core/` holds canonical portable knowledge; `.cursor/` is a Cursor compatibility surface that symlinks into `core/` plus Cursor-only adapter files.

## Method

1. Compared top-level directory structures under `core/` and `.cursor/`.
2. Listed files present in one tree but not the other (by relative path).
3. Verified all `.cursor/` symlinks resolve (`find .cursor -type l` — 19 links, all valid).
4. Spot-checked five paired paths with `cmp`:
   - `skills/SKILLS_CATALOG.md` — **IDENTICAL**
   - `execution/CANONICAL-LAWS.md` — **IDENTICAL**
   - `workflows/WORKFLOW-MODEL.md` — **IDENTICAL**
   - `agents/README.md` — **IDENTICAL**
   - `templates/ISSUE.md` — **IDENTICAL**

## Structure summary

| Location | File count (approx.) | Role |
|---|---|---|
| `core/` | 275 files | Canonical portable knowledge asset |
| `.cursor/` | 14 direct files + 19 symlinks into `core/` | Compatibility runtime surface |

### Symlinked from `.cursor/` → `core/` (19 entries)

`BASELINE.md`, `agents`, `bootstrap`, `checklists`, `commands`, `contracts`, `discovery`, `examples`, `execution`, `pilots`, `prompts`, `reports`, `runtime`, `session`, `skills`, `state`, `system`, `templates`, `workflows`, `workspace`

Packaging is documented in `.cursor/import-core.md` and `.cursor/README.md`.

### Present only under `.cursor/` (intentional — not drift)

| Path | Purpose |
|---|---|
| `.cursor/INDEX.yaml` | Adapter index |
| `.cursor/README.md` | Cursor entrypoint and operating model |
| `.cursor/import-core.md` | Packaging guidance (`core/` canonical, `.cursor/` adapter) |
| `.cursor/mcp.json` | Local MCP configuration |
| `.cursor/rules/` | Cursor always-on rules (9 `.mdc` files) — **no `core/rules/` mirror exists** |

### Present only under `core/` (intentional — not drift)

All portable knowledge layers that `.cursor/` reaches via symlink. There is no separate duplicate copy of symlinked content under `.cursor/`; edits to `core/skills/`, `core/workflows/`, etc. are immediately visible through `.cursor/skills/`, `.cursor/workflows/`, etc.

## Drift list

**No content drift** in symlinked paired paths.

**Documented asymmetry** (expected by design, not defects):

1. **`core/rules/` does not exist** — rules live only under `.cursor/rules/`. Bootstrap and identity rules are Cursor-runtime artifacts, not duplicated in `core/`. Renaming `00-linkdev-bootstrap.mdc` → `00-bootstrap.mdc` applies only under `.cursor/rules/`; there is no `core/` mirror to rename.
2. **Historical path references** — several `core/` files still cite `.cursor/rules/00-linkdev-bootstrap.mdc` in prompts and reports (e.g. `core/prompts/execution/*.md`, `core/reports/CORE-MIGRATION-ASSESSMENT.md`). These are stale **path strings**, not duplicate rule files. Updating them is optional cleanup; not required for equivalence. Operational entrypoints `.cursor/README.md` and `.cursor/INDEX.yaml` were updated in Stage 1b to `00-bootstrap.mdc`.
3. **Stage 1a docs** (`docs/LINKDEVELOPER-STAGE1.md`, `LINKDEVELOPER-STAGE1A-SPEC.md`, `LINKDEVELOPER-STAGE1A-REPORT.md`) reference the old bootstrap filename as historical audit evidence — left unchanged unless Carlos requests a docs refresh.

## Recommendation for Carlos

1. **Treat `core/` as canonical for edits** to workflows, skills, contracts, templates, and doctrine. Changes propagate to `.cursor/` automatically via symlinks.
2. **Edit `.cursor/rules/` directly** for always-on Cursor rules — there is no `core/rules/` copy.
3. **No bulk sync required** before Stage 1b workspace setup. Equivalence is sufficient for semi-manual operation.
4. **Optional follow-up** (post-1b): replace stale `00-linkdev-bootstrap` path strings in `core/prompts/execution/` and legacy reports when convenient — low priority.

## Stage 1b action taken

Per locked Decision 3: equivalence verified and documented. No bulk tree sync performed.
