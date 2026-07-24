# Autonomous Git Operations

**Status:** Active (Principal go-ahead 2026-07-24)  
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
| Reviewer | **Bugbot** | Review every PR into `development` |
| Fix agent | Short-lived **Cloud** agent on same branch | Repair CI/Bugbot failures; max **3** attempts |
| Integrator | GitHub Action (`linktrend-integrator-merge.yml`) | Merge into `development` when CI green + Bugbot pass |
| Promoter | GitHub Actions schedules | Tue/Fri staging; Mon main package |
| Lisa | OpenClaw / Telegram | One-line checkpoint status; ask Principal to Approve main |
| Principal | Carlos | Approve `staging`→`main` (~Mon 08:30); intervene on `Issues` |

## Calendar (Asia/Taipei)

| Event | Local time | UTC cron (no DST) | Behavior |
|---|---|---|---|
| Ship A | 06:00 | Cursor Automation | Poke implementers: commit, push, open/update PR → `development` |
| Pull A | 08:00 | Cursor Automation | All agents pull latest `development` |
| Ship B | 16:00 | Cursor Automation | Same as Ship A |
| Pull B | 18:00 | Cursor Automation | Same as Pull A |
| Staging promote | Tue & Fri 08:00 | `0 0 * * 2,5` | Auto `development`→`staging`; Fix agent if red, then retry |
| Main package | Mon 08:00 | `0 0 * * 1` | Package only; do **not** merge yet |
| Main Approve | Mon ~08:30 | Lisa Telegram | Principal says Approve → dispatch merge |

## Lisa one-line statuses (Telegram)

After each checkpoint, heartbeat/digest may include **only** lines like:

- `Ship A: Clear` / `Ship A: Issues`
- `Pull A: Clear` / `Pull A: Issues`
- `Ship B: Clear` / `Ship B: Issues`
- `Pull B: Clear` / `Pull B: Issues`
- `Staging promote (Tue): Clear` / `Staging promote (Fri): Issues`
- `Main ready (Mon): Clear` / `Main ready (Mon): Issues`

No lists or links in those lines. Detail stays in `memory/pipeline-status.md` (Lisa workspace) for when Carlos asks.

## Implementer checklist (every session + Ship waves)

1. Prefer Remote Control for long-lived agents; Mini awake + Keep Awake.
2. Start from latest `development` (Pull waves enforce sync).
3. Work on `issue/*`, `dev/<machine><ide>`, or `cursor/*`.
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
- Managed workflows: `core/github/managed-workflows/`
- Wire/sync: `scripts/wire-repo.sh`, `scripts/sync-managed-workflows.sh`
- Bugbot checklist: `core/checklists/BUGBOT-INHERITANCE.md`
- Cursor Automations setup: `docs/CURSOR-AUTOMATIONS-SETUP.md`
- Lisa procedure: openclaw_prime `linkbots/lisa/Personality files/agents/pipeline-status.md`
