# Native Codex discovery (IDE Development system source)

Physical `.agents/skills/` entrypoints so Codex can discover GitOps bootstrap skills **without** loading `.cursor`.

## Required physical skills

- `.agents/skills/agentsetup/SKILL.md`
- `.agents/skills/agentcomply/SKILL.md`

## Remaining approved skills

See `skills-manifest.json`. Remaining domain skills stay canonical under `core/skills/` and may be materialized into `.agents/skills/` when needed (manifest-driven). Claude Code surfaces are out of scope.

## Relation to managed-core platforms

Consumer installs receive adapters from `core/managed-core/platforms/codex/` into `.agents/skills/`. This repository keeps a native `.agents/` copy for self-verification as the system source (not a nested `.ide-development/` consumer install).
