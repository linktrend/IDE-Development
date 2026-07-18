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
2. Create `PIPELINE-STATE.json` from `.cursor/templates/PIPELINE-STATE.json` (schemaVersion 2).
3. For each Module, execute its ordered phases and required outputs per APPLICATION-PIPELINE.md:
   - Module 1: four hard-gated interview checkpoints → Intent → Technical PRD → independent review → Principal approval
   - Module 2: Technical Design + independent review before Issue planning; Starter Kit optional
   - Module 3: branch-per-Issue, PR + CI, Integrator merge to `development`
   - Module 4: test-planning + coverage-trace preflights, then verification; repair budget 3
   - Module 5: library contribution
   - Module 6: ship artifacts → Principal pre-deploy → `release_ready` (never deploy)
4. **Before every Module state transition**, run:

```bash
node .cursor/runtime/validate-application-pipeline.mjs --state <path-to-PIPELINE-STATE.json> --request-transition <module-id>:<target-state>
```

5. If the validator exits non-zero: **stop**. Do not warn-and-continue. Record the blocker in `PIPELINE-STATE.json`.
6. On gate rejection: automatically re-drive repair work up to `gateRepairBudget` (default 3), record severity, then brief the Principal if exhausted.
7. Reject self-report as proof. Issues require proof, independent review, and integration before `done`.
8. Stop at `release_ready` or `blocked`. Never deploy. Never auto-promote to staging/main.

## Stop conditions

- Missing Principal confirmation on Module 1 interview checkpoints or final Module 1 approval
- Rejected gate (after repair budget exhausted)
- Unmet Technical PRD acceptance criteria (Module 4)
- Validator rejection
- Explicit human stop
