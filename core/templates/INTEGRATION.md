---
integration_id: "<integration-id>"
subject_type: "issue"
subject_id: "<issue-id>"
integration_status: "pending"
integrated_outputs:
  - "<integrated output>"
downstream_effects:
  - "<affected dependency or readiness change>"
final_state: "<resulting state>"
optional_fields:
  integration_notes:
    - "<note>"
  conflicts_resolved:
    - "<conflict>"
  follow_up_issues:
    - "<issue-id>"
  release_relevance:
    - "<release note>"
---

# Integration

## Subject

Describe the work being integrated.

## Integrated Outputs

- ...

## Downstream Effects

- ...

## Final State

Record the resulting active-line state and whether downstream issues may now be considered for readiness.

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
