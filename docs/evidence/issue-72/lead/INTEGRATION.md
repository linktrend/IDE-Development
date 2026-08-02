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

## Codex correction (post-`dea8162`)

See [`codex-correction/README.md`](./codex-correction/README.md).

- Stripped trailing whitespace from Issue #72 evidence/archive markdown so `git diff --check origin/development...HEAD` passes.
- Redesigned moved-path reference check:

```bash
python3 docs/evidence/issue-72/lead/codex-correction/moved-path-ref-scan.py
```

  Distinguishes valid archive-pointer / historical citations from broken active dependencies; passing `ref-scan.rc` committed only when `RESULT=PASS`.
- Removed off-repo `/Users/linktrend/Projects/Archive/...` directory existence checks from `scripts/verify-ide-development.sh`; replaced with in-repo `docs/archive` (+ README) assertion. Normal command is `bash scripts/verify-ide-development.sh` with **no** `SKIP_LOCAL_ARCHIVE_CHECKS`.

## Validation (key exits)

Recorded on correction tip after whitespace + verifier fixes. Artifacts: `codex-correction/validation/`.

| Check | Exit | Notes |
|-------|------|-------|
| `git diff --check origin/development...HEAD` | 0 | `validation/git-diff-check.rc` |
| `PYTHONPATH=scripts python3 -m ide_development.build_manifest --verify` | 0 | `validation/manifest-verify.rc` |
| `bash scripts/verify-ide-development.sh` | 0 | no skip env; in-repo archive assertion |
| `bash tests/test-portable-v2-integration.sh` | 0 | verifier invoked without skip |
| `bash scripts/verify-platform-adoption.sh` | 0 | |
| `python3 docs/evidence/issue-72/lead/codex-correction/moved-path-ref-scan.py` | 0 | redesigned classification |
| Independent Grok review of corrections | FAIL→addressed | blockers cleared after post-commit re-proof |

## Hard stops honored

No review-ready, Packager, PR, Bugbot, merge, promote, tag/release, consumer mutation, GitHub cleanup apply, stash modification.
