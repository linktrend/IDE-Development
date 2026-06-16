---
proof_id: "<proof-id>"
subject_type: "issue"
subject_id: "<issue-id>"
status: "draft"
criteria_evidence:
  - criterion: "<criterion>"
    evidence: "<artifact, observation, or state change>"
artifacts:
  - "<artifact path or identifier>"
verification_summary:
  - "<verification statement>"
optional_fields:
  commands_run:
    - "<command or action>"
  observations:
    - "<observation>"
  failures:
    - "<failure>"
  open_gaps:
    - "<remaining gap>"
  trace_refs:
    - "<trace or log reference>"
  notes:
    - "<note>"
---

# Proof

## Subject

Describe the issue, phase, module, or program this proof applies to.

## Criteria To Evidence Map

- criterion:
  evidence:

## Artifacts

- ...

## Verification Summary

- ...

## Failures Or Gaps

- ...

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
