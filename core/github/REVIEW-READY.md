# Review-ready signal (out-of-diff)

When a work branch tip is finished and eligible for the Tue/Fri Review Packager, publish a **GitHub commit status** on that exact SHA. Do **not** add a readiness file or marker commit to the feature diff.

## Why not a file in the branch

Concurrent feature branches must not fight over a shared path like `.linktrend/review-ready.json`. Readiness is low-frequency workflow metadata, not product source.

## Status contract

| Field | Value |
|-------|--------|
| Context | `Linktrend Review Ready` |
| State when ready | `success` |
| Description | `issue=<id>` plus optional notes |
| Withdrawal | post `failure` (or `error`) for the same context on that SHA |

## Validity

- Packager accepts only the **latest successful** `Linktrend Review Ready` status on the **current branch tip SHA**.
- A later commit is automatically unready (new SHA has no success status).
- Repeated marking of the same SHA is idempotent.

## Agent checklist

1. Acceptance criteria + proof satisfied
2. Full working tree clean
3. Push so `HEAD == origin/<branch>`
4. `scripts/mark-review-ready.sh <issue-id> [notes]`
5. Set issue status to `review_ready`
6. Stop — Packager opens a **draft** PR; Bugbot only after fast-gate on that exact SHA

Withdraw: `scripts/clear-review-ready.sh [sha] [reason]`

Validate: `scripts/validate-review-ready.sh [sha]`

## Backends

- **GitHub** (default): Commit Statuses API
- **File** (tests): `LINKTREND_STATUS_BACKEND=file` + `LINKTREND_STATUS_DIR=...`

## Packager behavior

1. **Discover** (schedule/manual): ready tips → draft PRs only (no Bugbot, no serial CI wait)
2. **Evaluate** (PR/check): reread head → confirm readiness + fast-gate → reread head → mark ready → reread head → comment `cursor review` once → marker only in that comment
