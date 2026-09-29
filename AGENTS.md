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

Installed managed core: **`.ide-development/`** (versioned package; treat as read-only except via the official installer).

### Session entrypoints

- **New coding session:** follow **agentsetup** — create/reuse the GitHub issue and `issue/<n>-<slug>` via `python3 scripts/gitops/create_issue_branch.py`. Never ask humans for issue id/slug.
- **Already-open / wrong branch:** follow **agentcomply** — migrate dirty work onto the correct `issue/*` branch for this repo.
- **Codex / ChatGPT Work Agents:** use this root `AGENTS.md` managed section and physical `.agents/skills/<name>/SKILL.md`. Do **not** require `.cursor` to be loaded.
- **Cursor:** use physical `.cursor/commands/agentsetup.md` / `agentcomply.md` and `.cursor/skills/`.

### Lifecycle

- Work on `issue/<n>-<slug>` (or rare `dev/*`) → push checkpoint. The v2 Phase Packager and delivery controller are retired in v3 (IDE-22); see the v3 plan.
- Promote: the orchestrator promotes development → main after green CI and independent review.

### Agent rules

- Ship = checkpoint (commit + push). Max 3 ordinary repairs. (The v2 Phase Packager is retired in v3 (IDE-22); see the v3 plan.)
- Completion: the v2 completion gate is retired in v3 (IDE-22); see the v3 plan.
- Finished work: run appropriate tests/checks and auto-repair ordinary failures (≤3 cycles).
- Hard stops: no implementer PR, no self-merge, no self-review, no `main` promotion, no prefer-incoming.

### Deeper doctrine

When needed, open files under `.ide-development/` (and local `docs/` / `scripts/` already installed). Prefer progressive disclosure; do not scan the entire package.
<!-- END LINKTREND-IDE-MANAGED -->
