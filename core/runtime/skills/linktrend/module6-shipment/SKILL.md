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
- `6.5-deploy-policy`

## Required inputs

- Modules 1–5 complete or publication_pending policy satisfied
- proof artifacts

## Exact outputs

- critical verification result
- proof-manifest.sha256
- ship-criteria checklist
- independent program-release report
- deploy-policy decision (automatic, or waiting for Carlos)
- terminal release_ready or blocked

## Stop conditions

- missing proof manifest
- deploy would run with no `deploy/target.json`, no post-deploy health check plus automatic rollback, and no recorded OK from Carlos
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
- Terminal status is release_ready or blocked. Reaching `main` starts an automatic deploy (LiNKops GitHub Actions job: ephemeral Tailscale, deploy, health check, automatic rollback). If the repo has `deploy/target.json`, deploy is automatic with no approval. If it does not, deploy is automatic only when a post-deploy health check and automatic rollback exist; otherwise wait for Carlos's OK. The `deploy/target.json` schema is owned by LiNKops. No agent holds server credentials or SSH. gstack/ship is subordinate to the critical proof manifest and this deploy policy.
- Contains **no** Cursor Desktop model-routing policy.
