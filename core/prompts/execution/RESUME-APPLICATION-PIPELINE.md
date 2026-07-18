# RESUME-APPLICATION-PIPELINE

## Purpose

Resume an application Program from durable repository artifacts in a new Cursor session without relying on chat memory.

## Preconditions

- Target repo contains `docs/development/<program-id>/PIPELINE-STATE.json`
- Read `.cursor/execution/APPLICATION-PIPELINE.md`

## Steps

1. Load `PIPELINE-STATE.json` and validate it against `.cursor/contracts/APPLICATION-PIPELINE-STATE.schema.json` (conceptually / via validator usage).
2. Derive the next Module: first Module in fixed order whose state is not `complete` (Module 6 uses `release_ready` terminal, not `complete`).
3. Load that Module’s gate and phase artifacts.
4. Before any transition, call:

```bash
node .cursor/runtime/validate-application-pipeline.mjs --state <path> --request-transition <module-id>:<target-state>
```

5. Non-zero → stop and report blockers.
6. Continue until `release_ready`, `blocked`, or session end. Persist all state in the repository.

## Forbidden

- Inventing Module state from chat memory
- Skipping validator calls
- Deploying
- Creating a seventh top-level Module
