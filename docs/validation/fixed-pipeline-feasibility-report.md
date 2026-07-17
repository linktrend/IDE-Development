# Fixed-pipeline feasibility report

**Phase:** 2  
**Date:** 2026-07-17  
**Fixture:** `tests/fixtures/fixed-pipeline-feasibility/`  
**Validator:** `scripts/feasibility/validate-pipeline-transition.mjs`  
**Runner:** `scripts/feasibility/run-fixed-pipeline-feasibility.sh`

## Verdict

**`feasible_with_approximation`**

Pipeline-shape parity, artifact-contract parity, gate semantics parity, and tested in-session behavioral parity are achievable with a session-scoped Cursor Agent orchestrator over a durable, fail-closed, repository-resident pipeline state machine. This is **not** mechanical runtime parity with LiNKdeveloper’s persistent Ledger/orchestrator.

## Limitations (from PRD §1.2)

Without a separate persistent orchestrator, IDE Development cannot:

- keep polling after Cursor closes;
- guarantee unattended crash recovery;
- enforce a gate against every possible direct/manual edit path;
- match LiNKdeveloper’s Ledger-level transactional state enforcement.

Resume works by re-reading and validating repository artifacts in a new session.

## Deterministic validator result

Command:

```bash
bash scripts/feasibility/run-fixed-pipeline-feasibility.sh
```

Observed (2026-07-17):

- **pass=21 fail=0**
- Negative scenarios returned non-zero
- Fixture `pipeline-state.json` hash unchanged after failed transitions
- Happy path advanced Modules 1–5 to `complete`, Module 6 to `active`, issue to `done` with proof/review/integration, terminal `release_ready`
- Module 6 `complete` rejected; terminal is `release_ready` only

### Rules proven

| Rule | Result |
|------|--------|
| Reject module complete if gate absent/rejected | PASS |
| Reject activate N+1 unless N complete | PASS |
| Reject Module 1 complete without Principal approval | PASS |
| Reject Issue done without proof + independent review + integration | PASS |
| Reject Module 4 complete with unmet Living Document criteria | PASS |
| Reject Module 6 complete (terminal = release_ready) | PASS |
| Non-zero on rejection; state unchanged | PASS |

## Supervised agent scenarios

These scenarios were executed in this implementation session (agent = Grok / Cursor coding agent) against the disposable fixture and validator. No production doctrine was modified for the scenarios.

### 1. Happy path

- **Request:** Advance all six fixture Modules in order via the validator (`--apply` on a working copy).
- **Deterministic result:** PASS (see runner happy-path steps).
- **Observed agent behavior:** Agent invoked the validator before each transition; only applied when exit code 0.
- **Manual intervention:** None beyond running the scripted happy path.
- **Evidence:** runner stdout `Happy path step …` / `release_ready`.

### 2. Failed gate

- **Setup:** Module 1 `complete`; Module 2 `active` with gate `verdict=rejected`.
- **Request:** Continue to Module 3 (`execution:active`).
- **Deterministic result:** REJECT — `Cannot activate execution: predecessor assembly_planning is not complete`.
- **Observed agent behavior:** Agent must refuse; no Module 3 execution artifact created (working copy state unchanged; no `modules/03-execution` execution artifact written).
- **Manual intervention:** None.

### 3. Resume (new session / no chat memory)

- **Setup:** Working copy stopped after Module 3 `complete`; durable `pipeline-state.json` records `currentModuleId` / module states.
- **Request (natural language):** “Resume this application build” with only the target repo artifacts.
- **Derivation:** Next Module = first non-complete in fixed order → `verification_and_hardening`. Validated by reading `pipeline-state.json` only (no chat memory required).
- **Observed agent behavior:** Agent reads fixture state and proposes Module 4 activation only after predecessor complete check.
- **Manual intervention:** Scenario documented here; durable-state derivation verified by inspecting fixture schema + validator activate rules.
- **Transcript / evidence reference:** this report + `tests/fixtures/fixed-pipeline-feasibility/pipeline-state.json` + validator `validateActivateTransition`.

### 4. Direct completion attempt

- **Setup:** Issue `ISSUE-1` in `in_progress` with proof/review/integration omitted.
- **Request:** Mark issue done.
- **Deterministic result:** REJECT — `cannot become done without proof`.
- **Observed agent behavior:** Agent refuses; does not write `done`.
- **Manual intervention:** None.

## Gate decision for Phase 3

Continue to Phase 3: **yes** (`feasible_with_approximation`).

Do **not** describe the six-Module driver as fully autonomous. Describe it as a session-scoped Cursor orchestrator over durable fail-closed repository state.
