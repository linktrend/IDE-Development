# v3 delivery flow

**Status:** Active v3 (IDE-28).
**Live CI:** `.github/workflows/ci.yml` and `.github/linktrend-delivery-mode.json`.

## Flow

1. **Issue.** Work starts from an Issue. The Issue names any checks beyond the fast profile.
2. **Branch.** The worker uses `issue/<n>-<slug>`. Commit and push often. Never open a pull request.
3. **Fast checks.** Before each push, run `python3 scripts/gitops/run_delivery_profile.py fast`, the same command as CI job `Linktrend Fast Checks`. The fast profile includes fixture-aware secret scanning (`python3 scripts/gitops/secret_scan.py`). Also run the Issue's named checks.
4. **Package.** The orchestrator aggregates independently accepted Issue checkpoints into one `phase/*` candidate and opens one Phase PR to `development`. Individual Issue branches do not start GitHub CI or create PRs.
5. **Phase verification and review.** One combined run executes `Verify IDE Development` and writes its identity-bound Full inventory only after the existing Verify commands succeed. Fast checks run for every Phase head. The Ubuntu, macOS, and Windows installer matrix runs only when installer, workflow, fixture, or dependency inputs change. The shared path classifier governs both merge and promotion eligibility. An independent reviewer approves that exact head SHA. Bugbot is not part of eligibility.
6. **Merge.** Merge when Fast, Verify, `Linktrend Branch Source Policy`, independent review, and any path-applicable platform checks are green on the exact reviewed head. The development merge commit must retain the Phase head tree; any merge resolution that changes it needs a fresh reviewed Phase candidate.
7. **Promote.** Promotion to `main` reuses the same Phase run inventory only when repository, head commit, tree, dependencies, profile, and workflow identity still match. The `Linktrend Main Receipt Gate` downloads the artifact from that exact successful Verify run and fails closed on mismatch; it does not rerun Full. There is no second review. Staging is not part of the active delivery path.
8. **Deploy.** Deploy uses the promoted `main` tree that passed the promotion check.

## Repair ladder

CI failures and review `REQUEST_CHANGES` both count as failed attempts on the current rung. Until a live ledger exists, `scripts/orchestrator/runlog.py` stores the rung in `repair_rung` (`0`, `1`, or `2`). `scripts/orchestrator/watchdog.py` recommends the next rung.

| Rung | Who | Attempts | Then |
|---|---|---|---|
| 0 | Luna (Codex) or Grok (cursor-002). When the Issue started on Sol or Opus, that starting model is rung 0. | Up to 3 for Luna or Grok. One when the Issue started on Sol or Opus. | Rung 1, or rung 2 when the Issue started on Sol or Opus. |
| 1 | A stronger model, Sol or Opus. | 1 | Flag Carlos. |
| 2 | The other of Sol and Opus. Used when the Issue started on Sol or Opus. | 1 | Flag Carlos. |

When the ladder is exhausted, the orchestrator flags Carlos with a short plain-language question.

## CI as it runs today

`ci.yml` runs on Phase pull requests targeting `development`, on `ubuntu-24.04-arm`. Both Fast and Verify explicitly check out the PR head SHA. Verify has a 45-minute timeout.

- `Linktrend Fast Checks` runs `python3 scripts/gitops/run_delivery_profile.py fast`.
- `Verify IDE Development` runs the existing full-history checkout, pull-request baseline export, `CI=true bash scripts/verify-ide-development.sh`, and `bash scripts/verify-pipeline-states.sh` through the Full profile, then uploads the inventory from that run. Promotion downloads and verifies that artifact by run ID.

Secret scan stays inside the fast profile. The JSON key `profiles.full` is not the CI Full job.

## Retired

Retired, and not the live path: the v2 commit-status publisher and its evidence gate, the v2 review-gate classifier, the repair observer, promotion receipts, the v2 packaging and merge services, the host-based coordinator, and the intermediate promotion branch between `development` and `main`. In v3 the orchestrator packages, merges and promotes; workers build Issues; the Ledger (`ide_ledger`) records state. The v2 records are in `docs/archive/`.
