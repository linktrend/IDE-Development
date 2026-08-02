# Issue #72 Codex correction evidence

**Lead:** Cursor Grok 4.5 High
**Date:** 2026-08-02
**Scope:** Corrective fixes for Codex independent verification defects on Issue #72 tip `dea8162`.

## Defects addressed

1. **Trailing whitespace** — `git diff --check origin/development...HEAD` failed on Issue #72 evidence/archive markdown. Stripped trailing spaces/tabs in all reported files; semantics unchanged.
2. **Moved-path ref-scan** — prior `ref-scan.rc` was `1` because a naive `rg` treated valid pointer/historical citations as failures. Replaced with `moved-path-ref-scan.py`, which:
   - asserts each Lane B move destination exists;
   - asserts retained old paths are relocate pointer stubs;
   - classifies active-surface hits as **valid** (archive/pointer/historical/optional markers) vs **broken** (unmarked active dependency / hard-require);
   - excludes `docs/archive/**` and `docs/evidence/issue-72/**` as historical/self evidence.
3. **Off-repo Archive verifier dependency** — removed absolute `/Users/linktrend/Projects/Archive/...` checks and `SKIP_LOCAL_ARCHIVE_CHECKS` gate from `scripts/verify-ide-development.sh`. Replaced with in-repo assertions: `docs/ARCHIVE-INDEX.md`, `docs/archive/`, `docs/archive/README.md`. Updated active acceptance matrix H11 and portable v2 harness to run the verifier with no skip env. Historical archived/WP1 evidence commands left as recorded truth.

## Exact moved-path check

```bash
python3 docs/evidence/issue-72/lead/codex-correction/moved-path-ref-scan.py
```

Evidence outputs: `validation/ref-scan.out`, `validation/ref-scan.rc`.

## Hard stops honored

No PR, Bugbot, merge, promote, tag/release, consumer mutation, GitHub settings changes, close/delete of PRs/issues/branches/worktrees, or stash operations.
