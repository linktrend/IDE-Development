# Application Pipeline

## Purpose

Defines the fixed six-Module application-build pipeline for IDE Development.

This is a **session-scoped Cursor Agent orchestrator** over a durable, fail-closed, repository-resident pipeline state machine. It provides pipeline-shape parity with LiNKdeveloper, not mechanical runtime parity (no persistent process, durable database Ledger, heartbeat, or unattended crash recovery).

## Fixed Modules (stable IDs)

No application Program may rename, reorder, omit, or insert a seventh top-level Module. Product-specific decomposition belongs inside these Modules as Phases and Issues.

1. `intake_and_definition` — **Module 1 — Intake & Definition**
2. `assembly_planning` — **Module 2 — Assembly Planning**
3. `execution` — **Module 3 — Execution**
4. `verification_and_hardening` — **Module 4 — Verification & Hardening**
5. `library_contribution` — **Module 5 — Library Contribution**
6. `shipment` — **Module 6 — Shipment**

## Target-repo artifact layout

```text
docs/development/<program-id>/
  INTENT.md
  PRD.md
  LIVING-DOCUMENT.md
  PROGRAM.md
  PIPELINE-STATE.json
  modules/01-intake-and-definition/
  modules/02-assembly-planning/
  modules/03-execution/
  modules/04-verification-and-hardening/
  modules/05-library-contribution/
  modules/06-shipment/
  proof-manifest.sha256
```

## Transition rule

Before writing any Module state transition, the orchestrator MUST call:

```bash
node .cursor/runtime/validate-application-pipeline.mjs --state <path> --request-transition <module-id>:<target-state>
```

Non-zero exit means **stop**. There is no warn-only mode. Self-report is not proof. Module 6 terminal status for this scope is `release_ready` or `blocked` — never deploy from this pipeline work.

## Module gates (summary)

| Module | Gate essence |
|--------|----------------|
| 1 | Principal approval of PRD + Living Document recorded |
| 2 | Independent plan gate; criteria mapped; DAG valid; no unvetted OSS |
| 3 | All required Issues `done` with proof, independent review, integration |
| 4 | Independent full-criterion verification; repairs block Module 5 |
| 5 | Every reusable candidate contributed, matched, or explicitly non-reusable |
| 6 | Critical verification, proof manifest, ship criteria, release review, Principal pre-deploy |

## Related

- Schema: `.cursor/contracts/APPLICATION-PIPELINE-STATE.schema.json`
- Validator: `.cursor/runtime/validate-application-pipeline.mjs`
- Commands: `run-application-pipeline`, `resume-application-pipeline`
