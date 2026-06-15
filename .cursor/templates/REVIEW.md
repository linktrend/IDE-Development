---
review_id: "<review-id>"
subject_type: "issue"
subject_id: "<issue-id>"
verdict: "pending"
findings:
  - "<finding>"
evidence_basis:
  - "<proof or artifact reference>"
next_action: "<pass, fail, or blocked outcome>"
optional_fields:
  severity: "<severity>"
  warnings:
    - "<warning>"
  waivers:
    - "<waiver>"
  review_notes:
    - "<note>"
---

# Review

## Subject

Describe the work under review.

## Findings

- ...

## Evidence Basis

- ...

## Verdict

Use one of:

- `pending`
- `pass`
- `fail`
- `blocked`

## Next Action

State clearly whether the work proceeds to integration, returns for rework, or is blocked pending resolution.

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
