# Project Bootstrap

This document defines how a fresh repository adopts the `.cursor` system and reaches a minimum usable state.

## Purpose

Make a new repository executable under the canonical operating model without requiring scripts or hidden setup.

## Adoption Sequence

1. confirm `.cursor/` is the local source of truth for the repository
2. read `.cursor/README.md`
3. read `.cursor/execution/INDEX.yaml`
4. read `.cursor/templates/INDEX.yaml`
5. determine whether work begins with intent or with an existing approved objective
6. create or confirm the minimum required artifacts
7. choose the correct preferred command wrapper

## Minimum Required Artifacts

For a new project:

- `INTENT.md` if the objective still needs go or no-go validation
- `PROGRAM.md` once intent is accepted or explicitly overridden
- at least one `MODULE.md` for executable work

For a module-ready repository:

- `MODULE.md`
- `PHASE.md`
- `ISSUE.md`

## Minimum Viable System

A new repository can start safely when it has:

- `.cursor/README.md`
- execution doctrine
- canonical templates
- preferred commands
- at least one artifact path describing real work

## Startup Responsibilities

- establish repository scope and objective
- decide whether program creation is valid yet
- avoid creating modules before objective boundaries are clear
- preserve progressive disclosure by reading only the nearest artifacts

## Shutdown Responsibilities

Before stopping project bootstrap work:

- record whether the repository is intent-ready, program-ready, or module-ready
- leave the next required artifact obvious
- record blockers instead of leaving partial structure unexplained

## Runtime-Specific Startup Flows

### Human

- inspect the repository objective
- decide whether to start with intent or program structure
- create only the minimum needed artifacts

### Cursor

- read `.cursor/README.md`, then the command index
- route into `plan-program` or `plan-module`
- create the minimum artifact set required by the chosen command

### Codex

- follow the same startup path as Cursor
- keep the read set small
- stop once the repository reaches a clear executable boundary

### Claude

- follow the same artifact and doctrine sequence
- avoid introducing alternate bootstrap semantics

## Handoff Rule

Project bootstrap is complete when the next operator can identify:

- what the repository is trying to accomplish
- which artifact level is active
- which command should be used next
