# Start Here

This is the canonical first read for a fresh repository session or a fresh AI session.

## Purpose

Reach a safe operational starting point without scanning the entire `.cursor` system.

## Minimum Read Order

1. `.cursor/README.md`
2. this file
3. `.cursor/commands/INDEX.yaml`
4. if the work is greenfield or materially ambiguous, read `.cursor/discovery/INDEX.yaml`
5. only the bootstrap document that matches the task:
   - `PROJECT-BOOTSTRAP.md`
   - `MODULE-BOOTSTRAP.md`
   - `ISSUE-BOOTSTRAP.md`
   - `SESSION-STARTUP.md`
6. if the task is a natural-language resume or close-out request, also read `.cursor/session/INDEX.yaml`
7. if the task is a natural-language workspace adoption request, also read `.cursor/workspace/INDEX.yaml`
8. only then read the doctrine and template indexes required by that task

Do not begin by scanning the deeper execution layers. Use the bootstrap decision path first.

## Decision Path

- if the repository is new or not yet structured, read `PROJECT-BOOTSTRAP.md`
- if the user is defining a new module, read `MODULE-BOOTSTRAP.md`
- if the user is executing one atomic work unit, read `ISSUE-BOOTSTRAP.md`
- if the repository already contains active artifacts and work is resuming, read `SESSION-STARTUP.md`
- if the user says `Let's continue`, `Resume work`, `That's it for today`, or equivalent, read `.cursor/session/INDEX.yaml`
- if the user says `Install the system into this workspace`, `Adopt this workspace`, or `Wire this workspace`, read `.cursor/workspace/INDEX.yaml`

After choosing the task path:

- use `commands/INDEX.yaml` to select the preferred command wrapper
- then read only the doctrine, templates, workflows, state, and contracts required by that command

Discovery path selection:

- greenfield or ambiguous work: `DISCOVERY -> INTERVIEW -> INTENT`
- routine new work: `INTENT`
- tiny low-risk bug or simple bounded change: `SMALL-CHANGE -> PROOF -> REVIEW -> INTEGRATION`
- bugfix or atomic work: `ISSUE`

## Minimum Required System

The minimum viable `.cursor` working surface is:

- `.cursor/README.md`
- `.cursor/execution/`
- `.cursor/templates/`
- `.cursor/commands/`

Everything else improves guidance, specialization, or governance, but these are the minimum startup surfaces.

## Bootstrap Responsibilities

- determine whether the work begins at intent, program, module, or issue level
- load only the doctrine and templates required for that level
- choose the correct preferred command wrapper
- preserve issue atomicity and proof discipline
- avoid treating agents as the control structure
- delay deeper layer reading until the task path is clear
- do not start discovery unless ambiguity is real

## Fresh Runtime Notes

- Human: choose the task level, then follow the nearest bootstrap path
- Cursor: read the minimum path above and route into the preferred command layer
- Codex: read the minimum path above and avoid scanning unrelated directories
- Claude: use the same artifact and command path; do not invent alternate runtime semantics

## Stop Conditions

Do not proceed into execution until:

- the task level is clear
- the required artifact type is known
- the command entrypoint is known
- the minimum required artifacts exist or are ready to be created
