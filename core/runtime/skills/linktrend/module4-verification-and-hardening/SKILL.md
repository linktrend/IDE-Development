---
name: module4-verification-and-hardening
module_id: verification_and_hardening
harness: ide
---

# Module 4 — Verification & Hardening

## Module ID

`verification_and_hardening`

## Allowed phases

- `4.1-test-planning-preflight` — mechanical
- `4.2-test-case-coverage-trace` — mechanical vs Technical PRD acceptance criteria
- `4.3-full-test-and-build`
- `4.4-security-and-dependency-audit`
- `4.5-end-to-end-acceptance-verification`
- `4.6-repair-loop`
- `4.7-independent-module-gate`

## Required inputs

- integrated application
- Technical PRD acceptance criteria

## Exact outputs

- test-planning preflight result
- coverage-trace result (criteria ↔ tests)
- full verification evidence
- repair Issues for failed criteria
- independent Module gate

## Preflight checks (lightweight, mechanical)

1. **Test planning:** integrations/components have a locatable test shape (files or suites exist where expected).
2. **Coverage trace:** keyword/heuristic overlap between each Technical PRD acceptance criterion and test titles/names. Gaps become gate blockers / repair Inputs — they do not invent a full authored test-plan document.

## Stop conditions

- any unmet Technical PRD acceptance criterion without repair Issue
- independent verifier fail
- repair budget exhausted (`gateRepairBudget`, default 3) without resolution

## Gate repair

Failed criteria create repair Issues. Re-drive automatically up to the repair budget; then stop and brief the Principal. Record severity on rejections.

## Underlying vendored skills composed

- `gstack/health`
- `gstack/qa`
- `gstack/review`

Resolve skill files under `.cursor/runtime/skills/` only (physical vendored copies).

## Precedence

Issue/Module scope and pipeline gates override this composite skill. This composite overrides upstream skill suggestions. Upstream skills **cannot** override pipeline state, gates, scope, or proof requirements.

## Harness notes

- Do not reference the LiNKdeveloper repository at runtime.
- Before Module transitions, call `node .cursor/runtime/validate-application-pipeline.mjs --state <PIPELINE-STATE.json> --request-transition <module-id>:<target-state>`.
- Failed criteria create repair Issues and block Module 5. Do not fabricate Principal UI review. Criteria source is `TECHNICAL-PRD.md`, not a Living Document.
- Contains **no** Cursor Desktop model-routing policy.
