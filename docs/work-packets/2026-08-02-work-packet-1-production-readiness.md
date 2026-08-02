# Work Packet 1 — production-readiness proof and release candidate

**Status:** Prepared; execution not started
**Execution issue:** Create automatically with `agentsetup` only when Carlos authorizes dispatch
**Required starting checkpoint:** `76d2aae1fbf0d497fbfb0e06181b3932660c96ce` (`issue/66-production-hardening-physical-symlink-migration`)
**Owner:** Cursor Grok 4.5 High lead, with Cursor Grok 4.5 High subagents only
**Independent verifier:** Codex Desktop Orchestrator
**Delivery mode:** Commit, push, checkpoint only — no PR, Bugbot, review-ready, merge, or promotion

## Outcome

Produce a complete, independently testable IDE Development v2 release candidate from the latest portable-system checkpoint. Prove the installer, migration, Cursor and native Codex adapters, packaging, recovery, security controls, and read-only GitHub external-state verification across macOS, Linux, and Windows.

This packet prepares the code and evidence needed for production. It does not resolve or modify frozen PR #49, integrate checkpoint branches into `development`, promote to `staging` or `main`, publish a GitHub release, or roll out to consumers. Those integration and publication actions belong to Work Packet 2.

Claude Code remains excluded. Do not add Claude entrypoints, packaging, tests, or documentation claims.

## Locked starting state

1. Use `scripts/gitops/create_issue_branch.py` through `agentsetup` to create the new issue, branch, and worktree automatically. Do not ask Carlos for an issue number or branch name.
2. Start from clean `origin/development`, then incorporate exact checkpoint `76d2aae1fbf0d497fbfb0e06181b3932660c96ce` into the new issue branch without rewriting, squashing, force-pushing, or altering the existing Issue #66 branch.
3. Verify the incorporated history contains Issue #64 checkpoint `44a26f0d14bd0e237748a14dd611c40a7a0cba6f` and portable v2 checkpoint `0868c0034620c4ccb255457484f0342a12a0c833`.
4. Do not checkout, update, rebase, close, comment on, or otherwise mutate PR #49 or its frozen branch.
5. Do not incorporate unrelated checkpoint branches. Work Packet 2 will reconcile all intentionally checkpointed branches.

## Non-negotiable operating rules

- Lead model: `cursor-grok-4.5-high`.
- Every implementation, test, research, and review subagent: `cursor-grok-4.5-high` only.
- Spawn the maximum practical number of subagents concurrently using the disjoint ownership lanes below.
- Subagents do not commit, push, create issues, open PRs, trigger workflows, trigger Bugbot, mark review-ready, merge, promote, or change external state.
- The lead integrates reviewed changes and creates coherent checkpoint commits. Push only the Work Packet 1 issue branch.
- No consumer repository changes, no live GitHub-setting changes, no credentials, no secrets, no paid-resource enablement, and no GitHub tag or release publication.
- Disposable repositories and fixture-backed GitHub simulations are required. Read-only queries against `linktrend/IDE-Development` are allowed for external-state evidence.
- Preserve consumer-owned files and repository-specific technical instructions. Unknown conflicts fail closed.
- Do not claim production readiness when any required platform or acceptance gate is skipped, neutral, untested, or inferred.

## Maximum-safe parallel execution map

The lead performs startup reconciliation, assigns paths, integrates results, runs the final suite, commits, pushes, and writes the checkpoint handoff. Start lanes A–F concurrently. Start lane G only after A–F are integrated.

### Lane A — cross-platform installer matrix

**Owned paths:** new cross-platform test runner and GitHub Actions workflow; minimal platform-test fixtures. Do not edit installer behavior unless the lead reassigns a verified platform defect.

Deliver:

- one authoritative test command that runs on macOS, Ubuntu Linux, and Windows;
- Python standard-library tests for install, update, plan/dry-run, drift, verify, version, rollback, transaction locking, modes/permissions, paths containing spaces and Unicode, Git worktree metadata, and physical-file guarantees;
- true cross-process contention tests on each supported platform;
- Windows-safe assertions that do not pretend POSIX mode bits or symlink privileges exist;
- a branch-safe CI matrix that runs on pushed issue checkpoints without PR or Bugbot coupling;
- retained machine-readable test summaries for the final evidence bundle.

The lead may push a checkpoint to trigger the cross-platform matrix. It must not dispatch paid runners, modify billing, or change repository settings. If an included runner is unavailable because of quota or policy, record the exact external blocker and do not claim the platform passed.

### Lane B — clean-room install, upgrade, drift, and rollback

**Owned paths:** disposable-consumer acceptance harnesses and fixtures under `tests/`; no production installer edits unless the lead reassigns a confirmed defect.

Build end-to-end tests using fresh temporary Git repositories for:

1. brand-new repository installation;
2. repeat install and update idempotence;
3. upgrade from the sparse GitOps layout;
4. safe migration from an external `.cursor` symlink to physical managed entrypoints without reading from or writing to the external target;
5. existing physical `.cursor` containing consumer-owned rules, commands, and skills;
6. root `AGENTS.md` with consumer text outside managed markers;
7. repository-specific `.agents/skills` and technical instructions;
8. exact-known obsolete generic-rule removal and modified/unknown conflict refusal;
9. drift detection followed by deterministic repair;
10. interrupted transaction recovery and byte/mode-exact rollback;
11. extracted release-candidate package installation with no access to the IDE Development checkout.

Prove both Cursor and native Codex discovery from nested directories. Assert that no installed path resolves outside the disposable consumer and no absolute source-checkout path appears in installed files or state.

### Lane C — external GitHub state plan and verification

**Owned paths:** external-state inventory/planner/verifier runtime, schemas, fixtures, and tests. No live apply implementation may execute in this packet.

Cover the external state that cannot be packaged:

- GitHub App installation/authority and narrowly scoped privileged automation;
- repository variables and required workflow configuration;
- `development`, `staging`, and `main` protections;
- required checks and promotion-source policy;
- Manual-Only Bugbot posture and mention-only trigger contract;
- Carlos's restricted user-token boundary;
- workflow presence, enabled state, permissions, and latest relevant conclusions.

Requirements:

- `plan` and `verify` are read-only and produce deterministic JSON plus a short human summary;
- fixture-backed tests cover matched, drifted, forbidden, unavailable, malformed, and credential-missing states;
- repository-specific required checks and unrelated protection rules remain preserved;
- no command prints, stores, packages, or hashes secret values;
- a live read-only audit of `linktrend/IDE-Development` may record identifiers, settings posture, and conclusions but never credentials;
- every unverifiable setting is reported as `unknown` or `blocked`, never assumed compliant.

### Lane D — deterministic release-candidate packaging

**Owned paths:** package builder/verifier, release schemas, packaging tests, and generated-manifest source logic. Do not publish a tag or GitHub release.

Deliver a standard-library-only release-candidate command that:

- validates `VERSION`, managed-core version, schemas, and generated manifest consistency;
- regenerates and verifies the complete managed-core manifest deterministically;
- builds reproducible portable archives suitable for macOS/Linux and Windows extraction;
- emits SHA-256 checksums, package metadata, provenance containing only repository-relative identities, and rollback/install instructions;
- excludes credentials, Git metadata, host paths, external symlinks, caches, temporary files, and consumer data;
- verifies archive extraction and installation from a clean temporary directory;
- reports installed version and package checksum through machine-readable output;
- refuses release-candidate creation when the worktree is dirty, manifest hashes drift, tests/evidence are missing, or the version is inconsistent.

Generated binary archives belong in an ignored build directory or CI artifact, not committed source. Commit only deterministic source, schemas, tests, and small textual evidence explicitly required by repository policy.

### Lane E — security, fail-closed, and recovery acceptance

**Owned paths:** adversarial/security acceptance tests and fixtures; no production code unless the lead reassigns a reproduced defect.

Test:

- path traversal, absolute-path injection, symlink/junction escapes, link-swap attempts, and package/source symlinks;
- malformed manifests, duplicate destinations, wrong hashes, invalid modes, unexpected file types, and partial archives;
- concurrent mutation, stale locks, interrupted writes, corrupt journals, corrupt backups, and rollback failure;
- consumer-owned file preservation and managed-marker boundary enforcement;
- repository-scope confusion in GitHub/cleanup evidence;
- absence of credentials, tokens, private keys, local usernames, and absolute checkout paths in source packages and evidence;
- fail-closed exit codes and deterministic JSON for every refusal class.

Use disposable state only. No live deletion, cleanup apply, GitHub mutation, or consumer operation.

### Lane F — production documentation and operator handoff

**Owned paths:** active documentation, release-candidate runbook, rollback runbook, acceptance matrix, and append-only build log. Do not edit archived historical evidence except to add a clear active supersession pointer when necessary.

Ensure active docs explain in plain English:

- what IDE Development is and what it installs;
- one-command install/update entrypoints for source checkout and extracted release candidate;
- Cursor and native Codex discovery and precedence;
- preservation of legitimate repository-specific technical guidance;
- safe migration of obsolete generic rules and external symlinks;
- drift, verification, rollback, version, and release-candidate commands;
- external GitHub state boundaries and read-only verification;
- macOS/Linux/Windows support evidence;
- IDE Development as system source, not a consumer;
- Claude excluded;
- consumer rollout deferred and separately approval-gated;
- Work Packet 2 as the integration/publication stage.

### Lane G — independent integrated review

**Starts after lanes A–F are integrated. Owned paths:** none by default; read-only review. Any repair is returned to the owning lane or assigned explicitly by the lead.

Spawn at least three independent Grok 4.5 High reviewers in parallel:

1. installer/migration/rollback and cross-platform reviewer;
2. packaging/security/external-state reviewer;
3. contracts/docs/test-coverage reviewer.

Each reviewer must inspect diffs and execute relevant tests. A reviewer summary is evidence, not proof; the lead must reproduce every must-fix finding and rerun the affected suite.

## Required acceptance gates

### Source and checkpoint integrity

- Worktree clean after checkpoint commit.
- Branch tracks its exact remote; local HEAD equals remote HEAD.
- History contains exact starting checkpoint `76d2aae1fbf0d497fbfb0e06181b3932660c96ce` without rewriting it.
- `origin/development`, `staging`, `main`, PR #49, all consumer repositories, and unrelated worktrees remain untouched.
- `git diff --check` passes.
- No `.superpowers`, cache, temporary, credential, or generated binary artifact is committed.

### Installer and migration

- Full installer unit suite passes.
- Live migration black-box suite passes with no skipped required scenarios.
- Clean-room install/update/drift/verify/version/rollback passes from extracted release-candidate archives.
- External `.cursor` symlink migration produces physical consumer files, leaves the external target byte-identical, and rolls back exactly.
- Consumer-owned Cursor/Codex material and root `AGENTS.md` text remain byte-identical outside managed ownership.
- Repeated install/update is byte-identical and leaves no external path dependency.

### Cross-platform

- macOS, Ubuntu Linux, and Windows matrix jobs all conclude success on the exact checkpoint SHA.
- Platform-specific evidence identifies Python and OS versions.
- No required test is silently skipped because of symlink privileges, filesystem behavior, shell availability, or permission differences.
- Platform-specific exclusions are explicit, justified by the contract, and paired with an equivalent safety assertion.

### External state

- Fixture matrix passes for external-state plan/verify.
- Live `linktrend/IDE-Development` audit is read-only and records no secret values.
- App authority, user-token boundary, workflow posture, Manual-Only Bugbot contract, variables, and three-branch protection are confirmed or explicitly reported as blocked/unknown.
- No external apply operation occurred.

### Package and release candidate

- Manifest regeneration is deterministic and a second run is byte-identical.
- Package archives and checksum files reproduce byte-for-byte from the same source commit and toolchain.
- Archive contents contain only reviewed repository-relative paths and physical regular files/directories.
- Extracted archives install successfully without access to the source checkout.
- Release-candidate metadata binds version, source SHA, manifest hash, archive checksums, supported platforms, and acceptance evidence.
- No tag, GitHub release, package publication, or consumer deployment occurs.

### Full system regression

Run every relevant existing suite, including at minimum:

```bash
PYTHONPATH=scripts python3 -m unittest discover -s scripts/ide_development_tests -v
python3 tests/managed-core-migration-bb/run_tests.py --with-installer
python3 -m pytest tests/adapters -q
bash scripts/tests/test-repository-protection.sh
bash scripts/tests/test-stale-cleanup-controls.sh
bash scripts/tests/test-gitops-behavioral.sh
bash scripts/tests/test-gitops-lifecycle.sh
bash scripts/tests/test-gitops-review-packager.sh
bash tests/test-portable-v2-integration.sh
bash scripts/verify-platform-adoption.sh
SKIP_LOCAL_ARCHIVE_CHECKS=1 bash scripts/verify-ide-development.sh
```

If a command is unavailable on Windows, the cross-platform runner must execute the equivalent Python-owned contract tests and clearly identify the platform-specific division. Required macOS/Linux shell suites still must pass.

## Evidence bundle

Write a machine-readable Work Packet 1 evidence document containing:

- issue, branch, exact source and checkpoint SHAs;
- lead and subagent model identities;
- lane ownership and changed files;
- every command, platform, exit code, test/pass/skip/fail count, and artifact checksum;
- live read-only external-state observations with secret values excluded;
- independent-review findings and their resolution;
- remaining blockers, if any;
- explicit booleans confirming no PR, Bugbot trigger, review-ready mark, merge, promotion, consumer change, GitHub setting change, credential creation, tag, or release publication.

Store textual evidence at the repository-approved evidence path and make it reproducible from commands. Do not treat the evidence document itself as proof without the recorded outputs.

## Checkpoint procedure

1. Confirm all required gates pass on the exact intended commit contents.
2. Commit coherent changes with explicit file staging; do not use broad destructive cleanup.
3. Push only the Work Packet 1 issue branch.
4. Re-resolve remote SHA and rerun the fast integrity gate on that exact SHA.
5. Write/update the evidence bundle if its recorded SHA requires a final evidence-only checkpoint commit; push and verify again.
6. Stop. Do not invoke completion `review-ready`, Review Ready Publisher, Packager, Bugbot, Integrator, promotions, or cleanup apply.

## Definition of complete

Work Packet 1 is complete only when:

- all implementation lanes and independent reviews are complete;
- all required local and three-platform acceptance gates pass with no unexplained skip;
- the release candidate and checksums reproduce and install cleanly;
- external GitHub state has been verified read-only or explicitly identified as an external blocker;
- the exact clean checkpoint SHA is pushed;
- the evidence bundle is complete;
- no PR or external mutation has occurred.

If any required item cannot be proven, checkpoint only verified partial progress and report Work Packet 1 as incomplete. Do not reduce scope, waive a gate, or claim production readiness.

## Explicit exclusions for Work Packet 2

Work Packet 1 must not:

- repair, update, close, supersede, merge, or otherwise touch frozen PR #49;
- integrate into `development`, `staging`, or `main`;
- reconcile other intentionally checkpointed issue branches;
- publish a version tag, GitHub release, or package to an external registry;
- install or update any real consumer repository;
- apply GitHub App, secret, variable, Bugbot, ruleset, or branch-protection changes.

Work Packet 2 will reconcile frozen PR #49, Work Packet 1, and all other intentional checkpoints; perform governed integration and promotion; and handle final publication/rollout decisions under separate Carlos approval.
