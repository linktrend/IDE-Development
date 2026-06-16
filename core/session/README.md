# Session

This directory defines the canonical session lifecycle capability.

Use it when work is being resumed or deliberately closed for the day through natural-language requests rather than explicit command wrappers.

Read `INDEX.yaml` first.

Preferred documents are:

- `SESSION-LIFECYCLE.md` for the overall model
- `SESSION-START.md` for resume behavior
- `SESSION-END.md` for close-out behavior
- `HANDOFF-REPORT.md` for the handoff artifact contract

Workspace adoption is separate from daily session behavior.

- workspace adoption: one-time installation and wiring
- session lifecycle: ongoing start-of-day and end-of-day behavior

This layer extends existing bootstrap, runtime, workflow, state, and repository hygiene behavior. It does not introduce a new command family.
