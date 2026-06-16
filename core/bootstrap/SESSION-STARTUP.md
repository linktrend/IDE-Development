# Session Startup

This document defines the canonical responsibilities at the beginning of a working session.

## Purpose

Allow a human or AI runtime to resume or begin work with minimum context, explicit scope, and safe state awareness.

Natural-language triggers that should route here through `.cursor/session/` include:

- `Let's continue.`
- `Continue development.`
- `Pick up where we left off.`
- `Resume work.`

## Session Startup Sequence

1. read `.cursor/README.md`
2. determine the active repository from the files visible to the current chat
3. if no active repository is clearly visible, stop and ask which repository is intended
4. run `git pull`
5. read `.cursor/session/INDEX.yaml`
6. read the latest handoff report under `docs/handoff/YYYY-MM-DD.md`
7. reconstruct completed work, remaining work, blockers, and recommended next action
8. determine whether the active work is discovery, intent, program, module, or issue level
9. if the work is greenfield or materially ambiguous, read `.cursor/discovery/INDEX.yaml`
10. read the nearest bootstrap document for the active level
11. read the relevant command wrapper
12. read only the doctrine, state, workflow, and template files required by that command
13. inspect the active artifact tree
14. identify the next executable or decision-ready unit

## Minimum Session Inputs

- repository objective or active artifact path
- current work level
- current state of the active artifact
- known blockers, if any
- latest handoff report, if present

## Startup Responsibilities

- confirm what is already in progress
- verify the repository is current before resuming
- use the latest handoff report rather than hidden memory when available
- decide whether the session needs discovery before intent
- avoid re-planning already-planned work unless artifacts are inadequate
- compute readiness from artifacts rather than memory
- keep context loading narrow

Default session paths:

- greenfield or ambiguous: `DISCOVERY -> INTERVIEW -> INTENT`
- routine planning: `INTENT -> PROGRAM/MODULE`
- bugfix or atomic work: `ISSUE`

## Runtime-Specific Startup Flows

### Human

- read the current artifact tree
- identify the next real decision or executable unit

### Cursor

- read the entrypoint documents
- route into the preferred command surface
- load only the files required by that command

### Codex

- do the same as Cursor
- verify repository state before editing or claiming progress
- present the recommended next action before continuing

### Claude

- do the same as other AI runtimes
- keep reasoning anchored to the artifact tree

## Stop Conditions

Do not start execution until:

- the active repository is known
- the active artifact is known
- the next command is known
- the state of the active work unit is known
- the next unit is either `ready` or explicitly `blocked`
