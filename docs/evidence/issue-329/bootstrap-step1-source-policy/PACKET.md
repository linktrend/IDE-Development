# Bootstrap step 1 — source-policy context replace (HOLD)

## Status

**APPLIED + VERIFIED + HOLD**

Actor: `linktrend`
Repo: `linktrend/IDE-Development`
Candidate tooling: head `2f204781e093acad694b084e7c4ba0652fd17721` / tree `4556fb197c575c64cb1a152c00738c8651a3cb74`
Scope: atomically replace obsolete required context `Enforce allowed PR source branches` with live producer `Linktrend Branch Source Policy` on development, staging, and main.

## Ruleset IDs (unchanged)

| Branch | Ruleset | ID |
|---|---|---|
| development | development-autonomous-merge | 19728531 |
| staging | staging-autonomous-promote | 20218450 |
| main | main-autonomous-release | 20218451 |

## Before → After required contexts

### development
- before: `Cursor Bugbot`, `Verify IDE Development`, `Enforce allowed PR source branches`
- after: `Cursor Bugbot`, `Verify IDE Development`, `Linktrend Branch Source Policy`

### staging
- before: `Verify IDE Development`, `Enforce allowed PR source branches`
- after: `Verify IDE Development`, `Linktrend Branch Source Policy`

### main
- before: `Verify IDE Development`, `Enforce allowed PR source branches`
- after: `Verify IDE Development`, `Linktrend Branch Source Policy`

## Preserved

- `Cursor Bugbot` review requirement on development (no Review Gate cutover)
- `Verify IDE Development`
- strict required status checks = true
- bypass_actors (empty → empty)
- allow_auto_merge unchanged (noop)
- all non-check ruleset structure via `ruleset_body`/`merge_ruleset_rules`

## Preflight

- repository identity: linktrend/IDE-Development (admin=true)
- mechanism: rulesets
- native capability preflight: ok / assurance=protected
- producer live: workflow `Linktrend Branch Source Policy` active (id 315986457); recent PR runs success on sealed head

## Apply path

Default `./scripts/manage-repository-protections.sh apply` was **not** used: at this candidate it would also map `Cursor Bugbot` → `Linktrend Review Gate`.

Used accepted primitives from the same tooling head:
- `repository_protection.GitHubClient`
- `repository_protection.ruleset_body` / `apply_plan` (atomic three-branch update with rollback-on-failure)
- step1-only desired checks (source-policy rename map only)

## PR #326 sealed identity

Unchanged: head `2f204781e093acad694b084e7c4ba0652fd17721` / tree `4556fb197c575c64cb1a152c00738c8651a3cb74`

## Rollback

```bash
./scripts/manage-repository-protections.sh --repo linktrend/IDE-Development rollback --snapshot docs/evidence/issue-328-bootstrap-step1-source-policy/sanitized/step1-apply-plan.json --apply
```

## HOLD

No further bootstrap steps. No Bugbot→Review Gate cutover. No source changes, PR, merge, promotion, publication, or consumer rollout.
