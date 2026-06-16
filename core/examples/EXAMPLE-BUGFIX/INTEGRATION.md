---
integration_id: "SESSION-201-INTEGRATION"
subject_type: "issue"
subject_id: "SESSION-201"
integration_status: "integrated"
integrated_outputs:
  - "the session refresh defect is treated as closed for downstream work"
downstream_effects:
  - "phase completion is satisfied"
  - "module completion may proceed"
final_state: "done"
---

# Integration

## Subject

Issue `SESSION-201`.

## Integrated Outputs

- accepted defect closure

## Downstream Effects

- no later work in this example must re-prove the same defect

## Final State

The issue is `done` and downstream artifacts may rely on it.

## Gate Guidance

Only passing review should permit integration. Dependencies should treat integrated work, not merely executed work, as satisfied.

## Verbosity Guidance

- optional fields may be omitted when irrelevant
- do not fill sections with placeholder text
- prefer references over duplicated narrative
- record downstream effects clearly without bloating the artifact

## Progressive Disclosure

Read next:

1. the subject artifact
2. the review artifact
3. any dependent issue artifacts whose readiness may change
