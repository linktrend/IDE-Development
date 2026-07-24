# Cursor Automations Setup (Ship / Pull)

**Timezone:** Asia/Taipei  
**Doctrine:** `docs/AUTONOMOUS-GIT-OPERATIONS.md`

Cursor Automations live on the Cursor account/dashboard (not inside the git symlink). Create **four** Automations (or one Automation with four schedules if the product allows). Scope them to the Agents Window workspaces / repos that inherit this system.

## Standing prerequisites

- Mac Mini awake; Cursor **Remote Control** + **Keep Awake** on for long-lived implementers.
- Cloud Bugbot / Fix / Integrator do **not** need desk presence.
- After each run, update Lisa status file when the agent can write local files:
  - Path: `/Users/linktrend/.openclaw-lisa/workspace/memory/pipeline-status.md`
  - One line only, e.g. `Ship A: Clear` or `Pull B: Issues`

## Automation 1 — Ship A (06:00)

**Schedule:** Daily 06:00 Asia/Taipei  

**Prompt:**

```text
Ship A (Asia/Taipei). You are the Implementer under IDE Development autonomous Git ops.

For each in-scope repo in this workspace that has local changes on a work branch (issue/*, dev/*, cursor/*):
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

## Automation 2 — Pull A (08:00)

**Schedule:** Daily 08:00 Asia/Taipei  

**Prompt:**

```text
Pull A (Asia/Taipei). Sync to latest development.

For each in-scope work branch in this workspace:
1) Fetch origin.
2) Merge origin/development into the work branch (unless the repo already mandates rebase).
3) Report blockers briefly in your private notes only.

Write one line to
/Users/linktrend/.openclaw-lisa/workspace/memory/pipeline-status.md
: Pull A: Clear
or Pull A: Issues

Reply with that same one line only.
```

## Automation 3 — Ship B (16:00)

Same as Ship A; replace labels with `Ship B`.

## Automation 4 — Pull B (18:00)

Same as Pull A; replace labels with `Pull B`.

## Fix agent Automation (recommended)

**Trigger:** CI failure or Bugbot request-changes on a PR into `development` (if Cursor supports PR/check triggers); otherwise manual / Lisa escalate.

**Prompt:**

```text
You are the Cloud Fix agent (not the original Implementer).
Checkout the failing PR branch. Fix CI and/or Bugbot findings. Push.
Do not merge. Max 3 fix attempts on this branch historically; if already at 3, stop and leave Issues.
```

## Principal note

Creating these Automations is a dashboard step. After they exist, wired repos inherit agent behavior via `.cursor`; Automations supply the clock.
