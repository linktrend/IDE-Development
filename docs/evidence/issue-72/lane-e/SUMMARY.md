# Lane E SUMMARY — Issue #72 GitHub hygiene (PLAN ONLY)

**Verdict:** Post-WP03 inventory refreshed. Trees equal at `43b1333`. Seven remote WOULD_DELETE candidates (5 prior + 2 new promote leftovers). **No apply.** Awaits Codex verify + Principal.

**Evidence dir:** `docs/evidence/issue-72/lane-e/`
**Files:** `disposition.json`, `DISPOSITION.md`, `commands-and-results.md`, `SUMMARY.md`
**Prior plan (archived):** `docs/archive/evidence/wp02/lane-c/cleanup-plan-post-wp03.md`

## Counts by class

| Class | Approx count | Notes |
|-------|-------------:|-------|
| **DO-NOT-TOUCH** | 10+ | PR **#36/#37/#49**; permanent branches; stash@{0}; issue #23/#28; main checkout |
| **KEEP-ACTIVE** | 2 | Issue **#72** branch + worktree (local only) |
| **KEEP-FROZEN** | 6+ | PR #49 head / issues 43/44/51 / related WTs / repairs #50/#46 |
| **KEEP-OPEN** | 20+ | Open-PR heads, WP01 WTs, issue/63+/68 WTs blocking delete |
| **SUPERSEDED** | 10+ | PRs #52/#54/#56/#58/#60/#62 + merged #69/#70/#71; issue #68 content |
| **WOULD_DELETE-CANDIDATE** | 7 remote + 4 local-only | See high-risk below |
| **DEFER** | 6+ | #65; cleanup-orchestrator; ship05 mismatch; pull-wave-test; codex/cursor/dev |

## DO-NOT-TOUCH callouts

- **PR #36, #37, #49** — never close/alter in automated cleanup
- **Issue #72 branch** `issue/72-pre-launch-ide-development-codebase-cleanup-arch` + its worktree — active work; keep
- **`stash@{0}`** — must not be modified (drop/apply/clear forbidden)
- **`main` / `staging` / `development`** — protected

## High-risk items

1. Closing superseded PRs (#52–#62) without Codex ledger proof
2. Remote delete while caller checkout dirty (dry-run already EXIT 1)
3. Removing issue/68 or issue/63 worktrees without Principal/Lisa handoff
4. Touching prunable issue-23 WT while PR #36 open
5. Any stash operation on `stash@{0}`

## Apply blockers (always)

1. **Awaits Codex verify + Principal authorization**
2. Every object has `applyAuthorized: false`
3. Re-run remote dry-run to EXIT 0 from a **clean** checkout before `--apply`
4. Tip SHA match + no OPEN PR + no attached worktree + preserveResolutionOk for each delete

## Changed after WP03 integration

- #69/#70/#71 merged; trees equal `43b1333`
- New promote leftovers: `promote/main/8ac0afdc55fe`, `promote/staging/e6301fc920a4`
- issue/68 content merged; WT remains → not yet remote-deletable
- Issue #72 KEEP-ACTIVE added
- Prior plan moved under `docs/archive/evidence/wp02/lane-c/`
