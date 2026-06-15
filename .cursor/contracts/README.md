# Contracts

This directory defines the universal contract layer for handoffs between workflow stages, artifacts, and runtimes.

The contract layer is:

- artifact-driven
- runtime-independent
- implementation-free
- compatible with human, Cursor, Codex, Claude, and future runtimes

Read `INDEX.yaml` first, then load only the contract document required for the current question:

- `CONTRACT-MODEL.md` for the universal model
- `INPUT-CONTRACT.md` for stage entry requirements
- `OUTPUT-CONTRACT.md` for handoff outputs
- `STATE-CONTRACT.md` for valid state changes
- `SIDE-EFFECT-CONTRACT.md` for allowed and forbidden effects
- `VALIDATION-CONTRACT.md` for invariants and compliance checks
