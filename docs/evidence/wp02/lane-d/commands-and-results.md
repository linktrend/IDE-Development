# WP02 Lane D — Commands and Results

**Worktree:** `/Users/linktrend/Projects/IDE Development/.git/linktrend-worktrees/issue-68-work-packet-02-integration-lineage-stale-cleanup`  
**Binding timestamp:** `2026-08-02T03:12:13Z`  
**HEAD / source SHA:** `9cd3fec75075c6910b5a3bbb09b582e4cb3c94e4`  
**Tool extract:** `/tmp/wp02-lane-d-wp01-tools` from WP01 `89956878c54ff45e4aef1ff42883d209221b7a30`  
**Secrets:** none printed; values excluded from all evidence

## 1. Tool extract (WP01 tip → `/tmp`)

```bash
git show 89956878c54ff45e4aef1ff42883d209221b7a30:scripts/gitops/external_state_audit.py
git show 89956878…:scripts/gitops/repository_protection.py
git show 89956878…:scripts/manage-repository-protections.sh
git show 89956878…:scripts/gitops/resolve_automation_token.sh
# (+ related contracts / plan helpers)
```

**Result:** OK — local WP02 `external_state_audit.py` differs from WP01; live audit used WP01 extract under `/tmp` only (no shared WP02 path mutation outside `docs/evidence/wp02/lane-d/**`).

## 2. Process-env ambient token presence (names only)

Checked: `GH_TOKEN`, `GITHUB_TOKEN`, `LINKTREND_GITOPS_APP_PRIVATE_KEY`, `LINKTREND_BUGBOT_USER_TOKEN`, `LINKTREND_APP_TOKEN`, `AUTOMATION_TOKEN`, `BUGBOT_USER_TOKEN`.

**Result:** all **absent** from process environment.

## 3. `gh` auth identity (redacted)

```bash
gh auth status   # token value redacted
gh api user --jq '{login,id,type}'
gh api -i user   # captured X-Oauth-Scopes header only
```

**Result:** account `linktrend` via **keyring**; scopes `admin:repo_hook, gist, read:org, repo, workflow`. Not an App installation token.

## 4. Live external-state audit

```bash
python3 /tmp/wp02-lane-d-wp01-tools/scripts/gitops/external_state_audit.py report \
  --repo linktrend/IDE-Development --live \
  --json-output …/lane-d/raw/external-state-audit-live.raw.json --human
# exit 0

python3 …/external_state_audit.py verify --repo linktrend/IDE-Development --live \
  --json-output …/lane-d/raw/external-state-verify-live.raw.json
# exit 3 (NOT READY)

python3 …/external_state_audit.py plan --repo linktrend/IDE-Development --live \
  --json-output …/lane-d/raw/external-state-plan-live.raw.json
# exit 0

python3 …/external_state_audit.py apply --repo linktrend/IDE-Development --live
# exit 5 (apply refused)
```

**Human summary (report):**  
`External state NOT READY: 8/19 required checks unresolved [github_app.installation=blocked, github_app.authority_scope=unknown, bugbot.manual_trigger_only=unknown, carlos.user_token_boundary=unknown, protection.staging_ruleset=missing, protection.main_ruleset=missing, protection.promotion_source_policy=drift, workflows.permissions_posture=unknown]. Mutations: none.`

## 5. Live repository protection plan (read-only)

```bash
python3 /tmp/wp02-lane-d-wp01-tools/scripts/gitops/repository_protection.py \
  --repo linktrend/IDE-Development plan
# exit 0
```

**Result:** mechanism=`rulesets`; actions `development:noop`, `staging:create`, `main:create`; `allow_auto_merge` noop (`true`→`true`); `mutations: []`. Rollback snapshot written under `lane-d/notes/`.

**Apply not run.**

## 6. Supplemental read-only `gh api` probes

| Command | Result (redacted) |
|---------|-------------------|
| `GET repos/…/rulesets` | 1 ruleset: `development-autonomous-merge` id `19728531` active |
| `GET branches/development/protection` | protected; checks include Bugbot + Verify + source-policy |
| `GET branches/staging/protection` | 404 Branch not protected |
| `GET branches/main/protection` | 404 Branch not protected |
| `GET repos/…/installation` | **401** JWT could not be decoded |
| `GET /orgs/linktrend/installations` | 404 / needs `admin:org` |
| `GET /user/installations` | 403 needs GitHub App user token |
| `GET actions/variables` | names only listed |
| `GET actions/secrets` | **names only** listed |
| `GET actions/workflows` | 9 required workflows `state=active` |
| `GET actions/workflows/{id}/runs?per_page=1` | conclusions recorded (see audit JSON / notes) |

## 7. Files written (lane-d only)

| Path | Purpose |
|------|---------|
| `external-state-audit-live.json` | Redacted bound live audit package |
| `before-after-plan.md` | Deterministic union-preserving plan |
| `apply-decision.md` | `blocked` with rationale |
| `commands-and-results.md` | this file |
| `SUMMARY.md` | readiness verdict |
| `raw/**` | raw command outputs (operator debug; secrets excluded) |
| `notes/**` | redacted protection plan + conclusions |

## 8. Non-commands (explicitly not performed)

- No `repository_protection.py apply` / `--apply`  
- No ruleset/classic protection PUT/POST/DELETE  
- No Bugbot dashboard mutation  
- No secret create/update  
- No commit / push / PR / review-ready / Packager / Bugbot mention  
- No consumer repo access for mutation  
