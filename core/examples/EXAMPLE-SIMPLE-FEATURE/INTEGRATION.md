---
integration_id: "PROFILE-001-INTEGRATION"
subject_type: "issue"
subject_id: "PROFILE-001"
integration_status: "integrated"
integrated_outputs:
  - "the module may treat PROFILE-001 as satisfied"
  - "program roll-up may evaluate module completion"
downstream_effects:
  - "phase completion criteria are now satisfied"
  - "module completion may proceed to module-level review"
final_state: "done"
optional_fields:
  release_relevance:
    - "none for this example"
---

# Integration

## Subject

Issue `PROFILE-001`.

## Integrated Outputs

- the feature slice is recorded as accepted
- downstream roll-up is unlocked

## Downstream Effects

- phase completion becomes true
- module completion review may proceed

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
