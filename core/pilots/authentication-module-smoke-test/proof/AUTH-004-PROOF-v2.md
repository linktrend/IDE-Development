---
proof_id: "AUTH-004-proof-v2"
subject_type: "issue"
subject_id: "AUTH-004"
status: "accepted"
criteria_evidence:
  - criterion: "login contract is explicit"
    evidence: "Verification summary includes login request fields, success response, and failure conditions."
  - criterion: "signup contract is explicit"
    evidence: "Verification summary includes signup request fields, success response, and failure conditions."
  - criterion: "contracts align with schema assumptions"
    evidence: "Verification summary maps each contract to the AUTH-003 schema concepts."
artifacts:
  - ".cursor/pilots/authentication-module-smoke-test/modules/authentication/phases/implementation/issues/AUTH-004.md"
verification_summary:
  - "Login contract includes identity input, credential input, success token response, and failure outcomes."
  - "Signup contract includes identity creation input, credential creation input, success account response, and failure outcomes."
  - "Both contracts map to the AUTH-003 schema representation."
optional_fields:
  notes:
    - "Corrected proof after review rejection."
---

# Proof

## Subject

AUTH-004 corrected proof.

## Criteria To Evidence Map

- criterion: login contract is explicit
  evidence: request, response, and failure details listed
- criterion: signup contract is explicit
  evidence: request, response, and failure details listed
- criterion: contracts align with schema assumptions
  evidence: mapping back to AUTH-003 listed

## Artifacts

- AUTH-004 issue artifact

## Verification Summary

- login contract is explicit
- signup contract is explicit
- schema alignment is explicit

## Failures Or Gaps

- none

## Gate Guidance

This corrected proof is sufficient for review.

## Progressive Disclosure

Read next:

1. the subject artifact
2. this proof artifact
3. the review artifact that evaluates this proof
