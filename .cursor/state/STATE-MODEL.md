# State Model

## Purpose

This document defines the canonical execution state system shared by:

- commands
- workflows
- runtime
- contracts
- agents

## State Design Principles

1. State must be artifact-visible.
2. State must be runtime-independent.
3. State must preserve issue as the atomic executable unit.
4. State must not let higher-level artifacts bypass lower-level gates.
5. State must distinguish readiness, blockage, failure, retry, and terminal completion.

## Canonical State Vocabulary

### Intent States

- `draft`
- `under_review`
- `accepted`
- `rejected`
- `deferred`

### Program States

- `draft`
- `planned`
- `active`
- `blocked`
- `review_ready`
- `complete`

### Module States

- `draft`
- `planned`
- `active`
- `blocked`
- `review_ready`
- `complete`

### Phase States

- `draft`
- `planned`
- `active`
- `blocked`
- `review_ready`
- `complete`

### Issue States

- `draft`
- `planned`
- `blocked`
- `ready`
- `in_progress`
- `review_ready`
- `done`

### Proof States

- `draft`
- `collecting`
- `sufficient`
- `insufficient`

### Review States

- `pending`
- `pass`
- `fail`
- `blocked`

### Integration States

- `pending`
- `integrated`
- `blocked`

## State Ownership

- planning owns formation states such as `draft` and `planned`
- execution owns `in_progress`
- proof production owns proof sufficiency state
- review owns review verdict state
- integration owns integration completion state
- higher-level workflows own roll-up interpretation for program, module, and phase completion

## Shared Interpretation Rules

- `active` means a higher-level work unit contains executable or currently executing child work
- `review_ready` means a work unit has met its execution obligations and is waiting for required review
- `complete` means all required lower-level and local obligations are satisfied
- `blocked` means work cannot proceed without explicit resolution

## State Invariants

1. Issue remains the only atomic execution state machine.
2. `done` for issue always implies proof, review, and integration are complete.
3. `complete` for higher-level artifacts never weakens issue-level completion rules.
4. `pass` in review never implies integration already happened.
5. `integrated` never implies release-ready by itself.

## Read Next

1. `STATE-TRANSITIONS.md`
2. `READY-STATES.md`
3. `TERMINAL-STATES.md`
