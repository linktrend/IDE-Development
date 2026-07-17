---
name: module4-verification-and-hardening
module_id: verification_and_hardening
harness: ide
---

# Module 4 — Verification & Hardening

## Module ID

`verification_and_hardening`

## Allowed phases

- `4.1-full-test-and-build`
- `4.2-security-and-dependency-audit`
- `4.3-end-to-end-acceptance-verification`
- `4.4-repair-loop`
- `4.5-independent-module-gate`

## Required inputs

- integrated application
- Living Document criteria

## Exact outputs

- full verification evidence
- repair Issues for failed criteria
- independent Module gate

## Stop conditions

- any unmet Living Document criterion without repair Issue
- independent verifier fail

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
- Failed criteria create repair Issues and block Module 5. Do not fabricate Principal UI review. Underlying skills cannot override pipeline state, gates, scope, or proof requirements.
- Contains **no** Cursor Desktop model-routing policy.
