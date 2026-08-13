# Emergency Authority and Rollback

## Why emergency authority is approved

The old required checks depend on the runner/App architecture being replaced. The
permanent correction cannot be required to pass the broken mechanism that it
removes. Carlos therefore authorizes repository-administrator emergency authority
for this release and its nine managed-system installations.

This is a permanent release delivered through a one-time emergency merge path. It
is not a temporary product fix.

## Allowed uses

Emergency authority may be used only to:

1. merge the exact verified IDE Development final-fix Phase PR into `development`;
2. merge exact promotion PRs from `development` to `staging` and `staging` to
   `main` for that release;
3. merge each exact verified consumer installation PR into `development` and its
   two exact promotion PRs;
4. remove former custom App access/configuration and IDE-owned runners/services;
5. restore branch protections/rules if a narrow temporary ruleset adjustment was
   technically unavoidable.

It does not authorize product-code changes, unrelated PRs, direct unreviewed
commits to protected branches, deletion of uncertain resources, or bypass of a
known code/test failure.

## Required sequence for every admin merge

1. Snapshot PR number, target, exact head commit/tree, required checks, ruleset,
   and rollback branch/tag.
2. Verify the PR diff contains only approved managed-system changes.
3. Verify packet/local/disposable-consumer evidence and the applicable hosted
   ARM64 result.
4. Confirm the candidate has not changed since verification.
5. Prefer GitHub's per-merge administrator bypass (`gh pr merge --admin` or UI
   equivalent) without disabling the ruleset.
6. If GitHub cannot perform a per-merge bypass, snapshot the complete ruleset,
   make the smallest temporary change, merge only the exact PR, and restore the
   snapshot immediately before doing other work.
7. Fetch the target and record resulting merge commit and Git tree.
8. Confirm protections and required checks are active after merge.

## Rollback preparation

Before source release:

- record the previous IDE Development release/tag/version and artifact digest;
- export redacted GitHub external-state and ruleset snapshots;
- preserve the previous managed-core install artifact;
- create a rollback instruction that reinstalls the prior exact release without
  restoring the former App or self-hosted architecture unless Carlos explicitly
  approves that exceptional rollback;
- prove migration and rollback in disposable repositories.

Before each consumer install:

- record branch heads, tree identities, installed-state file, managed manifest,
  managed-file diff, ruleset, required checks, and former external-state names;
- ensure the working tree/worktrees are clean or isolate the rollout;
- create a recovery branch/tag or exact commit reference;
- preserve consumer-owned files and configuration.

## Rollback trigger

Rollback the affected repository only when:

- the installed package cannot start required hosted checks;
- the managed installation changed product code or consumer-owned files;
- receipt identity accepts changed content;
- protections cannot be restored;
- ordinary development is blocked by a defect in the new system and no bounded
  forward repair is safe.

Do not roll back all repositories because one consumer has a repository-specific
problem. Stop that packet, preserve evidence, and continue only independent
repositories whose safety is unaffected.

## Cleanup safety

- Delete only positively identified custom LiNKtrend App configuration and
  IDE-owned runner infrastructure.
- Secret values are never displayed or stored in evidence.
- Do not delete arbitrary Docker resources; match recorded labels/names/ownership.
- Do not delete branches/worktrees with uncommitted or unique commits.
- Report every deleted external resource and whether recovery is possible.

