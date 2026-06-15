---
module_id: "authentication"
title: "Authentication"
status: "complete"
parent_program: "authentication-module-smoke-test"
objective: "Represent and conceptually complete an Authentication module using canonical execution artifacts."
scope:
  - "requirements"
  - "data model"
  - "schema"
  - "API contracts"
  - "UI behavior"
  - "module validation"
out_of_scope:
  - "real application implementation"
  - "deployment"
phases:
  - phase_id: "planning"
    path: ".cursor/pilots/authentication-module-smoke-test/modules/authentication/phases/planning/PHASE.md"
  - phase_id: "implementation"
    path: ".cursor/pilots/authentication-module-smoke-test/modules/authentication/phases/implementation/PHASE.md"
  - phase_id: "validation"
    path: ".cursor/pilots/authentication-module-smoke-test/modules/authentication/phases/validation/PHASE.md"
read_first:
  - ".cursor/execution/INDEX.yaml"
  - ".cursor/execution/AUTONOMOUS-MODULE-EXECUTION.md"
  - ".cursor/pilots/authentication-module-smoke-test/PROGRAM.md"
read_forbidden:
  - "unrelated modules not required for this module"
module_definition_of_done:
  - "all required issues are done"
  - "AUTH-006 validation passes"
  - "module review passes"
optional_fields:
  depends_on_modules: []
  risk_summary:
    - "proof/review semantics may be underspecified in first use"
  interface_summary:
    - "authentication data, API, and UI behavior must remain aligned"
  notes:
    - "pilot module only"
---

# Module

## Objective

Show that a runtime can recursively traverse phases and issues for an Authentication module and complete it using doctrine and artifacts alone.

## Scope

### In Scope

- requirements definition
- authentication data model
- schema representation
- login and signup API contracts
- login and signup UI behavior
- module-level validation

### Out Of Scope

- code execution
- infrastructure

## Phases

List the phases for this module and the path to each phase artifact.

- `planning` → `phases/planning/PHASE.md`
- `implementation` → `phases/implementation/PHASE.md`
- `validation` → `phases/validation/PHASE.md`

## Progressive Disclosure Inputs

### Read First

- `.cursor/execution/INDEX.yaml`
- `.cursor/execution/AUTONOMOUS-MODULE-EXECUTION.md`
- `.cursor/pilots/authentication-module-smoke-test/PROGRAM.md`

### Read Forbidden

- unrelated modules not required for this module

## Module Definition Of Done

- all six issues are done
- all six integrations are present
- insufficient proof was rejected and corrected
- explicit module review passes
- explicit module integration records module completion

## Roll-Up Semantics

- issue completion rolls into phase progress
- phase completion rolls into module progress
- module completion requires the module definition of done and mandatory module review

## Gate Notes

- phase review is optional in this pilot
- issue review is mandatory for every issue
- module review is satisfied only after AUTH-006 and the explicit module review artifact
- module integration is satisfied only after the explicit module integration artifact

## Review Requirements

Module review is mandatory before the module should be treated as complete.

## Progressive Disclosure

Read next:

1. the current or first executable phase artifact
2. only the issue artifacts listed under that phase
3. the program artifact again only if module-level constraints are ambiguous
