---
proof_id: "SESSION-201-PROOF"
subject_type: "issue"
subject_id: "SESSION-201"
status: "complete"
criteria_evidence:
  - criterion: "the failing refresh condition is stated concretely"
    evidence: "ISSUE.md states that active sessions are logged out after refresh because expiry is checked against stale client state."
  - criterion: "the corrected behavior prevents premature logout"
    evidence: "The issue and module artifacts define that refreshed state must use the current expiry, preventing premature logout."
  - criterion: "review confirms the evidence closes the defect"
    evidence: "REVIEW.md cites this proof and issues a pass verdict."
artifacts:
  - ".cursor/examples/EXAMPLE-BUGFIX/ISSUE.md"
  - ".cursor/examples/EXAMPLE-BUGFIX/REVIEW.md"
  - ".cursor/examples/EXAMPLE-BUGFIX/INTEGRATION.md"
verification_summary:
  - "the defect is represented with before/after evidence rather than narrative only"
optional_fields:
  commands_run:
    - "execute-issue"
  observations:
    - "bugfix proof remains compact when it focuses on symptom, correction, and reviewability"
---

# Proof

## Subject

Issue `SESSION-201`.

## Criteria To Evidence Map

- criterion: failing behavior is explicit
  evidence: the issue objective and acceptance criteria state the stale-expiry symptom
- criterion: corrected behavior is explicit
  evidence: the issue describes the expected result after refresh
- criterion: closure is reviewable
  evidence: `REVIEW.md` references this proof directly

## Artifacts

- `ISSUE.md`
- `REVIEW.md`
- `INTEGRATION.md`

## Verification Summary

- the bug is described concretely
- the fixed behavior is described concretely
- closure is reviewable and integrated

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
