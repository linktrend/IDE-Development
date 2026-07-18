---
name: module6-shipment
module_id: shipment
harness: ide
---

# Module 6 — Shipment

## Module ID

`shipment`

## Allowed phases

- `6.1-full-critical-verification`
- `6.2-proof-manifest`
- `6.3-ship-criteria`
- `6.4-program-release-review`
- `6.5-principal-pre-deploy-gate`

## Required inputs

- Modules 1–5 complete or publication_pending policy satisfied
- proof artifacts

## Exact outputs

- critical verification result
- proof-manifest.sha256
- ship-criteria checklist
- independent program-release report
- Principal pre-deploy decision
- terminal release_ready or blocked

## Stop conditions

- any attempt to deploy
- missing proof manifest
- Principal pre-deploy decision missing
- validator rejects release_ready

## Underlying vendored skills composed

- `gstack/ship`
- `gstack/review`

Resolve skill files under `.cursor/runtime/skills/` only (physical vendored copies).

## Precedence

Issue/Module scope and pipeline gates override this composite skill. This composite overrides upstream skill suggestions. Upstream skills **cannot** override pipeline state, gates, scope, or proof requirements.

## Harness notes

- Do not reference the LiNKdeveloper repository at runtime.
- Before Module transitions, call `node .cursor/runtime/validate-application-pipeline.mjs --state <PIPELINE-STATE.json> --request-transition <module-id>:<target-state>`.
- MUST NOT deploy. Terminal status is release_ready or blocked. gstack/ship is subordinate to critical proof manifest and Principal pre-deploy gate. Principal Release OK remains mandatory in IDE Development (unlike LiNKdeveloper's automatic canary promotion).
- Contains **no** Cursor Desktop model-routing policy.
