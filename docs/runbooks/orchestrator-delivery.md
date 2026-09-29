# Orchestrator delivery: package, check, merge, promote (v3 Wave 1)

Workers push `issue/<PREFIX>-<n>-<slug>` branches. The orchestrator turns them
into one PR into `development`, merges it when CI and one independent review of
the exact head agree, then promotes `development` to `main`. There is no
`staging`. The orchestrator opens and merges PRs with its own tools; the
scripts in `scripts/orchestrator/` do the deterministic parts and print JSON.
They use only the standard library, run git with an allowlisted environment and
hooks disabled, and never print tokens (`GH_TOKEN` / `GITHUB_TOKEN` are optional
for public repos).

## 1. Package

```bash
python3 scripts/orchestrator/package.py --name wave-1-login \
  --branches issue/IDE-1-a issue/IDE-2-b --fast --push
```

- Builds `phase/<name>` from `origin/development` and merges each branch with `--no-ff` in the given order, in a scratch worktree. An existing phase branch is reused only when every commit on it comes from the base, the listed branches or a clean earlier phase merge.
- Exit 3 = conflict: the merge is aborted and `conflict.branch` / `conflict.files` name it. Never resolve it here or with `-X ours/theirs`; send it back to the worker (or the next repair rung) to merge `development` into their branch.
- Exit 1 = `--fast` failed (`fast.tail` has the output). Exit 2 = bad input or git error.
- Remote names must match `^[A-Za-z0-9][A-Za-z0-9._-]*$` and exist in `git remote`. Branch and ref arguments cannot lead with `-` and must pass `git check-ref-format` before git sees them. `--` is placed before ref positionals where git treats that as end of options.
- One branch without `--name` just reports `upToDate` / `behindBy`; open that branch's PR directly.

Open the PR from `phase/<name>` (or the single `issue/*` branch) into `development`.

## 2. Check, then merge

Wait for `Linktrend Fast Checks`, `Linktrend Branch Source Policy` and `Verify IDE Development`
on the head, get one independent review of that exact SHA, then:

```bash
python3 scripts/orchestrator/merge_check.py --repo linktrend/IDE-Development --pr 512 \
  --review-sha <sha the reviewer saw> --review-verdict APPROVE
```

Exit 0 means merge now (merge commit). Exit 1 lists `reasons`: a new push
(the head no longer equals the reviewed SHA, so review again), a red, cancelled,
timed-out or missing check, conflicts, or a wrong base. `--required` replaces
the default check list; `--allow-skipped <name>` accepts `skipped` for one check.
The script never merges.

A required check counts only as a **check run** (never a commit status) whose
`app.slug` is `github-actions` (`--check-app` replaces that allowlist). The latest
run per name and app wins, so a later failure overrides an earlier success.
`Verify IDE Development` and `Linktrend Fast Checks` must come from
`.github/workflows/ci.yml`, and `Linktrend Branch Source Policy` from
`.github/workflows/branch-source-policy.yml`, when the check-run payload exposes
that workflow (`check_suite` or the Actions run `path` / `name`). The list
check-runs API often does not include the workflow file; then the app slug is
the producer check and this gap is accepted. Commit statuses are reported and
never count as success. A failing status still fails the gate.

Mergeability fails closed: `mergeable` must be true and `mergeable_state` must
be `clean`. `null` or `unknown` reports `mergeability not yet computed; retry`.
`unstable` is accepted only with `--allow-nonrequired-pending` when every
required check is green and the only non-green checks are those listed pending
checks. The default is `clean` only.

## 3. Promote to `main`

```bash
python3 scripts/orchestrator/promote_main.py --push      # default: origin/development head
```

It requires `Verify IDE Development` success on the development SHA, creates
`promote/main/<12-char sha>` from it and merges `origin/main` in (normal merge),
so the PR is conflict-free and its tree equals the development SHA's tree. Open
the PR into `main` with the printed `prTitle` / `prBody` and merge it with a
**merge commit** (not squash or rebase, or the next promotion cannot match trees).

Exit 3 means `main` has changes that are not on `development` (hotfix or manual
edit). Land them on `development` first, then promote again. Exit 1 means the
development SHA is not green yet.

## The `Linktrend Receipt Gate` check

`main` protection requires `Linktrend Branch Source Policy`, `Verify IDE Development`
and `Linktrend Receipt Gate`. The last one is produced by
`.github/workflows/linktrend-promote-main.yml`, which runs
`scripts/orchestrator/promotion_check.py` from `development` on every PR into
`main`: the head must be `promote/main/*` from this repo, its tree must equal a
commit among the last 200 first-parent commits of `development`, and
`Verify IDE Development` must have succeeded on that commit.

The name is **legacy**: no receipt is involved. It stays because the live `main`
ruleset requires that context. If Carlos renames it in the ruleset, rename the
workflow and job `name:` (both copies: `.github/workflows/` and
`core/github/managed-workflows/`) and the context constants in
`scripts/gitops/repository_ci_contract.py`, `scripts/gitops/repository_protection.py`,
`.github/linktrend-repository-ci-contract.json` and `promotion_check.py` in the same PR.
