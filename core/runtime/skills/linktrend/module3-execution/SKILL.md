---
name: module3-execution
module_id: execution
harness: ide
---

# Module 3 — Execution

## Module ID

`execution`

## Allowed phases

- `3.1-issue-dispatch`
- `3.2-implement-and-proof`
- `3.3-independent-review`
- `3.4-integration`
- `3.5-module-gate`

## Required inputs

- Issue graph from Module 2
- bounded paths and acceptance criteria per Issue

## Exact outputs

- Issues done with proof + independent review + integration
- recomputed readiness
- Module gate verdict

## GitHub / branch discipline

For each Issue (when the target repo uses GitHub):

1. Create branch `issue/<issueId>-<slug>` from `development`.
2. Implement and collect non-vacuous proof on that branch.
3. Independent review (not the author).
4. When finished: mark review-ready (completion gate). **Review Packager** opens the PR; wait for CI/Bugbot. CI failure is a gate rejection — enter repair via Lisa ACP Repair Dispatcher (budget 3). Implementers do not open PRs.
5. When merge-ready, the delivery controller merges into `development`.

Do **not** auto-promote `development` → `staging` → `main`. Principal Release OK remains Module 6.

## Stop conditions

- self-report offered as proof
- review not independent
- integration skipped
- CI failed without repair attempt (or repair budget exhausted)
- Module gate missing Tier-B-equivalent verdict

## Gate repair

On Issue or Module gate rejection: automatically re-drive repair work up to `gateRepairBudget` (default 3). Record severity and reason in gate / `PIPELINE-STATE.json` `gateRejectionHistory`. On exhaustion: block and brief the Principal.

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
- Dispatch only dependency-ready Issues. Reject self-review.
- Contains **no** Cursor Desktop model-routing policy.
