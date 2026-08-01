# Lisa Local Cleanup Handoff

**Status:** Contract (IDE-owned) — Lisa implements later in openclaw_prime
**Date:** 2026-07-30

## Purpose

GitHub Actions may delete **remote** merged/abandoned branches (`linktrend-cleanup-merged.yml`).
**Local** worktree / branch cleanup on the Mac Mini remains Lisa’s responsibility and must not run inside GitHub.

## GitHub must never

- Delete operator local worktrees
- Run `git worktree remove` against Mini paths
- Assume a checkout path on the operator machine

## Lisa local cleanup (future)

When implemented in openclaw_prime, Lisa should:

1. Read remote cleanup outcomes / branch list from GitHub (or re-run dry-run logic via `gh`).
2. On Mini only: remove matching local branches/worktrees that are safe (merged/abandoned evidence).
3. Preserve active agent checkouts and dirty worktrees.
4. Report one-line Clear/Issues.

## Related

- `docs/contracts/STALE-CLEANUP-CONTROLS.md` — preserve list, open-PR (no auto-close), exact-tip apply gates, and **keep active worktrees**
- `scripts/cleanup-merged-branches.sh` (`--remote` for Actions; `--local` only on operator machines)
- `docs/contracts/REPAIR-DISPATCHER.md`
- `docs/contracts/LISA-OPENCLAW-FOLLOW-UP.md`
