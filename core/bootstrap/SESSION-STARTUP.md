# Session Startup

This document defines the canonical responsibilities at the beginning of a working session.

## Purpose

Allow a human or AI runtime to resume or begin work with minimum context, explicit scope, and safe state awareness.

## Session Startup Sequence

1. read `.cursor/README.md`
2. determine whether the active work is discovery, intent, program, module, or issue level
3. if the work is greenfield or materially ambiguous, read `.cursor/discovery/INDEX.yaml`
4. read the nearest bootstrap document for the active level
5. read the relevant command wrapper
6. read only the doctrine, state, workflow, and template files required by that command
7. inspect the active artifact tree
8. identify the next executable or decision-ready unit

## Minimum Session Inputs

- repository objective or active artifact path
- current work level
- current state of the active artifact
- known blockers, if any

## Startup Responsibilities

- confirm what is already in progress
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

### Claude

- do the same as other AI runtimes
- keep reasoning anchored to the artifact tree

## Stop Conditions

Do not start execution until:

- the active artifact is known
- the next command is known
- the state of the active work unit is known
- the next unit is either `ready` or explicitly `blocked`
