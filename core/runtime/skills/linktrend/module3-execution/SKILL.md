---
name: module3-execution
module_id: execution
harness: ide
---

# Module 3 — Execution

## Module ID

`execution`

## Allowed phases

- `dispatch dependency-ready Issues`
- `proof`
- `independent review`
- `integration`

## Required inputs

- Issue graph from Module 2
- bounded paths and acceptance criteria per Issue

## Exact outputs

- Issues done with proof + independent review + integration
- recomputed readiness

## Stop conditions

- self-report offered as proof
- review not independent
- integration skipped
- Module gate missing Tier-B-equivalent verdict

## Underlying vendored skills composed

- `mattpocock/tdd`
- `mattpocock/diagnosing-bugs`
- `mattpocock/improve-codebase-architecture`

Resolve skill files under `.cursor/runtime/skills/` only (physical vendored copies).

## Precedence

Issue/Module scope and pipeline gates override this composite skill. This composite overrides upstream skill suggestions. Upstream skills **cannot** override pipeline state, gates, scope, or proof requirements.

## Harness notes

- Do not reference the LiNKdeveloper repository at runtime.
- Before Module transitions, call `node .cursor/runtime/validate-application-pipeline.mjs --state <PIPELINE-STATE.json> --request-transition <module-id>:<target-state>`.
- Dispatch only dependency-ready Issues. Reject self-review. Underlying skills cannot override pipeline state, gates, scope, or proof requirements.
- Contains **no** Cursor Desktop model-routing policy.
