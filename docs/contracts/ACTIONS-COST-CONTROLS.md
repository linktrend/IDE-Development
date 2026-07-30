# Actions Cost Controls

**Status:** Active guidance
**Date:** 2026-07-30
**Owner:** IDE Development

## Reality check

There is **no** supported GitHub billing API for agents to read minute balances in Free-tier orgs reliably. Do **not** invent fake billing APIs or scrape billing pages.

## Controls we can enforce in YAML

1. **`timeout-minutes`** on every job (fail closed on runaway runs).
2. **`retention-days: 3`–`5`** on `actions/upload-artifact` (shorter = less storage).
3. **Tight `jobs.*.if`** on promote workflows so irrelevant `check_run` / `workflow_run` / non-promote PR events skip resolve/promote (minutes + self-wake risk).
4. **Filter own outcome check names** (`Linktrend * Outcome`, Packager/Integrator Result) so result checks do not re-wake the same workflow.
5. **Concurrency groups** with `cancel-in-progress: false` for promote (correctness over thrash).
6. Prefer **schedule + workflow_dispatch** over high-churn events when possible.

## Notification / wake event types (managed promote)

Allowed wake sources (still filtered by resolve relevance):

- `schedule`
- `workflow_dispatch`
- `pull_request_target` on promote heads (`promote/*`)
- `workflow_run` completed for named gate workflows (`CI`, `Branch Source Policy`) on promote heads
- external `check_run` completed (never `github-actions` app; never own outcome check names)

## Historical failure note

Using `${{ env.* }}` at **job-level** `env:` is invalid in GitHub Actions and can produce **zero-job** runs on push (expression errors). Job env must use `vars`/`secrets`/`github`/`needs`/`steps` contexts only; move `env.*` references into step `env:`.

## Operator monitoring

Use GitHub org/repo Actions usage UI and email budget alerts. Lisa may surface `Issues` when workflows are disabled for billing, but cannot query a secret billing meter from this contract.
