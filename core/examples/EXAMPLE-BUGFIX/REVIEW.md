---
review_id: "SESSION-201-REVIEW"
subject_type: "issue"
subject_id: "SESSION-201"
verdict: "pass"
findings:
  - "proof distinguishes pre-fix failure from corrected post-fix behavior"
  - "the defect closure claim is specific enough for downstream reliance"
evidence_basis:
  - ".cursor/examples/EXAMPLE-BUGFIX/PROOF.md"
next_action: "pass to integration"
---

# Review

## Subject

Issue `SESSION-201`.

## Findings

- the proof is defect-oriented rather than aspirational
- the closure claim is supported

## Evidence Basis

- `PROOF.md`

## Verdict

Use one of:

- `pending`
- `pass`
- `fail`
- `blocked`

Verdict for this example: `pass`

## Next Action

Proceed to integration and allow downstream work to treat the defect as closed.

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
