---
module_id: "notification-preferences"
title: "Notification Preferences"
status: "complete"
parent_program: "notification-preferences-program"
objective: "Provide a complete module-level example for preference management using the canonical execution model."
scope:
  - "preference categories and user-facing controls"
  - "module completion roll-up"
  - "explicit ownership and command routing"
out_of_scope:
  - "message delivery infrastructure"
phases:
  - phase_id: "notification-preferences-delivery"
    path: ".cursor/examples/EXAMPLE-MODULE/PHASE.md"
read_first:
  - ".cursor/execution/AUTONOMOUS-MODULE-EXECUTION.md"
  - ".cursor/examples/EXAMPLE-MODULE/PROGRAM.md"
  - ".cursor/commands/complete-module.md"
read_forbidden:
  - "unrelated examples"
module_definition_of_done:
  - "all required issues are done"
  - "module review confirms the user-facing objective is satisfied"
  - "module integration records the program-level effect"
optional_fields:
  interface_summary:
    - "users can enable or disable notification categories from one settings surface"
  notes:
    - "the example compresses a module into one representative issue to keep the artifact set minimal"
---

# Module

## Objective

Describe what this module must achieve and how it contributes to the parent program.

This module teaches the complete path that a runtime should follow after the user says "Complete this module."

## Scope

### In Scope

- one module delivery phase
- one issue with full completion artifacts
- explicit module roll-up behavior

### Out Of Scope

- exhaustive decomposition into many issues

## Phases

- `notification-preferences-delivery`: `.cursor/examples/EXAMPLE-MODULE/PHASE.md`

## Progressive Disclosure Inputs

### Read First

- `.cursor/examples/EXAMPLE-MODULE/PHASE.md`

### Read Forbidden

- unrelated examples

## Module Definition Of Done

- issue completion criteria are satisfied
- mandatory review passes
- integration records completion effects upward to the program

## Roll-Up Semantics

- issue completion rolls into phase progress
- phase completion rolls into module progress
- module completion requires the module definition of done and mandatory module review

## Gate Notes

This module is the clearest example of the doctrine that execution does not stop at implementation. Completion requires proof, review, integration, and explicit module roll-up.

## Review Requirements

Module review is mandatory before the module should be treated as complete.

## Operational Notes

- ownership is role-based but control remains dependency-driven
- the runtime begins here after command routing from `complete-module`
- the module consumes program scope and emits phase-ready issue work plus completed roll-up artifacts

## Progressive Disclosure

Read next:

1. the current or first executable phase artifact
2. only the issue artifacts listed under that phase
