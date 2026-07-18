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
- `2.2-library-query`
- `2.3-oss-research`
- `2.4-oss-vetting`
- `2.5-technical-design` — author `TECHNICAL-DESIGN.md`
- `2.6-technical-design-independent-review`
- `2.7-starter-kit-decision` — **optional**
- `2.8-issue-dependency-graph`
- `2.9-independent-plan-gate`

## Required inputs

- Principal-approved Intent + Technical PRD
- Library checkout SHA (when available)

## Exact outputs

- feature-to-component map
- `LIBRARY-QUERY-REPORT.md` with Library commit SHA (when available)
- `TECHNICAL-DESIGN.md` with independent review approved
- optional Starter Kit decision recorded in `PIPELINE-STATE.json` / Technical Design
- OSS research + vetting records
- dependency-acyclic Issue graph
- acceptance-criterion coverage map from every Technical PRD acceptance criterion to one or more Issues

## Starter Kit policy (IDE Development)

Starter Kits are **optional**. Recommend for greenfield when a suitable kit exists. Never fail or block Module 2 solely because no kit was selected. Existing product repositories normally record `declined` or `none`.

## Stop conditions

- Technical Design independent review is `needs_revision`
- unmapped Technical PRD acceptance criterion
- unvetted OSS
- cyclic Issue graph
- independent plan gate rejected (then automatic repair up to `gateRepairBudget`, default 3)

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
- Must query the shared Library (or record publication_pending/offline SHA). OSS vetting is mandatory. Do not start Issue planning until Technical Design review is approved.
- Record `technicalDesignPath` in `PIPELINE-STATE.json` and set `technicalDesignIndependentReviewApproved` (or `technicalDesignReviewDecision: "approved"`) on the Module 2 gate before requesting `assembly_planning:complete`.
- Contains **no** Cursor Desktop model-routing policy.
