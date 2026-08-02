# Wave 2 — App-backed completion bridge

## Outcome

Make a normal local implementer capable of completing an already-verified
issue branch without possessing a privileged credential.  The GitHub App must
publish `Linktrend Review Ready` from a trusted GitHub Actions context only
after it independently validates the requested branch, immutable SHA, and
machine-readable completion evidence.

## Scope and non-negotiable constraints

- The GitHub App remains the only identity for privileged status publication.
- Carlos's restricted user identity must not publish statuses, create this
  PR, merge, promote, or change settings; its existing Packager/Bugbot scope
  remains unchanged.
- The workflow source and validation scripts are checked out from the protected
  default branch.  The untrusted issue branch supplies data only.
- Validate branch naming, exact remote SHA, evidence schema, clean/pushed
  status, and issue/branch relationship; reject ambiguity or mutable refs.
- The dispatch interface is explicit, minimally scoped, dry-run/testable, and
  cannot be used to publish a status for another repository or SHA.
- Do not create, alter, or expose App credentials, secrets, variables, Bugbot
  settings, branch/ruleset settings, consumers, PRs, or promotions.
- Keep the established local `completion_gate.py review-ready` fail-closed.
  It must explain the App-backed route when local credentials are unavailable.
- Reconcile the stale `.linktrend/review-ready.json` wording in active canonical
  docs and managed payloads.  Historical archive references may remain.

## Parallel packets (Cursor Grok 4.5 High only)

1. Trusted workflow and dispatch-input validation.
2. App-backed publisher implementation and local gate diagnostics.
3. Test fixtures and adversarial validation tests.
4. Packager/readiness compatibility and exact-SHA integration tests.
5. Read-only external-state audit/report tooling and contract tests.
6. Documentation, managed-runtime synchronization, and rollout/rollback runbook.

## Acceptance evidence

- A dispatch from protected workflow source succeeds only for a real,
  pushed `issue/<number>-<slug>` branch, its exact SHA, and valid evidence.
- Mismatched SHA, malformed/foreign branch, changed evidence, missing App
  token, and local-token substitution all fail closed with no success status.
- The generated status is exactly `Linktrend Review Ready` on the immutable
  requested SHA, so existing Packager discovery can use it unchanged.
- Existing lifecycle and Wave 1 portable-core tests remain green.
- New workflow/static/adversarial tests pass without live GitHub mutation.

## Documentation packet (packet 6) — dispatch and rollback

Canonical docs (owned by this packet):

| Path | Role |
|------|------|
| `docs/contracts/AGENT-COMPLETION.md` | Fail-closed gate + App-backed route; no readiness file |
| `core/github/REVIEW-READY.md` | Status contract, publisher authority, dispatch, rollback |
| `docs/AUTONOMOUS-GIT-OPERATIONS.md` | Ship/Packager doctrine |
| `docs/OPEN-ISSUES.md` | Append-only build log item for Issue #44 |
| `core/github/managed-runtime/*` | Managed-core v2 agent payloads |

### Dispatch (rollout)

1. Land workflow + scripts on the protected default branch (via Integrator after review) — agents must not create credentials.
2. Implementer: push clean `issue/<n>-<slug>` tip → write evidence → `completion_gate.py review-ready`.
3. When local privileged publish is unavailable, `workflow_dispatch` **`linktrend-review-ready-publisher`** with this repo's exact branch + immutable SHA (dry-run first in test).
4. Workflow (default-branch source) re-validates and App-publishes `Linktrend Review Ready` on that SHA only.
5. Packager discovery unchanged (commit status only).

### Rollback

1. Withdraw a bad mark via App-backed dispatch only: `gh workflow run linktrend-review-ready-publisher.yml -f branch=<issue/…> -f sha=<40-char> -f action=withdraw -f reason=<why>` (dry-run first in test). Local `scripts/clear-review-ready.sh` fails closed without App credentials and prints that route — never withdraw with `GH_TOKEN`/`GITHUB_TOKEN`/human PAT.
2. Disable or revert `linktrend-review-ready-publisher.yml` on the default branch if the publisher misbehaves; tips without success status stay ineligible.
3. Intentional tip change: new commit is automatically unready — preferred roll-forward.
4. Credential incidents: escalate to Principal/ops; agents do not rotate secrets.

### Stale readiness-file language

Active canonical docs and managed-runtime payloads must not positively instruct creating, discovering, or consulting `.linktrend/review-ready.json`. Historical ADR/OPEN-ISSUES bullets may retain obsolete text only when a dated correction supersedes them (existing 2026-07-28 corrections remain valid).

## Handoff

This is an implementation wave only.  Commit and push the issue branch; do
not open a PR, trigger Bugbot, mark review-ready, merge, promote, or touch a
consumer.  Codex independently verifies before any review-ready request.
