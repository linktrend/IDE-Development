---
phase_id: "planning"
title: "Planning"
status: "complete"
parent_program: "authentication-module-smoke-test"
parent_module: "authentication"
objective: "Define requirements and the data model needed before implementation work may begin."
issues:
  - issue_id: "AUTH-001"
    path: ".cursor/pilots/authentication-module-smoke-test/modules/authentication/phases/planning/issues/AUTH-001.md"
  - issue_id: "AUTH-002"
    path: ".cursor/pilots/authentication-module-smoke-test/modules/authentication/phases/planning/issues/AUTH-002.md"
read_first:
  - ".cursor/pilots/authentication-module-smoke-test/modules/authentication/MODULE.md"
read_forbidden:
  - "unrelated phases or modules not needed for this phase"
phase_completion_criteria:
  - "AUTH-001 and AUTH-002 are done"
optional_fields:
  entry_conditions:
    - "module is active"
  exit_conditions:
    - "implementation phase issues may evaluate readiness"
  parallelism_notes:
    - "AUTH-002 depends on AUTH-001, so no concurrency exists in this phase"
  review_required: false
  notes:
    - "planning review is implicit through issue review"
---

# Phase

## Objective

Establish the planning artifacts that all downstream implementation issues depend on.

## Issues

List the issues in this phase and the path to each issue artifact.

- `AUTH-001`
- `AUTH-002`

## Progressive Disclosure Inputs

### Read First

- `../MODULE.md`

### Read Forbidden

- unrelated phases or modules not needed for this phase

## Phase Completion Criteria

- requirements are defined
- data model is defined

## Roll-Up Semantics

- issue completion rolls into phase progress
- phase completion may be based on issue completion alone or may also require explicit review if this phase or its parent module declares it

## Concurrency Notes

Document any helpful guidance about safe parallel execution. Issue dependencies remain authoritative.

No two issues are ready at the same time because `AUTH-002` depends on `AUTH-001`.

## Review Requirements

Phase review is optional unless this phase or its parent module explicitly requires it.

## Progressive Disclosure

Read next:

1. issue artifacts in this phase
2. only dependencies referenced by the chosen issue
3. proof, review, and integration artifacts only for the active issue
