# IDE Development — Current status

**Audience:** Principal and operators who need the truth without reading historical build logs.
**Date:** 2026-09-29
**Package:** **v3.0.0** (Wave 1 in progress; identity in `VERSION` is updated by its own issue)
**Platforms:** Cursor and native Codex. Claude Code is excluded.

This page is the concise current-status surface for v3.

---

## One-line verdict

**v3 Wave 0 is done. Wave 1 is in progress.** IDE Development is the shared development operating System: one orchestrator per repo, workers on short-lived issue branches, `development` and `main` only.

---

## Wave 0 (done)

Proven on the IDE-Development pilot (2026-09-29):

| Piece | Where to read it |
|---|---|
| Environment recipe | [`runbooks/project-setup-checklist.md`](./runbooks/project-setup-checklist.md) (Part B1) and `scripts/setup.sh` |
| cursor-002 dispatch | Same checklist, Part B3; client `scripts/dispatch/cursor002.py` |
| Codex on the orchestrator VM | Same checklist, Part B4; [`../../scripts/codex/README.md`](../scripts/codex/README.md) |
| Ledger design | [`../core/ledger/README.md`](../core/ledger/README.md) — Supabase schema `ide_ledger` in the LiNKplatform project; orchestrator writes via RPC only. Until it is live, the pilot run log stays in the Project store |
| Watchdog and run log | [`runbooks/watchdog-and-runlog.md`](./runbooks/watchdog-and-runlog.md) |
| Phase Issue convention | [`runbooks/phase-issue-convention.md`](./runbooks/phase-issue-convention.md) — one GitHub Issue per Phase; work IDs `IDE-<n>` |
| Project setup checklist | [`runbooks/project-setup-checklist.md`](./runbooks/project-setup-checklist.md) |

---

## Wave 1 (in progress)

Documentation, repo identity, and the rest of the v3 operating cutover. This page, the operations manual, and the README describe the v3 model. Later Wave 1 issues own version identity, manifests, and the scripts that still implement the previous flow.

---

## How v3 runs

- **One orchestrator per repo.** A Cursor Project on the cursor-001 account, frontier model. It plans Phases and Issues, dispatches workers, packages branches into pull requests into `development`, merges on green CI plus one independent review, and promotes `development` to `main`. Cheap helper subagents do routine jobs.
- **Workers.** Codex CLI on the orchestrator VM (Luna High everyday, Sol Medium hard; used while more than 25% of the allowance remains in every reported window) and cursor-002 via API (Grok 4.7 Medium everyday, Opus 5.5 Medium hard). Branches are `issue/<PREFIX>-<n>-<slug>`. Workers commit and push often and never open pull requests.
- **Checks.** Fast checks on the branch, one Full CI run per pull request, one exact-head review by a different model family (Bugbot optional).
- **Repair ladder.** Luna/Grok three times, then Sol/Opus once, then — if the work started on Sol/Opus — the other hard route once, then flag Carlos.
- **Branches.** `development` and `main` only. Deploys after `main` are automatic GitHub Actions jobs owned as a standard by the LiNKops repo, with a health check and rollback.
- **Carlos.** Gives intent and answers questions. He does not approve merges or releases.

---

## Boundaries that remain true

| Boundary | Rule |
|---|---|
| System vs consumer | This repository is the system source and self-verification target. It must not receive a nested install of `.ide-development/`. Other repos receive the managed core under `.ide-development/` |
| LiNKdeveloper | A separate Program and repository: the autonomous application factory. It is not this System |
| Claude | Excluded from current support |
| Ledger writes | Orchestrator only, via RPC, once `ide_ledger` is live |

---

## Start here next

1. This page
2. [`runbooks/project-setup-checklist.md`](./runbooks/project-setup-checklist.md)
3. [`IDE-DEVELOPMENT-OPERATIONS-MANUAL.md`](./IDE-DEVELOPMENT-OPERATIONS-MANUAL.md)
4. [`../README.md`](../README.md)
