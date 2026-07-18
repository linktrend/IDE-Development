# Module Gate — `<module-id>`

## Module

- ID: `intake_and_definition` | `assembly_planning` | `execution` | `verification_and_hardening` | `library_contribution` | `shipment`
- Path: `modules/<nn>-<slug>/`

## Verdict

- `pass` | `rejected` | _(pending)_
- Severity (on rejection): `critical` | `high` | `medium` | `low`
- Attempt: `<n>` of `gateRepairBudget` (default 3)

## Checks

| Check | Result | Evidence |
|-------|--------|----------|
| Predecessor module complete | | |
| Required outputs present | | |
| Independent reviewer (when required) | | |
| Principal decision (when required) | | |
| Technical PRD acceptance criteria (Module 4) | | |

## Principal decision (Modules 1 and 6)

- Recorded: yes/no
- Decision: approved | rejected | deferred
- Reason / reference:

## Repair

On rejection, automatically re-drive repair work up to the budget. On exhaustion, set blocked and brief the Principal.

## Blockers

-

## Machine-readable companion

Prefer `gate.json` alongside this document for the validator:

```json
{
  "moduleId": "<module-id>",
  "verdict": null,
  "severity": null,
  "attempt": 0,
  "unmetTechnicalPrdAcceptanceCriteria": [],
  "principalApprovalRecorded": false,
  "notes": ""
}
```
