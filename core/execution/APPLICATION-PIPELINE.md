# Application Pipeline

## Purpose

Defines the application-build pipeline for both Programs (IDE Development and LiNKdeveloper).

Six Modules always run. A conditional setup Module runs only when the entry mode is create-from-scratch. This is a **session-scoped Cursor Agent orchestrator** over a durable, fail-closed, repository-resident pipeline state machine.

## Entry modes

Record `entryMode` on `PIPELINE-STATE.json`:

| Mode | `entryMode` |
|---|---|
| Create from scratch | `from-scratch` |
| Pick up an unfinished development | `pick-up-unfinished` |
| Continue developing after the first release | `continue-after-release` |

### Assess existing repo

For `pick-up-unfinished`, `continue-after-release`, and any work started outside the Program, the orchestrator reads the repo, its open branches, pull requests, issues, and CI state, and writes a starting Ledger. The Ledger lists Issues with owners and states. Ledger IDs are `<PREFIX>-<n>`.

## Modules (stable IDs)

Do not rename, reorder, or omit the six Modules. Product-specific decomposition belongs inside them as Phases and Issues. The setup Module is conditional: it is not a rename of those six.

0. `setup` — **conditional setup Module** (`from-scratch` only)
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
  modules/00-setup/                 # only when entryMode is from-scratch
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

Non-zero exit means **stop**. There is no warn-only mode. Self-report is not proof. Module 6 terminal status is `release_ready` or `blocked`. Reaching `main` starts deploy under the deploy policy in Module 6.

## Module phases (canonical)

### Conditional setup Module — `setup`

Active only for `from-scratch`. It creates the repo, `scripts/setup.sh`, `.cursor/environment.json`, CI, and the `development` and `main` branches.

It is not activated for `pick-up-unfinished` or `continue-after-release`. In an existing repo, only light sanity fixes happen (git, `development` branch, CI present).

### Module 1 — Intake & Definition

Select `entryMode` first. For pick-up, continue-after-release, and work started outside the Program, run **assess existing repo** before the interview.

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

In an existing repo (`pick-up-unfinished` or `continue-after-release`), light sanity fixes (git / `development` branch / CI present) may be applied when missing. That is not the setup Module. The setup Module runs only for `from-scratch`. A Starter Kit is still optional.

### Module 3 — Execution

1. `3.1-issue-dispatch`
2. `3.2-implement-and-proof` — branch `issue/<id>-<slug>` from `development`
3. `3.3-independent-review`
4. `3.4-integration` — the orchestrator packages the PR. Workers never open PRs. When Full CI is green and one independent review (a different model family than the author) approves the exact head, the delivery controller into `development` merges it, then the orchestrator promotes `development` → `main`.
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
5. `6.5-deploy-policy` — deploy follows the policy below
6. Terminal: `release_ready` or `blocked`

**Deploy policy.** Reaching `main` starts an automatic deploy via the LiNKops GitHub Actions job (joins Tailscale ephemerally, deploys, health-checks, and rolls back).

- If the repo declares its target server in `deploy/target.json`, deploy is automatic with no approval.
- If it does not, deploy is automatic only when a post-deploy health check and automatic rollback exist. Otherwise the orchestrator waits for Carlos's OK.
- The `deploy/target.json` schema is owned by LiNKops. This pipeline only names the file and the rule. No agent holds server credentials or SSH.

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
| 6 | Critical verification, proof manifest, ship criteria, release review, deploy policy |

Mechanical enforcement (validator): Module 1/2 path + review + checkpoint fields; Module 4 unmet criteria; repair `attemptCount` must not exceed `gateRepairBudget` (default 3); Issue done requires proof/review/integration; shipment cannot become `complete`.

## Related

- Schema: `.cursor/contracts/APPLICATION-PIPELINE-STATE.schema.json`
- Validator: `.cursor/runtime/validate-application-pipeline.mjs`
- Commands: `run-application-pipeline`, `resume-application-pipeline`
