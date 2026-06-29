# Skill Migration Pass 1

## Purpose

Record the first skill import and refactor pass after reviewing external and legacy skill sources.

No source repository was imported wholesale. Selected skills were normalized into IDE Development skill format and aligned with the core artifact model.

## Sources Reviewed

- `LiNKtrend-System/LiNKdev/skills`
- `LiNKskills/skills`
- `link-awesome-openclaw-skills`
- `link-antigravity-kit`
- `addyosmani/agent-skills`
- `anthropics/skills`
- `skillmatic-ai/awesome-agent-skills`
- `VoltAgent/awesome-agent-skills`

## Key Finding

The legacy term to track is `gstack`, not `g skills`.

`LiNKtrend-System/LiNKdev/skills/gstack` is a large legacy skill system with browser QA, planning, review, ship, investigation, OpenClaw, host adapter, and script material. It should be mined selectively, not copied wholesale.

## Template Decision

Added `skills/skill-template/SKILL.md` as the IDE Development skill normalization target.

It is adapted from the LiNKskills golden template but aligned to:

- IDE Development artifacts
- proof, review, and integration gates
- progressive disclosure
- issue atomicity
- runtime-independent agent compliance

## Skills Added

- `code-review-and-quality`
- `git-safeguard`
- `incremental-implementation`
- `persistent-qa`
- `repository-manager`
- `skill-template`
- `task-decomposition`
- `test-driven-development`

## Source Adaptation

Adapted concepts from:

- `LiNKskills/skills/git-safeguard`
- `LiNKskills/skills/repository-manager`
- `LiNKskills/skills/persistent-qa`
- `LiNKskills/skills/task-decomposition`
- `LiNKskills/skills/skill-template`
- `addyosmani/agent-skills/skills/incremental-implementation`
- `addyosmani/agent-skills/skills/test-driven-development`
- `addyosmani/agent-skills/skills/code-review-and-quality`
- `link-antigravity-kit/.codex/skills/tdd-workflow`
- `link-antigravity-kit/.codex/skills/code-review-checklist`

## Deferred Candidates

High-value candidates for later passes:

- `systematic-debugging`
- `testing-patterns`
- `lint-and-validate`
- `api-patterns`
- `database-design`
- `architecture`
- `source-driven-development`
- `spec-driven-development`
- `webapp-testing`
- selected `gstack` QA, review, ship, browse, and investigate concepts

## Non-Import Sources

The awesome-list repositories are discovery references only. They do not provide local `SKILL.md` files suitable for direct import.

Anthropic skills should be treated primarily as format and pattern references unless a specific skill fills a direct local gap.
