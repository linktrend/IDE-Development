# Work Packet 02 — integration lineage, stale cleanup, and live readiness

**Status:** Execution in progress (Issue #68 · branch `issue/68-work-packet-02-integration-lineage-stale-cleanup`); lineage integration incomplete; not review-ready
**Authorization:** Principal-approved for WP02 execution; Issue #68 and work branch created via `agentsetup` / `create_issue_branch.py`. Live-state apply still requires lead proof against the approved packet before mutation.
**Required starting base:** fresh `origin/development`
**Required input checkpoints:** WP01 `89956878c54ff45e4aef1ff42883d209221b7a30`; cleanup lineage tip `5cf099155d9f7b5d95e094f74b288af7aec766af`; frozen PR #49 tip `0868c0034620c4ccb255457484f0342a12a0c833`
**Owner:** Cursor Grok 4.5 High lead, with Cursor Grok 4.5 High subagents only
**Independent verifier after completion:** Codex Desktop Orchestrator, in a separate Principal-approved phase
**Delivery mode:** commit, push, checkpoint only — no new PR, Bugbot trigger, review-ready publication, merge, promotion, tag, release, or consumer change

## Outcome

Create one clean, auditable issue-branch lineage containing every intentional and still-required IDE Development change. Reconcile the frozen PRs and checkpoint branches without modifying their frozen heads, complete stale-cleanup hardening, and bring the IDE Development repository's external GitHub state to a verified ready posture.

WP02 ends at a pushed issue-branch checkpoint. It does not integrate into `development`; that is WP03.

Claude Code remains excluded. IDE Development remains the system source and must not receive a nested consumer installation.

## Startup and immutable boundaries

1. After approval, use `agentsetup` / `scripts/gitops/create_issue_branch.py` to create the GitHub issue and `issue/<number>-<slug>` worktree automatically. Do not ask Carlos for an issue number or branch name.
2. Fetch and record exact local/remote SHAs, open issues, open PRs, worktrees, review-ready statuses, and protected-branch tips before mutation.
3. Start from clean `origin/development`; incorporate checkpoints through ordinary, reviewable Git history. No force-push, history rewrite, destructive reset, or prefer-incoming resolution.
4. Never commit, rebase, push, or otherwise alter the heads of PR #36, PR #37, PR #49, or any prior issue branch.
5. Do not close PRs/issues or delete branches/worktrees in WP02. Record the exact proposed disposition for WP03 cleanup after canonical integration.
6. Preserve credentials. Do not create, rotate, reveal, package, print, or persist tokens, private keys, or secrets.

## Maximum-safe parallel execution map

The lead owns reconciliation decisions, conflict resolution, external mutation approval checks, final validation, checkpoint commits, and push. Start lanes A–E concurrently after the startup snapshot. Start Lane F after integration of A–E. Subagents work only in disjoint paths or read-only audit surfaces and do not commit or push.

### Lane A — checkpoint and PR reconciliation ledger

Build a machine-readable ledger for every open/still-owned IDE Development PR, issue branch, and worktree, including at minimum PRs #36, #37, and #49 and issues/branches #23, #28, #43, #44, #51, #53, #55, #57, #59, #61, #63, #64, #66, and #67.

For every record, prove one classification:

- already present in `origin/development`;
- ancestor of the WP01 checkpoint;
- ancestor of cleanup tip `5cf0991`;
- uniquely required and incorporated into the new lineage;
- semantically superseded with a file/patch-equivalence explanation;
- intentionally deferred with an owner and reason; or
- safe to close/clean only after WP03 integration.

Use ancestry, patch IDs, file diffs, workflow/runtime manifest comparisons, issue/PR evidence, and current ownership. Branch names or issue status alone are never proof. The ledger must show that frozen PR #49's required content is represented by the canonical lineage while its reviewed SHA remains unchanged.

### Lane B — deterministic lineage construction and conflict analysis

Propose and validate the smallest ordinary-history construction that combines:

1. current `origin/development`;
2. exact WP01 checkpoint `8995687` and its contained portable-v2 lineage;
3. exact stale-cleanup tip `5cf0991` and its contained #51–#63 repair lineage; and
4. any unique, still-required content discovered in #23/#28 or other intentional checkpoints.

Before the lead integrates a source, produce a three-way conflict map and semantic overlap report. Resolve conflicts by current authoritative contracts and tests, never wholesale side selection. Preserve WP01 release-candidate, installer, native Codex, Cursor, GitOps, credential-boundary, and documentation behavior.

### Lane C — stale-cleanup hardening

Restore and complete the cleanup controls represented by `5cf0991`, including `scripts/tests/test-stale-cleanup-controls.sh`, on the canonical combined lineage.

Required behavior includes fail-closed repository resolution, rejection of malformed/ambiguous repository scope, preservation of open and closed PR heads where required, correct issue-branch matching, repository-scoped PR evidence, dry-run-by-default cleanup, exact authorization records, and no deletion by branch name alone.

Add integration tests proving the cleanup lineage and WP01 portable-system lineage coexist. Test open/frozen PR preservation, worktree ownership, ambiguous remotes, unavailable GitHub evidence, mismatched repositories, partially merged histories, retry/idempotence, and zero mutation on failed authorization.

No cleanup apply occurs in WP02. Produce a cleanup plan only.

### Lane D — live external GitHub-state readiness for IDE Development

Re-run the read-only external-state audit against `linktrend/IDE-Development` and bind it to a timestamp and source SHA. Cover:

- GitHub App installation and required non-secret authority metadata;
- privileged automation token provenance and zero ambient-token fallback;
- Carlos's restricted user-token boundary: Packager feature-PR creation and exact Bugbot trigger comment only;
- Manual-Only Bugbot posture;
- required repository variables and workflow names;
- workflow presence, enabled state, permissions, and relevant conclusions;
- protection of `development`, `staging`, and `main`, including source policy and required checks.

Generate a deterministic before/after plan that preserves unrelated repository rules. Live apply is allowed only for `linktrend/IDE-Development`, only after the lead proves the plan is within the approved standard, only through the repository's authorized GitHub App path, and only with a restorable before-state snapshot. Never use Carlos's restricted token for protection/settings mutations.

If an API cannot verify or apply a required setting, record it as blocked. For Manual-Only Bugbot, use an authenticated UI verification only if available and necessary; do not infer it. Do not change any consumer repository or consumer GitHub state.

### Lane E — manifests, documentation, and readiness evidence

Reconcile managed runtime manifests and active source-of-truth documents after the combined lineage. Remove obsolete statements that WP02 is future, but do not claim integration, release, or consumer rollout.

Produce deterministic evidence containing source/input/output SHAs, reconciliation classifications, conflicts and resolutions, external-state before/after summaries with secrets excluded, all commands and exits, and explicit prohibited-action booleans.

### Lane F — independent Cursor reviews

After A–E are integrated, launch three fresh Cursor Grok 4.5 High reviewers in parallel:

1. **Lineage reviewer:** prove every intentional checkpoint is incorporated, already present, or explicitly and correctly superseded.
2. **Security/GitOps reviewer:** audit cleanup fail-closed behavior, credential provenance, GitHub App authority, and zero unauthorized mutation.
3. **Portable-system regression reviewer:** verify installer, package, Cursor/Codex adapters, manifests, docs, and three-OS behavior remain intact.

Reviewers do not edit. The lead fixes valid findings, reruns affected suites, and may repeat one fresh review cycle.

## Required validation

Run all WP01 suites on the final combined content, including three-OS CI on the exact pushed checkpoint. Also require:

```bash
bash scripts/tests/test-stale-cleanup-controls.sh
bash scripts/tests/test-external-state-wp1.sh
bash scripts/tests/test-external-state-audit.sh
bash scripts/tests/test-repository-protection.sh
bash scripts/tests/test-gitops-behavioral.sh
bash scripts/tests/test-gitops-lifecycle.sh
bash scripts/tests/test-gitops-review-packager.sh
bash tests/test-portable-v2-integration.sh
SKIP_LOCAL_ARCHIVE_CHECKS=1 bash scripts/verify-ide-development.sh
```

Rebuild the release candidate from the final clean content and verify reproducibility, clean-room extraction/install, manifest consistency, checksums, rollback, and no source-checkout paths. Required checks may not be waived or silently skipped.

## Checkpoint procedure

1. Integrate only reviewed inputs into the new WP02 issue branch.
2. Run the complete validation matrix and resolve findings.
3. Commit coherent changes, push only the WP02 issue branch, and verify `HEAD == origin/<branch>`.
4. Bind evidence to the exact final checkpoint. If evidence requires a final commit, rerun the fast integrity and exact-tip CI gates.
5. Stop at checkpoint. Do not call `review-ready`, Packager, Bugbot, Integrator, promotion, cleanup apply, tag/release publication, or consumer rollout.

## Definition of complete

WP02 is complete only when the canonical checkpoint:

- contains or explicitly proves the disposition of every intentional checkpoint and frozen PR;
- preserves frozen heads while proving PR #49's required content is superseded by the canonical lineage;
- passes stale-cleanup, external-state, full WP01, security, packaging, and three-OS tests;
- leaves IDE Development's live external state verified ready, or identifies a concrete external blocker without overclaiming;
- has a complete cleanup/disposition plan for old PRs, issues, branches, and worktrees after WP03;
- is clean, pushed, and evidence-bound; and
- has not opened a PR, invoked Bugbot, merged, promoted, published, or changed a consumer.

Any unresolved required live-state blocker means WP02 is checkpointed but incomplete.
