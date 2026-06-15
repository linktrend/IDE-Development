# Commands

This directory contains thin command wrappers that route into local prompts.

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
