---
phase_id: "profile-display-name-delivery"
title: "Feature Delivery"
status: "complete"
parent_program: "profile-display-name-program"
parent_module: "profile-display-name"
objective: "Deliver and validate the minimum feature slice needed to satisfy the module objective."
issues:
  - issue_id: "PROFILE-001"
    path: ".cursor/examples/EXAMPLE-SIMPLE-FEATURE/ISSUE.md"
read_first:
  - ".cursor/examples/EXAMPLE-SIMPLE-FEATURE/MODULE.md"
read_forbidden:
  - "unrelated phases or modules"
phase_completion_criteria:
  - "all listed issues are done"
  - "no unresolved blockers remain"
optional_fields:
  parallelism_notes:
    - "no parallelism exists in this example because there is only one issue"
  review_required: false
  notes:
    - "phase review is intentionally omitted to demonstrate the conditional phase-review rule"
---

# Phase

## Objective

Describe the purpose of this phase and the checkpoint it represents.

This phase contains the smallest complete executable slice for the feature.

## Issues

List the issues in this phase and the path to each issue artifact.

- `PROFILE-001`: `.cursor/examples/EXAMPLE-SIMPLE-FEATURE/ISSUE.md`

## Progressive Disclosure Inputs

### Read First

- `.cursor/examples/EXAMPLE-SIMPLE-FEATURE/ISSUE.md`

### Read Forbidden

- unrelated phases or modules

## Phase Completion Criteria

- the issue reaches `done`
- issue integration updates downstream completion status

## Roll-Up Semantics

- issue completion rolls into phase progress
- phase completion may be based on issue completion alone or may also require explicit review if this phase or its parent module declares it

## Concurrency Notes

There is no concurrency in this example because only one issue exists. This teaches the minimum lifecycle, not parallel scheduling.

## Review Requirements

Phase review is optional unless this phase or its parent module explicitly requires it.

## Operational Notes

- workflow movement here is direct: module workflow hands off to issue workflow
- the phase consumes module scope and emits one ready issue

## Progressive Disclosure

Read next:

1. issue artifacts in this phase
2. only dependencies referenced by the chosen issue
3. proof, review, and integration artifacts only for the active issue
