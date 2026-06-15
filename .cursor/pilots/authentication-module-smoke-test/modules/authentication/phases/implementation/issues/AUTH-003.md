---
issue_id: "AUTH-003"
title: "Implement authentication schema"
status: "done"
parent_program: "authentication-module-smoke-test"
parent_module: "authentication"
parent_phase: "implementation"
depends_on:
  - "AUTH-002"
objective: "Represent the schema needed to support the authentication data model."
scope:
  - "schema entities"
  - "field mappings"
  - "integrity assumptions"
out_of_scope:
  - "API behavior"
  - "UI behavior"
inputs:
  - "AUTH-002 integrated data model"
expected_outputs:
  - "written schema representation"
acceptance_criteria:
  - "schema covers the required entities"
  - "schema aligns with the data model"
proof_requirements:
  - "proof references a schema representation"
review_requirements:
  - "review confirms alignment with AUTH-002"
integration_requirements:
  - "integration unlocks AUTH-004 and contributes to AUTH-006 readiness"
suggested_role_types:
  - "backend"
read_first:
  - ".cursor/pilots/authentication-module-smoke-test/modules/authentication/phases/planning/issues/AUTH-002.md"
read_forbidden:
  - "unrelated validation issues"
blocking_questions: []
optional_fields:
  priority: "high"
  risk_level: "medium"
  estimated_effort: "small"
  related_issues:
    - "AUTH-004"
    - "AUTH-006"
  notes:
    - "implementation chain begins here"
---

# Issue

## Objective

Represent the authentication schema implied by the data model.

## Scope

### Allowed

- schema structure
- data integrity assumptions

### Out Of Scope

- API contract behavior
- UI behavior

## Inputs

- AUTH-002 integrated data model

## Expected Outputs

- schema representation usable by downstream API work

## Acceptance Criteria

- required entities are represented
- data model alignment is explicit

## Dependency Notes

This issue becomes ready only after AUTH-002 integration.

## Proof Requirements

- proof references the schema representation

## Review Requirements

- review confirms schema alignment

## Integration Requirements

- integration unlocks AUTH-004

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
