# Friction Cleanup

## Purpose

Record the protective cleanup performed after readiness clarification.

## Legacy Command Cleanup

Legacy and deprecated `linkdev-*` command wrappers were moved into an archive and compatibility classification without changing their file paths.

This protects older references while making the preferred command surface clearer for new work.

Preferred command surface now includes:

- `plan-program`
- `plan-module`
- `small-change`
- `complete-module`
- `execute-issue`
- `review-issue`
- `integrate-issue`

Archived compatibility commands remain available only for older workflows that explicitly reference them.

## Lightweight Small-Change Path

Added `small-change` for tiny low-risk bugs and simple bounded changes.

This path reduces planning ceremony but preserves the core anti-incompletion gates:

- issue record
- proof
- review
- integration
- `done` only after verified integration

## Deferred Work

Skills migration remains deferred until after cleanup.

Existing repository skills, including any referred to as `g skills` or `gstack`, should be inventoried before import or refactor.
