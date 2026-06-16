# System

This directory defines the assembled top-level operating model of the `.cursor` system.

The system layer explains how the existing layers fit together:

- Doctrine
- Artifacts
- Agents
- Commands
- Runtime
- Workflows
- Contracts
- State
- System

Read `INDEX.yaml` first, then load only the system document needed for the current question:

- `SYSTEM-ARCHITECTURE.md` for the full operating model
- `LAYER-MODEL.md` for layer ownership and dependencies
- `EXECUTION-MAP.md` for end-to-end execution flow
- `RESPONSIBILITY-MATRIX.md` for ownership boundaries
- `COMPATIBILITY-MATRIX.md` for canonical versus compatibility versus legacy
- `EXTENSION-MODEL.md` for safe extension points
- `V1-BUILD-ORDER.md` for assembled release order
