# Issue Bootstrap

This document defines how an issue starts safely as the atomic unit of execution.

## Purpose

Ensure issue work begins with explicit readiness, clear acceptance criteria, and known proof, review, and integration expectations.

## Entry Conditions

- an `ISSUE.md` exists
- the issue objective is singular and concrete
- dependencies are explicit
- acceptance criteria are testable
- proof, review, and integration requirements are stated

## Required Artifacts

- `ISSUE.md`

Required during and after execution:

- `PROOF.md`
- `REVIEW.md`
- `INTEGRATION.md`

## Startup Sequence

1. read `.cursor/commands/execute-issue.md`
2. read `.cursor/templates/ISSUE.md`
3. verify `depends_on`
4. compute readiness
5. confirm no blocking questions prevent execution
6. execute the issue
7. produce proof
8. hand off to review
9. integrate only after a passing review

## Startup Responsibilities

- refuse to start an issue that is not actually ready
- preserve the mandatory state path through `review_ready`
- define proof before claiming completion
- distinguish missing evidence from blocked work

## Readiness Rule

An issue may start only when:

- all dependencies are satisfied
- no blocking questions remain unresolved
- required inputs are available
- scope is clear enough to prevent multi-issue sprawl

## Runtime-Specific Startup Flows

### Human

- inspect the issue for objective, scope, dependencies, and criteria
- start only when readiness is explicit

### Cursor

- route through `execute-issue`
- use issue, proof, review, and integration templates only as needed by the lifecycle stage

### Codex

- route through `execute-issue`
- stop if readiness cannot be justified from artifacts

### Claude

- use the same readiness and completion rules
- do not bypass review or integration

## Shutdown Responsibilities

Before ending issue work:

- leave the issue in a real state
- if work is incomplete, record whether it is still `in_progress` or genuinely `blocked`
- if execution is complete, leave proof and review state obvious
