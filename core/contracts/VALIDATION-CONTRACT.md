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

Gates are **fail-closed** (Law 16). Warn-only progression is forbidden. For application Programs, Module transitions must pass `.cursor/runtime/validate-application-pipeline.mjs` before state is written. Self-report is never proof.

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

## Repair routing (LiNKdeveloper reference)

When validation fails during review or integration, do not silently retry. Stage 2 LiNKdeveloper reference docs (`EXECUTOR_ROUTING_POLICY.md`, validation repair routing in `VALIDATION_RULEBOOK`) describe automatic repair-issue creation: a new `ISSUE.md` with `depends_on` pointing at the failing proof, preserving Canonical Law 11 (blocked work leaves a trail).

Stage 1 applies this concept through Layer 1 commands and `intelligent-routing` — return failed work to `execute-issue` or spawn an explicit repair issue with artifact trail. Hybrid gstack `/health` may assist diagnosis; repair routing remains Layer 1 governed. See `docs/HYBRID-SKILLS-REGISTRY.md` for hybrid vs Layer 1 boundaries. No LiNKdev runtime dependency.

## Read Next

1. `CONTRACT-MODEL.md`
2. `INPUT-CONTRACT.md`
3. `OUTPUT-CONTRACT.md`
4. `STATE-CONTRACT.md`
5. `SIDE-EFFECT-CONTRACT.md`
