# v3 CI contract

**Status:** Active v3 (IDE-28).
**Workflow:** `.github/workflows/ci.yml`
**Profile file:** `.github/linktrend-delivery-mode.json`

Required check names belong to live branch protection. Agents do not rename them.

## Triggers

`pull_request` to `development`, with jobs restricted to `phase/*` heads. Issue
checkpoint pushes and main promotion do not run this workflow.

Concurrency group: `ci-${{ github.workflow }}-${{ github.ref }}`, with `cancel-in-progress: true`.

Runner for both jobs: `ubuntu-24.04-arm`. Python 3.11. CI installs `jsonschema==4.26.0`.

## Jobs

### Linktrend Fast Checks

Timeout 10 minutes. The step runs:

```bash
python3 scripts/gitops/run_delivery_profile.py fast
```

That is the local command as well. The fast profile in `.github/linktrend-delivery-mode.json` (`timeoutMinutes`: 3) runs three argv commands:

1. `python3 -m py_compile` on the gitops, dispatch, orchestrator, and codex modules named in the profile.
2. Fixture-aware secret scanning: `python3 scripts/gitops/secret_scan.py`. Secret scan stays in the fast profile.
3. `python3 -m unittest` on the focused modules named in the profile.

### Verify IDE Development (Full)

Each combined Phase pull request head gets one Full run. A new head needs a new run.

Checkout uses `fetch-depth: 0`. On `pull_request`, the job ensures `origin/<base>` exists and exports `LINKTREND_TARGET_BASELINE_REF` and `LINKTREND_TARGET_BASELINE_SHA`. It installs Node 22, then runs:

```bash
CI=true bash scripts/verify-ide-development.sh
bash scripts/verify-pipeline-states.sh
```

`profiles.full` and `profiles.release` in the delivery-mode JSON are not this job. CI Full is `Verify IDE Development`.

The Verify job checks out the exact PR head, has a 45-minute timeout, and
uploads its complete Full inventory only after both commands pass. The
cross-platform installer matrix runs with a 60-minute limit only when the
shared changed-path classifier identifies installer, workflow, fixture, or
dependency inputs. All three matrix checks are required for those Phase PRs.

## Required check names

| Pull request target | Branch protection requires | Orchestrator also requires before merge |
|---|---|---|
| `development` | `Linktrend Fast Checks`, `Linktrend Branch Source Policy`, `Verify IDE Development`; plus the three `Installer matrix (...)` checks when the shared path classifier applies | independent review of the exact head |
| `main` | `Linktrend Branch Source Policy`, `Linktrend Main Receipt Gate` | — |

`Linktrend Main Receipt Gate` separates the active gate from the old staging
workflow, which also emitted the legacy `Linktrend Receipt Gate` context. It verifies the promoted
tree against a development merge commit whose second parent is the exact Phase
head. That Phase Verify run must have produced a reusable inventory with exact
repository, commit, tree, dependency, profile, and workflow identity. The gate
downloads that run's artifact and does not rerun Full. Promotion to `main` does
not re-review.

Missing required checks are not success.

## Run fast checks locally

From the repository root, before pushing:

```bash
python3 scripts/gitops/run_delivery_profile.py fast
```

Then run the checks named in the Issue.

## Retired

Retired, and not live gates: the v2 commit-status publisher and its evidence gate, the v2 review-gate classifier, the repair observer, promotion receipts, the v2 packaging and merge services, the host-based coordinator, and the intermediate promotion branch between `development` and `main`. The v2 named-gate ids (`fast-gate`, `release-gate`, and their promotion-branch sibling) are not the live required checks.
