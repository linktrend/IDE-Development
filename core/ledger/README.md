# ide_ledger — IDE Development Program Ledger

The Ledger is the record of truth for Issues, Phases, Runs, owners,
dependencies, decisions and exceptions. It lives in the Platform Supabase
project as its own schema, `ide_ledger`.

IDE Development owns the design. The SQL here is applied **only** through
LiNKplatform's migration flow (v3 Wave 3.1). Do not apply it to any shared
database by hand.

## Files

| Path | Purpose |
|---|---|
| `sql/ide_ledger.sql` | Schema, RPC functions, restricted role grants. Idempotent. |
| `sql/ide_ledger.verify.sql` | Read-only invariants (RLS on, no table grants, no PUBLIC EXECUTE, helpers private). Copy to Platform `supabase/verification/`. |
| `tests/ide_ledger_behaviour.sql` | Behaviour test run as the restricted role. |
| `../../scripts/ledger/test-ide-ledger-sql.sh` | Runs all of the above against a throwaway local Postgres (`IDE_SETUP_POSTGRES=1 bash scripts/setup.sh` installs it). |

## Model

- `repo` — one row per repo, with its ID prefix (`IDE` here). Issue IDs are `<prefix>-<n>`; branches are `issue/<prefix>-<n>-<slug>` (generated column).
- `phase` — ordered step of work; links the one-per-Phase GitHub Issue (`github_issue_number`).
- `issue` — atomic task with one `owner`, a state and the current repair rung (0 = first worker, 1–3 = ladder steps).
- `issue_dependency` — "A depends on B" edges; cycles are rejected.
- `run` — one row per attempt: executor, requested model, the model's self-report, result, head SHA, cost. `run_key` is client-generated so writes and pilot run-log imports are idempotent.
- `decision`, `exception` — decisions taken and problems raised (for example by the watchdog).
- `audit_log` — every RPC call, with the session user.

## Access

- All tables have RLS enabled with no policies and no grants.
- Every function is `SECURITY DEFINER` with `search_path = ''`.
- `ide_ledger_orchestrator` (created `NOLOGIN`) has `USAGE` on the schema and `EXECUTE` on the public RPCs only. Functions whose names start with `_` are internal.
- The login credential is created by the Platform migration flow (for example a login role granted membership in `ide_ledger_orchestrator`) and handed to the orchestrator as a Cursor runtime secret. No password lives in this repo. Workers never get it.

## RPCs

Writes: `register_repo`, `upsert_owner`, `upsert_phase`, `create_issue`, `set_issue_state`, `set_issue_owner`, `set_issue_phase`, `add_dependency`, `remove_dependency`, `start_run`, `finish_run`, `record_decision`, `raise_exception`, `resolve_exception`.

Reads: `get_issue`, `phase_summary`, `list_stalled_runs`.

## Local test

```bash
bash scripts/ledger/test-ide-ledger-sql.sh
```

Needs `initdb`, `pg_ctl` and `psql` (set `PG_BIN` if they are not on `PATH`). Without them it prints `SKIP`; set `IDE_LEDGER_SQL_REQUIRED=1` to fail instead.
