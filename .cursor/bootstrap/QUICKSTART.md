# Quickstart

Use this file when the task is already clear and you want the shortest safe route into work.

## Fast Path

1. Read `.cursor/README.md`
2. Read `.cursor/commands/INDEX.yaml`
3. Select the preferred command:
   - `plan-program`
   - `plan-module`
   - `complete-module`
   - `execute-issue`
   - `review-issue`
   - `integrate-issue`
4. Read only the doctrine and templates required by that command
5. Open the target artifact tree
6. Start work only when readiness is explicit

## Short Routing Table

- new idea or objective: `plan-program`
- new module: `plan-module`
- complete an existing module: `complete-module`
- execute one ready issue: `execute-issue`
- evaluate proof: `review-issue`
- record accepted work: `integrate-issue`

## Minimum Artifact Expectations

- program-level work: `INTENT.md`, then `PROGRAM.md`
- module-level work: `MODULE.md`, `PHASE.md`, `ISSUE.md`
- issue-level work: `ISSUE.md`, then `PROOF.md`, `REVIEW.md`, `INTEGRATION.md`

## Anti-Incompletion Reminders

- readiness is computed, not assumed
- issues must pass through `review_ready`
- review must inspect proof, not confidence
- integration records accepted work and downstream effects

## When Not To Use Quickstart

Do not use this shortcut if:

- repository adoption is incomplete
- the work level is unclear
- multiple modules or programs are being reconciled
- the active artifact tree is inconsistent
