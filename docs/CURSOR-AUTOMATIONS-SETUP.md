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

Otherwise skip creating Automations; Lisa owns the schedule (Ship A 06:00, Pull A 08:00, Ship B 16:00, Pull B 18:00 Asia/Taipei).

## Standing prerequisites (backup mode)

- Mac Mini awake; Cursor **Remote Control** + **Keep Awake** on for long-lived implementers.
- Cloud Bugbot / Fix / Integrator do **not** need desk presence.
- After each run, update Lisa status file when the agent can write local files:
  - Path: `/Users/linktrend/.openclaw-lisa/workspace/memory/pipeline-status.md`
  - One line only, e.g. `Ship A: Clear` or `Pull B: Issues`

## Automation 1 — Ship A (06:00) — backup only

**Schedule:** Daily 06:00 Asia/Taipei  

**Prompt:**

```text
Ship A (Asia/Taipei). You are the Implementer under IDE Development autonomous Git ops.
Primary clock is Lisa Option A; you are a backup Automation run.

Process ONE REPO AT A TIME in this exact order (skip missing paths):
1) /Users/linktrend/Projects/IDE Development
2) /Users/linktrend/Projects/openclaw_prime
3) /Users/linktrend/Projects/LiNKplatform
4) /Users/linktrend/Projects/LiNKskills
5) /Users/linktrend/Projects/LiNKbrain
6) /Users/linktrend/Projects/LiNKsites
7) /Users/linktrend/Projects/LiNKdeveloper
8) /Users/linktrend/Projects/LiNKlibraries
9) /Users/linktrend/Projects/LiNKautowork

For each repo with local changes or unpushed commits on a work branch (prefer issue/*; also cursor/*, rare dev/*):
1) Commit with conventional commits if there are changes.
2) Push the branch.
3) Open or update a PR targeting development.
4) Do not merge. Do not self-review. Do not touch staging/main.

If you can write local files, set the first line of
/Users/linktrend/.openclaw-lisa/workspace/memory/pipeline-status.md
to exactly: Ship A: Clear
or Ship A: Issues
(no lists, no links).

Reply with that same one line only.
```

## Automation 2 — Pull A (08:00) — backup only

**Schedule:** Daily 08:00 Asia/Taipei  

**Prompt:**

```text
Pull A (Asia/Taipei). Sync to latest development.
Primary clock is Lisa Option A; you are a backup Automation run.

Pull is NOT hard-gated on all PRs being merged; unfinished work rolls forward.

Process ONE REPO AT A TIME in this exact order (skip missing paths):
1) /Users/linktrend/Projects/IDE Development
2) /Users/linktrend/Projects/openclaw_prime
3) /Users/linktrend/Projects/LiNKplatform
4) /Users/linktrend/Projects/LiNKskills
5) /Users/linktrend/Projects/LiNKbrain
6) /Users/linktrend/Projects/LiNKsites
7) /Users/linktrend/Projects/LiNKdeveloper
8) /Users/linktrend/Projects/LiNKlibraries
9) /Users/linktrend/Projects/LiNKautowork

For each repo with a checked-out work branch (issue/*, cursor/*, rare dev/*):
1) Fetch origin.
2) Merge origin/development into the work branch (unless the repo already mandates rebase).
3) Report blockers briefly in your private notes only.

Write one line to
/Users/linktrend/.openclaw-lisa/workspace/memory/pipeline-status.md
: Pull A: Clear
or Pull A: Issues

Reply with that same one line only.
```

## Automation 3 — Ship B (16:00) — backup only

Same as Ship A; replace labels with `Ship B`.

## Automation 4 — Pull B (18:00) — backup only

Same as Pull A; replace labels with `Pull B`.

## Fix agent Automation (recommended either way)

**Trigger:** CI failure or Bugbot request-changes on a PR into `development` (if Cursor supports PR/check triggers); otherwise manual / Lisa escalate.

**Prompt:**

```text
You are the Cloud Fix agent (not the original Implementer).
Checkout the failing PR branch. Fix CI and/or Bugbot findings. Push.
Do not merge. Max 3 fix attempts on this branch historically; if already at 3, stop and leave Issues.
```

## Principal note

Creating these Automations is a dashboard step and is **optional**. Wired repos inherit agent behavior via `.cursor`; **Lisa Option A supplies the primary clock**.
