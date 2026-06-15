---
phase_id: "<phase-id>"
title: "<phase-title>"
status: "draft"
parent_program: "<program-id>"
parent_module: "<module-id>"
objective: "<phase objective>"
issues:
  - issue_id: "<issue-id>"
    path: ".cursor-or-repo-relative-path-to-issue-artifact"
read_first:
  - "<module artifact path>"
read_forbidden:
  - "unrelated phases or modules not needed for this phase"
phase_completion_criteria:
  - "<completion condition>"
optional_fields:
  entry_conditions:
    - "<entry condition>"
  exit_conditions:
    - "<exit condition>"
  parallelism_notes:
    - "<parallelism note>"
  review_required: false
  notes:
    - "<note>"
---

# Phase

## Objective

Describe the purpose of this phase and the checkpoint it represents.

## Issues

List the issues in this phase and the path to each issue artifact.

## Progressive Disclosure Inputs

### Read First

- ...

### Read Forbidden

- ...

## Phase Completion Criteria

- ...

## Roll-Up Semantics

- issue completion rolls into phase progress
- phase completion may be based on issue completion alone or may also require explicit review if this phase or its parent module declares it

## Concurrency Notes

Document any helpful guidance about safe parallel execution. Issue dependencies remain authoritative.

## Review Requirements

Phase review is optional unless this phase or its parent module explicitly requires it.

## Progressive Disclosure

Read next:

1. issue artifacts in this phase
2. only dependencies referenced by the chosen issue
3. proof, review, and integration artifacts only for the active issue
