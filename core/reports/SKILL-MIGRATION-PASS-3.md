# Skill Migration Pass 3

## Purpose

Record the third skill import and refactor pass.

This pass focused on frontend execution, security, performance, observability, deprecation, browser QA, release readiness, and retrospective learning.

## Skills Added

- `browser-qa`
- `deprecation-and-migration`
- `frontend-ui-engineering`
- `observability-and-instrumentation`
- `performance-optimization`
- `release-readiness`
- `retrospective-learning`
- `security-and-hardening`

## Source Adaptation

Adapted concepts from:

- `addyosmani/agent-skills/skills/frontend-ui-engineering`
- `addyosmani/agent-skills/skills/security-and-hardening`
- `addyosmani/agent-skills/skills/performance-optimization`
- `addyosmani/agent-skills/skills/observability-and-instrumentation`
- `addyosmani/agent-skills/skills/deprecation-and-migration`
- `addyosmani/agent-skills/skills/shipping-and-launch`
- `link-antigravity-kit/.codex/skills/frontend-design`
- `link-antigravity-kit/.codex/skills/vulnerability-scanner`
- `link-antigravity-kit/.codex/skills/performance-profiling`
- `anthropics/skills/skills/frontend-design`
- `LiNKtrend-System/LiNKdev/skills/gstack/qa`
- `LiNKtrend-System/LiNKdev/skills/gstack/qa-only`
- `LiNKtrend-System/LiNKdev/skills/gstack/browse`
- `LiNKtrend-System/LiNKdev/skills/gstack/ship`
- `LiNKtrend-System/LiNKdev/skills/gstack/land-and-deploy`
- `LiNKtrend-System/LiNKdev/skills/gstack/retro`
- `LiNKtrend-System/LiNKdev/skills/gstack/learn`
- `LiNKskills/skills/self-improvement`

## Normalization Rule

The skills were rewritten for IDE Development and avoid host-specific assumptions such as gstack installation, Claude-only paths, mandatory browser tooling, or external control planes.

Each skill keeps the core gates:

- scoped execution
- concrete evidence
- proof before review
- review before integration
- explicit blockers
- progressive disclosure

## Deferred Candidates

Potential later passes:

- `context-engineering`
- `documentation-and-adrs`
- `code-simplification`
- `ci-cd-and-automation`
- selected MCP/tool-builder material
- selected document/spreadsheet/presentation skills only if they add value beyond existing Codex tool skills
