---
issue_id: "AUTH-004"
title: "Implement login and signup API contracts"
status: "done"
parent_program: "authentication-module-smoke-test"
parent_module: "authentication"
parent_phase: "implementation"
depends_on:
  - "AUTH-003"
objective: "Represent the login and signup API contracts that depend on the authentication schema."
scope:
  - "login request and response contract"
  - "signup request and response contract"
out_of_scope:
  - "UI behavior"
inputs:
  - "AUTH-003 integrated schema representation"
expected_outputs:
  - "written API contract summary"
acceptance_criteria:
  - "login contract is explicit"
  - "signup contract is explicit"
  - "contracts align with schema assumptions"
proof_requirements:
  - "proof references both login and signup contract details"
review_requirements:
  - "review rejects incomplete or vague contract proof"
integration_requirements:
  - "integration unlocks AUTH-005 and contributes to AUTH-006 readiness"
suggested_role_types:
  - "backend"
  - "API designer"
read_first:
  - ".cursor/pilots/authentication-module-smoke-test/modules/authentication/phases/implementation/issues/AUTH-003.md"
read_forbidden:
  - "validation issue details not needed for contract definition"
blocking_questions: []
optional_fields:
  priority: "high"
  risk_level: "medium"
  estimated_effort: "small"
  related_issues:
    - "AUTH-005"
    - "AUTH-006"
  notes:
    - "first proof attempt is intentionally insufficient"
---

# Issue

## Objective

Represent the login and signup API contracts clearly enough for downstream UI behavior and validation.

## Scope

### Allowed

- request shapes
- response shapes
- behavioral expectations

### Out Of Scope

- UI interaction details

## Inputs

- AUTH-003 integrated schema representation

## Expected Outputs

- API contract summary for login and signup

## Acceptance Criteria

- login contract is explicit
- signup contract is explicit
- schema alignment is explicit

## Dependency Notes

This issue becomes ready only after AUTH-003 integration.

## Proof Requirements

- proof must show both contracts, not a vague statement that they exist

## Review Requirements

- review must reject insufficient proof

## Integration Requirements

- integration unlocks AUTH-005

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
