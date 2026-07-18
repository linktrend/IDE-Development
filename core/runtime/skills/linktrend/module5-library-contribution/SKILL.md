---
name: module5-library-contribution
module_id: library_contribution
harness: ide
---

# Module 5 — Library Contribution

## Module ID

`library_contribution`

## Allowed phases

- `5.1-candidate-extraction`
- `5.2-existing-library-deduplication`
- `5.3-entry-authoring`
- `5.4-entry-validation`
- `5.5-contribution-publication`
- `5.6-independent-module-gate`

## Required inputs

- reusable candidates from Modules 2–4
- Library query SHA

## Exact outputs

- LIBRARY-CONTRIBUTION.md
- contribution bundle or existing-match or explicit non-reusable rejection
- publication state merged|publication_pending|not_applicable

## Stop conditions

- candidate neither contributed, matched, nor explicitly rejected as non-reusable
- invalid contribution bundle

## Underlying vendored skills composed

- _(none — Module 5 uses Library contribution instructions only)_

Resolve skill files under `.cursor/runtime/skills/` only (physical vendored copies).

## Precedence

Issue/Module scope and pipeline gates override this composite skill. This composite overrides upstream skill suggestions. Upstream skills **cannot** override pipeline state, gates, scope, or proof requirements.

## Harness notes

- Do not reference the LiNKdeveloper repository at runtime.
- Before Module transitions, call `node .cursor/runtime/validate-application-pipeline.mjs --state <PIPELINE-STATE.json> --request-transition <module-id>:<target-state>`.
- No upstream skill is treated as sufficient. Until Principal confirms automatic PR creation, stop at publication_pending with a local bundle. Underlying skills cannot override pipeline state, gates, scope, or proof requirements.
- Optional note only: a successful pattern may be a future Starter Kit candidate — IDE Development does **not** run an automated kit-minting pipeline.
- Contains **no** Cursor Desktop model-routing policy.
