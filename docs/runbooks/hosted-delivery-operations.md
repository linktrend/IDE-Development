# Hosted delivery operations runbook

**Scope:** source-repository operations and evidence preparation only.
W2-P3 does not perform external mutation.

## Commit to main, in plain English

1. Confirm the Phase branch contains the accepted issue SHAs and record the
   exact Phase head.
2. Open or update the one Phase PR into `development`. Confirm fast checks,
   source policy, and consumer-owned required checks refer to that exact head.
3. Seal the final candidate head. Confirm the full suite and Bugbot run once
   for that sealed candidate, with no later commit.
4. Retain the successful full-suite receipt. For staging and main, verify the
   repository, Git tree, dependency, profile, and workflow identities before
   reusing it.
5. Promote through protected PRs. Main requires Carlos's explicit approval
   bound to the staging source, main base, and promotion PR head.
6. Record the final SHA, tree, checks, receipt digest, and any stop reason.

## External cleanup plan

Terra captures separate redacted inventories for repository resources and host
resources. Run the plan command with no `--apply`; it must report zero
external mutation:

```bash
python3 scripts/external/cleanup_plan.py \
  --scope repository --inventory /path/to/repository-inventory.json
python3 scripts/external/cleanup_plan.py \
  --scope host --inventory /path/to/host-inventory.json
```

The tool accepts only exact resource IDs and positive recorded IDE ownership.
Lookalikes and ambiguous items are preserved. Secret names may be reported;
secret values may not. The source executor does not apply live cleanup.

## Billing alerts

Record a monthly Actions usage report and review alert delivery. Alerts are
notifications only: there is no spending cap or automatic stop limit.

## Emergency authority

If a protected gate, identity, or external ownership check is unclear, stop and
preserve evidence. Carlos/Terra must make any emergency repository, protection,
credential, billing, host, Docker, or release decision through the authorized
operator procedure. Do not restore retired delivery infrastructure as a
workaround.

## Consumer and LiNKdeveloper boundary

Consumer rollout is a separate W3 packet and requires explicit approval per
repository. LiNKdeveloper remains an independent autonomous factory; it may
consume released contracts but does not inherit IDE Development's local Git or
promotion authority. No consumer is changed by this runbook.
