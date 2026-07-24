# ADR 0003: Autonomous Ship / Pull / Promote (Inherited via Wire)

**Status:** Accepted (Principal go-ahead 2026-07-24)  
**Date:** 2026-07-24  
**Timezone:** Asia/Taipei (no DST)

## Context

Agents were not consistently committing, pushing, or opening PRs into `development`. Review and merge into `development` lacked a deterministic Reviewer/Integrator path. Git promotion docs still said Principal-only for `staging` and `main`, which blocked an autonomous studio loop. Wiring a consumer to IDE Development only symlinked `.cursor` and did not install GitHub robots or Bugbot expectations.

## Decision

1. **IDE Development is the system SOT** for autonomous Git ops doctrine, managed workflow templates, Bugbot inheritance checklist, and Cursor Automation prompts.
2. **Inheritance is two layers:**
   - **A.** Agent behavior via `repo/.cursor` → IDE Development `.cursor` symlink (`scripts/wire-repo.sh`).
   - **B.** GitHub robots + Bugbot checklist installed/synced from `core/github/managed-workflows/` during wire/backfill (symlink alone is not enough).
3. **IDE Development itself** runs under the same regime.
4. **Roles (deterministic):**
   - **Implementer** — long-lived agents (Remote Control preferred): commit → push → PR → `development`.
   - **Reviewer** — **Bugbot** (Cursor GitHub-side), never the implementer.
   - **Fix agent** — always a short-lived **Cloud** agent on the same branch; max **3** attempts; then stop and surface `Issues`.
   - **Integrator** — merge-only automation into `development` when CI green + Bugbot pass.
   - **Promoter** — GitHub Actions schedules.
   - **Lisa** — Telegram one-line checkpoint status; Principal **Approve** for `staging`→`main` via Telegram.
5. **Calendar (Asia/Taipei):**

   | Event | Time |
   |---|---|
   | Ship A | 06:00 |
   | Pull A | 08:00 |
   | Ship B | 16:00 |
   | Pull B | 18:00 |
   | `development`→`staging` | Tue & Fri 08:00 auto |
   | `staging`→`main` | Mon 08:00 package; Principal Approve ~08:30 via Lisa/Telegram |

6. **Worktrees:** allowed; max **12**; max **20 GB**; delete after merge or abandon.
7. **Module 6 product Release OK / live deploy** remains Principal-gated. This ADR changes **Git branch promotion**, not product deploy authority.

## Alternatives considered

- Keep Principal-only for all promotions — rejected; blocks autonomy.
- Separate Mini Reviewer agent — rejected; Bugbot is independent and already productized.
- Symlink-only inheritance — rejected; does not install Actions/Bugbot.

## Consequences

- Update `.cursor/rules/01-git-branching.mdc` and `docs/AUTONOMOUS-GIT-OPERATIONS.md`.
- Managed workflows sync on wire/backfill; consumer-specific `ci.yml` is never overwritten by sync.
- Intent/PRD wording distinguishes Git promote vs Module 6 Release OK.
- Lisa HEARTBEAT/digest gain one-line pipeline checkpoints (Telegram).

## Validation / rollback

- Validation: wired repos have managed workflow files; doctrine docs resolve; promote crons match table (UTC = Taipei−8h).
- Rollback: restore prior promote YAML schedules; revert branching rule; stop Automations; leave Bugbot as-is.
