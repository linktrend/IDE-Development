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

1. A worker commits on its `issue/*` branch and pushes.
2. The orchestrator opens the pull request into `development` (`scripts/orchestrator/package.py`).
3. Full CI plus one exact-head review by a different model family (`scripts/orchestrator/merge_check.py`), then the orchestrator merges.
4. The orchestrator promotes through a temporary `promote/main/*` pull request into `main` (`scripts/orchestrator/promote_main.py`, checked by `Linktrend Receipt Gate`).
5. After `main`, deploy is automatic (`Linktrend Deploy`, when the repo declares `deploy/target.json`).

Long-lived branches are `development` and `main` only.

### Workers

- Commit small and push often. Never open pull requests.
- Run fast checks before the final push: `python3 scripts/gitops/run_delivery_profile.py fast`.
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

