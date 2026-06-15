# Product Intent

This is a pre-program validation artifact.

Use it before `PROGRAM.md` to decide whether an idea, request, or objective should become an executable program at all.

**Program ID:** `session-refresh-bugfix-program`  
**Status:** `approved`  
**Last Updated:** `2026-06-15`  
**Verdict:** `pass`  
**Eligible For Program Creation:** `true`

## Objective

Resolve a defect where active sessions are incorrectly logged out after refresh because expiry is evaluated against stale client state.

## Scope

### In Scope

- reproduce the defect behavior as an artifact-level example
- define the corrected behavior
- show the proof and review expectations for a bugfix

### Out of Scope

- broader session redesign
- analytics instrumentation

## Success Criteria

- [x] the defect is specific and reproducible
- [x] the work can be contained in one module
- [x] proof can distinguish pre-fix vs post-fix behavior

## Constraints

- keep the example implementation-free
- favor reproduction and validation evidence over narrative

## Verdict

- **Verdict:** `pass`
- **Eligible For Program Creation:** `true`

### Required Changes Before Program

- none

### Blocking Questions

- none

### Rationale

- the bugfix is bounded
- the lifecycle differs from the feature example because proof centers on defect resolution

## Approval

| Item | Status | Date |
|------|--------|------|
| Finished-state narrative | approved | 2026-06-15 |
| Intent document | approved | 2026-06-15 |

## Relationship To PROGRAM.md

- `INTENT.md` exists before `PROGRAM.md`
- `INTENT.md` evaluates whether work should become a program
- `PROGRAM.md` defines executable structure after intent is accepted
- a program should normally be created only when `INTENT.md` has verdict `pass` and `Eligible For Program Creation` is `true`, unless a human explicitly overrides

## Progressive Disclosure

Read next:

1. `PROGRAM.md`
2. then the single bugfix module
