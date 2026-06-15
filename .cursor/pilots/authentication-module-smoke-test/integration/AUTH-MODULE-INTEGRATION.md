---
integration_id: "AUTH-module-integration"
subject_type: "module"
subject_id: "authentication"
integration_status: "integrated"
integrated_outputs:
  - "module completion state accepted into pilot program state"
downstream_effects:
  - "program completion conditions satisfied"
final_state: "authentication module complete and integrated at module level"
optional_fields:
  integration_notes:
    - "This artifact makes module-level integration explicit."
---

# Integration

## Subject

Authentication module completion.

## Integrated Outputs

- module completion state

## Downstream Effects

- program completion conditions are satisfied
- pilot may be treated as complete

## Final State

Authentication module is explicitly integrated at module level and may be treated as complete.

## Gate Guidance

Only passing module review should permit this integration. Program-level completion may now rely on the module state.

## Verbosity Guidance

- optional fields may be omitted when irrelevant
- do not fill sections with placeholder text
- prefer references over duplicated narrative
- record downstream effects clearly without bloating the artifact

## Progressive Disclosure

Read next:

1. the subject artifact
2. the module review artifact
3. any higher-level artifact whose completion state changes
