# Retry States

## Purpose

This document defines when retries are allowed and how retry transitions preserve state history and ownership.

## Universal Retry Rule

Retry is permitted only when a previously blocking or failing condition has been addressed enough to justify re-entry into valid progression.

## Retry Triggers

Retry may follow:

- blocker resolution
- new evidence collection
- review finding remediation
- integration conflict resolution
- clarification of missing scope or decisions

## Retry Paths

### Intent

- `deferred -> under_review`

### Program, Module, Phase

- `blocked -> active`
- `blocked -> planned`

depending on whether execution can resume directly

### Issue

- `blocked -> planned`
- `blocked -> ready`
- `review_ready -> in_progress`

### Proof

- `insufficient -> collecting`

### Review

Review does not self-retry in place.

Instead:

- the subject re-enters execution or clarification
- a new review cycle begins from `pending`

### Integration

- `blocked -> pending`

## Retry Ownership

- the stage that resolves the underlying problem prepares the retry
- the downstream consumer validates whether retry conditions are now met

## Retry Invariants

1. Retry must not erase the prior failure trail.
2. Retry must not bypass review or integration.
3. Retry must be justified by changed conditions, not optimism alone.

## Read Next

1. `TERMINAL-STATES.md`
