# Delivery modes

**Status:** Active. This document describes the hosted phase-integration
profile consumed by managed-core. The frozen field meanings are defined in
`docs/archive/planning/github-compute-final-fix/FROZEN-INTERFACES.md`.

## Supported mode

`phase-integration` is the approved system profile. Issue branches are
checkpoint-only: workers push them and never open PRs. The orchestrator
packages finished Issue branches into one `phase/*` branch
(`scripts/orchestrator/package.py`), and one Phase PR carries the combined
result into `development`.

The configuration is `.github/linktrend-delivery-mode.json`:

- provider: `github-hosted`
- runner: `ubuntu-24.04-arm`
- checkpoint CI: `false`
- obsolete cancellation: `true`
- infrastructure attempts: `2`
- sealed candidates: `2`
- full-suite review: one combined Phase candidate only

Repository-owned fast, full, and release commands stay in the configuration.
The Full profile is the two existing Verify commands: `scripts/verify-ide-development.sh`
and `scripts/verify-pipeline-states.sh`. The first invokes the complete Fast
profile, including fixture-aware secret scanning. CI checks out the Phase PR's
exact head, writes the inventory only after success, then uploads it as an
artifact scoped to that workflow run. The cross-platform installer matrix runs
only when the shared changed-path classifier finds installer, workflow,
fixture, or dependency inputs in the combined Phase diff. Merge and promotion
apply the same classifier to the exact PR file list.

## Named gates

The stable Phase checks are `Linktrend Fast Checks`, `Verify IDE Development`,
and `Linktrend Branch Source Policy`; the three `Installer matrix (...)` checks
are required when the shared path classifier applies.
Main promotion requires `Linktrend Main Receipt Gate` plus source policy. Missing,
stale, neutral, or wrong-SHA evidence is not success.

## Promotion identity

Receipt reuse requires exact equality of repository, head commit, Git tree,
dependency digest, profile digest, and workflow digest. Promotion downloads the
inventory from the successful Verify run selected for the exact Phase head and
fails closed unless the existing profile runner accepts that same identity.
No Full rerun occurs during unchanged promotion.

## Non-goals

This contract does not authorize live repository settings, credential,
service, host, Docker, billing, consumer, pull-request, merge, or release
operations. Those operations require the W3 external procedure and explicit
operator authority.

## v2.5 Issue checkpoint (`V25_BOOTSTRAP_LEAN`)

Issue checkpoints do not require a commit status or `AUTOMATION_TOKEN`. Legacy
publisher/status outcomes are `WAIVED_LEGACY_GATE`, never PASS. Phase delivery
still uses one Phase PR, exact review, conditional Full, and the founder gate
for `main`. Administrator recovery is a named exact-head exception after
replacement proof.
