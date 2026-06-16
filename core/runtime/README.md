# Runtime

This directory defines the specification layer that turns the execution doctrine into runtime behavior.

The runtime remains human-driven for now. It does not introduce automation software, cloud agents, or external services.

Read `INDEX.yaml` first, then load only the runtime document required for the current question:

- `RUNTIME.md` for responsibilities and boundaries
- `STATE-MODEL.md` for states, lifecycle, failure, and retry
- `EXECUTION-LOOP.md` for recursive execution behavior
- `DEPENDENCY-RESOLUTION.md` for readiness, dependency handling, and concurrency
