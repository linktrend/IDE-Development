# Cursor Automations Setup (Optional Backup — Not Primary Clock)

**Timezone:** Asia/Taipei
**Doctrine:** `docs/AUTONOMOUS-GIT-OPERATIONS.md`
**Status:** Optional / backup only (Principal locked 2026-07-25)

## Primary clock is Lisa Option A

**Do not treat Cursor Automations as the studio Ship/Pull clock.**

| Role | Owner |
|---|---|
| **Primary** | Lisa OpenClaw cron on Mac Mini → Cursor ACP shipper/puller (Option A) |
| **Backup** | These Cursor Automations — only if Lisa ACP is unavailable and Carlos enables them |

Procedures and ACP prompts: openclaw_prime `linkbots/lisa/Personality files/agents/ship-pull-clock.md`.

## When to use this doc

- Lisa gateway / ACP is down and Carlos wants a temporary dashboard clock
- Disaster recovery while Mini is offline

Otherwise skip creating Automations; Lisa owns the schedule (Ship 05, Pull 07, Ship 16, Pull 18 Asia/Taipei).

## Standing prerequisites (backup mode)

- Mac Mini awake; Cursor **Remote Control** + **Keep Awake** on for long-lived implementers.
- Cloud Bugbot / Fix / Integrator do **not** need desk presence.
- After each run, update Lisa status file when the agent can write local files:
  - Path: `/Users/linktrend/.openclaw-lisa/workspace/memory/pipeline-status.md`
  - One line only, e.g. `Ship 05: Clear` or `Pull 18: Issues`

## Automation 1 — Ship 05 — backup only

**Schedule:** Daily 05:00 Asia/Taipei

**Prompt:**

```text
Ship 05 (Asia/Taipei). You are the Implementer under IDE Development autonomous Git ops.
Primary clock is Lisa Option A; you are a backup Automation run.

Process ONE REPO AT A TIME in this exact Ship/Pull order (skip missing paths; not consumer install order — see docs/GITOPS-CONSUMER-ROLLOUT.md):
1) /Users/linktrend/Projects/IDE Development
2) /Users/linktrend/Projects/openclaw_prime
3) /Users/linktrend/Projects/LiNKplatform
4) /Users/linktrend/Projects/LiNKskills
5) /Users/linktrend/Projects/LiNKbrain
6) /Users/linktrend/Projects/LiNKsites
7) /Users/linktrend/Projects/LiNKdeveloper
8) /Users/linktrend/Projects/LiNKlibraries
9) /Users/linktrend/Projects/LiNKautowork
10) /Users/linktrend/Projects/LiNKtrading-codebase

For each repo with local changes or unpushed commits on a work branch (prefer issue/*; also cursor/*, rare dev/*):
1) Commit with conventional commits if there are changes.
2) Push the branch (checkpoint only).
3) Do NOT open a PR. Do NOT request Bugbot. Do NOT mark review-ready unless the issue is actually finished (Packager opens PRs).
4) Do not merge. Do not self-review. Do not touch staging/main.

If you can write local files, set the first line of
/Users/linktrend/.openclaw-lisa/workspace/memory/pipeline-status.md
to exactly: Ship 05: Clear
or Ship 05: Issues
(no lists, no links).

Reply with that same one line only.
```

## Automation 2 — Pull 07 — backup only

**Schedule:** Daily 07:00 Asia/Taipei

**Prompt:**

```text
Pull 07 (Asia/Taipei). Sync to latest development.
Primary clock is Lisa Option A; you are a backup Automation run.

Pull is NOT hard-gated on all PRs being merged; unfinished work rolls forward.

Process ONE REPO AT A TIME in this exact Ship/Pull order (skip missing paths; not consumer install order — see docs/GITOPS-CONSUMER-ROLLOUT.md):
1) /Users/linktrend/Projects/IDE Development
2) /Users/linktrend/Projects/openclaw_prime
3) /Users/linktrend/Projects/LiNKplatform
4) /Users/linktrend/Projects/LiNKskills
5) /Users/linktrend/Projects/LiNKbrain
6) /Users/linktrend/Projects/LiNKsites
7) /Users/linktrend/Projects/LiNKdeveloper
8) /Users/linktrend/Projects/LiNKlibraries
9) /Users/linktrend/Projects/LiNKautowork
10) /Users/linktrend/Projects/LiNKtrading-codebase

For each repo with a checked-out work branch (issue/*, cursor/*, rare dev/*):
1) Fetch origin.
2) Merge origin/development into the work branch (unless the repo already mandates rebase).
3) Report blockers briefly in your private notes only.

Write one line to
/Users/linktrend/.openclaw-lisa/workspace/memory/pipeline-status.md
: Pull 07: Clear
or Pull 07: Issues

Reply with that same one line only.
```

## Automation 3 — Ship 16 — backup only

Same as Ship 05; replace labels with `Ship 16`.

## Automation 4 — Pull 18 — backup only

Same as Pull 07; replace labels with `Pull 18`.

## Repair Automation (backup only — Lisa ACP is primary)

**Primary path:** GitHub records durable repair tasks; **Lisa ACP Repair Dispatcher** dispatches Cursor ACP (see `docs/contracts/REPAIR-DISPATCHER.md`). Max 3 attempts; no prefer-incoming. Immediate failure types do not auto-repair. GitHub never spawns Cursor.

**Backup trigger:** Manual / Lisa escalate only (do not rely on Cursor Automations to spawn Fix agents).

**Prompt (if manually invoked):**

```text
You are a Lisa-dispatched Cursor ACP repair agent (not the original Implementer).
Same branch. Investigate CI/Bugbot/ordinary conflict failure. Fix with minimal diff.
Max 3 attempts total for this failure identity. If still failing, stop and surface Issues.
Do not merge. Do not prefer-incoming. Do not touch staging/main.
```
