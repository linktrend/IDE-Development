# External-state audit (automation / Bugbot / protection)

**Status:** Active — normal-token GitOps readiness bridge; **consumer** external-state installs remain deferred until their protected rollout PRs are ready.
**Date:** 2026-08-02
**Audience:** Operators confirming rollout readiness; Verifier; Implementers (read-only)
**SOT:** `docs/CURRENT-STATUS.md` · `docs/contracts/GITHUB-APP-GITOPS-CREDENTIALS.md` · `docs/contracts/BUGBOT-MENTION-ONLY.md` · `docs/GITOPS-CONSUMER-ROLLOUT.md` · `docs/archive/work-packets/2026-08-02-work-packet-1-production-readiness.md` · `docs/work-packets/2026-08-02-work-packet-04-consumer-rollout.md`
**Tooling:** `scripts/gitops/external_state_audit.py` (existing); WP1 Lane C expanded inventory/planner/verifier coverage under owned paths
**Tests:** `scripts/tests/test-external-state-audit.sh` (+ Lane C fixture matrix when landed)

---

## Purpose

Produce a **read-only, dry-run-default** report of the normal automation credential, Bugbot, and repository-protection state required before `Linktrend Review Ready` publication can be trusted in production.

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
| Secrets | `LINKTREND_AUTOMATION_TOKEN`, `LINKTREND_BUGBOT_USER_TOKEN` | Observe Actions secret **names** only; **never** retrieve or print values |
| Bugbot dashboard | `manualTriggerOnly` | Fixture or operator confirmation; GitHub API cannot prove mention-only |
| Protections | `development-autonomous-merge` ruleset, `allow_auto_merge` | Read-only ruleset/repo metadata |
| Process env leaks | Any of the secret env names above | Warn `present_in_process_env` without printing values; refuse emit if a value would leak into JSON |

Git working-tree files are **not** external state. Workflow YAML and local scripts are out of scope for this audit.

---

## Required checklist

| ID | Category | Required observation |
|----|----------|----------------------|
| `github_auth.automation_token_secret` | github_auth | `LINKTREND_AUTOMATION_TOKEN` secret **name** listed |
| `bugbot.user_token_secret` | bugbot | `LINKTREND_BUGBOT_USER_TOKEN` secret **name** listed |
| `bugbot.manual_trigger_only` | bugbot | `manualTriggerOnly=true` (mention-only) |
| `bugbot.check_name` | bugbot | Check name is `Linktrend Review Gate` (default or matching variable) |
| `protection.development_ruleset` | protection | Active `development-autonomous-merge` requires `Linktrend Review Gate` and `Linktrend Branch Source Policy` |
| `protection.allow_auto_merge` | protection | `allow_auto_merge=true` |
| `completion.status_context` | completion | Privileged context remains `Linktrend Review Ready` (normal-token publisher from trusted workflow context only) |

Related contracts:

- Normal automation credential / fail-closed token: `docs/contracts/GITHUB-APP-GITOPS-CREDENTIALS.md`
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
  "actions_secret_names": [
    "LINKTREND_AUTOMATION_TOKEN",
    "LINKTREND_BUGBOT_USER_TOKEN"
  ],
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
              { "context": "Linktrend Review Gate" },
              { "context": "Verify IDE Development" },
              { "context": "Linktrend Branch Source Policy" }
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
4. Do **not** change branch protections or Bugbot dashboard settings from an Implementer session — Principal / operator only.
5. Carlos's restricted user identity must not publish statuses; only the normal automation token in the trusted workflow context may publish `Linktrend Review Ready`.
6. Work Packet 1 agents must not treat a green verify report as permission to roll out consumers or apply protections — consumer installs/settings apply remain WP04 / Principal-gated (packet prepared; not executed until approval).

---

## Change control

Changing checklist IDs, secret/variable names, or ready criteria is a **contract change**: update this file, `scripts/gitops/external_state_audit.py`, and `scripts/tests/test-external-state-audit.sh` together.
