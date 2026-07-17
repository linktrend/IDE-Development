---
name: module1-intake-and-definition
module_id: intake_and_definition
harness: ide
---

# Module 1 — Intake & Definition

## Module ID

`intake_and_definition`

## Allowed phases

- `1.1-entry-classification`
- `1.2-interview-to-intent`
- `1.3-prd-drafting`
- `1.4-living-document`
- `1.5-principal-approval`

## Required inputs

- plain-language idea or existing PRD draft
- target repository root

## Exact outputs

- INTENT.md
- PRD.md
- LIVING-DOCUMENT.md
- recorded Principal decision

## Stop conditions

- Principal approval missing or rejected
- Living Document criteria cannot be made testable
- validator rejects Module 1 complete

## Underlying vendored skills composed

- `mattpocock/grill-with-docs`
- `gstack/spec`
- `mattpocock/to-spec`

Resolve skill files under `.cursor/runtime/skills/` only (physical vendored copies).

## Precedence

Issue/Module scope and pipeline gates override this composite skill. This composite overrides upstream skill suggestions. Upstream skills **cannot** override pipeline state, gates, scope, or proof requirements.

## Harness notes

- Do not reference the LiNKdeveloper repository at runtime.
- Before Module transitions, call `node .cursor/runtime/validate-application-pipeline.mjs --state <PIPELINE-STATE.json> --request-transition <module-id>:<target-state>`.
- Author Living Document explicitly. Human gate is mandatory. Underlying skills cannot override pipeline state, gates, scope, or proof requirements.
- Contains **no** Cursor Desktop model-routing policy.
