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

- Work on `issue/<n>-<slug>` (or `dev/*`) → push → Packager opens draft PR → Integrator merges to `development`.
- Promote: `development` → `staging` → `main` via temporary `promote/*` PRs only.

### Agent rules

- Ship = checkpoint (commit+push). Packager opens PRs. Max 3 ordinary repairs.
- Completion: `python3 scripts/gitops/completion_gate.py` (checkpoint | review-ready | blocked | status | write-evidence).
- Finished work runs appropriate tests/checks, auto-repairs ordinary failures with at most 3 bounded repair cycles, writes machine-readable evidence with `completion_gate.py write-evidence`, then calls `completion_gate.py review-ready`.
- `review-ready` is the authoritative fail-closed gate. Production publish **and withdraw** of **Linktrend Review Ready** is GitHub App only (trusted `linktrend-review-ready-publisher` workflow with `action=publish` or `action=withdraw` when local privileged credentials are unavailable). Do not publish or withdraw with a user PAT / Carlos restricted identity / `GITHUB_TOKEN` fallback. Do not call `mark-review-ready.sh` as a pre-gate publisher; it is only a compatibility wrapper that requires evidence and delegates to the gate. `clear-review-ready.sh` fails closed without App credentials and prints the App-backed withdraw route.
- Do **not** create or use `.linktrend/review-ready.json` (commit status only — see `core/github/REVIEW-READY.md`).
- If completion cannot pass, call `completion_gate.py blocked`. `.linktrend/completion-blocker.json` is only a **local cache**. The durable cross-machine record is the GitHub repair issue created/updated by the gate (when authenticated repo resolution succeeds). Do not claim durable registration if the command reports `durableRecord=false`.
- Repair tasks: `python3 scripts/gitops/repair_task.py` (upsert | dispatch-attempt | resolve | list).
- No prefer-incoming. No Cursor spawn claims from GitHub Actions.

### Consumer workflow / check configuration

Static `workflow_run.workflows` names are rendered at install time from the committed consumer config:

`.github/linktrend-gitops-consumer.json`

Fields: `ciWorkflowName`, `branchPolicyWorkflowName`, `bugbotCheckName`.

Repository Actions **variables** still configure required **check/job display names** for gates:

- `LINKTREND_INTEGRATOR_REQUIRED_CHECKS`
- `LINKTREND_STAGING_GATE_CHECKS` / `LINKTREND_RELEASE_GATE_CHECKS`

Do not confuse the two: workflow wake names come from the JSON config; gate check names come from Actions variables.

See `docs/GITOPS-CONSUMER-ROLLOUT.md` when present in the system repo.
<!-- END LINKTREND-IDE-MANAGED -->
