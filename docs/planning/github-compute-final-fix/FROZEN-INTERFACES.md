# Frozen Interfaces

These interfaces let Luna executors work in parallel. Terra may clarify types or
file names during preflight, but may not change semantics without recording the
reason and updating every affected packet before dispatch.

## 1. Delivery configuration

The installed repository exposes one versioned configuration object with these
logical fields (existing schemas may be migrated rather than duplicated):

```json
{
  "schemaVersion": 2,
  "mode": "phase-integration",
  "compute": {
    "provider": "github-hosted",
    "runner": "ubuntu-24.04-arm",
    "checkpointCI": false,
    "cancelObsolete": true,
    "maxInfrastructureAttempts": 2,
    "maxSealedCandidates": 2
  },
  "profiles": {
    "fast": { "commands": [], "timeoutMinutes": 5 },
    "full": { "commands": [], "required": true },
    "release": { "commands": [] }
  },
  "promotion": {
    "reuseExactReceipt": true,
    "identity": ["repository", "gitTree", "dependencyDigest", "profileDigest", "workflowDigest"]
  },
  "review": { "bugbot": "final-candidate-only" }
}
```

Repository-owned commands remain repository-owned. The installer supplies safe
defaults and validation, not guessed application commands.

## 2. Candidate identity

```text
CandidateIdentity = {
  repository,
  sourceBranch,
  headCommit,
  gitTree,
  dependencyDigest,
  profileDigest,
  workflowDigest
}
```

`headCommit` is evidence, but receipt reuse is decided by the remaining immutable
content inputs. This permits different protected-merge commits with identical
trees while rejecting any changed files or dependencies.

## 3. Full-suite receipt

```text
FullSuiteReceipt = {
  schemaVersion,
  candidateIdentity,
  workflowRunId,
  workflowRunAttempt,
  runnerLabel,
  startedAt,
  completedAt,
  conclusion,
  commandDigest,
  evidenceDigests,
  receiptDigest
}
```

Only `conclusion=success`, exact identity equality, recognized workflow identity,
and an unmodified digest are reusable. A receipt must remain available through
the completion of main promotion. Retention must exceed the expected promotion
window and be documented.

## 4. Lifecycle states

```text
checkpointed -> integrating -> draft-phase-pr -> sealed-candidate
sealed-candidate -> fast-checking -> full-checking -> review-complete
review-complete -> development-eligible -> staging-eligible -> main-eligible
any active state -> superseded | code-failed | infrastructure-retry | stopped-alert
```

There is no transition from ordinary checkpoint to CI. There is no transition
from changed promotion content to receipt reuse.

## 5. Required named checks

Use stable names across source and consumers:

- `Linktrend Fast Checks`
- `Linktrend Full Suite`
- `Linktrend Receipt Gate`
- `Linktrend Branch Source Policy`
- existing Bugbot required check/status as discovered in preflight

Terra must union these with repository-specific required checks; it must never
erase consumer-owned requirements.

## 6. Workflow events

- Checkpoint push on `issue/*` or `dev/*`: no managed workflow trigger.
- Phase PR opened/updated: fast workflow on PR events with a concurrency key scoped
  to repository + workflow + PR number and `cancel-in-progress: true`.
- Final candidate: explicit seal signal bound to exact head commit triggers Bugbot
  and full suite. A later commit invalidates the seal and receipt automatically.
- Promotion PR: receipt gate and source-policy check only; full suite is not
  triggered when identity matches.
- Manual rerun: permitted only while attempt count is below two and must retain
  the same exact candidate identity.

## 7. Authentication

- Test workflows: built-in `GITHUB_TOKEN`, `contents: read`, plus only permissions
  strictly required to publish native workflow results/artifacts.
- Same-repository metadata writes, if unavoidable: built-in `GITHUB_TOKEN` with an
  explicit minimal job-level permission block.
- PR creation, admin emergency merge, ruleset changes, runner deletion, secret
  deletion, and release publication: Terra using Carlos's authenticated repository
  administrator session and recording the actor/command/result without secrets.
- Forbidden: former custom App IDs/private keys/tokens, minting installation
  tokens, hidden fallback PATs, or printing credential values.

## 8. Legacy-removal inventory contract

Preflight produces a redacted inventory of:

- custom App installation and repository access;
- `LINKTREND_GITOPS_APP_*` and equivalent secrets/variables by name only;
- former App/Packager/Integrator/repair/promotion workflow dependencies;
- self-hosted runner registrations and labels;
- Mac launchd/coordinator services;
- Docker runner containers/images/volumes/networks owned by IDE Development;
- managed files in all nine consumers.

Deletion is allowed only for an item positively identified as owned by the former
IDE Development delivery system. Ambiguous items are preserved and reported.

## 9. Packet evidence

Every packet returns:

```text
packetId, attempt, branch, baseSha, commitSha, changedPaths,
commandsRun, passFail, failures, artifacts, prohibitedActionsConfirmed
```

Terra accepts an exact commit only after checking the diff, running packet
validation, and confirming prohibited paths/actions were not touched.
