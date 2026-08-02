# WP02 Lane C SUMMARY — stale-cleanup hardening

## Verdict

Cleanup controls from tip **`5cf0991`** are fully restored under `docs/evidence/wp02/lane-c/proposed/**` (blob-verified). **`test-stale-cleanup-controls.sh` restored: YES.** New coexistence tests authored. Post-WP03 cleanup plan written (dry-run only). Conflict notes recommend take-cleanup for five paths; merge both §14 blocks in `OPEN-ISSUES.md`.

## Proposed paths (repo-relative after lead copy)

```
docs/evidence/wp02/lane-c/proposed/
  .github/workflows/linktrend-cleanup-merged.yml
  core/github/managed-workflows/linktrend-cleanup-merged.yml
  docs/OPEN-ISSUES.md                          # tip; reconcile §14 with WP01
  docs/contracts/LISA-LOCAL-CLEANUP-HANDOFF.md
  docs/contracts/REPAIR-DISPATCHER.md
  docs/contracts/STALE-CLEANUP-CONTROLS.md
  docs/handoff/2026-08-01-issue-63-cleanup-repo-scope.md
  scripts/cleanup-merged-branches.sh
  scripts/gitops/cleanup_controls.py
  scripts/gitops/cleanup_preserve.defaults.json
  scripts/gitops/cleanup_stale_records.py
  scripts/gitops/repair_task.py
  scripts/tests/test-stale-cleanup-controls.sh          # RESTORED
  scripts/tests/test-gitops-behavioral.sh
  scripts/tests/test-cleanup-wp01-lineage-coexistence.sh  # NEW
  scripts/ide_development_tests/fixtures/security/cleanup/wrong-repo-evidence.json  # WP01 ref copy
  scripts/ide_development_tests/fixtures/security/cleanup/PROVENANCE.txt
  tests/security_acceptance/test_cleanup_wp01_coexistence.py  # NEW
```

Lane docs (not under proposed/):

- `integration-test-design.md`
- `cleanup-plan-post-wp03.md`
- `conflict-resolution-notes.md`
- `commands-and-results.md`
- `SUMMARY.md`
- `notes/diff-wp01-vs-cleanup-*.diff`

## Required behavior coverage (from tip)

| Requirement | Where |
|-------------|--------|
| Fail-closed repository resolution | `cleanup_controls.resolve_cleanup_repo`, shell `resolve_cleanup_repo` |
| Reject malformed/ambiguous scope | Issue #63 empty/invalid `--repo`; Issue #59 origin+upstream |
| Preserve open AND closed PR heads | `export_preserve_for_shell` + test §9 CLOSED/MERGED |
| Correct issue-branch matching | `issue_number_from_branch` / `^issue/(\d+)(?:-|$)` |
| Repository-scoped PR evidence | Issue #61 `--repo CLEANUP_REPO` on every `gh pr list` |
| Dry-run-by-default | shell + `cleanup_stale_records` / `plan-cleanup-completed` |
| Exact authorization; no delete-by-name | classify gates: evidence + tip SHA + no OPEN + no WT + preserve OK |

## New integration test path(s)

1. `proposed/scripts/tests/test-cleanup-wp01-lineage-coexistence.sh`
2. `proposed/tests/security_acceptance/test_cleanup_wp01_coexistence.py`

## Blockers

| ID | Blocker | Impact |
|----|---------|--------|
| B1 | WP01 tree not present on this worktree `HEAD` | Coexistence suite cannot be executed here until lead merges WP01 + cleanup into real `scripts/` / `tests/` |
| B2 | `docs/OPEN-ISSUES.md` three-way conflict | Lead must keep WP01 §14 (Issue #67) **and** cleanup Issue #51 block (as §15) |
| B3 | No live apply allowed in WP02 | Remote WOULD_DELETE candidates remain until WP03; plan only |
| B4 | Open PRs #36/#37 conflicting/deferred | Not auto-closeable; Principal decision outside Lane C |
| B5 | Fixture copy under proposed | `wrong-repo-evidence.json` is WP01-owned — skip copy if blob already present after WP01 merge |

## Non-actions (confirmed)

- No commits, pushes, PRs, Bugbot, review-ready
- No live branch/worktree/PR deletion
- No edits outside `docs/evidence/wp02/lane-c/**`
