# Consumer Rollout

## Release input

All consumers must install the same immutable IDE Development release produced by
W3-P1. Installation by moving branch, `latest`, local uncommitted source, or a
different release is forbidden.

Required release identity:

```text
version
tag
source commit
source Git tree
managed manifest digest
release artifact digest
```

## Per-consumer procedure

For each repository:

1. Fetch remotes and inspect root instructions.
2. Record current `development`, `staging`, `main`, open PRs, worktrees, dirty
   state, installed version, rulesets, required checks, runners, App access, and
   managed external-state names.
3. Stop and inform Terra if unique/dirty work overlaps managed paths. Do not lose
   or overwrite it.
4. Create a dedicated rollout issue branch/worktree from current
   `origin/development`.
5. Run the official installer with the exact release artifact and verify its
   digest before installation.
6. Review the diff. Allowed changes are managed IDE files, managed workflow files,
   managed scripts/contracts, managed AGENTS markers, manifest/install state, and
   the smallest repository-owned CI profile declaration required to name its fast,
   full, and release commands.
7. Reject any unexplained product source, product tests, dependencies, migrations,
   deployment files, secrets, or consumer-owned documentation changes.
8. Run installed-package verification and repository-defined fast checks locally
   when practical.
9. Commit and push one rollout checkpoint; open one PR into `development`.
10. Confirm the hosted ARM64 managed check starts. Seal the exact candidate.
11. Use the admin procedure to merge the exact verified PR.
12. Promote `development` -> `staging` -> `main` through PRs. Reuse the exact
    managed-package receipt when tree/dependency identity matches; run only the
    consumer's required release/smoke check if its own policy demands it.
13. Verify `main`, protections, required checks, installed version, removal of
    former App/self-hosted state, and absence of product-code changes.
14. Remove only merged clean temporary rollout resources.

## Repository-specific preservation

The installer must union managed required checks with each repository's existing
product checks. It must not normalize all repositories to one application test
command. Each repository owns its `fast`, `full`, and `release` commands.

LiNKdeveloper receives the managed package and complete removal of the former
custom App. This rollout does not redesign its Program Ledger, ProgramRunner,
ProductRun modules, VPS execution, or factory tests. That is the next separate
feature before VPS go-live.

## Parallel batches

### W3-P2

1. `openclaw_prime`
2. `LiNKplatform`
3. `LiNKskills`

### W3-P3

1. `LiNKbrain`
2. `LiNKsites`
3. `LiNKdeveloper`

### W3-P4

1. `LiNKlibraries`
2. `LiNKautowork`
3. `LiNKtrading-codebase`

Packets run in parallel; repositories inside each packet are processed serially.
A packet failure does not authorize changing another packet's repositories.

## External cleanup per repository

After the new workflow is proven:

- remove App IDs/private-key secret names and App-specific variables;
- remove former App installation repository access;
- remove obsolete custom status requirements only after replacing them with the
  new stable required checks;
- remove self-hosted runner registrations/labels/groups owned by IDE Development;
- remove Mac coordinator/runner dispatch configuration;
- verify no workflow references removed identities or labels;
- retain GitHub's normal built-in Actions integration and `GITHUB_TOKEN`.

Global deletion of the former custom App occurs only after all repository access
has been inventoried and all nine consumers plus IDE Development no longer need it.

## Consumer completion evidence

```text
repository
before development/staging/main SHAs and trees
rollout branch and PR URLs
installer release identity and digests
diff classification
checks and run URLs
admin merge actor/result
after development/staging/main SHAs and trees
installed version
ruleset/required-check verification
App/runner cleanup result
product-code untouched result
rollback reference
```
