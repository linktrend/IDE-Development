---
issue_id: "SESSION-201"
title: "Correct stale session expiry check on refresh"
status: "done"
parent_program: "session-refresh-bugfix-program"
parent_module: "session-refresh-bugfix"
parent_phase: "session-refresh-validation"
depends_on: []
objective: "Demonstrate that the stale-expiry session refresh defect can be identified, corrected, and validated through the canonical issue lifecycle."
scope:
  - "document failing behavior"
  - "define corrected behavior"
  - "produce bugfix proof"
out_of_scope:
  - "token rotation redesign"
inputs:
  - ".cursor/examples/EXAMPLE-BUGFIX/MODULE.md"
  - ".cursor/commands/execute-issue.md"
  - ".cursor/workflows/ISSUE-WORKFLOW.md"
expected_outputs:
  - "bugfix proof that references before/after behavior"
  - "review verdict on defect closure"
  - "integration record for downstream confidence"
acceptance_criteria:
  - "the failing refresh condition is stated concretely"
  - "the corrected behavior prevents premature logout"
  - "review confirms the evidence closes the defect"
proof_requirements:
  - "show both the reproduced problem and the corrected expected result"
review_requirements:
  - "review must fail if proof does not distinguish old and new behavior"
integration_requirements:
  - "record that session-related downstream work may assume the defect is closed"
suggested_role_types:
  - "backend-developer"
  - "qa-automation-engineer"
read_first:
  - ".cursor/examples/EXAMPLE-BUGFIX/PHASE.md"
  - ".cursor/state/STATE-MODEL.md"
read_forbidden:
  - "unrelated examples"
blocking_questions: []
optional_fields:
  risk_level: "medium"
  notes:
    - "state path used in this example: draft -> planned -> ready -> in_progress -> review_ready -> done"
---

# Issue

## Objective

State the single concrete outcome this issue must achieve.

The issue must prove that the stale refresh-expiry defect is resolved well enough for an independent reviewer to accept closure.

## Scope

### Allowed

- defect reproduction statement
- corrected behavior statement
- proof, review, and integration

### Out Of Scope

- broader session improvements

## Inputs

- module scope
- issue workflow
- execute-issue command

## Expected Outputs

- proof of defect closure
- passing review
- integrated bugfix state

## Acceptance Criteria

- the issue is executable immediately because it has no dependencies
- proof distinguishes the bug from the fixed behavior
- integration records that later issues may rely on the closed defect

## Dependency Notes

No dependencies exist. The issue is `ready` as soon as planning artifacts are complete.

## Proof Requirements

- pre-fix symptom
- post-fix expected result
- traceable references to review and integration

## Review Requirements

- independent reviewer must verify that the defect is actually closed

## Integration Requirements

- downstream session work may rely on integrated closure, not just claimed closure

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

## Operational Notes

- command usage: `execute-issue` -> `review-issue` -> `integrate-issue`
- workflow movement: issue workflow -> review workflow -> integration workflow
- contract handoff: issue outputs are consumed by proof, then review, then integration
- ownership: implementer closes the defect, reviewer validates closure, integrator records downstream trust

## Progressive Disclosure

Read next:

1. the artifacts listed in `read_first`
2. the proof artifact for this issue once execution work is complete
3. the review artifact after proof exists
