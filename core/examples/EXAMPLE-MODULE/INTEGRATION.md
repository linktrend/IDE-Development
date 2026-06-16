---
integration_id: "NOTIFY-101-INTEGRATION"
subject_type: "issue"
subject_id: "NOTIFY-101"
integration_status: "integrated"
integrated_outputs:
  - "the module may treat NOTIFY-101 as satisfied"
  - "program roll-up may evaluate the notification-preferences module as complete"
downstream_effects:
  - "phase completion is satisfied"
  - "module completion review may proceed"
  - "program completion may be inferred because only one module exists in this example"
final_state: "done"
optional_fields:
  integration_notes:
    - "this example makes upward roll-up explicit"
---

# Integration

## Subject

Issue `NOTIFY-101`.

## Integrated Outputs

- accepted issue result
- unlocked module completion path

## Downstream Effects

- the phase is complete
- the module may roll up to complete after mandatory module review
- the program may then roll up to complete

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
