# Failure States

## Purpose

This document defines how failure is represented without introducing implementation-specific or automation-specific semantics.

## Universal Failure Rule

Failure is represented through explicit blocked, insufficient, or failed outcome states rather than through hidden implicit assumptions.

## Failure Representation By Work Unit

### Intent

Failure appears as:

- `rejected`
- `deferred`

### Program, Module, Phase

Failure appears as:

- `blocked`
- inability to reach required review-ready or complete conditions

### Issue

Failure appears as:

- `blocked`
- return from `review_ready` to `in_progress`

### Proof

Failure appears as:

- `insufficient`

### Review

Failure appears as:

- `fail`
- `blocked`

### Integration

Failure appears as:

- `blocked`

## Failure Handling Rules

1. Failure must remain visible in artifacts.
2. Failure must not be collapsed into completion labels.
3. Failure may lead to retry, rework, deferment, or stop conditions depending on scope.

## Ownership Rule

- the stage experiencing failure records it
- the next controlling stage decides whether work retries, reworks, blocks, or terminates

## Read Next

1. `RETRY-STATES.md`
2. `TERMINAL-STATES.md`
