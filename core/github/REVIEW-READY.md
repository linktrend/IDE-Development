# Review-ready signal (out-of-diff)

When a work branch tip is finished and eligible for the Tue/Fri Review Packager, publish a **GitHub commit status** on that exact SHA. Do **not** add a readiness file or marker commit to the feature diff.

## Why not a file in the branch

Concurrent feature branches must not fight over a shared path like `.linktrend/review-ready.json`. Readiness is low-frequency workflow metadata, not product source. That path must **not** exist, must **not** be discovered by Packager/Pull, and must **not** be written by agents.

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

## Publisher authority (Wave 2)

| Path | Who | When |
|------|-----|------|
| **App-backed publisher (production)** | GitHub App installation token inside `linktrend-review-ready-publisher.yml` | Trusted Actions context after independent re-validation |
| Local `completion_gate.py review-ready` | Same App token **only if** already present in a trusted context | Fail closed otherwise; print App-backed dispatch diagnostics |
| Carlos restricted user / `GITHUB_TOKEN` / PAT fallback | **Forbidden** for this status | Packager/Bugbot user scope unchanged; must not publish readiness |

Workflow source and validation scripts are checked out from the **protected default branch**. The untrusted issue branch supplies branch tip data and evidence only.

## App-backed dispatch contract

**Workflow file:** `.github/workflows/linktrend-review-ready-publisher.yml` (managed template: `core/github/managed-workflows/` when synced)
**Trigger:** `workflow_dispatch` only (explicit, minimally scoped, dry-run/testable)
**Input validator:** `scripts/gitops/review_ready_dispatch.py`

### Required bindings (contract)

Exact input names live in the workflow YAML / dispatch validator. The contract requires all of:

1. **This repository only** — cannot publish for another repo.
2. **Exact branch name** matching `issue/<number>-<slug>` **or** configured `phase/<slug>` (reject foreign/mutable refs and legacy `feature/`/`dev/` prefixes).
3. **Immutable SHA** — full commit SHA that must equal the current remote tip of that branch.
4. **Issue relationship** — for Issue tips, issue number consistent with the branch name (reject ambiguity). Phase tips skip GitHub Issues binding and use `phase:<slug>` in the status description only.
5. **Action** — `publish` (default) or `withdraw`. Withdraw posts non-success for the same status context and does **not** require completion evidence.
6. **Evidence** (publish only) — schema-versioned completion evidence tied to that exact SHA (see `docs/contracts/AGENT-COMPLETION.md`).
7. **Optional dry-run** — validate everything, publish/withdraw nothing.

### Fail closed (no success status)

Mismatched SHA, malformed/foreign branch, changed/missing evidence, missing App token, human-token substitution, or cross-repo/SHA attempts must fail with **no** successful `Linktrend Review Ready` status written.

### Operator / agent steps

1. Finish work; keep proof; working tree clean; push so `HEAD == origin/<branch>`.
2. Ensure the branch is verified `issue/<number>-<slug>` **or** a configured Phase tip (`phase/<slug>` by default). App publisher rejects `feature/`, `dev/`, and other legacy allowlist prefixes. If still on a legacy allowed branch, migrate with `create_issue_branch.py` / `/agentcomply` before requesting App publish — the local gate fails closed with that remediation and will not invent a doomed dispatch command.
3. Write evidence: `python3 scripts/gitops/completion_gate.py write-evidence` (or equivalent schema JSON).
4. Run `python3 scripts/gitops/completion_gate.py review-ready`.
5. If local privileged publish is unavailable **and** the branch is App-eligible, dispatch `linktrend-review-ready-publisher` with this repo's exact branch + SHA (dry-run first when testing).
6. Confirm status on that SHA: `scripts/validate-review-ready.sh <sha>`.
7. Set issue status to `review_ready` and stop — Packager opens the draft PR.

## Rollback

| Situation | Action |
|-----------|--------|
| Wrong SHA marked, or need to withdraw readiness | App-backed only: `gh workflow run linktrend-review-ready-publisher.yml -f branch=<issue/…> -f sha=<40-char> -f action=withdraw -f reason=<why> -f dry_run=false` (trusted default-branch workflow mints the App token and posts non-success for context `Linktrend Review Ready`). Local `scripts/clear-review-ready.sh [sha] [reason]` fails closed without App credentials and prints that exact route — never use `GH_TOKEN` / `GITHUB_TOKEN` / a human PAT to withdraw. |
| Bad publisher workflow on default branch | Revert or disable `linktrend-review-ready-publisher.yml` on the protected default branch; Packager continues to ignore tips without a success status |
| Suspected credential misuse | Do **not** rotate or rewrite secrets from agents; escalate to Principal / ops per `docs/contracts/GITHUB-APP-GITOPS-CREDENTIALS.md` |
| Local gate noise / incomplete work | Do not dispatch; call `completion_gate.py blocked` or continue on the issue branch |

Compatibility wrappers: `scripts/mark-review-ready.sh` requires evidence and delegates to the gate (not a pre-gate publisher). `scripts/clear-review-ready.sh` is a local fail-closed helper for withdraw diagnostics / App-token contexts — not a substitute for App authority and not a human-token status writer.

A new functional commit on the branch is automatically unready (new tip SHA has no success status) — preferred roll-forward when the tip changed intentionally.

## Backends

- **GitHub** (default): Commit Statuses API via App automation token for privileged publish
- **File** (tests): `LINKTREND_STATUS_BACKEND=file` + `LINKTREND_STATUS_DIR=...`

## Packager behavior

1. **Discover** (schedule/manual): ready tips → draft PRs only (no Bugbot, no serial CI wait)
2. **Evaluate** (PR/check): reread head → confirm readiness + fast-gate → reread head → mark ready → reread head → comment `@cursor review` once → marker only in that comment. Request accounting counts only comments with an executable trigger (`@cursor review` or `bugbot run`) **plus** `<!-- linktrend-bugbot-requested: <sha> -->`; bare historical `cursor review` + marker does **not** consume the 2-request limit.

Packager discovery remains **commit-status only**. It must not read `.linktrend/review-ready.json`.
