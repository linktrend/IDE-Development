# Ready States

## Purpose

This document defines the conditions under which a work unit is ready to enter the next stage.

## Universal Readiness Rule

Readiness is computed, not declared.

A work unit is ready only when its required inputs, dependencies, decisions, and upstream states are satisfied.

## Intent Readiness

`INTENT.md` is ready for review when:

- objective is explicit
- scope exists
- constraints exist
- a go or no-go decision can be made

## Program Readiness

`PROGRAM.md` is ready to become active when:

- intent has been accepted or explicitly overridden
- modules are defined
- program definition of done exists
- top-level constraints are explicit

## Module Readiness

`MODULE.md` is ready to become active when:

- parent program exists
- phases or executable issue paths exist
- module definition of done exists
- module scope is decomposed far enough to produce issues

## Phase Readiness

`PHASE.md` is ready to become active when:

- issues are defined
- local entry conditions are satisfied
- phase boundaries are coherent

## Issue Readiness

`ISSUE.md` is ready when:

- dependencies are satisfied
- scope is bounded
- required inputs exist
- acceptance criteria are testable
- no unresolved blocker remains

## Proof Readiness

`PROOF.md` is ready for review when:

- evidence is mapped to criteria
- evidence is concrete enough to evaluate
- major gaps are either resolved or explicitly recorded

## Review Readiness

`REVIEW.md` is ready to be produced when:

- a reviewable subject exists
- proof exists
- applicable criteria are clear

## Integration Readiness

`INTEGRATION.md` is ready to be produced when:

- review verdict is `pass`
- integration scope is understood
- no unresolved integration blocker prevents progression

## Ownership Rule

The upstream producer prepares readiness conditions.

The downstream consumer validates them.

## Read Next

1. `BLOCKED-STATES.md`
2. `TERMINAL-STATES.md`
