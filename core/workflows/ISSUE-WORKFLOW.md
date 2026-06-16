# Issue Workflow

## Purpose

This workflow defines the atomic execution path from ready issue to proof production.

## Responsibilities

- verify issue readiness
- execute only within declared issue scope
- produce proof sufficient for independent review
- preserve blocker trails when execution cannot complete

## Workflow Boundary

This workflow governs:

- `ISSUE.md`
- `PROOF.md`
- issue state transitions up to `review_ready`

It does not perform final review or final integration.

## Input Contract

Required inputs:

- `ISSUE.md`
- all dependencies required by `depends_on`
- required inputs listed by the issue

Required artifacts:

- issue artifact
- proof artifact or proof update

## Entry Conditions

- issue state is `ready`
- dependencies are satisfied
- required inputs exist
- no unresolved blocker prevents execution

## Transitions

1. Confirm readiness.
2. Move the issue to `in_progress`.
3. Execute within declared scope.
4. Record outputs, observations, and failures.
5. Produce or update `PROOF.md`.
6. Move the issue to `review_ready` when proof is sufficient for review.

## Output Contract

Required outputs:

- executed work or explicit blocker trail
- proof artifact with evidence mapped to criteria
- issue state moved to `review_ready` or `blocked`

## Exit Conditions

The workflow exits successfully when:

- proof exists
- the issue is reviewable
- the issue has reached `review_ready`

The workflow exits unsuccessfully when:

- execution cannot proceed or complete
- evidence is too incomplete to support review
- the issue becomes blocked

## Ownership

Typical owners:

- human operator
- implementation resource
- design or QA support resource where needed

## Side Effects

- changes issue state
- creates or updates proof
- may expose new blockers or follow-up work

## Read Next

1. `REVIEW-WORKFLOW.md`
