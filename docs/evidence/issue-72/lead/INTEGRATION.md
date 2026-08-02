# Issue #72 lead integration record

**Lead:** Cursor Grok 4.5 High  
**Branch:** `issue/72-pre-launch-ide-development-codebase-cleanup-arch`  
**Date:** 2026-08-02

## Lane outcomes

| Lane | Result |
|------|--------|
| A | Active docs + CURRENT-STATUS + WP04 packet |
| B | Archive hierarchy + stubs + indexes |
| C | Archived `claude/` only; retained chatgpt/codex + wire/sync scripts |
| D | `.gitignore` expanded; no tracked junk deleted |
| E | PLAN ONLY disposition (no apply) |
| F | git-hygiene PASS; dead-code PASS; docs-truth FAIL→repaired (F1–F7) → re-review |

## Lead repairs

- Applied Lane B link-fix requests on BUILD-LOG / OPEN-ISSUES / GITOPS / EXTERNAL-STATE / contracts
- Retargeted Claude packaging docs to `docs/archive/platform-entrypoints/claude/`
- Regenerated MANIFEST via `python3 -m ide_development.build_manifest` (no hand-edit)
- Docs-truth majors F1–F3 + minors F4–F7

## Validation (key exits)

| Check | Exit | Notes |
|-------|------|-------|
| `git diff --check` | 0 | |
| MANIFEST `--verify` | 0 | after regen |
| `SKIP_LOCAL_ARCHIVE_CHECKS=1 verify-ide-development.sh` | 0 | off-repo Archive snapshots absent on this machine (documented skip) |
| `tests/test-portable-v2-integration.sh` | 0 | |
| `verify-platform-adoption.sh` | 0 | |
| `test-stale-cleanup-controls.sh` | 0 | |
| `test-cleanup-wp01-lineage-coexistence.sh` | 0 | |
| `test-gitops-behavioral.sh` | 0 | |
| `test-gitops-lifecycle.sh` | 0 | |
| `pytest tests/security_acceptance/test_cleanup_wp01_coexistence.py` | 0 | |

## Hard stops honored

No review-ready, Packager, PR, Bugbot, merge, promote, tag/release, consumer mutation, GitHub cleanup apply, stash modification.
