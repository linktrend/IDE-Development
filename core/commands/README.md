# Commands

This directory contains command wrappers that provide a short operational summary and then route into local prompts.

Preferred commands for new work are:

- `plan-program`
- `plan-module`
- `complete-module`
- `execute-issue`
- `review-issue`
- `integrate-issue`

Legacy `linkdev-*` and related compatibility commands remain only for continuity with older flows.

Current compatibility status:

- `linkdev-go`, `linkdev-dispatch`, `linkdev-wire-post-dispatch`, and `wire-linkdev` are retained as legacy commands
- `linkdev-ui-automations` and `linkdev-wire-post-ui` are retained as deprecated compatibility aliases

Future work should use the newer execution command layer and its doctrine-driven prompts.

Natural-language session start and session end behavior is handled through `.cursor/session/` and bootstrap routing, not through an additional command family.

Natural-language workspace adoption behavior is handled through `.cursor/workspace/` and bootstrap routing, not through an additional command family.
