# IDE Development — system source (Codex / ChatGPT Work Agents)

This repository is **LiNKdeveloper / IDE Development**: the shared Stage 1 Application
Factory system source. It authors `core/managed-core/` and is the **internal
self-verification target**.

It is **not** a consumer rollout entry and must **not** receive a nested
`.ide-development/` install of itself.

## Native discovery (no `.cursor` required)

- Physical skills: `.agents/skills/agentsetup/SKILL.md`, `.agents/skills/agentcomply/SKILL.md`
- Package source: `core/managed-core/`
- Installer (for disposable/approved consumers only): `python3 scripts/ide-development.py`
- When the managed section below mentions `.ide-development/`, that is the **consumer** install path. In this system repository open `core/managed-core/` instead (no nested self-install).

<!-- BEGIN LINKTREND-IDE-MANAGED -->
## LiNKtrend IDE-managed development system (do not edit between markers)

This section is maintained by LiNKtrend install/sync tooling. Repository-owned guidance may live **outside** these markers.

### Session entrypoints

- New session: follow agentsetup. Already-open or wrong branch: follow agentcomply.
- Work IDs are Ledger IDs (`<PREFIX>-<n>`, for example `IDE-33`). The branch is `issue/<PREFIX>-<n>-<slug>`, given by the orchestrator; `scripts/gitops/create_issue_branch.py` is the branch helper. Never ask a human for an ID or slug.

### Lifecycle

1. A worker commits and pushes its `issue/*` checkpoint. Issue branches do not open PRs or start GitHub CI; workers run local focused checks.
2. The orchestrator combines accepted checkpoints on one `phase/*` branch and opens one Phase PR into `development` (`scripts/orchestrator/package.py`).
3. That Phase PR gets one combined CI run (`Linktrend Fast Checks`, `Verify IDE Development`, and platform matrix only when its path classifier applies) plus one independent exact-head review (`scripts/orchestrator/merge_check.py`). Merge only when all applicable evidence covers the same Phase head and the development merge preserves its tree.
4. The orchestrator promotes through a temporary `promote/main/*` pull request into `main` (`scripts/orchestrator/promote_main.py`, checked by `Linktrend Main Receipt Gate`). The gate reuses the matching Phase Verify inventory; it does not rerun Full.
5. After `main`, deploy is automatic (`Linktrend Deploy`, when the repo declares `deploy/target.json`).

Long-lived branches are `development` and `main` only.

### Workers

- Commit small and push often. Never open pull requests.
- Run the local fast profile before handoff: `python3 scripts/gitops/run_delivery_profile.py fast`. GitHub CI runs once on the combined Phase PR, not on each Issue.
- Consumer workflow names come from `.github/linktrend-gitops-consumer.json`.
- End with a lessons note.

### Orchestrator

- Repair ladder: Luna/Grok ×3, then Sol/Opus ×1, then the other of Sol/Opus ×1, then flag Carlos. Recorded with `scripts/orchestrator/runlog.py` and watched by `scripts/orchestrator/watchdog.py`.
- Cheap-helper rule: keep planning, judgement reviews, decisions and talking to Carlos on the frontier model; hand routine lookups, summaries and mechanical checks to a cheap helper subagent.

### Hard stops

- No self-review.
- No prefer-incoming.
- Never bypass branch protection.
<!-- END LINKTREND-IDE-MANAGED -->
