# Application Pipeline

## Purpose

Defines the fixed six-Module application-build pipeline for IDE Development.

This is a **session-scoped Cursor Agent orchestrator** over a durable, fail-closed, repository-resident pipeline state machine. It provides pipeline-shape parity with LiNKdeveloper for the shared product-building flow — not mechanical runtime parity (no persistent process, durable database Ledger, heartbeat, unattended crash recovery, mandatory Starter Kit, or automatic promotion to staging/main).

## Fixed Modules (stable IDs)

No application Program may rename, reorder, omit, or insert an additional top-level Module. Product-specific decomposition belongs inside these Modules as Phases and Issues.

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
  TECHNICAL-PRD.md
  TECHNICAL-DESIGN.md          # authored in Module 2
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

`PRD.md` and `LIVING-DOCUMENT.md` are retired for new application Programs. Their content lives in `TECHNICAL-PRD.md`.

## Transition rule

Before writing any Module state transition, the orchestrator MUST call:

```bash
node .cursor/runtime/validate-application-pipeline.mjs --state <path> --request-transition <module-id>:<target-state>
```

Non-zero exit means **stop**. There is no warn-only mode. Self-report is not proof. Module 6 terminal status for this scope is `release_ready` or `blocked` — never deploy from this pipeline work.

## Module phases (canonical)

### Module 1 — Intake & Definition

1. `1.1-entry-classification`
2. `1.2-interview-elicitation`
3. `1.3-interview-analysis` — Principal confirms
4. `1.4-interview-prioritization` — Principal confirms (MoSCoW)
5. `1.5-interview-intent` — Principal confirms → `INTENT.md`
6. `1.6-technical-prd` — author `TECHNICAL-PRD.md`
7. `1.7-technical-prd-independent-review`
8. `1.8-principal-approval` — human gate on Intent + Technical PRD

### Module 2 — Assembly Planning

1. `2.1-feature-component-map`
2. `2.2-library-query`
3. `2.3-oss-research`
4. `2.4-oss-vetting`
5. `2.5-technical-design` — author `TECHNICAL-DESIGN.md`
6. `2.6-technical-design-independent-review`
7. `2.7-starter-kit-decision` — **optional** (recommend for greenfield; never required)
8. `2.8-issue-dependency-graph`
9. `2.9-independent-plan-gate`

Light pre-Execution sanity (git / `development` branch / CI present) may be fixed when missing. This is **not** a seventh Module and does **not** require a Starter Kit.

### Module 3 — Execution

1. `3.1-issue-dispatch`
2. `3.2-implement-and-proof` — branch `issue/<id>-<slug>` from `development`
3. `3.3-independent-review`
4. `3.4-integration` — PR + CI; merge-ready → Integrator into `development`
5. `3.5-module-gate`

### Module 4 — Verification & Hardening

1. `4.1-test-planning-preflight` — mechanical
2. `4.2-test-case-coverage-trace` — mechanical vs Technical PRD acceptance criteria
3. `4.3-full-test-and-build`
4. `4.4-security-and-dependency-audit`
5. `4.5-end-to-end-acceptance-verification`
6. `4.6-repair-loop`
7. `4.7-independent-module-gate`

### Module 5 — Library Contribution

1. `5.1-candidate-extraction`
2. `5.2-existing-library-deduplication`
3. `5.3-entry-authoring`
4. `5.4-entry-validation`
5. `5.5-contribution-publication`
6. `5.6-independent-module-gate`

### Module 6 — Shipment

1. `6.1-full-critical-verification`
2. `6.2-proof-manifest`
3. `6.3-ship-criteria`
4. `6.4-program-release-review`
5. `6.5-principal-pre-deploy-gate` — **Principal Release OK required**
6. Terminal: `release_ready` or `blocked` (never deploy)

## Gate repair (session-scoped)

When a Tier-A (Issue) or Tier-B (Module) gate rejects:

1. Record severity (`critical` | `high` | `medium` | `low`) and a short rejection reason in the gate artifact / `PIPELINE-STATE.json`.
2. Automatically create or re-drive repair work — do **not** wait for the Principal to say "try again."
3. Cap retries at **3** attempts per Issue or Module gate unless `PIPELINE-STATE.json` sets a lower `gateRepairBudget`.
4. On exhaustion: set Module/Issue `blocked`, leave a briefing trail, and stop for Principal judgment.

## Module gates (summary)

| Module | Gate essence |
|--------|----------------|
| 1 | Intent path + Technical PRD path; confirmed interview checkpoints (`analysis`, `prioritization`, `intent`); Technical PRD independent review approved; Principal approval recorded |
| 2 | Technical Design path; Technical Design independent review approved; criteria mapped; DAG valid; no unvetted OSS |
| 3 | All required Issues `done` with proof, independent review, integration (PR/CI) |
| 4 | Independent full-criterion verification against Technical PRD; repairs block Module 5 |
| 5 | Every reusable candidate contributed, matched, or explicitly non-reusable |
| 6 | Critical verification, proof manifest, ship criteria, release review, Principal pre-deploy |

Mechanical enforcement (validator): Module 1/2 path + review + checkpoint fields; Module 4 unmet criteria; repair `attemptCount` must not exceed `gateRepairBudget` (default 3); Issue done requires proof/review/integration; shipment cannot become `complete`.

## Related

- Schema: `.cursor/contracts/APPLICATION-PIPELINE-STATE.schema.json`
- Validator: `.cursor/runtime/validate-application-pipeline.mjs`
- Commands: `run-application-pipeline`, `resume-application-pipeline`
