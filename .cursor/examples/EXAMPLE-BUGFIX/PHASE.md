---
phase_id: "session-refresh-validation"
title: "Bug Reproduction And Closure"
status: "complete"
parent_program: "session-refresh-bugfix-program"
parent_module: "session-refresh-bugfix"
objective: "Carry the bugfix from defect statement through verified closure."
issues:
  - issue_id: "SESSION-201"
    path: ".cursor/examples/EXAMPLE-BUGFIX/ISSUE.md"
read_first:
  - ".cursor/examples/EXAMPLE-BUGFIX/MODULE.md"
read_forbidden:
  - "unrelated examples"
phase_completion_criteria:
  - "the bugfix issue is done"
optional_fields:
  parallelism_notes:
    - "no concurrency is modeled because reproducing and resolving one defect is the entire teaching scope"
  review_required: false
---

# Phase

## Objective

Describe the purpose of this phase and the checkpoint it represents.

This phase shows how a defect moves from identified problem to validated closure.

## Issues

- `SESSION-201`: `.cursor/examples/EXAMPLE-BUGFIX/ISSUE.md`

## Progressive Disclosure Inputs

### Read First

- `.cursor/examples/EXAMPLE-BUGFIX/ISSUE.md`

### Read Forbidden

- unrelated examples

## Phase Completion Criteria

- the defect-resolution issue reaches `done`

## Roll-Up Semantics

- issue completion rolls into phase progress
- phase completion may be based on issue completion alone or may also require explicit review if this phase or its parent module declares it

## Concurrency Notes

No parallel execution exists in this example because the reproduction and correction belong to the same atomic issue.

## Review Requirements

Phase review is optional unless this phase or its parent module explicitly requires it.

## Operational Notes

- this phase primarily demonstrates issue workflow and review workflow for defects

## Progressive Disclosure

Read next:

1. issue artifacts in this phase
2. proof, review, and integration artifacts only for the active issue
