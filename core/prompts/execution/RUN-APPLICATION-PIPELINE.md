# RUN-APPLICATION-PIPELINE

## Purpose

Orchestrate a new application Program through the fixed six-Module pipeline in one Cursor session (or until blocked).

## Preconditions

- Read `.cursor/execution/APPLICATION-PIPELINE.md`
- Read `.cursor/execution/CANONICAL-LAWS.md`
- Target repository is writable
- Do not deploy

## Steps

1. Instantiate `docs/development/<program-id>/` with exactly these six Modules in order:
   - `01-intake-and-definition`
   - `02-assembly-planning`
   - `03-execution`
   - `04-verification-and-hardening`
   - `05-library-contribution`
   - `06-shipment`
2. Create `PIPELINE-STATE.json` from `.cursor/templates/PIPELINE-STATE.json`.
3. For each Module, execute its ordered phases and required outputs per APPLICATION-PIPELINE.md.
4. **Before every Module state transition**, run:

```bash
node .cursor/runtime/validate-application-pipeline.mjs --state <path-to-PIPELINE-STATE.json> --request-transition <module-id>:<target-state>
```

5. If the validator exits non-zero: **stop**. Do not warn-and-continue. Record the blocker in `PIPELINE-STATE.json`.
6. Reject self-report as proof. Issues require proof, independent review, and integration before `done`.
7. Stop at `release_ready` or `blocked`. Never deploy.

## Stop conditions

- Missing Principal approval (Module 1)
- Rejected gate
- Unmet Living Document criteria (Module 4)
- Validator rejection
- Explicit human stop
