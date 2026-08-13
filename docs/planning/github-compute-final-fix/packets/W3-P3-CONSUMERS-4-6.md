# W3-P3 — Consumer Rollout: LiNKbrain, LiNKsites, LiNKdeveloper

## Objective

Install and promote the exact W3-P1 release in three consumers, serially within
this packet, while W3-P2 and W3-P4 may run in parallel.

## Repositories

1. `/Users/linktrend/Projects/LiNKbrain` / `linktrend/LiNKbrain`
2. `/Users/linktrend/Projects/LiNKsites` / `linktrend/LiNKsites`
3. `/Users/linktrend/Projects/LiNKdeveloper` / `linktrend/LiNKdeveloper`

## Required procedure

Follow `CONSUMER-ROLLOUT.md` and `EMERGENCY-AUTHORITY-AND-ROLLBACK.md` exactly for
each repository. Use separate issue branches/worktrees and one PR per repository.
Install only the immutable W3-P1 artifact after digest verification. Verify each
diff is managed-system-only. Preserve LiNKbrain advisory/provenance code, LiNKsites
application/CI commands, and LiNKdeveloper Program Ledger/ProductRun factory code.

LiNKdeveloper must receive complete removal of the former custom App even though
its separate VPS factory correction is deferred. Do not redesign or deploy the
factory here. Record any repository-owned CI profile needed for its final
independent check without routing continuous ProductRun work to GitHub.

Use hosted ARM64, admin-merge exact heads, promote through staging/main using
receipt reuse, verify protections, and remove repository-specific App/self-hosted
state.

## Packet acceptance

- All three remote main branches contain exact installed release.
- LiNKdeveloper has no former custom App dependency and remains otherwise
  functionally unchanged.
- Per-repository PR/promotion URLs, SHAs/trees, checks, version, external cleanup,
  product-code preservation, ruleset verification, and rollback references exist.

## Prohibited

No VPS deployment, ProductRun redesign, other consumer edit, IDE source edit,
global App deletion, unrelated cleanup, or spending limit.

## Handoff

Return one structured evidence record per repository and a packet PASS/HOLD.

