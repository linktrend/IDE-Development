# State Transitions

## Purpose

This document defines allowed and invalid transitions for all canonical work units.

## Universal Transition Rules

1. No transition may bypass required upstream obligations.
2. No transition may hide a failed review or failed integration behind a completion label.
3. Transition authority belongs to the stage that owns that transition.
4. Application-pipeline Module transitions are fail-closed via `.cursor/runtime/validate-application-pipeline.mjs` (Law 16). Non-zero means stop; no warn-only path.
5. Issues cannot become `done` without proof, independent review pass, and integration.

## Intent Transitions

Allowed:

- `draft -> under_review`
- `under_review -> accepted`
- `under_review -> rejected`
- `under_review -> deferred`
- `deferred -> under_review`

Invalid:

- `draft -> accepted` without explicit review
- `rejected -> accepted` without re-entering review

## Program, Module, And Phase Transitions

Allowed:

- `draft -> planned`
- `planned -> active`
- `active -> blocked`
- `blocked -> active`
- `active -> in_review`
- `in_review -> complete`

Invalid:

- `planned -> complete`
- `active -> complete` without required review where applicable
- `blocked -> complete`

## Issue Transitions

Allowed:

- `planned -> ready`
- `ready -> in_progress`
- `in_progress -> in_review`
- `in_review -> done`
- `planned -> blocked`
- `ready -> blocked`
- `in_progress -> blocked`
- `in_review -> blocked`
- `blocked -> planned`
- `blocked -> ready`
- `in_review -> in_progress`
- any non-`done` state `-> cancelled`

Issue states match the Ledger. `in_review` in older state files is read as
`in_review` and never written.

Invalid:

- `planned -> done`
- `ready -> done`
- `in_progress -> done`
- any transition that bypasses `in_review`

## Proof Transitions

Allowed:

- `draft -> collecting`
- `collecting -> sufficient`
- `collecting -> insufficient`
- `insufficient -> collecting`

Invalid:

- `draft -> sufficient` without evidence collection

## Review Transitions

Allowed:

- `pending -> pass`
- `pending -> fail`
- `pending -> blocked`

Invalid:

- `fail -> pass` without a new review cycle
- `blocked -> pass` without re-entry to review

## Integration Transitions

Allowed:

- `pending -> integrated`
- `pending -> blocked`
- `blocked -> pending`

Invalid:

- `blocked -> integrated` without re-entering pending integration work

## Ownership Rule

- planning owns planning transitions
- execution owns issue execution transitions
- proof production owns proof sufficiency transitions
- reviewers own review verdict transitions
- integrators own integration transitions

## Read Next

1. `READY-STATES.md`
2. `FAILURE-STATES.md`
3. `RETRY-STATES.md`
