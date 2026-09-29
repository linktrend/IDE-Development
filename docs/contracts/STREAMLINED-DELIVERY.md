# v3 delivery flow

**Status:** Active v3 (IDE-28).
**Live CI:** `.github/workflows/ci.yml` and `.github/linktrend-delivery-mode.json`.

## Flow

1. **Issue.** Work starts from an Issue. The Issue names any checks beyond the fast profile.
2. **Branch.** The worker uses `issue/<n>-<slug>`. Commit and push often. Never open a pull request.
3. **Fast checks.** Before each push, run `python3 scripts/gitops/run_delivery_profile.py fast`, the same command as CI job `Linktrend Fast Checks`. The fast profile includes fixture-aware secret scanning (`python3 scripts/gitops/secret_scan.py`). Also run the Issue's named checks.
4. **Package.** The orchestrator packages finished Issue branches into one pull request or several. Every pull request targets `development`.
5. **Pull request.** Each pull request gets exactly one Full CI run on its head (`Verify IDE Development`) and one independent review of that exact head SHA. The reviewer model is a different family from the author (a GPT model for Grok or Opus work; a Claude or Grok model for Codex work). Bugbot is optional.
6. **Merge.** Merge when `Linktrend Fast Checks`, `Linktrend Branch Source Policy`, and `Verify IDE Development` are green on the exact reviewed head and the review approves. A new commit needs a new review of the new head; the review record states that it covered at least the delta. `REQUEST_CHANGES` is a failed attempt on the current repair rung.
7. **Promote.** Promotion to `main` reuses the reviewed `development` result. There is no re-review. Pull requests into `main` require `Linktrend Branch Source Policy` and `Linktrend Receipt Gate`. That gate checks that the promoted tree equals a `development` commit whose Full CI was green.
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

`ci.yml` runs on push and pull_request to `main` and `development`, on `ubuntu-24.04-arm`.

- `Linktrend Fast Checks` runs `python3 scripts/gitops/run_delivery_profile.py fast`.
- `Verify IDE Development` is the Full run: full-history checkout, pull-request baseline export, `CI=true bash scripts/verify-ide-development.sh`, then `bash scripts/verify-pipeline-states.sh`.

Secret scan stays inside the fast profile. The JSON key `profiles.full` is not the CI Full job.

## Retired

Retired, and not the live path: Review Ready status and its publisher, completion-gate evidence, the review-gate classifier, the repair observer, promotion receipts, the packager, the delivery controller, Lisa, and staging.
