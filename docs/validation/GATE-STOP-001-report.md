# GATE-STOP-001 report

**Date:** 2026-07-17  
**Fixture:** `tests/fixtures/gate-stop-progression/`  
**Runner:** `scripts/test-gate-stop-progression.sh`

## Negative scenario (must stop progression)

| Step | Artifact | Result |
|------|----------|--------|
| Criterion | create `output.txt` with exact text `verified` | required |
| Executor wrote | `negative/output.txt` = `unverified` | mismatch |
| False proof | `negative/PROOF.md` claims pass | rejected by review |
| Independent review | `negative/REVIEW.md` verdict `fail` | cites mismatch |
| Integration | `negative/INTEGRATION.md` status `refused` | refused |
| Issue state | `negative/ISSUE.md` remains `in_progress` | not `done` |
| Dependent | `negative/dependent-ISSUE.md` `blocked` | blocked |
| Module gate | `negative/module-gate.json` `rejected` | fail |
| Continue anyway | validator `execution:complete` with rejected gate | non-zero; state unchanged |
| Waiver | `negative/waiver-attempt.json` missing authority/reason/scope/expiry | rejected |

## Positive control

Correct file → real proof → independent pass → integration → Issue `done` → dependent `ready`.

## Supervised transcript / evidence

- Deterministic runner output from `bash scripts/test-gate-stop-progression.sh`
- Validator: `core/runtime/validate-application-pipeline.mjs`
- This report path: `docs/validation/GATE-STOP-001-report.md`

A documentation-only pass is insufficient; the runner exercises artifact inspection and validator rejection.
