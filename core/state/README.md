# State

This directory defines the universal execution state layer shared by doctrine, runtime, workflows, contracts, commands, and agents.

The state layer is:

- artifact-driven
- runtime-independent
- implementation-free
- compatible with human, Cursor, Codex, Claude, and future runtimes

Read `INDEX.yaml` first, then open only the state document required for the current question:

- `STATE-MODEL.md` for the shared state vocabulary
- `STATE-TRANSITIONS.md` for allowed and invalid transitions
- `READY-STATES.md` for ready conditions
- `BLOCKED-STATES.md` for blocked conditions
- `FAILURE-STATES.md` for failure handling
- `RETRY-STATES.md` for retry behavior
- `TERMINAL-STATES.md` for terminal completion and stop conditions
