---
proof_id: "PROFILE-001-PROOF"
subject_type: "issue"
subject_id: "PROFILE-001"
status: "complete"
criteria_evidence:
  - criterion: "the issue is shown as ready because it has no dependencies"
    evidence: "ISSUE.md declares an empty depends_on list and states that readiness is immediate after planning."
  - criterion: "execution moves to review_ready only after proof exists"
    evidence: "This proof artifact exists and the issue notes the required state path ending in review_ready before review."
  - criterion: "integration happens only after passing review"
    evidence: "REVIEW.md records verdict pass and INTEGRATION.md records integration after that verdict."
artifacts:
  - ".cursor/examples/EXAMPLE-SIMPLE-FEATURE/ISSUE.md"
  - ".cursor/examples/EXAMPLE-SIMPLE-FEATURE/REVIEW.md"
  - ".cursor/examples/EXAMPLE-SIMPLE-FEATURE/INTEGRATION.md"
verification_summary:
  - "the atomic issue lifecycle is complete and traceable"
  - "evidence is concrete enough for independent review"
optional_fields:
  commands_run:
    - "execute-issue"
  observations:
    - "a single-issue example removes dependency ambiguity and highlights mandatory gates"
---

# Proof

## Subject

Issue `PROFILE-001`.

## Criteria To Evidence Map

- criterion: the issue is immediately ready
  evidence: empty dependency list in `ISSUE.md`
- criterion: proof exists before review
  evidence: this artifact is referenced by `REVIEW.md`
- criterion: integration follows passing review
  evidence: `INTEGRATION.md` cites `REVIEW.md` as the gate input

## Artifacts

- `ISSUE.md`
- `REVIEW.md`
- `INTEGRATION.md`

## Verification Summary

- the issue lifecycle is complete
- the completion claim is evidence-backed

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
