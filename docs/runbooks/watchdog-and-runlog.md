# Watchdog and run log (v3 Wave 0.6)

The orchestrator records every Issue attempt and checks, on a timer, for stuck
runs, failure loops and work that is not pushed.

## Run log

One record per attempt, format `ide-runlog/v1`
(`core/contracts/RUN-LOG-RECORD.schema.json`). Fields mirror `ide_ledger.run`:

| Field | Meaning |
|---|---|
| `issue`, `attempt`, `run_key` | Ledger Issue ID (`IDE-<n>`), attempt number, idempotency key |
| `executor` | `codex-cli`, `cursor-002`, `cursor-001-subagent`, `orchestrator`, `other` |
| `requested_model`, `reasoning_effort` | What the orchestrator asked for, resolved at dispatch time |
| `self_reported_model` | What the agent said it was (providers do not report the model that ran) |
| `repair_rung` | 0 = first worker; 1 = Sol/Opus; 2 = the other of Sol/Opus |
| `result` | `running`, `success`, `failure`, `stalled`, `cancelled` |
| `head_sha`, `branch`, `external_ref` | Pushed commit, `issue/IDE-<n>-<slug>`, agent or session ID |
| `failure_summary`, `cost_usd` | Short reason; cost when known |
| `started_at`, `updated_at`, `ended_at` | UTC timestamps; `updated_at` moves on every heartbeat |

**Pilot storage.** Until `ide_ledger` is applied (Wave 3.1) records are files
in the Project store: `<root>/<ISSUE>/attempt-<NNN>.json`. The root is
`--root`, else `$IDE_RUNLOG_DIR`, else the pilot Project store's
`internal/runlog/` (`/cursor/stores/bc-802cc0ab-6b61-4d1c-922d-43ab3b8ff094/internal/runlog`).
The default is the resolved store path, not `/cursor/stores/self`, which points
at a different store on each worker VM. Other Projects set `IDE_RUNLOG_DIR` to
their own resolved store path. Only the orchestrator writes it.

```bash
RL=scripts/orchestrator/runlog.py
key=$(python3 $RL start --issue IDE-12 --executor cursor-002 \
  --requested-model grok-4.7 --reasoning-effort medium \
  --branch issue/IDE-12-fix-login --external-ref bc-... | jq -r .run_key)
python3 $RL heartbeat --issue IDE-12 --run-key "$key"          # while polling the worker
python3 $RL finish --issue IDE-12 --run-key "$key" --result success \
  --self-reported-model "Grok 4.7" --head-sha 1a2b3c4
```

**Import into the Ledger** once it is live: `python3 $RL export-sql` prints
`ide_ledger.start_run` / `finish_run` calls in one transaction. They are
idempotent on `run_key`, so the import can be re-run. The Issues must exist in
the Ledger first (`create_issue` with `p_number` keeps pilot IDs).

## Watchdog

```bash
python3 scripts/orchestrator/watchdog.py --repo /workspace --fetch --exit-zero
```

Checks:

- **Stalled runs** — `running` with no heartbeat for `--stall-minutes` (default 90).
- **Repeated failures** — consecutive `failure`/`stalled` attempts at the same repair rung, checked against the repair ladder for the model the Issue started on:
  - Luna/Grok start: rung 0 allows `--max-failures` tries (default 3), then rung 1 (Sol/Opus) gets one, then "flag Carlos".
  - Sol/Opus start: rung 0 allows one try, then rung 2 (the other of Sol/Opus) gets one, then "flag Carlos". Rung 1 is skipped because the Issue is already on a strong model.

  The report recommends the next rung or "flag Carlos".
- **Unpushed work** — for each `--repo` (all worktrees): dirty `issue/*` worktrees, `issue/*` branches never pushed, or ahead of `origin`. Without `--fetch` it compares against the last fetched refs.

Output is one JSON report (`kind: ide-watchdog-report`). Exit 0 = clean,
1 = findings, 2 = watchdog error; `--exit-zero` returns 0 whenever the check
itself ran.

The watchdog only reads. The orchestrator acts on each finding: poll or
restart the worker, finish the attempt as `stalled`, move to the next repair
rung, push, or flag Carlos. Once the Ledger is live it also records the
finding with `ide_ledger.raise_exception`.

## Timer

The orchestrator subscribes one recurring timer (cursor-subscriptions
`subscribe_timer`), for example name `ide-watchdog`, `delaySeconds: 1800`,
with a prompt such as:

> Run `python3 scripts/orchestrator/watchdog.py --repo /workspace --fetch --exit-zero`. If `ok` is false, handle each finding (hand routine follow-up to a cheap helper), record what you did, then end the turn.

Re-subscribing with the same name replaces the timer. Remove it with
`unsubscribe` when the Project is idle.
