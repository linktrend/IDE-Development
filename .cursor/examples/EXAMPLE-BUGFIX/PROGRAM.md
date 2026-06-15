---
program_id: "session-refresh-bugfix-program"
title: "Session Refresh Expiry Bugfix"
status: "complete"
objective: "Correct the stale-expiry session refresh bug and show the full defect-resolution lifecycle."
scope:
  - "reproduce the defect"
  - "define corrected session refresh behavior"
  - "complete proof, review, and integration"
out_of_scope:
  - "session architecture redesign"
modules:
  - module_id: "session-refresh-bugfix"
    path: ".cursor/examples/EXAMPLE-BUGFIX/MODULE.md"
read_first:
  - ".cursor/execution/INDEX.yaml"
  - ".cursor/commands/plan-program.md"
  - ".cursor/examples/EXAMPLE-BUGFIX/INTENT.md"
read_forbidden:
  - "unrelated examples"
program_definition_of_done:
  - "the bugfix module is complete"
  - "evidence demonstrates defect closure"
global_constraints:
  - "proof must compare failing behavior against corrected behavior"
release_requirements:
  - "none for this canonical example"
optional_fields:
  owner: "product-owner"
---

# Program

This artifact should normally be created only after `INTENT.md` has verdict `pass` and `Eligible For Program Creation` is `true`, unless a human explicitly overrides.

## Objective

Teach how a defect-oriented change moves through the same canonical execution model.

## Scope

### In Scope

- one bugfix module
- one validation phase
- one defect-resolution issue

### Out Of Scope

- multi-defect coordination

## Modules

- `session-refresh-bugfix`: `.cursor/examples/EXAMPLE-BUGFIX/MODULE.md`

## Progressive Disclosure Inputs

### Read First

- `.cursor/examples/EXAMPLE-BUGFIX/MODULE.md`

### Read Forbidden

- unrelated examples

## Global Constraints

- use the same canonical command path as other work
- proof must remain concrete

## Program Definition Of Done

- defect resolution is recorded by issue completion and module roll-up

## Roll-Up Semantics

- program progress rolls up from module progress
- program completion requires required modules to be complete
- program completion alone does not imply release readiness
- release readiness additionally requires release-level validation where applicable

## Release Requirements

- not applicable here

## Operational Notes

- key command emphasis: `execute-issue`, `review-issue`, `integrate-issue`
- the defect flow consumes the same doctrine as feature work; only the evidence shape changes

## Progressive Disclosure

Read next:

1. the target module artifact
2. only the constraints relevant to that module
