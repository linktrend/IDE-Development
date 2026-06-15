# Module Bootstrap

This document defines how a new module starts and becomes ready for autonomous execution.

## Purpose

Move from approved scope into a module artifact tree that a human or AI runtime can execute without guessing.

## Entry Conditions

- the parent program exists or the module has been explicitly authorized
- module scope is bounded enough to decompose
- the runtime knows whether the task is planning or execution

## Required Artifacts

- `MODULE.md`
- at least one `PHASE.md`
- at least one `ISSUE.md`

Additional artifacts appear later during execution:

- `PROOF.md`
- `REVIEW.md`
- `INTEGRATION.md`

## Startup Sequence

1. read `.cursor/commands/plan-module.md`
2. read `.cursor/templates/MODULE.md`
3. read `.cursor/templates/PHASE.md`
4. read `.cursor/templates/ISSUE.md`
5. define the module objective and boundaries
6. define phases that reflect meaningful checkpoints
7. define issues as atomic executable units
8. set dependencies explicitly
9. stop planning once a ready issue can be computed

## Startup Responsibilities

- preserve the hierarchy `Program -> Module -> Phase -> Issue`
- keep issues atomic
- avoid mixing proof, review, and integration into planning artifacts prematurely
- ensure `read_first` and `read_forbidden` keep context loading narrow

## Readiness Rule

Module bootstrap is successful when:

- the module artifact exists
- phases exist
- issues exist
- dependencies are explicit
- at least one issue can be identified as `ready` or `blocked` for a stated reason

## Runtime-Specific Startup Flows

### Human

- define module scope
- decompose the module into phases and issues
- verify that issue boundaries are real and not placeholder tasks

### Cursor

- route through `plan-module`
- create only the minimum phase and issue set needed to begin

### Codex

- route through `plan-module`
- compute readiness from dependencies instead of assumed sequencing

### Claude

- use the same artifact path and readiness logic
- do not replace issue-level execution with agent-level sequencing

## Shutdown Responsibilities

Before ending module bootstrap:

- record which issue is first executable
- record why non-ready issues are not ready
- leave the next execution command obvious
