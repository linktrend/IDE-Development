# W3-P2 — Consumer Rollout: openclaw_prime, LiNKplatform, LiNKskills

## Objective

Install and promote the exact W3-P1 release in three consumers, serially within
this packet, while W3-P3 and W3-P4 may run in parallel.

## Repositories

1. `/Users/linktrend/Projects/openclaw_prime` / `linktrend/openclaw_prime`
2. `/Users/linktrend/Projects/LiNKplatform` / `linktrend/LiNKplatform`
3. `/Users/linktrend/Projects/LiNKskills` / `linktrend/LiNKskills`

## Required procedure

Follow `CONSUMER-ROLLOUT.md` and `EMERGENCY-AUTHORITY-AND-ROLLBACK.md` exactly for
each repository. Use a separate issue branch/worktree and one PR into development.
Install only the immutable W3-P1 artifact after digest verification. Review every
diff for managed-system-only scope. Verify hosted ARM64, admin-merge exact head,
promote through staging/main without repeating full suite for identical identity,
restore/verify protections, and remove that repository's former App/self-hosted
external state. Preserve OpenClaw, Platform, and Skills product/runtime code.

## Packet acceptance

- All three remote main branches contain exact installed release.
- Per-repository PR/promotion URLs, SHAs/trees, checks, version, external cleanup,
  product-code preservation, ruleset verification, and rollback references exist.
- A repository failure stops only that repository; safe completed siblings remain
  valid and no other packet is modified.

## Prohibited

No edits to other consumers, IDE source, product code, global App deletion,
unrelated branches/worktrees, or spending limits.

## Handoff

Return one structured evidence record per repository and a packet PASS/HOLD.

