---
program_id: "<program-id>"
title: "<program-title>"
status: "draft"
objective: "<plain-english objective>"
scope:
  - "<in-scope item>"
out_of_scope:
  - "<out-of-scope item>"
modules:
  - module_id: "<module-id>"
    path: ".cursor-or-repo-relative-path-to-module-artifact"
read_first:
  - ".cursor/execution/INDEX.yaml"
  - ".cursor/execution/CANONICAL-LAWS.md"
  - ".cursor/execution/MINIMUM-RUNTIME-MODEL.md"
read_forbidden:
  - "unrelated module trees not needed for current program work"
program_definition_of_done:
  - "<completion condition>"
global_constraints:
  - "<constraint>"
release_requirements:
  - "<release requirement>"
optional_fields:
  owner: "<human or team owner>"
  priority: "<priority>"
  success_metrics:
    - "<metric>"
  risk_summary:
    - "<risk>"
  decision_log_refs:
    - "<path or id>"
  notes:
    - "<note>"
---

# Program

This artifact should normally be created only after `INTENT.md` has verdict `pass` and `Eligible For Program Creation` is `true`, unless a human explicitly overrides.

## Objective

Describe the total outcome this program must achieve.

## Scope

### In Scope

- ...

### Out Of Scope

- ...

## Modules

List the modules that make up the program and the path to each module artifact.

## Progressive Disclosure Inputs

### Read First

- ...

### Read Forbidden

- ...

## Global Constraints

- ...

## Program Definition Of Done

- ...

## Roll-Up Semantics

- program progress rolls up from module progress
- program completion requires required modules to be complete
- program completion alone does not imply release readiness
- release readiness additionally requires release-level validation where applicable

## Release Requirements

- ...

## Progressive Disclosure

Read next:

1. the target module artifact
2. only the global constraints relevant to that module
3. related integration artifacts only when evaluating higher-level completion
