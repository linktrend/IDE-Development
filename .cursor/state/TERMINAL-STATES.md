# Terminal States

## Purpose

This document defines terminal completion and terminal non-completion states for work units.

## Universal Terminal Rule

Work may stop only when it is either:

- complete under the required contract and workflow rules
- genuinely unable to continue without external resolution

## Terminal Completion States

### Intent

Terminal completion:

- `accepted`
- `rejected`

`deferred` is not terminal completion.

### Program, Module, Phase

Terminal completion:

- `complete`

### Issue

Terminal completion:

- `done`

### Proof

Proof has no standalone terminal completion outside its consumer relationship.

Its terminal useful state is:

- `sufficient`

### Review

Review terminal states:

- `pass`
- `fail`
- `blocked`

### Integration

Integration terminal useful state:

- `integrated`

## Terminal Non-Completion States

Terminal non-completion applies when work stops without being complete because:

- intent is rejected
- work remains genuinely blocked
- human governance decides not to continue

## Stop Conditions By Layer

### Runtime Stop

The runtime may stop when:

- the requested scope is complete
- no executable issue remains and genuine blockers remain

### Workflow Stop

A workflow may stop when:

- exit conditions are satisfied
- progression is invalid or blocked and cannot be resolved inside the workflow

### Command Stop

A command may stop when:

- its scoped objective is complete
- it hands off to the next required workflow stage
- it reaches a genuine blocked condition

## Ownership Rule

- the current controlling stage determines whether terminal conditions are met
- review and integration gates still control completion legitimacy

## Invariants

1. Terminal completion never bypasses required lower-level gates.
2. Terminal blocked stop must preserve a visible blocker trail.
3. Runtime stop and completion are not synonymous.

## Read Next

1. `STATE-MODEL.md`
2. `STATE-TRANSITIONS.md`
