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

### Workers

- Use `issue/<PREFIX>-<n>-<slug>` from the orchestrator.
- Commit and push often. Never open PRs.
- Run fast checks: `python3 scripts/gitops/run_delivery_profile.py fast`.
- End with a lessons note.

### Orchestrator

- Packages with `scripts/orchestrator/package.py`.
- Requires Full CI and one exact-head review by a different model family (`scripts/orchestrator/merge_check.py`), then merges.
- Promotes with `scripts/orchestrator/promote_main.py` (`promote/main/*` into `main`, checked by `Linktrend Receipt Gate`).
- There is no staging branch.
- Repair ladder: Luna/Grok ×3, then Sol/Opus ×1, then the other of Sol/Opus ×1, then flag Carlos. Recorded with `scripts/orchestrator/runlog.py` and watched by `scripts/orchestrator/watchdog.py`.

### Hard stops

- No self-review.
- No prefer-incoming.
- Never bypass branch protection.
<!-- END LINKTREND-IDE-MANAGED -->
