---
issue_id: "AUTH-006"
title: "Validate authentication module definition of done"
status: "done"
parent_program: "authentication-module-smoke-test"
parent_module: "authentication"
parent_phase: "validation"
depends_on:
  - "AUTH-003"
  - "AUTH-004"
  - "AUTH-005"
objective: "Validate that the Authentication module has reached its definition of done."
scope:
  - "module-level validation"
  - "completion assessment"
out_of_scope:
  - "new implementation work"
inputs:
  - "integrated AUTH-003"
  - "integrated AUTH-004"
  - "integrated AUTH-005"
expected_outputs:
  - "validation summary stating whether the module is complete or blocked"
acceptance_criteria:
  - "module definition of done is evaluated explicitly"
  - "remaining gaps are either absent or clearly stated"
proof_requirements:
  - "proof references all prerequisite integrated issues and module completion criteria"
review_requirements:
  - "review confirms module completion or identifies genuine blockers"
integration_requirements:
  - "integration records module completion state"
suggested_role_types:
  - "qa"
  - "technical lead"
read_first:
  - ".cursor/pilots/authentication-module-smoke-test/modules/authentication/MODULE.md"
  - ".cursor/pilots/authentication-module-smoke-test/modules/authentication/phases/implementation/issues/AUTH-003.md"
  - ".cursor/pilots/authentication-module-smoke-test/modules/authentication/phases/implementation/issues/AUTH-004.md"
  - ".cursor/pilots/authentication-module-smoke-test/modules/authentication/phases/implementation/issues/AUTH-005.md"
read_forbidden:
  - "unrelated pilot artifacts"
blocking_questions: []
optional_fields:
  priority: "high"
  risk_level: "low"
  estimated_effort: "small"
  related_issues: []
  notes:
    - "final issue in the pilot"
---

# Issue

## Objective

Determine whether the Authentication module is complete or genuinely blocked.

## Scope

### Allowed

- validation of module definition of done
- completion assessment

### Out Of Scope

- new schema, API, or UI work

## Inputs

- integrated AUTH-003
- integrated AUTH-004
- integrated AUTH-005

## Expected Outputs

- validation summary on module completion

## Acceptance Criteria

- module definition of done is explicitly evaluated
- completion or blockage is explicitly stated

## Dependency Notes

This issue becomes ready only after AUTH-003, AUTH-004, and AUTH-005 are all integrated.

## Proof Requirements

- proof references the module definition of done and all prerequisite integrated issues

## Review Requirements

- review confirms whether the module is complete

## Integration Requirements

- integration records the module completion state

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
