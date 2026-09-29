<!-- BEGIN LINKTREND-IDE-MANAGED -->
## LiNKtrend IDE-managed GitOps (do not edit between markers)

This section is maintained by LiNKtrend wire/sync tooling (do not edit between markers).
Consumer-specific guidance may live **outside** these markers.

### Session entrypoints (all platforms)

- **New coding session:** follow agentsetup — create/reuse the GitHub issue and `issue/<n>-<slug>` automatically via `python3 scripts/gitops/create_issue_branch.py`. Never ask humans for issue id/slug.
- **Already-open / wrong branch:** follow agentcomply — migrate dirty work onto the correct `issue/*` branch for this repo.
- Cursor: `/agentsetup` and `/agentcomply` map to `.cursor/commands/agentsetup.md` and `.cursor/commands/agentcomply.md` (skills under `.cursor/skills/`).
- Codex / ChatGPT Work Agents: use this root `AGENTS.md` managed section plus the same scripts; do not require the IDE Development checkout path.

### Lifecycle

- Work on `issue/<n>-<slug>` (or `dev/*`) → push. The v2 Phase Packager and delivery controller are retired in v3 (IDE-22); see the v3 plan.
- Promote: the orchestrator promotes development → main after green CI and independent review.

### Agent rules

- Ship = checkpoint (commit+push). Max 3 ordinary repairs. (The v2 Phase Packager is retired in v3 (IDE-22); see the v3 plan.)
- Completion: the v2 completion gate is retired in v3 (IDE-22); see the v3 plan.
- Finished work runs appropriate tests/checks and auto-repairs ordinary failures with at most 3 bounded repair cycles.
- Repair tasks: `python3 scripts/gitops/repair_task.py` (upsert | dispatch-attempt | resolve | list).
- No prefer-incoming. No Cursor spawn claims from GitHub Actions.

### Consumer workflow / check configuration

Static `workflow_run.workflows` names are rendered at install time from the committed consumer config:

`.github/linktrend-gitops-consumer.json`

Fields: `fastWorkflowName`, `ciWorkflowName`, `branchPolicyWorkflowName`, `bugbotCheckName`, and optional `runnerType` (`github-hosted`; retired self-hosted profiles are rejected). Both workflow names are exact display names that must run on the same Phase PR head.

Repository Actions **variables** still configure required **check/job display names** for gates:

- `LINKTREND_INTEGRATOR_REQUIRED_CHECKS`
- `LINKTREND_STAGING_GATE_CHECKS` / `LINKTREND_RELEASE_GATE_CHECKS`

Do not confuse the two: workflow wake names come from the JSON config; gate check names come from Actions variables.

See `docs/GITOPS-CONSUMER-ROLLOUT.md` when present in the system repo.
<!-- END LINKTREND-IDE-MANAGED -->
