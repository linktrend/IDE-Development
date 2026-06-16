---
proof_id: "NOTIFY-101-PROOF"
subject_type: "issue"
subject_id: "NOTIFY-101"
status: "complete"
criteria_evidence:
  - criterion: "notification categories are clearly defined"
    evidence: "ISSUE.md states that category definition is part of scope and expected outputs."
  - criterion: "settings behavior is clear enough for a runtime or human implementer"
    evidence: "ISSUE.md and MODULE.md define the behavior boundary as user-facing controls in one settings surface."
  - criterion: "proof, review, and integration make module roll-up safe"
    evidence: "REVIEW.md passes the issue and INTEGRATION.md records that the module may treat the issue as satisfied."
artifacts:
  - ".cursor/examples/EXAMPLE-MODULE/ISSUE.md"
  - ".cursor/examples/EXAMPLE-MODULE/REVIEW.md"
  - ".cursor/examples/EXAMPLE-MODULE/INTEGRATION.md"
verification_summary:
  - "the issue is ready, executed, reviewed, and integrated"
  - "the module now has evidence-backed grounds for completion"
optional_fields:
  commands_run:
    - "complete-module"
    - "execute-issue"
    - "review-issue"
    - "integrate-issue"
  observations:
    - "module execution becomes understandable when the issue clearly references workflow, contracts, and state"
---

# Proof

## Subject

Issue `NOTIFY-101`.

## Criteria To Evidence Map

- criterion: categories are defined
  evidence: scope and outputs in `ISSUE.md`
- criterion: settings behavior is defined
  evidence: module objective and issue objective align on one settings surface
- criterion: roll-up is safe
  evidence: review and integration artifacts exist and are passing

## Artifacts

- `ISSUE.md`
- `REVIEW.md`
- `INTEGRATION.md`

## Verification Summary

- the atomic issue is complete
- the module can rely on the integrated result

## Failures Or Gaps

- none

## Gate Guidance

Proof must be non-vacuous. Every completion claim should be traceable to evidence.

## Verbosity Guidance

- optional fields may be omitted when irrelevant
- do not fill sections with placeholder text
- prefer references over duplicated narrative
- keep proof concrete and concise

## Progressive Disclosure

Read next:

1. the subject artifact
2. this proof artifact
3. the review artifact that evaluates this proof
