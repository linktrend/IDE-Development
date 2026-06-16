---
phase_id: "validation"
title: "Validation"
status: "complete"
parent_program: "authentication-module-smoke-test"
parent_module: "authentication"
objective: "Validate that the Authentication module definition of done has been satisfied."
issues:
  - issue_id: "AUTH-006"
    path: ".cursor/pilots/authentication-module-smoke-test/modules/authentication/phases/validation/issues/AUTH-006.md"
read_first:
  - ".cursor/pilots/authentication-module-smoke-test/modules/authentication/MODULE.md"
read_forbidden:
  - "unrelated modules or pilot trees"
phase_completion_criteria:
  - "AUTH-006 is done"
optional_fields:
  entry_conditions:
    - "implementation phase complete"
  exit_conditions:
    - "module may be considered complete"
  parallelism_notes:
    - "single validation issue; no concurrency"
  review_required: true
  notes:
    - "phase review is effectively represented by AUTH-006 review and the pilot report"
---

# Phase

## Objective

Validate the module-level definition of done after all implementation issues are integrated.

## Issues

- `AUTH-006`

## Progressive Disclosure Inputs

### Read First

- `../MODULE.md`

### Read Forbidden

- unrelated modules or pilot trees

## Phase Completion Criteria

- module validation issue passes

## Roll-Up Semantics

- issue completion rolls into phase progress
- phase completion may be based on issue completion alone or may also require explicit review if this phase or its parent module declares it

## Concurrency Notes

Only one issue exists in this phase, so there is no concurrency.

## Review Requirements

Phase review is optional unless this phase or its parent module explicitly requires it.

This phase explicitly requires review through `review_required: true`.

## Progressive Disclosure

Read next:

1. issue artifacts in this phase
2. only dependencies referenced by the chosen issue
3. proof, review, and integration artifacts only for the active issue
