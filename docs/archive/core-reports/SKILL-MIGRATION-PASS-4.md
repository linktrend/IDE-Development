# Skill Migration Pass 4

## Purpose

Record the fourth skill import and refactor pass.

This pass focused on context quality, documentation, simplification, CI/CD, MCP/tool design, and practical Python/Node.js runtime guidance.

## Skills Added

- `ci-cd-and-automation`
- `code-simplification`
- `context-engineering`
- `documentation-and-adrs`
- `mcp-builder`
- `nodejs-best-practices`
- `python-patterns`
- `tool-architect`

## Source Adaptation

Adapted concepts from:

- `addyosmani/agent-skills/skills/context-engineering`
- `addyosmani/agent-skills/skills/documentation-and-adrs`
- `addyosmani/agent-skills/skills/code-simplification`
- `addyosmani/agent-skills/skills/ci-cd-and-automation`
- `link-antigravity-kit/.codex/skills/documentation-templates`
- `link-antigravity-kit/.codex/skills/clean-code`
- `link-antigravity-kit/.codex/skills/mcp-builder`
- `link-antigravity-kit/.codex/skills/python-patterns`
- `link-antigravity-kit/.codex/skills/nodejs-best-practices`
- `anthropics/skills/skills/mcp-builder`
- `LiNKskills/skills/tool-architect`

## Normalization Rule

Skills were rewritten for IDE Development and avoid assuming:

- a specific IDE runtime
- mandatory MCP availability
- mandatory external tool registries
- mandatory package manager or framework

Each skill preserves:

- progressive disclosure
- repository-local patterns first
- explicit proof
- explicit blockers
- compatibility preservation

## Deferred Candidates

Potential later passes:

- document/file skills only where they add to the local document workflow
- `mobile-design`
- `i18n-localization`
- `seo-fundamentals` / `geo-fundamentals`
- selected `gstack` planning and review workflows if they add distinct value
