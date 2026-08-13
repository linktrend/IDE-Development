# Decisions and Scope

## Approved plain-English design

Agents may save work to GitHub frequently without starting tests. When a Phase of
related work is ready, those accepted commits are combined into one reviewable PR.
GitHub gives that PR a fresh isolated ARM64 machine. Short checks run during final
assembly; any check for an older commit is cancelled when a newer commit replaces
it. Bugbot and the expensive full suite run against the sealed final candidate.

After the candidate passes and enters `development`, promotion does not test the
same files all over again. A short gate proves that the promoted Git tree and
dependencies match the successful receipt. If they match, staging/main reuse the
receipt. If they do not match, promotion stops; it never silently treats different
content as tested.

## Decisions frozen by Carlos

1. GitHub remains source hosting, PR, branch-protection, and CI provider.
2. GitHub-hosted Linux ARM64 is the normal CI execution environment.
3. The standard private-repository label is `ubuntu-24.04-arm` unless a live
   preflight proves GitHub has withdrawn it. Do not substitute self-hosted labels.
4. Checkpoint commits and pushes do not start Actions.
5. Related issue work is bundled into one or a few Phase PRs.
6. Fast checks target less than five minutes.
7. One full suite runs on the final sealed candidate when the repository requires
   it; the full suite is expected to consume most Actions compute.
8. Obsolete fast/full runs for superseded candidate commits are cancelled.
9. No exact candidate gets more than two infrastructure attempts. A second
   infrastructure failure stops and alerts; code failures return to development
   and create a new candidate only after actual code changes.
10. No more than two sealed candidate revisions are allowed without stopping and
    reporting the unstable requirement or integration problem.
11. Staging and main run only receipt/identity and branch-policy gates when content
    is unchanged.
12. The former custom LiNKtrend GitHub App is removed everywhere, including
    LiNKdeveloper, because LiNKdeveloper is not live and will receive its separate
    autonomous-VPS correction later.
13. GitHub's built-in per-job `GITHUB_TOKEN` is not the former custom App. It may
    be used with least privilege inside Actions. Human/Terra operations use the
    authenticated repository administrator through normal `gh`/GitHub access.
14. Mac Mini/self-hosted runner infrastructure is removed rather than retained as
    a dormant fallback.
15. Usage alerts are enabled. No spending limit or automatic usage stop is set
    during the measurement period.
16. The permanent release and all nine consumer promotions may use repository
    administrator emergency merge authority for this correction only.

## In scope

- Managed delivery configuration/schema/state.
- Workflow triggers, concurrency, cancellation, retry, and runner routing.
- Phase PR lifecycle and exact-candidate sealing.
- Fast/full/release profiles and repository-owned command configuration.
- Full-suite receipts and promotion reuse.
- Minimal `GITHUB_TOKEN` permissions and normal authenticated operator flows.
- Deletion of former App logic, secrets/variables by name, workflows, scripts,
  contracts, tests, labels, runner registrations, host services, and containers.
- Installer/manifest/version/release changes.
- IDE Development self-verification and permanent release.
- Exact-version rollout to all nine consumers.
- GitHub Actions usage alerts and usage evidence, with no stop limit.
- Documentation, migration, rollback, and final evidence.

## Out of scope

- Changing product/business code in consumer repositories.
- Redesigning LiNKdeveloper's ProductRun factory or deploying it to its VPS.
- Running LiNKdeveloper's continuous factory tests on GitHub.
- GitLab migration.
- Replacing Bugbot.
- Deleting unrelated branches/worktrees or concurrent feature work.
- Requiring identical commit hashes across branches; the required identity is the
  Git tree and declared dependency identity because protected PR merges can create
  different merge commits with identical files.

## Product-code boundary

Consumer repositories will change because `.ide-development/`, managed workflows,
managed scripts, managed AGENTS sections, manifests, and installation state are
versioned repository files. Those are development-system changes. Executors must
not alter application source, product tests, database migrations, infrastructure,
or business configuration except for a narrowly necessary repository-owned CI
profile declaration reviewed by Terra.

## Expected compute behavior

- Checkpoint: zero Actions jobs.
- Draft Phase PR update: fast checks only; prior update cancels.
- Sealed final Phase candidate: fast checks, Bugbot, one full suite.
- Merge to development: short verification only if the tested Git tree is the same.
- Development to staging: short receipt/identity/policy gate.
- Staging to main: short receipt/identity/policy gate.
- Different tree or dependency identity: stop and require a new final candidate;
  do not reuse the old receipt.
