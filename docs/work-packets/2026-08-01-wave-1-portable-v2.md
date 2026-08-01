# Wave 1 work packet: portable IDE Development v2

**Issue:** #43  
**Branch:** `issue/43-build-portable-ide-development-v2-managed-core-i`  
**Base:** `origin/development` at `edbcb86cacbf99f65aed76063a3a188117bfcf86`  
**Owner:** Cursor Grok 4.5 High lead, with Cursor Grok 4.5 High subagents only  
**Verifier:** Codex Desktop Orchestrator

## Outcome

Turn IDE Development from a Mac-local shared checkout plus sparse GitOps wiring into a versioned, portable software-development operating system that can be installed or updated inside a Git repository without external absolute symlinks.

Wave 1 must deliver the managed-core architecture, transactional installer, full native Codex entrypoints, deterministic migration/conflict behavior, managed repository-protection contract, updated documentation, and comprehensive disposable-repository tests. It must not modify a real consumer repository or live GitHub settings.

Claude Code is explicitly outside this wave and outside the current v2 release scope. Preserve existing historical files unless an active document must stop claiming current Claude support; do not add `.claude`, root `CLAUDE.md`, Claude skills, or Claude installer behavior.

IDE Development is the source/system repository and internal self-verification target. It is not a consumer rollout entry and must not receive a nested installed copy of itself during this wave.

## Model and parallelism contract

1. The lead model must be `cursor-grok-4.5-high`.
2. Every implementation, research, test, or review subagent must also be `cursor-grok-4.5-high`. Never use Auto, Composer, GPT, Claude, Gemini, or a fast/low/medium Grok variant.
3. Spawn the maximum practical number of Grok 4.5 High subagents concurrently, subject to the disjoint ownership map below.
4. If Cursor cannot prove a subagent is using Grok 4.5 High, do not run that subagent. Record the limitation and let the Grok lead do that packet.
5. Subagents must not commit, push, open PRs, mark review-ready, change GitHub settings, or touch real consumers. The lead integrates and performs the single checkpoint commit/push only after all packets and tests pass.

## Locked architecture

- Installed managed core: committed `.ide-development/` inside each consumer.
- Physical managed files by default. No absolute, external, or checkout-to-checkout symlinks. Do not depend on symlink privileges on Windows.
- Native Codex discovery: root `AGENTS.md` managed block and physical `.agents/skills/<name>/SKILL.md` entries.
- Cursor discovery: physical `.cursor/rules`, `.cursor/commands`, and `.cursor/skills` entries.
- Consumer-owned content outside manifest ownership or managed markers is preserved.
- Managed-file drift is detected by stored hashes. Unknown conflicts fail closed.
- Superseded generic files may be removed only when a reviewed migration-catalog identity/hash matches exactly.
- Every mutating operation is planned first, transactional, and produces rollback information.
- GitHub credentials and secret values are never packaged. External settings receive plan, apply, and verify tooling with dry-run by default.
- `development`, `staging`, and `main` protection is required managed-system behavior for every installed repository. Existing repository-specific required checks must be preserved and combined deterministically.
- Version target is v2.0.0, but this wave must not create a Git tag or GitHub release.

## Parallel work packets

### WP1 — architecture, manifest, and precedence contract

**Owned paths:** new v2 ADR/contract files under `docs/adr/`, `docs/contracts/`, and `core/managed-core/`; no installer implementation files.

Define:

- managed-core directory layout;
- manifest schema with version, ownership class, source hash, destination, mode, platform, merge strategy, and supersession identity;
- installed-state and transaction schema;
- precedence rules: IDE Development governs shared lifecycle; repository-specific technical guidance remains unless it conflicts with an explicitly identified managed lifecycle rule;
- conflict matrix and fail-closed behavior;
- external-state boundary;
- self-verification versus consumer rollout distinction.

### WP2 — transactional cross-platform installer engine

**Owned paths:** new Python package under `scripts/ide_development/`, executable entrypoint `scripts/ide-development.py`, installer-focused unit tests/fixtures under a new dedicated test directory. Do not edit documentation or existing GitOps scripts.

Use Python standard library only. Implement:

- `install`, `update`, `plan`/`--dry-run`, `drift`, `verify`, `version`, and `rollback`;
- deterministic plans and machine-readable JSON output;
- repository and manifest validation;
- atomic writes and exact pre-change backups under Git-local metadata;
- recovery from interrupted transactions;
- installed-state hashes;
- idempotent repeat install/update;
- physical file materialization;
- no-write dry-run guarantee;
- safe operation with paths containing spaces and Windows path semantics;
- clear exit codes for clean, drift, conflict, invalid package, and rollback failure.

### WP3 — native Codex and Cursor managed-core adapters

**Owned paths:** new managed templates/adapters under `core/managed-core/platforms/`, `.agents/` additions required to make this repository itself natively understandable by Codex, and adapter-specific tests. Coordinate any root `AGENTS.md` write with the lead only.

Implement:

- a concise root `AGENTS.md` managed section that points to the installed core and preserves repository-owned text outside markers;
- physical `.agents/skills` adapters for at least agentsetup and agentcomply, plus a manifest-driven path for the remaining approved repository skills;
- physical Cursor rules/commands/skills sourced from the installed managed core;
- automatic-discovery tests from repository root and nested directories;
- no dependency on `.cursor` being read by Codex;
- no Claude entrypoints.

### WP4 — migration, conflict detection, and rollback scenarios

**Owned paths:** migration catalog and new black-box fixtures/tests only. Do not implement the installer engine itself.

Cover:

- existing external `.cursor` symlink migration;
- existing physical `.cursor` with consumer-owned content;
- current sparse GitOps installation upgrade;
- exact-known obsolete generic rule removal;
- unknown or modified conflicts fail closed;
- dirty repository preservation;
- interrupted transaction recovery;
- byte-exact rollback;
- repeat install/update idempotence;
- proof that no installed path resolves outside the consumer;
- proof that no credentials or absolute local checkout paths are packaged.

### WP5 — managed repository protections and external-state verification

**Owned paths:** new protection/configuration scripts, contracts, and focused tests; existing `scripts/apply-development-merge-ruleset.sh` may be refactored only if compatibility is preserved.

Implement a repository-agnostic, dry-run-first plan/apply/verify mechanism for:

- `development`: strict required checks, source policy, Bugbot, autonomous Integrator compatibility;
- `staging`: promotion-only PR sources and required staging gates;
- `main`: promotion-only PR sources, required release gates, and Main Approve compatibility;
- preservation/union of legitimate repository-specific required checks;
- no credential creation or secret reads;
- explicit before/after plan and rollback instructions;
- safe handling of GitHub ruleset/branch-protection availability differences.

Do not apply settings to IDE Development or any consumer in this wave.

### WP6 — active documentation, versioning, rollout inventory, and integration harness

**Owned paths:** `README.md`, `SETUP.md`, active architecture/operations/rollout docs, `VERSION`, and top-level integration test wrappers. Do not edit implementation modules owned by other packets.

Update active documentation so it:

- describes physical managed installation rather than consumer-to-system `.cursor` symlinks;
- explains install/update/drift/verify/version/rollback in plain English;
- removes Claude from current supported-platform claims and roadmap;
- treats IDE Development as system source and internal self-verification, not a consumer rollout;
- records consumer rollout order as: `openclaw_prime`, `LiNKplatform`, `LiNKskills`, `LiNKbrain`, `LiNKsites`, `LiNKdeveloper`, `LiNKlibraries`, `LiNKautowork`, `LiNKtrading-codebase`;
- requires a read-only drift report and separate Carlos approval before each consumer;
- makes `development`, `staging`, and `main` protection standard system behavior;
- keeps GitHub App, secrets, variables, Bugbot, and repository settings external;
- identifies v2.0.0 without tagging or publishing a release.

## Lead integration duties

The Grok 4.5 High lead must:

1. Inspect repository instructions and current architecture before integrating.
2. Confirm every subagent model and file-ownership boundary.
3. Reconcile packet interfaces without broad rewrites.
4. Ensure the package installs the complete approved shared development lifecycle, not only GitOps.
5. Preserve current GitOps behavior and consumer `ci.yml`.
6. Run all acceptance gates below.
7. Repair ordinary failures in at most three bounded cycles.
8. Commit and push one checkpoint to the issue branch only after success.
9. Stop without opening a PR, requesting Bugbot, merging, promoting, or calling `completion_gate.py review-ready`; Codex independently verifies first.
10. Return a machine-readable summary of subagents/models, changed files, commands, tests, risks, and commit SHA.

## Acceptance gates

- Existing suites remain green:
  - `bash scripts/tests/test-gitops-lifecycle.sh`
  - `bash scripts/tests/test-gitops-review-packager.sh`
  - `bash scripts/tests/test-gitops-behavioral.sh`
  - `bash scripts/verify-platform-adoption.sh`
  - `SKIP_LOCAL_ARCHIVE_CHECKS=1 bash scripts/verify-ide-development.sh`
- New installer, migration, adapter, and protection tests pass.
- A clean temporary repository installs successfully.
- An existing temporary repository preserves consumer-owned instructions, rules, skills, workflows, and CI.
- A second install/update is byte-identical.
- Dry-run changes no repository or Git metadata.
- Drift categories are precise and machine-readable.
- Rollback restores exact pre-install bytes and modes.
- No installed file or link resolves outside the consumer repository.
- Root and nested Codex discovery are verified through `AGENTS.md` and `.agents/skills` without relying on `.cursor`.
- No Claude runtime files are added.
- Protection planning covers all three governed branches and performs no live mutation during tests.
- `git diff --check` and relevant syntax/lint validation pass.
- Final worktree contains only intended Wave 1 changes.

## Hard stops

- No real consumer changes.
- No OpenClaw, Lisa, LiNKbrain, or LiNKtrading edits.
- No live GitHub settings, credentials, App, Bugbot, ruleset, secret, variable, tag, or release changes.
- No dependency additions or services.
- No deletion of stale PRs, worktrees, branches, issues, or stash in this wave; cleanup is a separate approved action.
- No implementer-created PR, self-review, self-merge, or promotion.
