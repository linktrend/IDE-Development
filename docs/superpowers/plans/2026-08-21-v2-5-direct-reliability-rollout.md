# IDE Development v2.5 Direct Reliability and Rollout Plan

**Goal:** Close the dogfood reliability gaps exposed during v2.5 development, integrate one exact Phase candidate, prove it in LiNKplatform, and roll the same package to the remaining consumers without repeating equivalent evidence.

**Starting identity:** `2b9e50aaf4b9b1625127bf97956b577f8feff6df` / tree `10068aa71ef147795356e1479ac054193d0d055b` on `issue/356-harden-ide-development-v2-5-direct-execution-rel`.

**Authority:** Founder-directed direct Codex execution. Cursor agents, Terra orchestration, and scheduled chat heartbeat remain disabled. Obsolete v2.4 publisher ceremony and duplicated unchanged verification are waived; exact identity, security, canary, rollback, and protected promotion are not.

## Root-cause baseline

1. The packaged heartbeat logic is callable code and its cleanroom test supplies in-memory adapters, but the product has no concrete durable invocation boundary. This allowed a chat/orchestrator turn to stop despite a persisted safe next action.
2. The rollout configuration in `delivery_controller.py` configures promotion branch names; it is not a consumer cohort controller. The manifest-required canary gate, same-turn downstream fan-out, per-target isolation, and receipt reuse therefore lack a reusable runtime.
3. `scripts/verify-ide-development.sh` uses a BSD-incompatible `mktemp` suffix pattern. On macOS the literal candidate can collide and fail before tests run.
4. `scripts/tests/test-gitops-lifecycle.sh` invokes `verify-platform-adoption.sh`, while the parent verifier invokes it again. This repeats an equivalent installation proof without increasing confidence.

## Task 1: Add failing regression tests

**Files:**

- Add `tests/execution_protocol/test_rollout_controller.py`
- Modify `scripts/tests/test_manifest_persistence_recovery.py`
- Modify `scripts/tests/test_generated_output_closure.py`
- Modify `tests/cleanroom_acceptance/test_package_materialization.py`

**Required failures before implementation:**

- A persisted actionable repair cannot produce a quiet/no-action decision at the concrete file-backed controller boundary.
- Downstream mutation is impossible before all canaries pass; after pass, all safe available slots are filled in one turn.
- A repository-specific failure isolates one target; a systemic failure stops the cohort and schedules rollback.
- An exact package/environment receipt suppresses an unchanged rerun; changed identity invalidates it.
- The main verifier uses a portable terminal-`X` `mktemp` template and platform adoption appears only once in the top-level path.
- Managed and extracted packages can import and execute the new generic rollout runtime.

Run: `python3 -m unittest tests.execution_protocol.test_rollout_controller scripts.tests.test_manifest_persistence_recovery scripts.tests.test_generated_output_closure tests.cleanroom_acceptance.test_package_materialization -v`

## Task 2: Implement the minimum reusable controls

**Files:**

- Add `core/execution/rollout.py`
- Add `scripts/gitops/heartbeat_controller.py`
- Modify `core/execution/__init__.py`
- Modify `scripts/ide_development/build_manifest.py`
- Modify `scripts/verify-ide-development.sh`
- Modify `scripts/tests/test-gitops-lifecycle.sh`
- Modify managed doctrine/config only where the executable interface requires it

**Behavior:**

- Use one deterministic rollout state machine with manifest-provided cohorts and capacity; no repository names or fixed cohort sizes in product code.
- Use receipt identity to reuse unchanged proof and invalidate changed proof.
- Provide a file-backed heartbeat command that validates, reconciles, persists, reads back, and exits nonzero when actionable work has not been dispatched. It must never silently translate missing adapters into success.
- Use a BSD/GNU portable temporary filename.
- Keep platform-adoption coverage once at the top-level verifier and remove the nested duplicate.

## Task 3: Regenerate and verify the package

Run in order:

1. `python3 -m scripts.ide_development.build_manifest`
2. `python3 scripts/gitops/generated_output_closure.py --verify`
3. Focused test command from Task 1
4. `git diff --check origin/development...HEAD`
5. `bash scripts/verify-ide-development.sh` (includes the consumer-profile matrix once)

Do not rerun a completed exact-tree command unless its inputs or environment changed.

## Task 4: Integrate and canary

1. Commit and push issue 356.
2. Fast-forward/cherry-pick the exact accepted commit onto `phase/v2.5`; regenerate only if integration changes bytes.
3. Update PR #343 and run the minimum required exact-head checks.
4. Produce the reproducible v2.5 package/release receipt.
5. Install that exact package into an isolated LiNKplatform issue branch, verify managed paths, run its required local/hosted checks, and exercise rollback/re-update.
6. Repair systemic defects in IDE Development first; repeat only invalidated canary evidence.

## Task 5: Promote and roll out

1. Merge Phase through the protected delivery path into `development`.
2. Promote the same verified tree through `staging` and `main`, reusing the exact receipt.
3. After LiNKplatform passes, prepare isolated issue branches for the other eight consumers and update them concurrently where their repository locks do not conflict.
4. Keep repository-specific failures isolated; stop all targets only for a systemic package defect.
5. Record exact before/after commits and trees, package digest, checks, rollback, and final portfolio reconciliation.
