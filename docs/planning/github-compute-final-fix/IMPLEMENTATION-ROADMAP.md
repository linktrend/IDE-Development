# Implementation Roadmap

## Objective

Release and deploy a permanent IDE Development delivery system that uses paid
GitHub-hosted ARM64 compute efficiently and removes the Mac Mini/self-hosted/custom
App delivery architecture.

## Preflight gate (Terra only)

Before Wave 1:

1. Read the binding documents and root `AGENTS.md`.
2. Fetch all remotes without modifying branches.
3. Record planning commit `P0` and latest `origin/development` as implementation
   base `B0`.
4. Inventory dirty files, worktrees, branches, open PRs, and the separate concurrent
   feature. Stop only for overlapping uncommitted work that cannot be isolated.
5. Inventory current delivery implementation, managed manifest, workflows,
   required checks, rulesets, runners, containers, services, App configuration,
   billing/Actions status, and the nine consumers.
6. Confirm GitHub-hosted `ubuntu-24.04-arm` is available to a private canary and
   that funded Actions jobs can start. This is a small preflight job, not a suite.
7. Create `phase/github-compute-final-fix` from `B0`.
8. Create separate packet branches/worktrees from `B0`. Never let two Luna agents
   share a worktree.
9. Record frozen ownership and any differences between assumed and actual paths.

Preflight evidence: `P0`, `B0`, Phase SHA, open/concurrent work inventory, current
version, exact consumers, runner/App inventory, ruleset snapshot, and successful
hosted-ARM64 canary.

## Dependency graph

```text
Preflight
  |
  +--> W1-P1 compute config and hosted-runner routing --+
  +--> W1-P2 candidate lifecycle and cost triggers -----+--> Wave 1 integration gate
  +--> W1-P3 receipts, promotion and authentication -----+
                                                        |
  +--> W2-P1 workflow/phase integration <---------------+
  +--> W2-P2 installer, manifest and legacy removal <----+
  +--> W2-P3 tests, migration docs and cleanup tooling <--+
                                                        |
                                                Wave 2 combined gate
                                                        |
                                      W3-P1 source release and promotion
                                                        |
                   +------------------+------------------+------------------+
                   |                  |                  |
             W3-P2 consumers 1-3 W3-P3 consumers 4-6 W3-P4 consumers 7-9
                   +------------------+------------------+------------------+
                                                        |
                                            final cross-repository closure
```

## Wave 1 — Independent foundations

Run W1-P1, W1-P2, and W1-P3 in parallel with Luna High. Their owned paths must be
confirmed non-overlapping during preflight. Each packet freezes its public
interface before implementation.

Wave 1 gate:

- Terra verifies each accepted exact commit.
- Terra integrates accepted commits serially onto the Phase branch.
- After each cherry-pick, run targeted tests for that packet and all previously
  integrated packets.
- Resolve conflicts deliberately; never use prefer-incoming or bulk overwrite.
- Run the combined configuration/state/receipt unit suites.
- If integration exposes an interface defect, return only the owning packet for
  repair; do not send all packets back.

## Wave 2 — Managed system integration

After Wave 1 passes, run W2-P1, W2-P2, and W2-P3 in parallel from the updated
Phase integration SHA or from dedicated branches whose bases and dependencies are
explicitly recorded. Terra must reassign any path overlap before dispatch.

Wave 2 gate:

- Serial integration of exact accepted commits.
- Full local self-verification.
- Disposable private consumer installation test.
- Static search proving no active custom App or self-hosted runner dependency.
- Migration test from the currently released managed-core version.
- Rollback rehearsal to the recorded previous release.
- One live GitHub-hosted ARM64 canary: checkpoint produces no workflow; Phase PR
  runs fast check; superseding commit cancels old run; sealed candidate runs one
  full suite; second infrastructure failure stops in a controlled fixture; exact
  receipt is accepted and a changed-tree receipt is rejected.

No consumer production repository changes occur in Waves 1 or 2.

## Wave 3 — Permanent release and nine-repository rollout

### W3-P1 source release (serial prerequisite)

Terra or one Luna prepares one Phase PR into IDE Development `development` from
the combined Phase branch. One Bugbot review and one final full suite run against
the sealed exact head. Ordinary repair is limited to two sealed candidates.

After PASS, use repository-administrator emergency authority as defined in
`EMERGENCY-AUTHORITY-AND-ROLLBACK.md` to merge the exact verified PR into
`development`, then promote through `staging` and `main`. Promotion checks receipt
identity only. Tag and publish one immutable managed-core release. Record release
version, tag, commit, tree, manifest digest, and package digest.

W3-P1 is complete only when IDE Development remote `main` contains the permanent
release and the release artifact can be installed into a disposable consumer.

### W3-P2, W3-P3, W3-P4 consumer rollout (parallel after W3-P1)

Split the nine consumers into three non-overlapping packets:

- W3-P2: `openclaw_prime`, `LiNKplatform`, `LiNKskills`
- W3-P3: `LiNKbrain`, `LiNKsites`, `LiNKdeveloper`
- W3-P4: `LiNKlibraries`, `LiNKautowork`, `LiNKtrading-codebase`

Each executor handles repositories serially inside its packet; the three packets
run concurrently. Install only the exact W3-P1 release. Open one managed-system PR
per consumer into `development`, verify no product-code change, use emergency
authority to merge the exact verified head, and promote through staging/main with
receipt/policy checks. Preserve repository-specific required tests and rules.

## Final closure gate

Terra verifies all ten repositories (source plus nine consumers):

- expected remote branch heads and trees;
- exact installed managed-core version;
- no former App workflows/secrets/variables/installation access;
- no self-hosted runner registrations/labels/services/containers owned by this
  system;
- hosted ARM64 workflow starts successfully;
- checkpoint produces no Actions run;
- required checks and branch protections are active;
- no spending stop limit exists; usage alerts are enabled;
- no product code or concurrent feature work was changed;
- rollback artifacts and before-state snapshots are retained.

Only then remove this feature's merged temporary Phase, issue, and promotion
branches/worktrees. Never delete a branch/worktree with unique or dirty work.

## Time and compute controls

- Use local unit tests during packet development when safe.
- Run GitHub-hosted fast checks only for integration candidates, not every packet
  checkpoint.
- Run the full suite once for the final source candidate and once per consumer only
  if that consumer has repository-owned product checks that cannot be represented
  by the managed package proof. The default rollout proof is managed-system fast
  validation plus exact release verification, not nine redundant source suites.
- Cache dependencies using lockfile-keyed caches with bounded retention.
- Upload only concise test/evidence artifacts; avoid large duplicated build output.
- Record actual minutes by repository/workflow for post-release tuning.
