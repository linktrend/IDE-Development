---
integration_id: "AUTH-003-integration"
subject_type: "issue"
subject_id: "AUTH-003"
integration_status: "integrated"
integrated_outputs:
  - "schema representation accepted into pilot state"
downstream_effects:
  - "AUTH-004 dependencies satisfied"
  - "AUTH-006 partially unblocked but not ready yet"
final_state: "AUTH-003 done"
optional_fields: {}
---

# Integration

## Subject

AUTH-003 schema representation.

## Integrated Outputs

- schema representation

## Downstream Effects

- AUTH-004 may now be marked ready
- AUTH-006 still waits on AUTH-004 and AUTH-005

## Final State

AUTH-003 is integrated and done.

## Gate Guidance

Integrated output satisfies downstream dependency needs.

## Progressive Disclosure

Read next:

1. the subject artifact
2. the review artifact
3. any dependent issue artifacts whose readiness may change
