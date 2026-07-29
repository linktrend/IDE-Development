# Agent Completion Contract

**Status:** Active
**Date:** 2026-07-30
**Owner:** IDE Development (GitOps)

## Purpose

Define how Implementers finish a work session without opening PRs or falsely claiming review-ready.

## Authority

`review-ready` is the authoritative, fail-closed completion path. The gate validates the exact pushed branch state and machine-readable evidence before it publishes **`Linktrend Review Ready`** with `scripts/gitops/readiness_status.py`.

Bare `--tests-ok`, `COMPLETION_TESTS_OK=1`, and arbitrary text in `COMPLETION_EVIDENCE` are not sufficient production proof.

## Modes (`scripts/gitops/completion_gate.py`)

| Mode | Meaning | Exit |
|---|---|---|
| `checkpoint` | Commit+push save; work unfinished | `0` ok |
| `review-ready` | Validate finished work, then publish **`Linktrend Review Ready`** | `0` ok, `78` incomplete, `1` failed |
| `blocked` | Write durable blocker JSON | `2` blocked |
| `status` | Report current completion state | `0` ok |
| `write-evidence` | Write schema-versioned completion evidence for current `HEAD` | `0` ok |

Exit codes: `0` ok, `78` incomplete, `2` blocked, `1` failed.

## States

- `checkpointed_unfinished`
- `review_ready`
- `blocked`
- `failed`

## `review_ready` requirements (all required)

Order is part of the contract:

1. Verify exact pushed SHA and branch state:
   - `HEAD` resolves to a SHA.
   - working tree is clean.
   - branch is not `development`, `staging`, `main`, or detached.
   - `HEAD == origin/<branch>` after fetch.
2. Require machine-readable evidence JSON tied to that exact `HEAD` SHA.
3. Only after those checks pass, publish **`Linktrend Review Ready`** through `scripts/gitops/readiness_status.py`.

The successful status is an output of the gate, not an input prerequisite.

## Evidence schema (`schemaVersion: 1`)

Completion evidence must be JSON and must be tied to the exact `HEAD` being marked:

```json
{
  "schemaVersion": 1,
  "headSha": "<exact HEAD SHA>",
  "classification": "tests",
  "acceptance": "Acceptance criteria summary",
  "commands": [
    {
      "cmd": "scripts/tests/test-gitops-lifecycle.sh",
      "exitCode": 0,
      "evidencePath": ".linktrend/test-gitops-lifecycle.out"
    }
  ]
}
```

Allowed `classification` values:

- `tests`: normal implementation proof. Every command must have `exitCode: 0`.
- `docs_only`: documentation-only proof. It still records validation commands and must include `docsOnlyJustification` with at least 20 characters.

## Hard rules

- Implementers **never** open or update PRs. Review Packager opens PRs.
- Ship waves = checkpoint only (no Bugbot, no review-ready unless truly finished).
- Incomplete review-ready claims must fail closed (exit `78`), not soft-succeed.
- Agents call `python3 scripts/gitops/completion_gate.py review-ready` directly, or call `write-evidence` first and then `review-ready`.
- `scripts/mark-review-ready.sh` is only a compatibility wrapper. It requires an evidence file and delegates to the gate. It must never be used as a pre-gate publisher.

## Automatic completion behavior for agents

When an issue appears complete:

1. Run the appropriate tests/checks for the touched surface.
2. Repair ordinary failures automatically, with at most **3** bounded repair cycles.
3. Write machine-readable evidence with `completion_gate.py write-evidence` or an equivalent schema-versioned JSON file under `.linktrend/`.
4. Call `python3 scripts/gitops/completion_gate.py review-ready` only after validation succeeds. The gate publishes the status.
5. If validation or repair cannot complete, leave the branch ineligible and write a durable blocker:

```bash
python3 scripts/gitops/completion_gate.py blocked \
  --reason "why completion is blocked" \
  --attempted-repairs 3
```

The blocker is written to `.linktrend/completion-blocker.json`.

## Related

- `docs/AUTONOMOUS-GIT-OPERATIONS.md`
- `core/github/REVIEW-READY.md`
- `docs/contracts/REPAIR-DISPATCHER.md`

## Blocked completion (local durable)

`completion_gate.py blocked` writes `.linktrend/completion-blocker.json` under the workdir.
`.linktrend/` is **gitignored** so the blocker is durable on disk without risk of accidental commit.
Do not force-add or commit that path.
