# Upgrade a consumer from v2.5.2 to v3.0.0

**Audience:** the orchestrator (or an operator) upgrading a consumer repository in Wave 6.
**Package:** v3.0.0. **Starting point:** a consumer on v2.5.2.

## What the upgrade does

`python3 scripts/ide-development.py update --target <consumer>` (run from an IDE Development v3.0.0 checkout) is one transaction:

- Replaces and adds the v3 managed files and sets `.ide-development/installed-state.json` to `packageVersion` 3.0.0.
- **Deletes** every managed file that v2.5.2 installed and v3 no longer ships: 62 paths, listed in `core/managed-core/migrations/catalog.json` with `sincePackageVersion: 3.0.0` (131 entries: the v2.5.2 hash of each path plus every different hash the same path had in an older published v2 release). A file is deleted only when its bytes equal released bytes.
- **Deletes** the v2 root workflows in `.github/workflows/` (`linktrend-development-to-staging.yml`, `linktrend-integrator-merge.yml`, `linktrend-repair-observer.yml`, `linktrend-review-gate.yml`, `linktrend-review-packager.yml`, `linktrend-review-ready-publisher.yml`, `linktrend-staging-to-main.yml`). v2 rendered these per consumer, so a file is deleted only when it equals a published v2 rendering of it for that consumer's `.github/linktrend-gitops-consumer.json` (any published template from v2.1.0 to v2.5.2, both v2 orchestration profiles).
- Never deletes a changed file. A locally modified retired file stops the update with exit 11 and a `unknown_content` conflict naming the path: *"retired managed file was modified locally … refusing removal"*. Nothing is written.
- `rollback` restores the exact v2.5.2 bytes and modes, including the removed root workflows.

`scripts/sync-managed-workflows.sh <consumer>` applies the same hash-guarded removal of retired root workflows (exit 11 and a `CONFLICT:` line for a modified copy), syncs the v3 set (`branch-source-policy.yml`, `linktrend-cleanup-merged.yml`, `linktrend-promote-main.yml`), and adds `linktrend-deploy.yml` only when the consumer has `deploy/target.json` (`docs/contracts/DEPLOY-CALLER.md`). `scripts/backfill-managed-workflows.sh` reports every consumer with conflicts and exits 11 at the end.

## How a consumer Project upgrades (Wave 6)

1. **Prepare CI first.** In v2, `Linktrend Fast Checks` was produced by the retired `linktrend-review-packager.yml`. In v3 the consumer's own `ci.yml` must have a job named `Linktrend Fast Checks` that runs on pull requests into `development` (`core/github/CI-GATE-CONTRACTS.md`). Land that on `development` before step 3, or pull requests lose a required check.
2. **Plan.** `python3 scripts/ide-development.py plan --json --target <consumer>`. Expect `remove` actions for the retired files and workflows and zero conflicts. For each conflict: compare the file with the released bytes; keep any real local change somewhere owned by the consumer, then delete or restore the file, and plan again.
3. **Update** on an `issue/*` branch of the consumer: `update --json`, then `sync-managed-workflows.sh <consumer>`, then `verify --json` and `drift --json` (both exit 0; no `orphan_managed`). Commit and push; the consumer's orchestrator packages it like any other change.
4. **Branch protection.** After the change is on `development` and `main`, the rulesets must stop requiring the retired contexts, or every pull request waits forever. Required contexts in v3: `development` — `Linktrend Fast Checks`, `Linktrend Branch Source Policy`, and `Verify IDE Development`; `main` — `Linktrend Branch Source Policy`, `Linktrend Main Receipt Gate`. The matrix is dynamically enforced by the orchestrator only when the shared changed-path classifier applies. Remove any of: `Linktrend Review Gate`, `Linktrend Full Suite`, `Linktrend Reconciled Fast Checks`, `Linktrend Reconciled Tree Canary`, `Linktrend Recovery Receipt`, `Linktrend Final Candidate Bugbot Request`, `Linktrend Phase Ready`, `Linktrend Staging Gate`, `Linktrend Release Gate`, `Linktrend Coordinator`, the Review Ready status. Preserve staging history until its divergent commits are reconciled and archived. Protection changes are made by the orchestrator through `scripts/manage-repository-protections.sh`, never bypassed.
5. **Deploy.** A consumer that deploys adds `deploy/target.json` (schema owned by LiNKops) and re-runs the workflow sync to get `linktrend-deploy.yml`.

Consumers on an older published v2 release can update directly: the catalog carries every published hash of each retired path, and the root-workflow check covers every published template (the consumer profile matrix upgrades v2.3.6 and v2.3.7 layouts this way with zero conflicts and no drift). Files that a pre-v2.5.2 release retired without a migration stay as preserved orphans and show as `orphan_managed` in `drift`; review and delete them deliberately.

`linktrend/openclaw_prime` keeps its customization-scoped admission: `docs/contracts/OPENCLAW-CUSTOMIZATION-ADMISSION.md` admits the v3.0.0 package under the same contract.

## Proof: dry-run upgrade of a real consumer copy (2026-09-29)

The Issue named `linktrend/LiNKprofiles`; that repository does not exist (`git clone` and the GitHub API both return not found). The proof used `linktrend/LiNKskills` instead: public, `.ide-development/` installed, `packageVersion` 2.5.2, cloned at `28334c4` into a temporary directory with push disabled. Nothing was pushed to it.

**As cloned.** v3 `plan`: exit 11, 11 conflicts, nothing written. All 11 are managed files LiNKskills edited after installing v2.5.2 (for example `scripts/gitops/secret_scan.py`, `scripts/gitops/completion_gate.py`); the v2.5.2 installer's own `verify` reports the same 11. The retired ones among them are refused, not deleted. All 7 root workflows were recognised (they are v2.3.8 renderings from before a later config change).

**Normalized to a real v2.5.2 state.** In the temporary copy, the 11 edited files were restored to their v2.5.2 package bytes and the read-only modes that git does not store were restored. The v2.5.2 installer's `verify` then exited 0 with no drift.

| Step | Result |
|---|---|
| `plan` (dry run) | exit 0, 0 conflicts; 69 remove, 67 create, 137 replace, 1 marker upsert, 255 unchanged |
| `update` | exit 0, applied; `packageVersion` 2.5.2 → **3.0.0** |
| Removed | **69**: 62 retired managed files + 7 retired root workflows (list below) |
| Added / replaced | **67** added, **137** replaced (+ `AGENTS.md` marker block) |
| `verify` | exit 0, `ok: true`, 0 conflicts, 0 drift |
| `drift` | exit 0, no entries, **0 `ORPHAN_MANAGED`** |
| `.github/workflows/` after | `branch-source-policy.yml`, `ci.yml`, `linktrend-cleanup-merged.yml`, `linktrend-release-gate.yml`, `successor-release.yml` — no retired workflow; the last two and `ci.yml` are LiNKskills' own and untouched |
| `rollback` | exit 0; every file's bytes and mode identical to the v2.5.2 state; `git status` clean |

Removed root workflows: the 7 listed above. Removed managed files: `.ide-development/content/config/{manifest-persistence,portfolio-control-loop}.json`; `.ide-development/content/doctrine/{LINKTREND-REVIEW-GATE,MANIFEST-PERSISTENCE-RECOVERY,RECEIPT-SEAL-AND-RECOVERY}.md`; `.ide-development/execution/manifest_persistence.py`; `.ide-development/schemas/{delivery-operation,linktrend-review-gate,manifest-persistence,phase-handoff,phase-record,portfolio-control-loop,transition-receipt}.schema.json`; `.ide-development/tests/test_{candidate_lifecycle,delivery_controller,gate_receipts,linktrend_review_gate,manifest_persistence_recovery,phase_packager_coordinator,promotion_receipt_gate,receipt_seal_and_recovery}.py`; `.ide-development/workflows/linktrend-{development-to-staging,integrator-merge,review-gate,review-packager,review-ready-publisher,staging-to-main}.yml`; `core/execution/manifest_persistence.py`; `core/managed-core/content/config/manifest-persistence.json`; `core/managed-core/schemas/manifest-persistence.schema.json`; `scripts/gitops/{administrator_recovery,bugbot_user_credentials,completion_gate,conflict_task,delivery_controller,gate_receipt,heartbeat_controller,linktrend_review_gate,main_approve_package_discover,main_approve_package_reuse,packager_coordinator,packager_logic,portfolio_control_loop,promotion_receipt_gate,receipt_loop_detector,receipt_seal,repair_observer,repair_task,resolve_event_pr,review_ready_dispatch,review_ready_publisher_bootstrap,verify_reconciled_fast_dispatch,verify_reconciled_tree,wait_named_gate,write_outcome}.py`; `scripts/gitops/coordinator/{__init__,config,receipts,state}.py`; `scripts/gitops/{promote_main,promote_staging,resolve_bugbot_user_token}.sh`.

**Other v2.5.2 consumers (as-is plan only).** `LiNKautowork`: all 5 present root workflows recognised; 2 conflicts, both retired files it edited locally. `LiNKsites`: 3 of 6 root workflows recognised; the other 3 are renderings of unreleased development-branch templates and are reported as conflicts (as designed: only published bytes are deleted automatically), plus 5 locally edited managed files. Each needs the step 2 review before its Wave 6 update.

## Automated proof

`scripts/ide_development_tests/test_v3_upgrade.py` builds a real v2.5.2 consumer without network: it extracts the v2.5.2 release commit `5a64f7f` from local git objects, installs it with its own v2.5.2 installer, and renders the root workflows with the v2.5.2 sync script (both orchestration profiles). It then proves plan/update/verify/drift/rollback as above, that a modified retired file or workflow is a conflict and nothing is written, that the v3 sync removes retired workflows and adds the deploy caller only with `deploy/target.json`, and that the catalog equals the generator output. It skips only when the release commit is not in the local clone (shallow checkouts).

Regenerate the catalog and known bytes after a manifest change: `cd scripts && python3 -m ide_development.v3_retirements --write`, then `python3 -m ide_development.build_manifest --write`.
