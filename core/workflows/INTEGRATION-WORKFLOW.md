# Integration Workflow

## Purpose

This workflow defines how passing work is incorporated into the active line and how downstream readiness is recomputed.

## Responsibilities

- integrate only work with passing review
- record downstream effects
- change issue state to `done` only after integration succeeds
- recompute readiness for dependent work

## Workflow Boundary

This workflow governs:

- `REVIEW.md`
- `INTEGRATION.md`
- downstream readiness updates

It does not create proof or review verdicts.

## Input Contract

Required inputs:

- subject artifact
- passing review artifact
- current dependency context

Required artifacts:

- integration artifact

## Entry Conditions

- review verdict is `pass`
- integration scope is understood
- no unresolved integration blocker prevents incorporation

## Transitions

1. Load the subject and passing review artifacts.
2. Record integrated outputs.
3. Record downstream effects.
4. Update final state.
5. Recompute readiness for dependent issues.
6. Roll completion upward where appropriate.

## Output Contract

Required outputs:

- `INTEGRATION.md`
- explicit final state
- downstream readiness effects

## Exit Conditions

The workflow exits successfully when:

- integration is recorded
- the subject is dependency-satisfying
- downstream readiness has been recomputed

The workflow exits unsuccessfully when:

- integration conflicts or risks prevent safe incorporation
- the subject remains non-integrated and therefore non-complete

## Ownership

Typical owners:

- human operator
- integrator resource
- orchestrator resource for downstream recomputation

## Side Effects

- changes completion state
- enables downstream work
- contributes to phase, module, and program roll-up

## Read Next

1. `ISSUE-WORKFLOW.md`
2. `MODULE-WORKFLOW.md`
