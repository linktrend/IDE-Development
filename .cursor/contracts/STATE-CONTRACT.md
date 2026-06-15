# State Contract

## Purpose

This document defines valid state changes, ownership of state progression, and state invariants across the lifecycle.

## Contract Responsibilities

The state contract governs:

- allowed transitions
- transition prerequisites
- transition ownership
- invalid state jumps

## Universal State Rule

No work unit may advance to a downstream-complete state unless its required upstream contract obligations are already satisfied.

## Issue State Contract

Normative issue states:

- `draft`
- `planned`
- `blocked`
- `ready`
- `in_progress`
- `review_ready`
- `done`

Allowed progression:

- `draft -> planned`
- `planned -> ready`
- `ready -> in_progress`
- `in_progress -> review_ready`
- `review_ready -> done`

Allowed recovery:

- `blocked -> planned`
- `blocked -> ready`
- `review_ready -> in_progress`

Invalid progression:

- `in_progress -> done`
- `ready -> done`
- `planned -> done`
- any progression that bypasses review or integration

## Higher-Level State Contract

Programs, modules, and phases may maintain their own status fields, but their completion is computed from:

- child completion
- local completion criteria
- required review and integration obligations

They must not override issue-level state semantics.

## Ownership Rule

- execution owns movement to `review_ready`
- review owns the review verdict
- integration owns the final progression to dependency-satisfying completion
- higher-level workflows own roll-up interpretation, not issue state bypass

## Invariants

1. `done` always implies proof, review, and integration are complete.
2. `review_ready` always implies proof exists.
3. `blocked` always implies a visible reason.
4. No downstream issue may treat non-integrated work as dependency-satisfying.

## Read Next

1. `SIDE-EFFECT-CONTRACT.md`
2. `VALIDATION-CONTRACT.md`
