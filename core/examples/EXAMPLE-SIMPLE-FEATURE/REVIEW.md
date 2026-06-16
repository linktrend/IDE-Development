---
review_id: "PROFILE-001-REVIEW"
subject_type: "issue"
subject_id: "PROFILE-001"
verdict: "pass"
findings:
  - "acceptance criteria are explicitly mapped to evidence"
  - "no unsupported completion claims remain"
evidence_basis:
  - ".cursor/examples/EXAMPLE-SIMPLE-FEATURE/PROOF.md"
  - ".cursor/examples/EXAMPLE-SIMPLE-FEATURE/ISSUE.md"
next_action: "pass to integration"
optional_fields:
  review_notes:
    - "this example demonstrates the minimum independent review handoff"
---

# Review

## Subject

Issue `PROFILE-001`.

## Findings

- proof is concrete and traceable
- the issue state model is respected

## Evidence Basis

- `PROOF.md`
- `ISSUE.md`

## Verdict

Use one of:

- `pending`
- `pass`
- `fail`
- `blocked`

Verdict for this example: `pass`

## Next Action

Proceed to integration and allow module roll-up to advance.

## Review Scope

Issue review is mandatory.
Module review is mandatory.
Program or release review is mandatory.
Phase review is optional unless explicitly required by a phase or module artifact.

## Gate Guidance

Review must reject vacuous completion. Findings must refer back to actual proof or observed outputs.

## Verbosity Guidance

- optional fields may be omitted when irrelevant
- do not fill sections with placeholder text
- prefer references over duplicated narrative
- findings should be complete but concise

## Progressive Disclosure

Read next:

1. the subject artifact
2. the proof artifact
3. the integration artifact only if verdict is `pass`
