---
module_id: "<module-id>"
title: "<module-title>"
status: "draft"
parent_program: "<program-id>"
objective: "<module objective>"
scope:
  - "<in-scope item>"
out_of_scope:
  - "<out-of-scope item>"
phases:
  - phase_id: "<phase-id>"
    path: ".cursor-or-repo-relative-path-to-phase-artifact"
read_first:
  - ".cursor/execution/INDEX.yaml"
  - ".cursor/execution/AUTONOMOUS-MODULE-EXECUTION.md"
  - "<program artifact path>"
read_forbidden:
  - "unrelated modules not required for this module"
module_definition_of_done:
  - "<completion condition>"
optional_fields:
  depends_on_modules:
    - "<module-id>"
  risk_summary:
    - "<risk>"
  interface_summary:
    - "<interface or dependency note>"
  notes:
    - "<note>"
---

# Module

## Objective

Describe what this module must achieve and how it contributes to the parent program.

## Scope

### In Scope

- ...

### Out Of Scope

- ...

## Phases

List the phases for this module and the path to each phase artifact.

## Progressive Disclosure Inputs

### Read First

- ...

### Read Forbidden

- ...

## Module Definition Of Done

- ...

## Roll-Up Semantics

- issue completion rolls into phase progress
- phase completion rolls into module progress
- module completion requires the module definition of done and mandatory module review

## Gate Notes

Document any module-level readiness, review, integration, or release expectations.

## Review Requirements

Module review is mandatory before the module should be treated as complete.

## Progressive Disclosure

Read next:

1. the current or first executable phase artifact
2. only the issue artifacts listed under that phase
3. the program artifact again only if module-level constraints are ambiguous
