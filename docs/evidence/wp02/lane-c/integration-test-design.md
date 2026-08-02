# WP02 Lane C — Integration test design

**Lane:** C (stale-cleanup hardening)
**Date:** 2026-08-02
**Immutable inputs:** cleanup `5cf099155d9f7b5d95e094f74b288af7aec766af`, WP01 `89956878c54ff45e4aef1ff42883d209221b7a30`, development `991abc319782008ef93af95002be0d7f3d5a937c`

## Goal

Prove that after the lead merges **WP01 portable-system lineage** then **cleanup tip controls**, both lineages coexist: cleanup fail-closed hardening remains authoritative for delete/authorization, and WP01 repo-scope / portable security fixtures remain authoritative for installer and evidence scope.

## Merge order assumed by tests

1. `origin/development` base
2. WP01 checkpoint (portable-v2, security_acceptance, wrong-repo fixture)
3. Cleanup tip `5cf0991` (cleanup_controls, stale suite, shell `--repo`)
4. Lane C proposed additions (new coexistence tests only)

## Existing coverage retained (cleanup tip)

`scripts/tests/test-stale-cleanup-controls.sh` (restored from tip; 1891 lines) already covers Issues #51–#63 unit/shell behavior: preserve CLOSED/MERGED heads, worktree KEEP, ambiguous remotes, scoped PR evidence, invalid `--repo`, repair_task / cleanup_stale_records repo propagation, wrong implicit context.

Do not weaken or delete those cases when integrating.

## New tests (Lane C proposed)

| Path | Role |
|------|------|
| `scripts/tests/test-cleanup-wp01-lineage-coexistence.sh` | End-to-end coexistence harness (required scenarios below) |
| `tests/security_acceptance/test_cleanup_wp01_coexistence.py` | Unit bridge between WP01 `validate_repository` and cleanup `normalize_caller_repo` / issue matching |

### Scenario matrix (`test-cleanup-wp01-lineage-coexistence.sh`)

| # | Scenario | Pass criteria |
|---|----------|---------------|
| 0 | Presence gate | Cleanup modules + `STALE-CLEANUP-CONTROLS.md` + WP01 `wrong-repo-evidence.json` + `test_repo_scope_evidence.py` + `test-portable-v2-integration.sh` all exist |
| 1 | Mismatched repositories (WP01) | Fixture `applyForbidden` + `validate_repository` → `repository_mismatch` |
| 2 | Open/frozen PR preservation | `export-preserve` retains CLOSED preserve PR `headRefName` in `branches`/`prHeads`; `preserveResolutionOk=true` |
| 3 | Worktree ownership | Attached worktree and/or OPEN PR → `KEEP`; no `DELETED_` |
| 4 | Ambiguous remotes | origin+upstream without `--repo`/env → no `WOULD_DELETE`/`DELETED_` even if fake `gh` would authorize MERGED |
| 5 | Unavailable GitHub evidence | Always-failing `gh` → `preserveResolutionOk=false`, preserve PR unresolved |
| 6 | Mismatched repo authorization | `plan-cleanup-completed --apply` with wrong/empty `--repo` → file unchanged (zero mutation) |
| 7 | Partially merged histories | Moved tip SHA mismatch → KEEP; OPEN wins over historical MERGED → KEEP |
| 8 | Retry / idempotence | Two dry-runs identical decision lines; two failed-auth `--apply` leave branch set unchanged |
| 9 | Import coexistence | `cleanup_controls` + `repair_task` load from same tree without clash |

## Validation command set (post-integrate)

```bash
bash scripts/tests/test-stale-cleanup-controls.sh
bash scripts/tests/test-cleanup-wp01-lineage-coexistence.sh
python3 -m unittest tests.security_acceptance.test_cleanup_wp01_coexistence
bash tests/test-portable-v2-integration.sh
bash scripts/tests/test-gitops-behavioral.sh
```

## Out of scope for these tests

- Live `--apply` against `linktrend/IDE-Development`
- Closing PRs/issues, deleting remote branches, removing operator worktrees
- Consumer repositories
- Credential / App / Bugbot mutation
