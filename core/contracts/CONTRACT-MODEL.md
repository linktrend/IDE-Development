# Contract Model

## Purpose

The contract layer defines the rules that govern handoffs between work units, workflow stages, and runtimes.

It ensures that progression through the system is:

- explicit
- verifiable
- stage-bounded
- runtime-independent

## Contract Responsibilities

The contract layer must:

1. define producer and consumer relationships
2. define required inputs and required outputs
3. define valid state changes
4. define expected and forbidden side effects
5. define ownership boundaries
6. define invariants that must remain true across handoffs

## Contract Boundary

The contract layer does not:

- replace doctrine
- replace runtime behavior
- replace workflows
- implement automation

It governs the quality and validity of handoffs between those layers.

## Universal Contract Principle

Every work unit is governed by the same universal contract questions:

1. Who produces it?
2. Who consumes it?
3. What must exist before it can be consumed?
4. What must exist after it is produced?
5. What state change does it authorize?
6. What side effects are allowed or required?
7. What invariants must remain true?

## Work Units Covered

Contracts apply to:

- `INTENT.md`
- `PROGRAM.md`
- `MODULE.md`
- `PHASE.md`
- `ISSUE.md`
- `PROOF.md`
- `REVIEW.md`
- `INTEGRATION.md`

## Producer And Consumer Model

### Intent

- producer: planner and human decision-makers
- consumer: program workflow

### Program

- producer: planning workflow
- consumer: module workflow

### Module

- producer: program and module planning
- consumer: phase and issue decomposition, runtime execution

### Phase

- producer: module workflow
- consumer: issue workflow and module roll-up

### Issue

- producer: module planning and decomposition
- consumer: runtime execution

### Proof

- producer: issue execution
- consumer: review workflow

### Review

- producer: review workflow
- consumer: integration workflow or rework path

### Integration

- producer: integration workflow
- consumer: downstream issue readiness, higher-level roll-up

## Ownership Rules

- a producer owns creation quality for the current handoff
- a consumer owns acceptance or rejection of the handoff
- no producer may self-authorize final acceptance where independent review is required
- ownership is stage-local, not global to a single role

## Invariants

The following must always remain true:

1. Issue remains the atomic executable unit.
2. Dependencies determine sequencing.
3. Proof precedes review.
4. Review precedes integration.
5. Integration precedes dependency satisfaction for downstream issues.
6. Agents are resources, not the control structure.
7. Higher-level artifacts do not bypass issue-level execution semantics.

## Read Next

1. `INPUT-CONTRACT.md`
2. `OUTPUT-CONTRACT.md`
3. `STATE-CONTRACT.md`
4. `SIDE-EFFECT-CONTRACT.md`
5. `VALIDATION-CONTRACT.md`
