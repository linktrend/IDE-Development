# Execution Map

## Purpose

This document traces how work moves through the assembled `.cursor` system.

## Entry Path

Typical entry:

1. user request
2. command or direct artifact selection
3. doctrine loading
4. artifact loading
5. runtime loop
6. workflow transitions
7. contract validation
8. state progression
9. higher-level completion roll-up

## Lifecycle Map

`Intent -> Program -> Module -> Phase -> Issue -> Proof -> Review -> Integration -> Complete`

## Layer Participation By Stage

### Intent

- doctrine defines pre-program rules
- artifacts define `INTENT.md`
- workflows move intent toward program formation
- contracts validate the handoff into program work
- state tracks intent outcome

### Program

- artifacts define `PROGRAM.md`
- agents may plan or clarify scope
- commands may initiate planning
- workflows move program scope toward module work
- state tracks whether program work is draft, planned, active, blocked, or complete

### Module And Phase

- artifacts define module and phase boundaries
- runtime and workflows reduce scope to issues
- contracts validate decomposition quality
- state tracks higher-level progression

### Issue

- issue is the atomic executable unit
- runtime computes readiness
- workflows govern execution path
- contracts validate handoffs
- state governs progression to `done`

### Proof, Review, Integration

- artifacts capture evidence, judgment, and incorporation
- workflows define progression
- contracts validate legality of the handoff
- state tracks sufficiency, pass/fail, and integration status

## Stop Conditions

The assembled system permits stopping only when:

- requested scope is complete under doctrine, workflow, contract, and state rules
- or no executable work remains and genuine blockers are explicit

## Read Next

1. `RESPONSIBILITY-MATRIX.md`
2. `COMPATIBILITY-MATRIX.md`
