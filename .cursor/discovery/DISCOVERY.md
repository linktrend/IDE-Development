# Discovery

## Purpose

Discovery is the optional pre-intent layer for greenfield or ambiguous work.

Its job is to reduce uncertainty enough to write a defensible `INTENT.md` without inventing requirements.

## Position In The Operating Model

Optional flow:

`DISCOVERY -> INTERVIEW -> INTENT -> PROGRAM -> MODULE -> PHASE -> ISSUE -> PROOF -> REVIEW -> INTEGRATION`

Canonical execution flow remains unchanged after intent:

`INTENT -> PROGRAM -> MODULE -> PHASE -> ISSUE -> PROOF -> REVIEW -> INTEGRATION`

## When Discovery Is Required

Use discovery when at least one of these is true:

- the project is completely new
- the request is materially under-specified
- the user has not identified who the work is for, why it matters, or what success means
- major constraints are unknown
- multiple plausible interpretations exist and choosing one would be guesswork

## When Discovery Is Optional

Use discovery if it would materially reduce risk, but skip it if intent can already be written responsibly.

Typical optional cases:

- early product ideation
- rough ideas that are promising but still fuzzy
- larger feature requests where user value and scope are not yet clear

## When Discovery Should Be Skipped

Skip discovery when the ask is already concrete enough for `INTENT.md` or `ISSUE.md`.

Typical skip cases:

- bug fixes
- existing modules with clear scope
- routine work
- small self-contained features
- mechanical operations

## Required Output

Discovery ends by producing or enabling a strong `INTENT.md`.

Discovery does not produce a substitute artifact.

## Entry And Exit Conditions

Entry:

- the operator believes the ask is ambiguous or greenfield
- a live, responsive human is available if interview is needed

Exit:

- uncertainty is reduced enough to write `INTENT.md`
- the operator can state the objective, scope, constraints, and success conditions without guessing

## Progressive Disclosure

Read next:

1. `INTERVIEW.md` if questioning is needed
2. `INTENT.md` once confidence is high enough
