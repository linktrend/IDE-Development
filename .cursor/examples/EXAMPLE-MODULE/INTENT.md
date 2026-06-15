# Product Intent

This is a pre-program validation artifact.

Use it before `PROGRAM.md` to decide whether an idea, request, or objective should become an executable program at all.

**Program ID:** `notification-preferences-program`  
**Status:** `approved`  
**Last Updated:** `2026-06-15`  
**Verdict:** `pass`  
**Eligible For Program Creation:** `true`

## Objective

Create a notification preferences capability that lets users control email and in-app notification categories from one settings surface.

## Scope

### In Scope

- define the notification preferences program
- represent one module-level slice end to end
- make module completion and roll-up explicit

### Out of Scope

- delivery infrastructure changes
- push notification transport

## Success Criteria

- [x] the objective is specific enough to become a program
- [x] one module can illustrate module-level execution
- [x] command, workflow, contract, and state participation can be shown without code

## Constraints

- keep the example implementation-free
- focus on module execution rather than exhaustive decomposition

## Verdict

- **Verdict:** `pass`
- **Eligible For Program Creation:** `true`

### Required Changes Before Program

- none

### Blocking Questions

- none

### Rationale

- this example can demonstrate the user command "Complete this module" directly

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
2. then `MODULE.md`
