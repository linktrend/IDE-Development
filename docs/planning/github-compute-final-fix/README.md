# IDE Development GitHub Compute Final Fix

Status: approved implementation authority package  
Principal approval: 2026-08-13 (Asia/Taipei)  
Repository: `linktrend/IDE-Development`  
Planning issue: #246

## Outcome

Replace the fragile Mac Mini, ephemeral self-hosted runner, and former custom
LiNKtrend GitHub App delivery path with a permanent GitHub-hosted ARM64 delivery
profile. Ordinary checkpoints consume no Actions compute. Related work is
integrated into one or a few Phase pull requests. Fast checks run on the latest
Phase candidate, obsolete runs are cancelled, Bugbot reviews the final candidate,
and the repository-owned full suite runs once for the final exact candidate.
Promotion to `staging` and `main` verifies and reuses the same exact-tree receipt
instead of rerunning the full suite.

The released managed-core version is then installed and promoted through
`development` -> `staging` -> `main` in these nine consumers:

1. `linktrend/openclaw_prime`
2. `linktrend/LiNKplatform`
3. `linktrend/LiNKskills`
4. `linktrend/LiNKbrain`
5. `linktrend/LiNKsites`
6. `linktrend/LiNKdeveloper`
7. `linktrend/LiNKlibraries`
8. `linktrend/LiNKautowork`
9. `linktrend/LiNKtrading-codebase`

IDE Development is the system source and must not receive a nested
`.ide-development/` installation.

## Binding document order

The Terra Medium orchestrator must read these files before dispatching work:

1. `README.md`
2. `DECISIONS-AND-SCOPE.md`
3. `FROZEN-INTERFACES.md`
4. `IMPLEMENTATION-ROADMAP.md`
5. `EMERGENCY-AUTHORITY-AND-ROLLBACK.md`
6. `CONSUMER-ROLLOUT.md`
7. `TERRA-ORCHESTRATOR-RUNBOOK.md`
8. every file under `packets/`
9. `TERRA-GOAL.md`

If two documents appear inconsistent, the order above controls. Terra must
record the conflict and choose the safer interpretation; it must ask Carlos only
if the conflict changes scope, cost authority, deletion targets, or release
semantics.

## Packet index

### Wave 1 — parallel foundations

- `packets/W1-P1-COMPUTE-CONFIG.md`
- `packets/W1-P2-CANDIDATE-LIFECYCLE.md`
- `packets/W1-P3-RECEIPTS-PROMOTION-AUTH.md`

### Wave 2 — parallel managed-system integration

- `packets/W2-P1-WORKFLOW-PHASE-INTEGRATION.md`
- `packets/W2-P2-PACKAGE-INSTALLER-LEGACY.md`
- `packets/W2-P3-TESTS-DOCS-CLEANUP.md`

### Wave 3 — serial source release, then parallel consumer batches

- `packets/W3-P1-SOURCE-RELEASE.md` — must finish first
- `packets/W3-P2-CONSUMERS-1-3.md`
- `packets/W3-P3-CONSUMERS-4-6.md`
- `packets/W3-P4-CONSUMERS-7-9.md`

## Execution model

- Orchestrator and verifier: GPT-5.6 Terra Medium.
- Executors: GPT-5.6 Luna High through Codex CLI, never Cursor CLI.
- Maximum parallel executors: three, subject to non-overlapping path ownership.
- Terra verifies that each packet was actually completed; no separate audit role.
- Each Luna receives at most two attempts for the same packet. After two failed
  attempts, Terra takes over that packet and completes it.
- Packet branches start from the immutable implementation base and use separate
  worktrees. Accepted commits are integrated serially into one Phase branch.
- A completely separate feature may be under development concurrently. Its
  branches, worktrees, PRs, files, commits, and tests must remain untouched.

## Non-negotiable completion conditions

- No checkpoint-triggered GitHub Actions.
- No custom LiNKtrend GitHub App, App secrets, App workflows, or App installation
  remains in IDE Development or any of the nine consumers.
- No Mac Mini runner, ephemeral runner, self-hosted label, coordinator service,
  runner container, or temporary runner registration remains for this system.
- GitHub-hosted `ubuntu-24.04-arm` runs candidate checks.
- A final full-suite receipt is bound to repository, exact Git tree, dependency
  identity, profile, workflow version, and successful run.
- Unchanged staging/main content reuses that receipt; it does not rerun the full
  suite.
- Infrastructure failures receive at most two attempts for one exact candidate,
  then stop with a clear alert.
- Usage alerts are enabled, but no spending limit or stop-usage budget is imposed.
- The permanent release reaches IDE Development `main` and the exact released
  managed-core version reaches `main` in all nine consumers.
- Final evidence includes PR URLs, merge SHAs, tree identities, release/tag,
  checks, receipt reuse, GitHub external-state cleanup, and rollback proof.
