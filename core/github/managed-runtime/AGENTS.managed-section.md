<!-- BEGIN LINKTREND-IDE-MANAGED -->
## LiNKtrend IDE-managed GitOps (do not edit between markers)

This section is maintained by `scripts/sync-agents-managed-section.sh`.
Consumer-specific guidance may live **outside** these markers.

### Lifecycle

- Work on `issue/<n>-<slug>` (or `dev/*`) → push → Packager opens draft PR → Integrator merges to `development`.
- Promote: `development` → `staging` → `main` via temporary `promote/*` PRs only.

### Agent rules

- Ship = checkpoint (commit+push). Packager opens PRs. Max 3 ordinary repairs.
- Completion: `python3 scripts/gitops/completion_gate.py` (checkpoint | review-ready | blocked | status | write-evidence).
- Finished work runs appropriate tests/checks, auto-repairs ordinary failures with at most 3 bounded repair cycles, writes machine-readable evidence with `completion_gate.py write-evidence`, then calls `completion_gate.py review-ready`.
- `review-ready` is the authoritative fail-closed gate that publishes **Linktrend Review Ready**. Do not call `mark-review-ready.sh` as a pre-gate publisher; it is only a compatibility wrapper that requires evidence and delegates to the gate.
- If completion cannot pass, call `completion_gate.py blocked` so `.linktrend/completion-blocker.json` records the durable blocker and the branch stays ineligible.
- Repair tasks: `python3 scripts/gitops/repair_task.py` (upsert | dispatch-attempt | resolve | list).
- No prefer-incoming. No Cursor spawn claims from GitHub Actions.

### Consumer CI check variables

Set repository Actions variables (display names must match CI job/check names):

- `LINKTREND_INTEGRATOR_REQUIRED_CHECKS`
- `LINKTREND_STAGING_GATE_CHECKS` / `LINKTREND_RELEASE_GATE_CHECKS`
- `LINKTREND_CI_WORKFLOW_NAME` (default `CI`)
- `LINKTREND_BRANCH_POLICY_WORKFLOW_NAME` (default `Branch Source Policy`)
- `LINKTREND_BUGBOT_CHECK_NAME` (default `Cursor Bugbot`)

See `docs/GITOPS-CONSUMER-ROLLOUT.md`.
<!-- END LINKTREND-IDE-MANAGED -->
