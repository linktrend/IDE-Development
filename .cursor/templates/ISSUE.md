---
issue_id: "<issue-id>"
title: "<issue-title>"
status: "draft"
parent_program: "<program-id>"
parent_module: "<module-id>"
parent_phase: "<phase-id>"
depends_on:
  - "<issue-id>"
objective: "<single clear objective>"
scope:
  - "<allowed work>"
out_of_scope:
  - "<forbidden or excluded work>"
inputs:
  - "<required input>"
expected_outputs:
  - "<expected output>"
acceptance_criteria:
  - "<testable criterion>"
proof_requirements:
  - "<required evidence>"
review_requirements:
  - "<review expectation>"
integration_requirements:
  - "<integration expectation>"
suggested_role_types:
  - "<role type>"
read_first:
  - "<artifact path>"
read_forbidden:
  - "<path or category not required for this issue>"
blocking_questions:
  - "<open blocking question>"
optional_fields:
  priority: "<priority>"
  risk_level: "<risk level>"
  estimated_effort: "<estimate>"
  related_issues:
    - "<issue-id>"
  notes:
    - "<note>"
---

# Issue

## Objective

State the single concrete outcome this issue must achieve.

## Scope

### Allowed

- ...

### Out Of Scope

- ...

## Inputs

- ...

## Expected Outputs

- ...

## Acceptance Criteria

- ...

## Dependency Notes

List any context needed to interpret `depends_on`. Dependencies determine readiness.

## Proof Requirements

- ...

## Review Requirements

- ...

## Integration Requirements

- ...

## Blocking Questions

- ...

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
