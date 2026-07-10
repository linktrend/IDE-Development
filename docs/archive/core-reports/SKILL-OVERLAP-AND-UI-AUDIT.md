# Skill Overlap And UI Audit

Status: completed
Date: 2026-06-16

## Scope

This audit paused skill import work to check for overlap in the current IDE Development skill catalog and to review `linktrend/LiNKtrend-System` for UI/UX governance patterns that should be carried into the IDE Development system.

Reviewed source:

- `core/skills`
- `core/skills/SKILLS_CATALOG.md`
- `linktrend/LiNKtrend-System/docs/workspace/MVO-UI-POLICY.md`
- `linktrend/LiNKtrend-System/LiNKdev/product/grounding/UI_AUTHORITY.md`
- `linktrend/LiNKtrend-System/LiNKaios/linkaios-web/src/components`

The local `LiNKtrend-System` review clone was fetched and matched `origin/main` at commit `ebfcbde5021f13af6b0d6c3a3f847973659b2df3`.

## Overlap Findings

The current catalog has intentional adjacency but no skill that should be deleted immediately.

Keep as separate skills:

- `frontend-ui-engineering` and `tailwind-patterns`
  - `frontend-ui-engineering` governs UI architecture, accessibility, layout, centralized components, and browser proof.
  - `tailwind-patterns` governs Tailwind class usage, tokens, responsive constraints, and maintainable utility composition.
- `webapp-testing` and `browser-qa`
  - `webapp-testing` is for user-flow and web behavior tests.
  - `browser-qa` is for browser-driven evidence, screenshots, viewport checks, and visible defect confirmation.
- `testing-patterns`, `test-driven-development`, and `persistent-qa`
  - `testing-patterns` chooses test shape.
  - `test-driven-development` uses tests to drive behavior changes.
  - `persistent-qa` acts as independent verification and regression review.
- `release-readiness` and `deployment-procedures`
  - `release-readiness` decides whether integrated work is shippable.
  - `deployment-procedures` plans, executes, verifies, and rolls back deployments.
- `mcp-builder` and `tool-architect`
  - `mcp-builder` is for MCP servers and agent-callable tool interfaces.
  - `tool-architect` is for small local helper tools or CLIs.
- `app-builder`, `task-decomposition`, and `incremental-implementation`
  - `app-builder` scaffolds or extends applications.
  - `task-decomposition` breaks work into dependency-aware issues.
  - `incremental-implementation` executes larger changes in verified slices.
- `server-management`, `deployment-procedures`, and `ci-cd-and-automation`
  - `server-management` handles runtime processes, health checks, logs, and diagnostics.
  - `deployment-procedures` handles deployment execution.
  - `ci-cd-and-automation` handles automated pipelines and gates.

Recommendation: keep all current skills for now. Clarify catalog descriptions if routing friction appears during real use, but do not merge or delete before usage data proves a problem.

## LiNKtrend-System UI Findings

`LiNKtrend-System` has a centralized UI governance model, not just a component library.

Key design controls:

- Surface classification:
  - Class A: LiNKaios operator UI
  - Class B: LinkSites customer/template UI
  - Class C: upstream/kitchen product UI
- Authority stack for Class A:
  - UI system documentation
  - Cursor UI standards rule
  - `ui-standards.ts` behavior tokens
  - host skills for composite families
- Centralized primitives and composites:
  - shadcn/ui primitives under `@/components/ui/*`
  - shell components such as `ShellMainFrame`, breadcrumbs, and `ShellPageHeader`
  - data tables, action queues, summary metric cards, forms, status pills, and shared formatting helpers
- Agent rules:
  - do not hand-roll parallel buttons, tables, breadcrumbs, page titles, or status indicators
  - put reusable UI changes in the central component layer
  - do not apply operator shell patterns to customer marketing/template sites
  - do not rebuild upstream product UIs inside the operator app when the correct behavior is traceability or deep linking

## Action Taken

Updated `core/skills/frontend-ui-engineering/SKILL.md` with a new `Centralized UI System Rule`.

The skill now requires agents to:

- classify the UI surface before implementation
- read UI authority/design-system docs first when they exist
- use centralized shadcn/ui primitives, lucide icon patterns, shell components, tokens, and composites
- place reusable changes in the central component layer
- avoid one-off duplicate UI systems
- include proof of the centralized components or tokens used or changed

Updated `core/skills/SKILLS_CATALOG.md` with protective overlap routing.

The catalog now distinguishes:

- primary UI work from Tailwind implementation details
- web behavior testing from screenshot/browser evidence
- test strategy, TDD execution, independent QA, and code review
- spec, planning, decomposition, incremental implementation, and app scaffolding
- release readiness, deployment execution, CI/CD automation, runtime management, and observability
- local helper tools from MCP tool interfaces
- repository safety, migration, simplification, and retrospective work

## Remaining Work

No additional skill import should happen until the next review pass decides whether the current 48-skill catalog is too broad for routing. The next practical cleanup, if needed, is catalog wording rather than deleting skills.
