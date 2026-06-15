# Start Here

This is the canonical first read for a fresh repository session or a fresh AI session.

## Purpose

Reach a safe operational starting point without scanning the entire `.cursor` system.

## Minimum Read Order

1. `.cursor/README.md`
2. `.cursor/execution/INDEX.yaml`
3. `.cursor/templates/INDEX.yaml`
4. `.cursor/commands/INDEX.yaml`
5. the single bootstrap document that matches the task:
   - `PROJECT-BOOTSTRAP.md`
   - `MODULE-BOOTSTRAP.md`
   - `ISSUE-BOOTSTRAP.md`
   - `SESSION-STARTUP.md`

## Decision Path

- if the repository is new or not yet structured, read `PROJECT-BOOTSTRAP.md`
- if the user is defining a new module, read `MODULE-BOOTSTRAP.md`
- if the user is executing one atomic work unit, read `ISSUE-BOOTSTRAP.md`
- if the repository already contains active artifacts and work is resuming, read `SESSION-STARTUP.md`

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
