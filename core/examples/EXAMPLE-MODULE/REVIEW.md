---
review_id: "NOTIFY-101-REVIEW"
subject_type: "issue"
subject_id: "NOTIFY-101"
verdict: "pass"
findings:
  - "the issue is clearly atomic"
  - "the completion claim is supported by explicit proof and integration handoff"
evidence_basis:
  - ".cursor/examples/EXAMPLE-MODULE/PROOF.md"
  - ".cursor/examples/EXAMPLE-MODULE/ISSUE.md"
next_action: "pass to integration and module roll-up"
optional_fields:
  review_notes:
    - "this example is the clearest reference for the user command 'Complete this module'"
---

# Review

## Subject

Issue `NOTIFY-101`.

## Findings

- readiness, execution, proof, and integration are all explicit
- the module can safely consume this issue as complete

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

Proceed to integration and then evaluate module completion.

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
