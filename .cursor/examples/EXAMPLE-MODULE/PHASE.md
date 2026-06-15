---
phase_id: "notification-preferences-delivery"
title: "Preferences Delivery"
status: "complete"
parent_program: "notification-preferences-program"
parent_module: "notification-preferences"
objective: "Carry the module through one representative execution slice and into module completion."
issues:
  - issue_id: "NOTIFY-101"
    path: ".cursor/examples/EXAMPLE-MODULE/ISSUE.md"
read_first:
  - ".cursor/examples/EXAMPLE-MODULE/MODULE.md"
read_forbidden:
  - "unrelated examples"
phase_completion_criteria:
  - "the representative issue is done"
  - "the module can proceed to mandatory module review"
optional_fields:
  parallelism_notes:
    - "parallelism is intentionally omitted here so the module-level flow stays obvious"
  review_required: false
---

# Phase

## Objective

Describe the purpose of this phase and the checkpoint it represents.

This phase converts the module objective into one atomic executable slice.

## Issues

- `NOTIFY-101`: `.cursor/examples/EXAMPLE-MODULE/ISSUE.md`

## Progressive Disclosure Inputs

### Read First

- `.cursor/examples/EXAMPLE-MODULE/ISSUE.md`

### Read Forbidden

- unrelated examples

## Phase Completion Criteria

- the issue reaches `done`
- module-level review may begin

## Roll-Up Semantics

- issue completion rolls into phase progress
- phase completion may be based on issue completion alone or may also require explicit review if this phase or its parent module declares it

## Concurrency Notes

This example suppresses concurrency intentionally. Real modules may expose parallel issues once dependencies are satisfied.

## Review Requirements

Phase review is optional unless this phase or its parent module explicitly requires it.

## Operational Notes

- this phase acts as the direct handoff from module workflow to issue workflow

## Progressive Disclosure

Read next:

1. issue artifacts in this phase
2. proof, review, and integration artifacts only for the active issue
