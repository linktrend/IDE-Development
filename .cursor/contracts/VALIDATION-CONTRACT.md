# Validation Contract

## Purpose

This document defines how contract compliance is judged across handoffs.

## Contract Responsibilities

The validation contract governs:

- handoff acceptance
- invariant checking
- ownership rules for acceptance or rejection
- minimum compliance expectations

## Validation Rule

A handoff is valid only when:

1. required inputs are present
2. required outputs are present
3. state progression is valid
4. side effects are allowed and visible
5. invariants remain true

## Producer And Consumer Validation Model

- the producer validates completeness before handoff
- the consumer validates acceptability at handoff
- review and integration stages perform especially strict validation because they control progression

## Work Unit Validation Requirements

### Intent

Must validate:

- the verdict is explicit
- program eligibility is explicit

### Program

Must validate:

- module structure exists
- constraints are explicit
- definition of done exists

### Module

Must validate:

- phases and/or issue references are explicit
- module definition of done exists

### Phase

Must validate:

- issue grouping is explicit
- completion criteria are explicit

### Issue

Must validate:

- scope is bounded
- dependencies are explicit
- acceptance is testable

### Proof

Must validate:

- evidence maps to criteria
- completion claims are non-vacuous

### Review

Must validate:

- proof sufficiency
- criteria satisfaction
- independence of judgment

### Integration

Must validate:

- review passed
- downstream effects are recorded
- completion state is legitimate

## Invariants

The following invariants must always hold:

1. Issue is the atomic executable unit.
2. Dependencies determine sequencing.
3. Proof precedes review.
4. Review precedes integration.
5. Integration precedes downstream dependency satisfaction.
6. Higher-level completion never weakens lower-level gate requirements.
7. Agents are resources, not the control structure.

## Remaining Ambiguity Rule

If a handoff cannot be validated confidently, the system should:

- reject progression
- record the ambiguity
- return the work to clarification, rework, or blocker resolution

## Read Next

1. `CONTRACT-MODEL.md`
2. `INPUT-CONTRACT.md`
3. `OUTPUT-CONTRACT.md`
4. `STATE-CONTRACT.md`
5. `SIDE-EFFECT-CONTRACT.md`
