---
name: module1-intake-and-definition
module_id: intake_and_definition
harness: ide
---

# Module 1 — Intake & Definition

## Module ID

`intake_and_definition`

## Allowed phases

- entry-mode selection: `from-scratch` | `pick-up-unfinished` | `continue-after-release`
- assess existing repo — for `pick-up-unfinished`, `continue-after-release`, and any work started outside the Program. Read the repo, open branches, pull requests, issues, and CI state. Write a starting Ledger of Issues with owners and states. Ledger IDs are `<PREFIX>-<n>`.
- `1.1-entry-classification`
- `1.2-interview-elicitation`
- `1.3-interview-analysis` — Principal confirms before advance
- `1.4-interview-prioritization` — Principal confirms (MoSCoW)
- `1.5-interview-intent` — Principal confirms → `INTENT.md`
- `1.6-technical-prd` — author `TECHNICAL-PRD.md`
- `1.7-technical-prd-independent-review`
- `1.8-principal-approval` — human gate on Intent + Technical PRD

## Required inputs

- plain-language idea or existing PRD-shaped / Technical PRD draft
- target repository root

## Exact outputs

- `INTENT.md` (confirmed Intent — plain English; not the Technical PRD)
- `TECHNICAL-PRD.md` (single product-definition document; replaces former PRD + Living Document)
- independent review verdict for Technical PRD
- recorded Principal decision approving Intent + Technical PRD

## Stop conditions

- Principal declines or does not confirm a hard-gated interview checkpoint
- Principal approval missing or rejected
- Technical PRD required sections missing or vacuous
- Technical PRD independent review is `needs_revision` and not resolved
- validator rejects Module 1 complete

## Interview hard gates

Checkpoints `1.3`, `1.4`, and `1.5` require an explicit Principal confirming reply before the session may advance. Ambiguous replies do not count as confirmation. Vacuous or placeholder-only checkpoint content fails closed.

Intent's validation **is** the Principal confirmation at `1.5`. Intent does not require a separate cross-family AI review. The Technical PRD does.

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
- Select `entryMode` before interview work. Run assess-existing-repo for pick-up, continue-after-release, and work started outside the Program. `from-scratch` uses the conditional setup Module (repo, `scripts/setup.sh`, `.cursor/environment.json`, CI, `development` and `main`). That Module stays off in an existing repo; only light sanity fixes happen there.
- Author Technical PRD explicitly. Human gate is mandatory. Do not create `PRD.md` or `LIVING-DOCUMENT.md` for new Programs.
- Record `confirmedInterviewCheckpoints: ["analysis","prioritization","intent"]`, `intentPath`, `technicalPrdPath` in `PIPELINE-STATE.json`, and set `technicalPrdIndependentReviewApproved` (or `technicalPrdReviewDecision: "approved"`) on the Module 1 gate before requesting `intake_and_definition:complete`.
- Contains **no** Cursor Desktop model-routing policy.
