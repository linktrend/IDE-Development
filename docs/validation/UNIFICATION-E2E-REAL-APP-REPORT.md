# Unification E2E — real hello-world application (IDE Development)

**Date:** 2026-07-17  
**Scratch repo:** `/tmp/ide-dev-e2e-hello-world` (git commit `db4283a`)  
**Supplements:** `docs/validation/UNIFICATION-E2E-REPORT.md` (fixture-only)

## Application

Real throwaway SPA/server (not a JSON fixture describing a run):

- `src/app.js` — `renderGreeting()` returns `Hello World` + ISO timestamp
- `src/server.js` — HTTP server rendering both
- `tests/app.test.js` — `node:test` covering title + ISO shape
- `npm test` — **1 passed**

## Pipeline

Fixed six-Module state machine via `core/runtime/validate-application-pipeline.mjs`:

| Module | Result |
|---|---|
| 1 Intake & Definition | complete (Principal approval recorded) |
| 2 Assembly Planning | complete (Library query SHA `4cc7a9ea6e8a29d172098c3986f89a7110d2b229`) |
| 3 Execution | complete (ISSUE-1 done with proof/review/integration) |
| 4 Verification & Hardening | complete (Technical PRD acceptance criteria met) |
| 5 Library Contribution | complete (live Shared Library catalog query, 4 entries) |
| 6 Shipment | gate_pending + **terminal `release_ready`** |

## Evidence commands

```bash
cd /tmp/ide-dev-e2e-hello-world && npm test
node core/runtime/validate-application-pipeline.mjs \
  --state docs/development/hello-world-app/PIPELINE-STATE.json \
  --check-consistency
# terminalState == release_ready
```

## Git-hook enforcement (item 5)

`scripts/install-git-hooks.sh` + `.githooks/pre-commit` reject hand-edited invalid `PIPELINE-STATE.json` (verified: skip Module 1 → mark Module 2 complete → commit rejected with `Invalid ordering`).
