# Execution Loop

## Purpose

This document defines the human-driven runtime loop for carrying out doctrine-compliant execution.

## Entry Scope

The runtime may begin from:

- a program request
- a module request
- a phase request
- a single issue request

Even when the request starts above issue level, execution still proceeds through issues.

## Standard Loop

1. Load the relevant index and doctrine.
2. Load the target artifact.
3. Reduce the target scope to an issue graph.
4. Compute which issues are currently ready.
5. Select one or more ready issues.
6. Assign each selected issue to an available resource.
7. Execute the issue within declared scope.
8. Produce or update proof.
9. Move the issue to `review_ready`.
10. Perform independent review.
11. If review passes, integrate the work.
12. Mark the issue `done` only after integration succeeds.
13. Recompute downstream readiness.
14. Continue until the target scope is complete or genuinely blocked.

## Scope Reduction

### Program Request

For a program request, the runtime:

- loads the program artifact
- identifies the target modules
- reduces active work to module issue graphs

### Module Request

For a module request, the runtime:

- loads the module artifact
- inspects its phases
- enumerates issues under those phases

### Phase Request

For a phase request, the runtime:

- loads the phase artifact
- enumerates its issues
- computes issue-level readiness inside that phase

### Issue Request

For an issue request, the runtime:

- loads the issue artifact
- verifies readiness
- executes only that issue

## Concurrency In The Loop

The loop may select more than one issue only when:

- all selected issues are independently ready
- none depends on another selected issue's not-yet-integrated output
- shared-scope risk is acceptable

Concurrency is optional, not mandatory.

## Completion Conditions

### Issue Complete

An issue is complete only after:

- proof
- passing review
- successful integration

### Phase Complete

A phase is complete when:

- its required issues are done
- its local completion criteria are satisfied
- any explicitly required phase review is complete

### Module Complete

A module is complete when:

- required child issues are done
- phase criteria are satisfied
- module definition of done is satisfied
- required module review is complete
- required module-level integration effects are recorded

### Program Complete

A program is complete when:

- required modules are complete
- program definition of done is satisfied
- required program or release review is complete

## Genuine Block Condition

The runtime should stop only when no executable issue remains and the unresolved work depends on:

- unsatisfied dependencies
- unresolved decisions
- failed reviews awaiting rework
- failed integration awaiting correction
- unavailable mandatory inputs

Mere difficulty, uncertainty, or incomplete work is not by itself a genuine block.

## Read Next

1. `DEPENDENCY-RESOLUTION.md`
2. `STATE-MODEL.md`
