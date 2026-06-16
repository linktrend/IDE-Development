---
program_id: "profile-display-name-program"
title: "Profile Display Name Feature"
status: "complete"
objective: "Deliver a minimal profile display name capability with proof, review, and integration completed."
scope:
  - "capture display name in profile settings"
  - "persist display name in profile data"
  - "render display name in user-facing profile surfaces"
out_of_scope:
  - "usernames"
  - "avatars"
  - "moderation controls"
modules:
  - module_id: "profile-display-name"
    path: ".cursor/examples/EXAMPLE-SIMPLE-FEATURE/MODULE.md"
read_first:
  - ".cursor/execution/INDEX.yaml"
  - ".cursor/execution/CANONICAL-LAWS.md"
  - ".cursor/commands/plan-program.md"
  - ".cursor/examples/EXAMPLE-SIMPLE-FEATURE/INTENT.md"
read_forbidden:
  - "unrelated example trees"
program_definition_of_done:
  - "the module is complete"
  - "the module review passes"
  - "the program intent is satisfied without open blockers"
global_constraints:
  - "keep the example implementation-free"
  - "show a single-path lifecycle with explicit completion evidence"
release_requirements:
  - "none beyond program-level confirmation because this is a teaching example"
optional_fields:
  owner: "product-owner"
  priority: "medium"
  success_metrics:
    - "a new runtime can understand the full flow by reading one example tree"
---

# Program

This artifact should normally be created only after `INTENT.md` has verdict `pass` and `Eligible For Program Creation` is `true`, unless a human explicitly overrides.

## Objective

Describe the total outcome this program must achieve.

The outcome is a small but complete feature lifecycle that demonstrates how approved intent turns into executable module work.

## Scope

### In Scope

- one module
- one phase
- one issue
- one proof, review, and integration sequence

### Out Of Scope

- multi-module coordination
- release packaging

## Modules

List the modules that make up the program and the path to each module artifact.

- `profile-display-name`: `.cursor/examples/EXAMPLE-SIMPLE-FEATURE/MODULE.md`

## Progressive Disclosure Inputs

### Read First

- `.cursor/examples/EXAMPLE-SIMPLE-FEATURE/MODULE.md`

### Read Forbidden

- unrelated example trees

## Global Constraints

- use the preferred command layer: `plan-program`, `plan-module`, `execute-issue`, `review-issue`, `integrate-issue`
- keep evidence concrete and concise

## Program Definition Of Done

- the module is complete
- the module review passes
- the final integration records that the feature is available to downstream work

## Roll-Up Semantics

- program progress rolls up from module progress
- program completion requires required modules to be complete
- program completion alone does not imply release readiness
- release readiness additionally requires release-level validation where applicable

## Release Requirements

- not applicable for this minimal example

## Operational Notes

- ownership begins with the product owner for scope and shifts to the planner for decomposition
- command usage starts with `plan-program`
- workflow movement follows program workflow into module workflow
- the program consumes approved intent and produces one executable module

## Progressive Disclosure

Read next:

1. the target module artifact
2. only the global constraints relevant to that module
3. related integration artifacts only when evaluating higher-level completion
