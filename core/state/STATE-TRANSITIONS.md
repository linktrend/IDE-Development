# State Transitions

## Purpose

This document defines allowed and invalid transitions for all canonical work units.

## Universal Transition Rules

1. No transition may bypass required upstream obligations.
2. No transition may hide a failed review or failed integration behind a completion label.
3. Transition authority belongs to the stage that owns that transition.

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
- `active -> review_ready`
- `review_ready -> complete`

Invalid:

- `planned -> complete`
- `active -> complete` without required review where applicable
- `blocked -> complete`

## Issue Transitions

Allowed:

- `draft -> planned`
- `planned -> ready`
- `ready -> in_progress`
- `in_progress -> review_ready`
- `review_ready -> done`
- `draft -> blocked`
- `planned -> blocked`
- `ready -> blocked`
- `in_progress -> blocked`
- `review_ready -> blocked`
- `blocked -> planned`
- `blocked -> ready`
- `review_ready -> in_progress`

Invalid:

- `planned -> done`
- `ready -> done`
- `in_progress -> done`
- any transition that bypasses `review_ready`

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
