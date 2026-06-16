---
issue_id: "AUTH-002"
title: "Define authentication data model"
status: "done"
parent_program: "authentication-module-smoke-test"
parent_module: "authentication"
parent_phase: "planning"
depends_on:
  - "AUTH-001"
objective: "Define the data entities and relationships needed for authentication."
scope:
  - "user identity fields"
  - "credential records"
  - "session model"
out_of_scope:
  - "schema implementation"
inputs:
  - "AUTH-001 integrated requirements"
expected_outputs:
  - "written data model summary"
acceptance_criteria:
  - "core authentication entities are defined"
  - "relationships and boundaries are explicit"
proof_requirements:
  - "proof references a data model summary"
review_requirements:
  - "review confirms the model follows the requirements"
integration_requirements:
  - "integration records that implementation issues may rely on the data model"
suggested_role_types:
  - "backend"
  - "technical lead"
read_first:
  - ".cursor/pilots/authentication-module-smoke-test/modules/authentication/phases/planning/issues/AUTH-001.md"
read_forbidden:
  - "validation-phase issues"
blocking_questions: []
optional_fields:
  priority: "high"
  risk_level: "medium"
  estimated_effort: "small"
  related_issues:
    - "AUTH-003"
  notes:
    - "becomes ready only after AUTH-001 integration"
---

# Issue

## Objective

Define the data model that later schema and API issues depend on.

## Scope

### Allowed

- entity definitions
- field expectations
- relationship descriptions

### Out Of Scope

- schema implementation
- API behavior

## Inputs

- integrated AUTH-001 requirements

## Expected Outputs

- data model summary suitable for downstream implementation issues

## Acceptance Criteria

- core entities are explicit
- relationships are explicit

## Dependency Notes

This issue is not ready until AUTH-001 is integrated.

## Proof Requirements

- data model summary exists in proof artifact

## Review Requirements

- review confirms alignment with AUTH-001

## Integration Requirements

- integration unlocks AUTH-003

## Blocking Questions

- none

## State Semantics

- `draft`: not executable yet
- `planned`: defined but not ready
- `blocked`: cannot proceed because a dependency, gate, or decision is unresolved
- `ready`: dependencies and gates are satisfied
- `in_progress`: active execution is underway
- `review_ready`: execution and proof are complete enough for mandatory independent review
- `done`: proof, review, and integration are complete

## Gate Guidance

- readiness depends on satisfied dependencies and no unresolved blockers
- issues must pass through `review_ready`; they must not jump directly from `in_progress` to `done`
- proof must exist before review
- review must pass before integration
- integration must complete before downstream issues may rely on this issue
- issue `done` requires proof, review, and integration

## Progressive Disclosure

Read next:

1. the artifacts listed in `read_first`
2. only the dependency issues listed in `depends_on`
3. the proof artifact for this issue once execution work is complete

Do not scan unrelated modules, phases, or issue trees unless this issue explicitly requires them.
