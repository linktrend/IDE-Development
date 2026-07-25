# ADR 0003: Autonomous Ship / Pull / Promote (Inherited via Wire)

**Status:** Accepted (Principal go-ahead 2026-07-24)  
**Date:** 2026-07-24  
**Timezone:** Asia/Taipei (no DST)

## Context

Agents were not consistently committing, pushing, or opening PRs into `development`. Review and merge into `development` lacked a deterministic Reviewer/Integrator path. Git promotion docs still said Principal-only for `staging` and `main`, which blocked an autonomous studio loop. Wiring a consumer to IDE Development only symlinked `.cursor` and did not install GitHub robots or Bugbot expectations.

## Decision

1. **IDE Development is the system SOT** for autonomous Git ops doctrine, managed workflow templates, Bugbot inheritance checklist, and Ship/Pull clock doctrine.
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
   - **Lisa** — **primary Ship/Pull clock** (Option A): cron on Mini spawns Cursor ACP shipper/puller; Telegram one-line checkpoint status; Principal **Approve** for `staging`→`main` via Telegram.
5. **Calendar (Asia/Taipei)** — wave names are **clock times** (not A/B letters):

   | Event | Time |
   |---|---|
   | Ship 05 | 05:00 |
   | Pull 07 | 07:00 |
   | Ship 16 | 16:00 |
   | Pull 18 | 18:00 |
   | `development`→`staging` | Tue & Fri 08:00 auto |
   | `staging`→`main` | Mon 08:00 package; Principal Approve 08:30 via Lisa morning digest (Telegram reply) |

6. **Worktrees:** allowed; max **12**; max **20 GB**; delete after merge or abandon.
7. **Module 6 product Release OK / live deploy** remains Principal-gated. This ADR changes **Git branch promotion**, not product deploy authority.
8. **Studio branching default:** short-lived `issue/<id>-slug` per governed work (`/agentsetup`, `/agentcomply`); not forever `dev/*` home.

## Alternatives considered

- Keep Principal-only for all promotions — rejected; blocks autonomy.
- Separate Mini Reviewer agent — rejected; Bugbot is independent and already productized.
- Symlink-only inheritance — rejected; does not install Actions/Bugbot.
- Cursor Automations as primary Ship/Pull clock (Option B) — rejected 2026-07-25; Lisa Option A is primary; Automations optional backup only.

## Consequences

- Update `.cursor/rules/01-git-branching.mdc` and `docs/AUTONOMOUS-GIT-OPERATIONS.md`.
- Managed workflows sync on wire/backfill; consumer-specific `ci.yml` is never overwritten by sync.
- Intent/PRD wording distinguishes Git promote vs Module 6 Release OK.
- Lisa HEARTBEAT/digest gain one-line pipeline checkpoints (Telegram).
- Lisa owns Ship/Pull cron + ACP prompts in openclaw_prime; `docs/CURSOR-AUTOMATIONS-SETUP.md` reframed as backup.

## Validation / rollback

- Validation: wired repos have managed workflow files; doctrine docs resolve; promote crons match table (UTC = Taipei−8h); Lisa ship/pull cron jobs exist on Mini when awake.
- Rollback: restore prior promote YAML schedules; revert branching rule; disable Lisa ship/pull crons; leave Bugbot as-is.

---

## Amendment — 2026-07-25 (Principal locked)

**Option A:** Lisa is the Ship/Pull clock (OpenClaw cron → Cursor ACP shipper/puller on Mini). Forget Option B / Cursor Automations as primary clock.

Clarifications locked the same day:

- Times (Asia/Taipei): Ship 05 / Pull 07 / Ship 16 / Pull 18 (hour labels; morning pair advanced 2026-07-25 so 08:30 digest covers all four daily waves).
- Ship: commit → push → open/update PR → `development` → STOP (no merge/self-review).
- Pull: merge latest `origin/development` into work branches on disk; not hard-gated on all PRs merged; unfinished rolls forward.
- One repo at a time (sequential).
- Studio default: short-lived `issue/<id>-slug` (not forever `dev/*`).
- `/agentsetup` / `/agentcomply` are for **Implementers** (one repo); workspace **Orchestrators** do not get a forever session-home issue branch.
- Bugbot already ON — no human Bugbot enablement work in this amendment.
- Mini must be awake for Lisa ACP at runtime (ops prerequisite; not a code secret).

---

## Amendment — 2026-07-25 (digest 08:30 + morning Ship/Pull)

Principal locked:

- Morning digest moves **06:45 → 08:30**; email includes Pipeline (D) + Monday Main Approve when Clear; Telegram keeps Battery (C) + same Approve.
- Heartbeat at **06:45**; **no 08:45** heartbeat (digest owns that Review #1 slot).
- Morning Ship **05:00**, Pull **07:00** (evening 16/18 unchanged).
- After each Ship/Pull wave: Telegram one-liner **and** email one-liner (Clear or Issues).
- Overnight local coding **19:00–04:00** (was 19:00–07:00) so coding stops before Ship 05.
