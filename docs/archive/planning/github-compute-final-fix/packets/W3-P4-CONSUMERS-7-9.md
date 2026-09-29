# W3-P4 — Consumer Rollout: LiNKlibraries, LiNKautowork, LiNKtrading-codebase

## Objective

Install and promote the exact W3-P1 release in three consumers, serially within
this packet, while W3-P2 and W3-P3 may run in parallel.

## Repositories

1. `/Users/linktrend/Projects/LiNKlibraries` / `linktrend/LiNKlibraries`
2. `/Users/linktrend/Projects/LiNKautowork` / `linktrend/LiNKautowork`
3. `/Users/linktrend/Projects/LiNKtrading-codebase` / `linktrend/LiNKtrading-codebase`

## Required procedure

Follow `CONSUMER-ROLLOUT.md` and `EMERGENCY-AUTHORITY-AND-ROLLBACK.md` exactly for
each repository. Use separate issue branches/worktrees and one PR per repository.
Install only the immutable W3-P1 artifact after digest verification. Review diffs
for managed-system-only scope. Preserve Library catalog/integrity, Autowork runtime,
and Trading safety/risk code and repository-specific checks.

Use hosted ARM64, admin-merge exact verified heads, promote through staging/main
using receipt reuse, verify protections, and remove repository-specific former
App/self-hosted state.

## Packet acceptance

- All three remote main branches contain exact installed release.
- Per-repository PR/promotion URLs, SHAs/trees, checks, version, external cleanup,
  product-code preservation, ruleset verification, and rollback references exist.

## Prohibited

No other consumer/IDE source edit, trading/product behavior change, global App
deletion, unrelated cleanup, or spending limit.

## Handoff

Return one structured evidence record per repository and a packet PASS/HOLD. Terra
may delete the global former custom App only after combining PASS evidence from all
three Wave 3 consumer packets and independently verifying zero remaining access.
