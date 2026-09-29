# Phase Issue convention (v3 Wave 0.7)

GitHub shows **one Issue per Phase**. It is the readable summary Carlos can
follow. Per-Issue detail (state, owner, attempts, models, results, decisions,
exceptions) lives only in the Ledger, `ide_ledger`
(`core/ledger/README.md`).

## Rules

- The orchestrator opens the Phase Issue from `.github/ISSUE_TEMPLATE/phase-summary.yml` when the Phase is planned, and records its number in the Ledger (`ide_ledger.upsert_phase(..., p_github_issue_number)`).
- Title: `[Phase <prefix>/<phase_key>] <title>`, for example `[Phase IDE/0.5] Ledger design`. Label: `phase`.
- Ledger Issues are **not** GitHub Issues. They are rows in the table, identified by Ledger ID (`IDE-<n>`), with branch `issue/IDE-<n>-<slug>`.
- The "Ledger Issues" table is regenerated from `ide_ledger.phase_summary(prefix, phase_key)` whenever an Issue changes state. Until the Ledger is live (Wave 3.1), the orchestrator fills it from its plan and the pilot run log.
- Phase PRs into `development` reference the Phase Issue (`Refs #<n>`); the last PR of the Phase uses `Closes #<n>` once all acceptance checks pass.
- Decisions and exceptions are listed by Ledger ID with one line each; the Ledger holds the detail.
- Workers never edit Phase Issues.

## Example table

| Ledger ID | Title | Owner | State | Depends on | Branch |
|---|---|---|---|---|---|
| IDE-4 | Ledger schema | project:ide-development | in_review | — | `issue/IDE-4-ledger-schema` |
| IDE-5 | Watchdog and run log | project:ide-development | in_review | IDE-4 | `issue/IDE-5-watchdog-runlog` |
