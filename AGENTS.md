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

- Work on `issue/<n>-<slug>` (or rare `dev/*`) → push checkpoint → Phase Packager/Coordinator (`scripts/gitops/packager_coordinator.py`) opens the draft Phase PR → delivery controller (`scripts/gitops/delivery_controller.py`) merges to `development` through GitHub protection. Retained `packager_discover.py` is not the Phase Packager. Review Ready does not itself trigger a merge.
- Promote: `development` → `staging` → `main` via temporary `promote/*` PRs only (controller-owned; main waits for explicit founder approval).

### Agent rules

- Ship = checkpoint (commit + push). Packager opens PRs. Max 3 ordinary repairs.
- Completion: `python3 scripts/gitops/completion_gate.py` (`checkpoint` | `review-ready` | `blocked` | `status` | `write-evidence`).
- Finished work: run appropriate tests/checks, auto-repair ordinary failures (≤3 cycles), `write-evidence`, then `review-ready`.
- `review-ready` validates evidence then publishes **Linktrend Review Ready** only via the privileged normal-token path (or fails closed with normal-token dispatch diagnostics). Do not call `mark-review-ready.sh` as a pre-gate publisher.
- If completion cannot pass, call `completion_gate.py blocked`.
- Hard stops: no implementer PR, no self-merge, no self-review, no staging/main promotion, no prefer-incoming.

### Deeper doctrine

When needed, open files under `.ide-development/` (and local `docs/` / `scripts/` already installed). Prefer progressive disclosure; do not scan the entire package.
<!-- END LINKTREND-IDE-MANAGED -->

## AgentLens codebase navigation

- Before exploring source, read `.agentlens/INDEX.md` and route through the relevant module documentation.
- Before modifying a module, read its `memory.md`; use `outline.md` to locate symbols in large files and `imports.md` to inspect dependencies.
- If the generated documentation is stale, regenerate it from the repository root with `agentlens .`.
