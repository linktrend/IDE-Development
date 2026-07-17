---
program_id: "<program-id>"
title: "<program-title>"
status: "draft"
objective: "<plain-english objective>"
scope:
  - "<in-scope item>"
out_of_scope:
  - "<out-of-scope item>"
program_kind: "application | non-application"
modules:
  # Application Programs MUST list exactly these six, in order (paths under docs/development/<program-id>/modules/):
  - module_id: "intake_and_definition"
    path: "modules/01-intake-and-definition/MODULE.md"
  - module_id: "assembly_planning"
    path: "modules/02-assembly-planning/MODULE.md"
  - module_id: "execution"
    path: "modules/03-execution/MODULE.md"
  - module_id: "verification_and_hardening"
    path: "modules/04-verification-and-hardening/MODULE.md"
  - module_id: "library_contribution"
    path: "modules/05-library-contribution/MODULE.md"
  - module_id: "shipment"
    path: "modules/06-shipment/MODULE.md"
read_first:
  - ".cursor/execution/INDEX.yaml"
  - ".cursor/execution/CANONICAL-LAWS.md"
  - ".cursor/execution/MINIMUM-RUNTIME-MODEL.md"
  - ".cursor/execution/APPLICATION-PIPELINE.md"
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

**Application Programs:** list exactly the six fixed Modules in order (IDs from `.cursor/execution/APPLICATION-PIPELINE.md`). Do not rename, reorder, omit, or add a seventh top-level Module.

**Non-application governed work:** generic Module semantics remain available; list domain modules as needed.

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
