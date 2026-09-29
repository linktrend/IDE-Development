#!/usr/bin/env bash
# Applies core/ledger/sql/ide_ledger.sql to a throwaway local Postgres
# cluster (twice, to prove idempotency), then runs the verification and
# behaviour SQL. Never connects to a shared database.
#
# Needs Postgres server binaries (initdb, pg_ctl, psql). Set PG_BIN to their
# directory if they are not on PATH. Exits 0 with SKIP when they are missing
# unless IDE_LEDGER_SQL_REQUIRED=1.

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
SQL_DIR="$ROOT/core/ledger"

if [ -z "${PG_BIN:-}" ]; then
  if command -v initdb >/dev/null 2>&1; then
    PG_BIN="$(dirname "$(command -v initdb)")"
  else
    PG_BIN="$(ls -d /usr/lib/postgresql/*/bin 2>/dev/null | sort -V | tail -1 || true)"
  fi
fi

if [ -z "$PG_BIN" ] || [ ! -x "$PG_BIN/initdb" ]; then
  if [ "${IDE_LEDGER_SQL_REQUIRED:-0}" = "1" ]; then
    echo "FAIL: Postgres binaries not found (set PG_BIN)" >&2
    exit 1
  fi
  echo "SKIP: Postgres binaries not found; ide_ledger SQL test not run"
  exit 0
fi

work="$(mktemp -d "${TMPDIR:-/tmp}/ide-ledger-pg.XXXXXX")"
cleanup() {
  "$PG_BIN/pg_ctl" -D "$work/data" -m immediate stop >/dev/null 2>&1 || true
  rm -rf "$work"
}
trap cleanup EXIT

"$PG_BIN/initdb" -D "$work/data" -U postgres -A trust >/dev/null
"$PG_BIN/pg_ctl" -D "$work/data" -l "$work/pg.log" \
  -o "-k $work -c listen_addresses='' -c port=54329" -w start >/dev/null

export PGOPTIONS="-c client_min_messages=warning"

run_psql() {
  "$PG_BIN/psql" -X -q -v ON_ERROR_STOP=1 -h "$work" -p 54329 -U postgres -d postgres "$@"
}

# Supabase API roles, so the revokes and verification paths are exercised.
run_psql -c "create role anon nologin; create role authenticated nologin; create role service_role nologin;"

run_psql -f "$SQL_DIR/sql/ide_ledger.sql"
run_psql -f "$SQL_DIR/sql/ide_ledger.sql"
run_psql -At -f "$SQL_DIR/sql/ide_ledger.verify.sql"
run_psql -At -f "$SQL_DIR/tests/ide_ledger_behaviour.sql"
run_psql -f "$SQL_DIR/sql/ide_ledger.sql"
run_psql -At -f "$SQL_DIR/sql/ide_ledger.verify.sql"

echo "PASS: ide_ledger SQL applied twice, verified, behaviour tested, re-applied on data"
