# Commands

This directory contains command wrappers that provide a short operational summary and then route into local prompts.

Preferred commands for new work are:

- `plan-program`
- `plan-module`
- `small-change`
- `complete-module`
- `execute-issue`
- `review-issue`
- `integrate-issue`

`small-change` is the lightweight path for tiny low-risk bugs or simple bounded changes. It reduces planning ceremony, but it does not remove proof, review, integration, or the rule that `done` means verified.

## Archive And Compatibility

Legacy `linkdev-*` and related commands are quarantined under [`compatibility-archive/`](compatibility-archive/README.md).

They remain available for older references, but they are not part of the preferred command surface for new work.

Archived compatibility commands:

- `compatibility-archive/linkdev-go.md`
- `compatibility-archive/linkdev-dispatch.md`
- `compatibility-archive/linkdev-wire-post-dispatch.md`
- `compatibility-archive/wire-linkdev.md`

Archived deprecated aliases:

- `compatibility-archive/linkdev-ui-automations.md`
- `compatibility-archive/linkdev-wire-post-ui.md`

Future work should use the newer execution command layer and its doctrine-driven prompts.

Natural-language session start and session end behavior is handled through `.cursor/session/` and bootstrap routing, not through an additional command family.

Natural-language workspace adoption behavior is handled through `.cursor/workspace/` and bootstrap routing, not through an additional command family.
