# Autonomous Git Operations

**Status:** Active (Principal go-ahead 2026-07-24; Option A clock locked 2026-07-25)  
**ADR:** `docs/adr/0003-autonomous-ship-pull-promote.md`  
**Timezone:** Asia/Taipei  
**SOT home:** This repo (IDE Development). Wired consumers inherit Layer A (`.cursor`) and Layer B (managed GitHub workflows + Bugbot checklist).

## Two-layer inheritance

| Layer | What | How |
|---|---|---|
| **A. Agent behavior** | Rules, skills, ship/pull checklists | `./scripts/wire-repo.sh` → `repo/.cursor` symlink |
| **B. Robots** | Managed `.github/workflows/*` + Bugbot enablement checklist | Same wire script syncs from `core/github/managed-workflows/`; does **not** overwrite consumer `ci.yml` |

IDE Development itself uses the same managed workflows (it is in scope).

## Roles

| Role | Who | Job |
|---|---|---|
| Implementer | Long-lived local / Remote Control / Cloud agents | Branch → commit → push → PR → `development` |
| Reviewer | **Bugbot** | Review every PR into `development` (pass = GitHub check `Cursor Bugbot` → `success`) |
| Fix agent | Short-lived **Cloud** agent on same branch | Repair CI/Bugbot failures; max **3** attempts |
| Integrator | GitHub Action (`linktrend-integrator-merge.yml`) | Merge into `development` when CI green + `Cursor Bugbot` success (not GitHub APPROVE) |
| Promoter | GitHub Actions schedules | Tue/Fri staging; Mon main package |
| Lisa | OpenClaw / Telegram (**primary Ship/Pull clock**) | Cron → spawn Cursor ACP shipper/puller on Mini; one-line checkpoint status; ask Principal to Approve main |
| Principal | Carlos | Approve `staging`→`main` (Mon 08:30 via digest; reply on Telegram); intervene on `Issues` |

## Primary clock — Lisa Option A (locked)

**Lisa is the Ship/Pull clock.** She runs OpenClaw cron on the Mac Mini and spawns Cursor ACP agents (shipper / puller). Cursor Automations are **not** the primary clock (optional backup only — see `docs/CURSOR-AUTOMATIONS-SETUP.md`).

| Event | Local time | Who fires | Behavior |
|---|---|---|---|
| Ship 05 | 05:00 | Lisa cron → Cursor ACP shipper | One repo at a time (sequential): commit work branch → push → open/update PR → `development` → **STOP** (no merge / no self-review) |
| Pull 07 | 07:00 | Lisa cron → Cursor ACP puller | Merge latest `origin/development` into work branches on disk; **not** hard-gated on all PRs merged; unfinished work rolls forward |
| Ship 16 | 16:00 | Lisa cron → Cursor ACP shipper | Same as Ship 05 |
| Pull 18 | 18:00 | Lisa cron → Cursor ACP puller | Same as Pull 07 |
| Staging promote | Tue & Fri 08:00 | GitHub Promoter (`0 0 * * 2,5` UTC) | Auto `development`→`staging`; Fix agent if red, then retry |
| Main package | Mon 08:00 | GitHub Promoter (`0 0 * * 1` UTC) | Package only; do **not** merge yet |
| Morning digest | 08:30 | Lisa cron | Email + Telegram day-ahead; Pipeline lines; Mon Main Approve ask when Clear |
| Main Approve | Mon 08:30 | Lisa digest (Telegram reply) | Principal says Approve on Telegram → dispatch merge |

**Runtime prerequisite (human/ops):** Mini must be awake (Keep Awake / Remote Control) so Lisa ACP can spawn. Documented in openclaw_prime Lisa ship/pull clock procedure.

**Repo order (sequential — Principal-locked 2026-07-25):** process exactly one repo at a time, in this order (skip missing paths):

1. IDE Development  
2. openclaw_prime  
3. LiNKplatform  
4. LiNKskills  
5. LiNKbrain  
6. LiNKsites  
7. LiNKdeveloper  
8. LiNKlibraries  
9. LiNKautowork  

ACP prompts and absolute paths: openclaw_prime `linkbots/lisa/Personality files/agents/ship-pull-clock.md`.

## Studio branching default (locked)

- Prefer short-lived **`issue/<id>-slug`** per governed work (not forever `dev/*` home).
- `cursor/*` for cloud/dashboard agents.
- `dev/<machine><ide>` rare ad-hoc only.
- Bootstrap: `/agentsetup`. Already-open migration: `/agentcomply`.
- **Implementer vs Orchestrator:** `/agentsetup` and `/agentcomply` are for **Implementers** that own work in **one repo**. A workspace **Orchestrator** must not be forced onto a random/stolen `issue/*` as “session home.” Orchestrators coordinate (and may spawn/direct per-repo Implementers); they do not get a forever home issue branch. Accidental dirty edits in a repo → hand off to that repo’s Implementer + `/agentcomply` there, or open a correctly named issue for that specific change. Multi-root ambiguity → ask which repo. Do not silently adopt an unrelated open PR branch.
- **Branch rule (any agent):** no code/repo touch → no branch required. The moment any agent touches a repo, run `/agentsetup` or `/agentcomply` for **that** repo and use `issue/<id>-slug` for the work package.

## Lisa one-line statuses (Telegram + Ship/Pull email)

Clock labels use **local hour** (Asia/Taipei), not A/B letters. After each Ship/Pull wave, Lisa announces **and emails** the one line (Clear or Issues). Heartbeat/digest may also include **only** lines like:

- `Ship 05: Clear` / `Ship 05: Issues`
- `Pull 07: Clear` / `Pull 07: Issues`
- `Ship 16: Clear` / `Ship 16: Issues`
- `Pull 18: Clear` / `Pull 18: Issues`
- `Staging promote (Tue): Clear` / `Staging promote (Fri): Issues`
- `Main ready (Mon): Clear` / `Main ready (Mon): Issues`

No lists or links in those lines. Detail stays in `memory/pipeline-status.md` (Lisa workspace) for when Carlos asks.

## Implementer checklist (every session + Ship waves)

1. Prefer Remote Control for long-lived agents; Mini awake + Keep Awake (required for Lisa ACP clock).
2. Start from latest `development` (Pull waves enforce sync).
3. Work on **`issue/*`** by default (`dev/*` or `cursor/*` only when appropriate).
4. Commit with conventional commits; push often.
5. Open or update PR → `development`.
6. Do **not** self-merge; do **not** promote to `staging`/`main`.
7. Do **not** review your own PR (Bugbot is Reviewer).

## Fix path

On CI red or Bugbot fail: spawn Cloud Fix agent on that branch (not “send back to original implementer”). After 3 failed attempts: stop; Lisa one-liner `Issues`; no force-merge.

## Worktrees

Allowed. Caps: **12** worktrees, **20 GB** total Cursor-managed. Delete after merge or abandon.

## Module 6 vs Git promote

- **Git promote** (`development`→`staging`→`main`): this document + ADR 0003.
- **Product live deploy / Module 6 Release OK:** still Principal-gated; unchanged by this system.

## Related paths

- Rules: `.cursor/rules/01-git-branching.mdc`, `.cursor/rules/02-autonomous-ship-pull.mdc`
- Skills/commands: `/agentsetup`, `/agentcomply`
- Managed workflows: `core/github/managed-workflows/`
- Wire/sync: `scripts/wire-repo.sh`, `scripts/sync-managed-workflows.sh`
- Bugbot checklist: `core/checklists/BUGBOT-INHERITANCE.md`
- Cursor Automations (optional backup): `docs/CURSOR-AUTOMATIONS-SETUP.md`
- Lisa Option A clock: openclaw_prime `linkbots/lisa/Personality files/agents/ship-pull-clock.md`
