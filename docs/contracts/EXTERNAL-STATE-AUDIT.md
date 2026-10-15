# External-state audit (automation and protection)

**Status:** Active, read-only readiness bridge for GitHub automation and repository protection.
**Audience:** Operators confirming external state; verifiers and implementers (read-only).
**Tool:** `scripts/gitops/external_state_audit.py`.

## Purpose and limits

The audit reports observable normal automation credential, GitHub App,
repository-protection, and workflow state. It does not create Apps, secrets,
variables, provider settings, rulesets, pull requests, statuses, or promotions.
Its report always has `mutations: []`; `apply` and mutating HTTP methods are
refused.

The v3 package has no managed Bugbot invocation or Bugbot eligibility check.
The audit emits `bugbot.provider_coverage` as `unknown` and
`unobservable_via_github_api`: GitHub cannot establish Cursor account/dashboard
provider state. This informational row is not a readiness gate. It does not
claim Bugbot is disabled, and old fixture values for `bugbot`, legacy secret
names, or old check-name variables are ignored. The legacy
[Bugbot retirement notice](BUGBOT-MENTION-ONLY.md) supersedes the historical
mention-only instructions.

The audit still checks for the `LINKTREND_AUTOMATION_TOKEN` Actions secret name
only; secret values are never retrieved or printed. Secret-like process
environment values are redacted from output. Repository-specific protection
rules and required checks must be preserved when comparing desired protection
state, including the `development-autonomous-merge` ruleset.

## Modes

| Mode | Mutates? | Live calls? | Exit 0 when |
|---|---|---|---|
| `report` (default) | Never | Only with `--live` or `--fixture-dir` | Report JSON emitted |
| `plan` | Never | Only with `--live` or `--fixture-dir` | Plan JSON emitted |
| `verify` | Never | Only with `--live` or `--fixture-dir` | Every required check is ready |
| `apply` | Never | No | Never; refused with exit 5 |

Without `--live` or `--fixture-dir`, the tool emits a dry-run report with
unchecked observations. Use fixtures for offline checks. Live mode is GET-only.
A green fixture report is not evidence of production readiness or authorization
to install consumers or alter settings.

## CLI

```bash
python3 scripts/gitops/external_state_audit.py report --repo linktrend/IDE-Development
python3 scripts/gitops/external_state_audit.py verify \
  --repo linktrend/Fixture --fixture-dir /path/to/fixture
python3 scripts/gitops/external_state_audit.py verify \
  --repo linktrend/IDE-Development --live
```

Fixture `state.json` may contain historical `bugbot` properties, but the audit
ignores them and does not interpret them as provider evidence. Never place
secret values in fixtures.

## Agent and operator prohibitions

1. Do not use this tool as a license to create or rotate credentials.
2. Do not print, artifact, or commit secret values, PEMs, or PATs.
3. Do not treat `summary.ready=true` on a fixture as production readiness.
4. Do not change branch protections or external Cursor provider settings from an Implementer session; the Principal/operator owns those changes.
5. Do not use historical Bugbot credentials, checks, mention commands, or configuration as part of v3 automation.
6. Do not treat a green audit report as permission to roll out consumers or apply protections.
