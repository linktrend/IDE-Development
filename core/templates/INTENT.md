# Product Intent

This is a pre-program validation artifact.

Use it before `PROGRAM.md` to decide whether an idea, request, or objective should become an executable program at all.

**Program ID:** `<program-id>`  
**Status:** `draft | approved`  
**Last Updated:** `YYYY-MM-DD`
**Verdict:** `pass | revise | reject | defer`
**Eligible For Program Creation:** `true | false`

## Objective

Describe what development must accomplish when the work is complete. Focus on behavior, outcomes, and user experience rather than file trees.

## Scope

### In Scope

- ...

### Out of Scope

- ...

## Success Criteria

- [ ] ...
- [ ] ...

## Constraints

- applicable rules
- security or compliance boundaries
- environment or integration assumptions

## Verdict

- **Verdict:** `pass | revise | reject | defer`
- **Eligible For Program Creation:** `true | false`

### Required Changes Before Program

- ...

### Blocking Questions

- ...

### Rationale

- ...

## Approval

| Item | Status | Date |
|------|--------|------|
| Finished-state narrative | pending / approved | |
| Intent document | pending / approved | |

## Relationship To PROGRAM.md

- `INTENT.md` exists before `PROGRAM.md`
- `INTENT.md` evaluates whether work should become a program
- `PROGRAM.md` defines executable structure after intent is accepted
- a program should normally be created only when `INTENT.md` has verdict `pass` and `Eligible For Program Creation` is `true`, unless a human explicitly overrides

## Progressive Disclosure

Read next:

1. `PROGRAM.md` only if the intent is accepted
2. otherwise, only the minimum review or decision artifacts needed to resolve the go or no-go decision
