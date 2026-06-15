---
program_id: "notification-preferences-program"
title: "Notification Preferences Program"
status: "complete"
objective: "Show how a real module-oriented request becomes executable and reaches complete state through the canonical system."
scope:
  - "one notification preferences module"
  - "one module-delivery phase"
  - "one representative issue"
out_of_scope:
  - "notification transport implementation"
  - "cross-product preference sync"
modules:
  - module_id: "notification-preferences"
    path: ".cursor/examples/EXAMPLE-MODULE/MODULE.md"
read_first:
  - ".cursor/execution/INDEX.yaml"
  - ".cursor/commands/complete-module.md"
  - ".cursor/examples/EXAMPLE-MODULE/INTENT.md"
read_forbidden:
  - "unrelated examples"
program_definition_of_done:
  - "the notification preferences module is complete"
  - "program-level completion can be inferred from module completion because only one module exists"
global_constraints:
  - "keep the example small but realistic"
  - "show the complete module command path"
release_requirements:
  - "none for this canonical example"
optional_fields:
  owner: "product-owner"
  success_metrics:
    - "a runtime can learn module execution from this example alone"
---

# Program

This artifact should normally be created only after `INTENT.md` has verdict `pass` and `Eligible For Program Creation` is `true`, unless a human explicitly overrides.

## Objective

Demonstrate the module-oriented user request path: "Complete this module."

## Scope

### In Scope

- one module
- one phase
- one representative issue
- explicit module completion semantics

### Out Of Scope

- multi-module concurrency
- release packaging

## Modules

- `notification-preferences`: `.cursor/examples/EXAMPLE-MODULE/MODULE.md`

## Progressive Disclosure Inputs

### Read First

- `.cursor/examples/EXAMPLE-MODULE/MODULE.md`

### Read Forbidden

- unrelated examples

## Global Constraints

- use `complete-module` as the primary command wrapper
- show review and integration as mandatory completion gates

## Program Definition Of Done

- module completion is explicit and review-backed

## Roll-Up Semantics

- program progress rolls up from module progress
- program completion requires required modules to be complete
- program completion alone does not imply release readiness
- release readiness additionally requires release-level validation where applicable

## Release Requirements

- not applicable here

## Operational Notes

- command emphasis: `complete-module` delegates into issue execution, review, and integration
- workflow movement: program workflow -> module workflow -> issue workflow -> review workflow -> integration workflow

## Progressive Disclosure

Read next:

1. the target module artifact
2. only the global constraints relevant to that module
