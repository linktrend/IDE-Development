---
proof_id: "AUTH-004-proof-v1"
subject_type: "issue"
subject_id: "AUTH-004"
status: "insufficient"
criteria_evidence:
  - criterion: "login contract is explicit"
    evidence: "States that a login contract exists."
  - criterion: "signup contract is explicit"
    evidence: "No concrete signup contract details provided."
  - criterion: "contracts align with schema assumptions"
    evidence: "Alignment is asserted but not demonstrated."
artifacts:
  - ".cursor/pilots/authentication-module-smoke-test/modules/authentication/phases/implementation/issues/AUTH-004.md"
verification_summary:
  - "A vague statement claims login and signup API contracts were defined."
optional_fields:
  open_gaps:
    - "No explicit login request or response details"
    - "No explicit signup request or response details"
    - "No concrete schema alignment evidence"
  notes:
    - "Intentional insufficient proof for anti-incompletion testing."
---

# Proof

## Subject

AUTH-004 initial proof attempt.

## Criteria To Evidence Map

- criterion: login contract is explicit
  evidence: vague statement only
- criterion: signup contract is explicit
  evidence: missing
- criterion: contracts align with schema assumptions
  evidence: asserted but not shown

## Artifacts

- AUTH-004 issue artifact

## Verification Summary

- A vague completion claim exists, but concrete contract details do not.

## Failures Or Gaps

- insufficient evidence for both contracts
- insufficient evidence for schema alignment

## Gate Guidance

This proof is intentionally insufficient and should be rejected in review.

## Progressive Disclosure

Read next:

1. the subject artifact
2. this proof artifact
3. the review artifact that evaluates this proof
