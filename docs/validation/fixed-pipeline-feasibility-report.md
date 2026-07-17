# Fixed-pipeline feasibility report

**Phase:** 2 (+ engineering max for manual-edit gap)  
**Date:** 2026-07-17  
**Fixture:** `tests/fixtures/fixed-pipeline-feasibility/`  
**Validator:** `core/runtime/validate-application-pipeline.mjs` (`--check-consistency` + transitions)  
**Hooks:** `.githooks/pre-commit`, `.githooks/pre-push` via `scripts/install-git-hooks.sh`

## Verdict

**`feasible_with_git_hooks`** (upgraded from `feasible_with_approximation`)

Pipeline-shape parity, artifact-contract parity, gate semantics parity, tested in-session behavioral parity, **and** fail-closed git commit/push rejection of invalid `PIPELINE-STATE.json` hand-edits are achieved.

This is still **not** mechanical runtime parity with LiNKdeveloper’s persistent Ledger/orchestrator (no crash-recovery loop after Cursor closes).

## What was closed with pure engineering

| Gap | Closure |
|---|---|
| Direct manual edit of `PIPELINE-STATE.json` then commit | `pre-commit` runs `--check-consistency` and rejects |
| Push of invalid pipeline state | `pre-push` same check |
| Skip Module N while activating N+1 | Consistency ordering rule rejects |

**Evidence (2026-07-17):** throwaway repo staged a state with `assembly_planning=complete` while `intake_and_definition=pending`; hook exited non-zero with:

```text
REJECT: Invalid ordering: assembly_planning is complete but predecessor intake_and_definition is pending
pre-commit: REJECT invalid pipeline state in PIPELINE-STATE.json
HOOK_EXIT=1
HOOK_REJECT_OK
```

Install in any target repo using the fixed pipeline:

```bash
bash /path/to/IDE-Development/scripts/install-git-hooks.sh
```

## Narrow remainder (genuinely impossible without a persistent process)

The **only** remaining ungated path is a raw filesystem edit that is **never committed or pushed** (and never re-validated by a resume session). Anyone who later commits, pushes, or runs `/resume-application-pipeline` hits the validator/hooks. Closing edits that never enter git would require a persistent filesystem watcher or OS-level enforcement — that is deploy/runtime infrastructure, not session engineering.

Also still out of scope without a separate process:

- keep polling after Cursor closes
- unattended crash recovery
- Ledger-level transactional locks

## Deterministic validator result

```bash
bash scripts/feasibility/run-fixed-pipeline-feasibility.sh
```

Observed: **pass=21 fail=0** (GATE-STOP-001 + feasibility runner also green via `verify-ide-development.sh`).

## Gate decision

Continue: **yes**. Describe the driver as a session-scoped Cursor orchestrator over durable fail-closed repository state **plus git-hook enforcement for normal git workflows**.
