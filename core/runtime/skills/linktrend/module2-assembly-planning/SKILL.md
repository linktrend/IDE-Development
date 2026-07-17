---
name: module2-assembly-planning
module_id: assembly_planning
harness: ide
---

# Module 2 — Assembly Planning

## Module ID

`assembly_planning`

## Allowed phases

- `2.1-feature-component-map`
- `2.2-library-starter-kit-query`
- `2.3-oss-research`
- `2.4-oss-vetting`
- `2.5-issue-dependency-graph`
- `2.6-independent-plan-gate`

## Required inputs

- approved PRD + Living Document
- Library checkout SHA (when available)

## Exact outputs

- feature-to-component map
- LIBRARY-QUERY-REPORT.md with Library commit SHA
- starter-kit decision
- OSS research + vetting records
- dependency-acyclic Issue graph
- acceptance-criterion coverage map

## Stop conditions

- unmapped Living Document criterion
- unvetted OSS
- cyclic Issue graph
- independent plan gate rejected

## Underlying vendored skills composed

- `mattpocock/research`
- `mattpocock/to-tickets`
- `gstack/plan-ceo-review`

Resolve skill files under `.cursor/runtime/skills/` only (physical vendored copies).

## Precedence

Issue/Module scope and pipeline gates override this composite skill. This composite overrides upstream skill suggestions. Upstream skills **cannot** override pipeline state, gates, scope, or proof requirements.

## Harness notes

- Do not reference the LiNKdeveloper repository at runtime.
- Before Module transitions, call `node .cursor/runtime/validate-application-pipeline.mjs --state <PIPELINE-STATE.json> --request-transition <module-id>:<target-state>`.
- Must query the shared Library (or record publication_pending/offline SHA). OSS vetting is mandatory. Underlying skills cannot override pipeline state, gates, scope, or proof requirements.
- Contains **no** Cursor Desktop model-routing policy.
