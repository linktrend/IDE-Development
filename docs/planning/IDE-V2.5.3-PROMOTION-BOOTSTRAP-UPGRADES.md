# IDE Development 2.5.3 promotion and bootstrap upgrades

Status: required next-release work discovered during the 2026-09-04 portfolio promotion.

## Outcome

Make routine repository promotion safe and proportionate without weakening
protected development, Phase review, or production authority.

## Required changes

1. **First staging creation.** Provide a governed bootstrap operation that
   creates a missing `staging` ref at an exact protected `development` commit,
   verifies its tree, and installs or restores the normal staging ruleset in
   the same transaction. It must fail closed on an existing divergent ref.
2. **Documentation-only promotion.** Classify an exact diff as documentation
   only and accept deterministic generated-output closure plus the normal fast
   and branch-policy checks. Do not run the application Full suite when no
   executable, dependency, workflow, migration, or security-policy file changed.
3. **Promotion receipt continuity.** Bind reusable validation to the tested
   source commit and tree, then explicitly record the promotion merge commit.
   A merge commit with the tested tree must not be rejected merely because its
   commit ID differs. Parentage, source identity, tree equality, and target ref
   must all remain verified.
4. **Manual Full dispatch baselines.** Require or safely default the target
   baseline SHA/ref. A dispatch without a pull-request payload must never
   resolve an empty `origin/` reference.
5. **Uniform consumer policy.** OpenClaw Prime uses the standard Phase fast
   admission and protected-promotion policy. Its upstream-fork boundary remains
   useful for ownership and live safety, but must not block ordinary repository
   documentation or LiNKtrend-owned engineering changes.

## Safety boundaries

This does not authorize credentials, paid or live providers, staging runtime
deployment, production rollout, sensitive data, or operational acceptance.
Temporary bootstrap authority must be explicit, repository-scoped, auditable,
and followed by verification that every ruleset is active.

## Acceptance

- Missing staging can be created from an exact protected development identity.
- Documentation-only Phase and promotion changes avoid application Full runs.
- A tested source tree remains valid after a governed promotion merge.
- Manual validation never constructs `origin/` from absent event data.
- OpenClaw Prime accepts the same ordinary Phase source categories as peers.
- Focused tests cover positive, stale, divergent, and out-of-scope cases.
