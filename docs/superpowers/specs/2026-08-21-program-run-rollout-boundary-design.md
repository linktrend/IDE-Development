# Program Run Rollout Boundary Design

## Decision

IDE Development is a reusable development system, so its installed package must not contain a portfolio-specific repository list, fixed canary, rollout order, cohort size, or approval packet. A Program Run is the sole source of rollout targets and topology for each execution. A run may contain one target or many.

## Change

- Remove the historical nine-repository rollout order from reusable doctrine.
- Remove the portfolio-specific external cleanup plan from the managed package and package manifest.
- Retain only generic safety boundaries in reusable doctrine: system source is not its own consumer, configuration supplies targets, and protected external mutation remains approval-gated.
- Leave historical rollout evidence and repository-specific operating records unchanged.
- Release the changed package bytes as v2.5.1.
- Materialize the three canonical execution-contract files omitted by v2.5.0 and
  let runtime discovery resolve both the system-source and installed-consumer layouts.

## Verification

- A package-boundary test rejects the known portfolio repository names and the removed cleanup-plan artifact.
- Existing rollout tests prove configuration-driven topology, including a single-target run.
- Manifest verification and a disposable extracted-package installation prove the generated package remains complete.
- A v2.5.0-to-v2.5.1 upgrade canary must discover all required execution surfaces
  and load the execution-manifest schema from the installed package.

## Non-goals

No new rollout abstraction, scheduler, provider integration, or repository-specific migration logic is added.
