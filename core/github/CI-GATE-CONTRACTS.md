# v3 CI contract

**Status:** Active v3 (IDE-28).
**Workflow:** `.github/workflows/ci.yml`
**Profile file:** `.github/linktrend-delivery-mode.json`

Required check names belong to live branch protection. Agents do not rename them.

## Triggers

`push` and `pull_request` for branches `main` and `development`.

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

Each pull request head gets one Full run. A new head needs a new run.

Checkout uses `fetch-depth: 0`. On `pull_request`, the job ensures `origin/<base>` exists and exports `LINKTREND_TARGET_BASELINE_REF` and `LINKTREND_TARGET_BASELINE_SHA`. It installs Node 22, then runs:

```bash
CI=true bash scripts/verify-ide-development.sh
bash scripts/verify-pipeline-states.sh
```

`profiles.full` and `profiles.release` in the delivery-mode JSON are not this job. CI Full is `Verify IDE Development`.

## Required check names

| Pull request target | Branch protection requires | Orchestrator also requires before merge |
|---|---|---|
| `development` | `Linktrend Fast Checks`, `Linktrend Branch Source Policy` | `Verify IDE Development` green on the exact head |
| `main` | `Linktrend Branch Source Policy`, `Linktrend Receipt Gate` | — |

`Linktrend Receipt Gate` keeps its legacy ruleset name. The v3 job behind that name is the promotion check, delivered by another Issue. It verifies that the promoted tree equals a `development` commit whose Full CI (`Verify IDE Development`) was green. Promotion to `main` does not re-review.

Missing required checks are not success.

## Run fast checks locally

From the repository root, before pushing:

```bash
python3 scripts/gitops/run_delivery_profile.py fast
```

Then run the checks named in the Issue.

## Retired

Retired, and not live gates: Review Ready status and its publisher, completion-gate evidence, the review-gate classifier, the repair observer, promotion receipts, the packager, the delivery controller, Lisa, and staging. The names `fast-gate`, `staging-gate`, and `release-gate` are not the live required checks.
