# Side-Effect Contract

## Purpose

This document defines the allowed, required, and forbidden side effects associated with valid handoffs.

## Contract Responsibilities

The side-effect contract governs:

- artifact creation and updates
- state changes
- readiness recomputation
- higher-level roll-up

## Universal Side-Effect Rule

A side effect is valid only if it is:

- traceable to the current stage
- permitted by the doctrine
- visible in artifacts
- consistent with state and dependency rules

## Allowed Side Effects

Allowed side effects include:

- creating or updating the expected artifact for the current stage
- progressing state when prerequisites are met
- recording blockers, failures, or review findings
- recomputing downstream readiness after integration
- updating higher-level completion status based on child completion

## Required Side Effects

### Issue Execution

Must produce:

- proof or explicit blocker trail

### Review

Must produce:

- explicit verdict
- findings
- next action

### Integration

Must produce:

- final state recording
- downstream readiness implications

## Forbidden Side Effects

Forbidden side effects include:

- hidden dependencies
- hidden completion claims
- silent state changes
- downstream dependency satisfaction before integration
- agent-based sequencing rules that override artifact-based control

## Ownership Rule

The acting stage owns the side effects it causes.

The next consuming stage owns rejection of side effects that are invalid, missing, or contradictory.

## Invariants

1. Every required side effect must be artifact-visible.
2. No side effect may contradict doctrine.
3. No side effect may bypass review or integration gates.

## Read Next

1. `VALIDATION-CONTRACT.md`
