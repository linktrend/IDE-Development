# Module Gate — `<module-id>`

## Module

- ID: `intake_and_definition` | `assembly_planning` | `execution` | `verification_and_hardening` | `library_contribution` | `shipment`
- Path: `modules/<nn>-<slug>/`

## Verdict

- `pass` | `rejected` | _(pending)_

## Checks

| Check | Result | Evidence |
|-------|--------|----------|
| Predecessor module complete | | |
| Required outputs present | | |
| Independent reviewer (when required) | | |
| Principal decision (when required) | | |

## Principal decision (Modules 1 and 6)

- Recorded: yes/no
- Decision: approved | rejected | deferred
- Reason / reference:

## Blockers

-

## Machine-readable companion

Prefer `gate.json` alongside this document for the validator:

```json
{
  "moduleId": "<module-id>",
  "verdict": null,
  "notes": ""
}
```
