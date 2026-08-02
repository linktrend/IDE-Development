# External-state audit (App / Bugbot / protection)

**Status:** Active — Wave 2 App-backed completion bridge; WP1 plan/verify complete; WP02 IDE Development live readiness closed under packet; **consumer** external-state apply / installs remain deferred (WP04 prepared / not executed)
**Date:** 2026-08-02
**Audience:** Operators confirming rollout readiness; Verifier; Implementers (read-only)
**SOT:** `docs/CURRENT-STATUS.md` · `docs/contracts/GITHUB-APP-GITOPS-CREDENTIALS.md` · `docs/contracts/BUGBOT-MENTION-ONLY.md` · `docs/GITOPS-CONSUMER-ROLLOUT.md` · `docs/archive/work-packets/2026-08-02-work-packet-1-production-readiness.md` · `docs/work-packets/2026-08-02-work-packet-04-consumer-rollout.md`
**Tooling:** `scripts/gitops/external_state_audit.py` (existing); WP1 Lane C expanded inventory/planner/verifier coverage under owned paths
**Tests:** `scripts/tests/test-external-state-audit.sh` (+ Lane C fixture matrix when landed)

---

## Purpose

Produce a **read-only, dry-run-default** report of the external GitHub App, Bugbot, and repository-protection state required before App-backed `Linktrend Review Ready` publication can be trusted in production.

This tool **reports**. It does **not** create Apps, secrets, variables, Bugbot settings, rulesets, PRs, statuses, or promotions.

### Work Packet 1 boundary (mandatory)

| Mode | WP1 allowed? |
|---|---|
| `plan` / dry-run checklist | Yes |
| `report` / `verify` (fixture or live GET) | Yes — read-only |
| Live audit of `linktrend/IDE-Development` | Yes — identifiers/posture/conclusions only; **never credentials** |
| `apply` / mutate / create / delete | **No** — out of WP1 entirely |

Every unverifiable setting must be reported as `unknown` or `blocked`, never assumed compliant. Repository-specific required checks and unrelated protection rules must be preserved in plans (union, do not delete).

Consumer rollout remains deferred; external-state readiness does **not** authorize consumer installs.

---

## External-state boundary

| Kind | Examples | Audit behavior |
|------|----------|----------------|
| Non-secret config | `LINKTREND_GITOPS_APP_ID` variable | May observe presence + numeric shape; does not echo unnecessary detail |
| Secrets | `LINKTREND_GITOPS_APP_PRIVATE_KEY`, `LINKTREND_BUGBOT_USER_TOKEN` | Observe Actions secret **names** only; **never** retrieve or print values |
| Installations | GitHub App installed on the repo | Presence metadata only |
| Bugbot dashboard | `manualTriggerOnly` | Fixture or operator confirmation; GitHub API cannot prove mention-only |
| Protections | `development-autonomous-merge` ruleset, `allow_auto_merge` | Read-only ruleset/repo metadata |
| Process env leaks | Any of the secret env names above | Warn `present_in_process_env` without printing values; refuse emit if a value would leak into JSON |

Git working-tree files are **not** external state. Workflow YAML and local scripts are out of scope for this audit.

---

## Required checklist

| ID | Category | Required observation |
|----|----------|----------------------|
| `github_app.app_id_variable` | github_app | `LINKTREND_GITOPS_APP_ID` present and numeric |
| `github_app.private_key_secret` | github_app | `LINKTREND_GITOPS_APP_PRIVATE_KEY` secret **name** listed |
| `github_app.installation` | github_app | App installation present on the repository |
| `bugbot.user_token_secret` | bugbot | `LINKTREND_BUGBOT_USER_TOKEN` secret **name** listed |
| `bugbot.manual_trigger_only` | bugbot | `manualTriggerOnly=true` (mention-only) |
| `bugbot.check_name` | bugbot | Check name is `Cursor Bugbot` (default or matching variable) |
| `protection.development_ruleset` | protection | Active `development-autonomous-merge` requires `Cursor Bugbot` and `Enforce allowed PR source branches` |
| `protection.allow_auto_merge` | protection | `allow_auto_merge=true` |
| `completion.status_context` | completion | Privileged context remains `Linktrend Review Ready` (App-backed publisher only) |

Related contracts:

- App minting / fail-closed automation token: `docs/contracts/GITHUB-APP-GITOPS-CREDENTIALS.md`
- Bugbot mention-only: `docs/contracts/BUGBOT-MENTION-ONLY.md`
- Agent completion / status context: `docs/contracts/AGENT-COMPLETION.md`

---

## Modes

| Mode | Mutates? | Live calls? | Exit 0 when |
|------|----------|-------------|-------------|
| `report` (default) | **Never** | Only with `--live` or `--fixture-dir` | Report JSON emitted |
| `verify` | **Never** | Only with `--live` or `--fixture-dir` | Every required check `status=ok` |

Default without `--live` / `--fixture-dir` is **dry-run**: emit the checklist with `observed=unchecked` / `status=unchecked`. This is intentional — agents must not probe production settings casually, and tests must not depend on live GitHub.

There is **no** `apply`, `fix`, `create`, or `delete` mode. Any mutating HTTP method is refused (`exit 5`).

**Work Packet 1:** treat “no apply” as a hard process rule even if future tooling adds an apply path — WP1 evidence must show zero mutations.

---

## CLI

```bash
# Default dry-run checklist (no live GitHub calls, no mutations)
python3 scripts/gitops/external_state_audit.py
python3 scripts/gitops/external_state_audit.py report --repo linktrend/IDE-Development

# Offline / CI fixtures
python3 scripts/gitops/external_state_audit.py verify \
  --repo linktrend/Fixture \
  --fixture-dir /path/to/fixture

# Operator read-only live GETs (still never mutates; never prints secrets)
python3 scripts/gitops/external_state_audit.py verify --repo linktrend/IDE-Development --live
```

### Fixture shape (`state.json`)

```json
{
  "actions_variables": [
    { "name": "LINKTREND_GITOPS_APP_ID", "value": "12345" }
  ],
  "actions_secret_names": [
    "LINKTREND_GITOPS_APP_PRIVATE_KEY",
    "LINKTREND_BUGBOT_USER_TOKEN"
  ],
  "installation": { "id": 1, "app_slug": "linktrend-gitops" },
  "bugbot": { "manualTriggerOnly": true, "enabled": true },
  "rulesets": [
    { "id": 10, "name": "development-autonomous-merge", "enforcement": "active" }
  ],
  "ruleset_details": {
    "10": {
      "id": 10,
      "name": "development-autonomous-merge",
      "enforcement": "active",
      "rules": [
        {
          "type": "required_status_checks",
          "parameters": {
            "required_status_checks": [
              { "context": "Cursor Bugbot" },
              { "context": "Verify IDE Development" },
              { "context": "Enforce allowed PR source branches" }
            ]
          }
        }
      ]
    }
  },
  "repo": { "allow_auto_merge": true }
}
```

Never place secret **values** in fixtures. Use `actions_secret_names` (names only).

---

## Report schema (`schemaVersion: 1`)

Machine-readable JSON on stdout (optional `--json-output PATH`):

| Field | Meaning |
|-------|---------|
| `dryRun` | Always `true` |
| `mutations` | Always `[]` |
| `source` | `dry-run` \| `fixture` \| `live` |
| `checks[]` | Evaluated rows with `id`, `category`, `required`, `expected`, `observed`, `status`, `detail` |
| `summary.ready` | `true` only when every required check is `ok` |
| `warnings` | Secret-env presence warnings (names only) |

### Exit codes

| Code | Meaning |
|------|---------|
| `0` | `report` emitted, or `verify` ready |
| `3` | `verify` not ready (missing / drift / unchecked required items) |
| `5` | Refused (e.g. `--live` with `--fixture-dir`, or mutate attempt) |
| `1` | Unexpected failure |

---

## Agent and operator prohibitions

1. Do **not** use this tool as a license to create or rotate credentials.
2. Do **not** print, artifact, or commit secret values, PEMs, or PATs.
3. Do **not** treat `summary.ready=true` on a fixture as proof of production readiness.
4. Do **not** change branch protections, Bugbot dashboard settings, or App installs from an Implementer session — Principal / operator only.
5. Carlos's restricted user identity must not publish statuses; the GitHub App remains the only privileged publisher for `Linktrend Review Ready`.
6. Work Packet 1 agents must not treat a green verify report as permission to roll out consumers or apply protections — consumer installs/settings apply remain WP04 / Principal-gated (packet prepared; not executed until approval).

---

## Change control

Changing checklist IDs, secret/variable names, or ready criteria is a **contract change**: update this file, `scripts/gitops/external_state_audit.py`, and `scripts/tests/test-external-state-audit.sh` together.
