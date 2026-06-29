# Skills Catalog

Use this file to route into local skills.

## Rules

1. Read this catalog first.
2. Open only the skill needed for the task.
3. Prefer the smallest skill that covers the work.
4. If a skill is missing, improve the nearest existing skill before creating a parallel one.

## Overlap Routing

Use these rules when multiple skills appear relevant.

### UI And Frontend

- Use `frontend-ui-engineering` for UI architecture, centralized components, accessibility, layout, responsive behavior, and visual proof.
- Use `tailwind-patterns` only when the main question is Tailwind class structure, tokens, responsive utility usage, or CSS maintainability.
- Use `mobile-design` when the primary concern is touch interaction, mobile navigation, platform behavior, or small-screen ergonomics.
- Use `i18n-localization` when UI work depends on locale files, translated strings, date/number formatting, RTL, or language fallback.

### Web Testing And Browser Proof

- Use `webapp-testing` for user flows, route behavior, form behavior, e2e-style checks, and app functionality in a browser.
- Use `browser-qa` for visual/browser evidence: screenshots, viewport checks, visible defects, rendered-state comparison, and QA notes.
- Use `lint-and-validate` after changes when the task is mainly running or fixing build, lint, typecheck, or focused test commands.

### Test Strategy And QA

- Use `testing-patterns` to decide what type of test to write or how to structure test coverage.
- Use `test-driven-development` when tests should drive a bug fix or behavior change from failing proof to passing proof.
- Use `persistent-qa` for independent verification, regression review, defect retest, and final QA evidence.
- Use `code-review-and-quality` for reviewing a patch or PR for correctness, maintainability, scope, and missing proof.

### Planning And Implementation Flow

- Use `spec-driven-development` when intent is unclear, high-impact, or needs acceptance criteria before planning.
- Use `plan-writing` to turn a known request into an implementation-ready plan.
- Use `task-decomposition` to split complex work into dependency-aware issues.
- Use `incremental-implementation` to execute a larger change in small verified slices.
- Use `app-builder` when scaffolding or extending an application using existing stack conventions.
- Use `intelligent-routing` when the task is to select the right command, skill, artifact path, or agent role.

### Architecture, APIs, Data, And Source Grounding

- Use `architecture` for system boundaries, tradeoffs, integration decisions, and structural design.
- Use `api-patterns` for API contracts, versions, errors, interfaces, and request/response behavior.
- Use `database-design` for schemas, migrations, indexes, data access, and data safety.
- Use `source-driven-development` when implementation must be grounded in authoritative local docs, official docs, specs, or upstream code.
- Use `documentation-and-adrs` when the output is durable documentation or a decision record.

### Operations, Release, And Runtime

- Use `server-management` for running processes, environment variables, logs, health checks, and local/runtime diagnostics.
- Use `ci-cd-and-automation` for pipeline configuration, automated gates, and workflow automation.
- Use `deployment-procedures` for deployment planning, execution, verification, and rollback.
- Use `release-readiness` to decide whether integrated work is shippable or blocked.
- Use `observability-and-instrumentation` for logs, metrics, traces, and diagnostics added to the product.
- Use `performance-optimization` when the main goal is measurement-backed performance improvement.

### Tools, Agents, And Automation

- Use `tool-architect` for small local helper tools, CLIs, and scripts that agents can run safely.
- Use `mcp-builder` for MCP servers or agent-callable tool interfaces.
- Use `parallel-agents` when coordinating independent issue work across multiple agents.
- Use `context-engineering` when the task is to shape minimum useful context for an agent session.

### Repository Safety And Change Management

- Use `git-safeguard` before staging, committing, pushing, publishing, or handling dirty worktrees.
- Use `repository-manager` for workspace hygiene, handoffs, artifact placement, and repo organization.
- Use `deprecation-and-migration` when moving, archiving, retiring, or replacing old systems.
- Use `code-simplification` when reducing complexity while preserving behavior.
- Use `retrospective-learning` after completed work, failed reviews, blockers, or repeated friction.

### Language And Shell Skills

- Use language-specific skills only when the implementation is mainly in that language or runtime:
  - `nodejs-best-practices`
  - `python-patterns`
  - `rust-pro`
- Use shell-specific skills only when writing or reviewing shell commands/scripts:
  - `bash-linux`
  - `powershell-windows`

### LiNKaios Host UI Composites

- Use `data-table`, `action-queue`, and `personal-information-forms` when the UI task directly touches those shared LiNKaios component families.
- Use `frontend-ui-engineering` first for general UI work, then use the relevant host composite skill if the component family applies.

## Available Skills

- `skills/action-queue/SKILL.md` — feed-style attention rows for LiNKaios UI
- `skills/api-patterns/SKILL.md` — API and interface design, contracts, errors, versioning, and boundaries
- `skills/architecture/SKILL.md` — architecture decisions with explicit tradeoffs, constraints, and integration boundaries
- `skills/app-builder/SKILL.md` — scaffold or extend applications using existing stack conventions and verifiable slices
- `skills/bash-linux/SKILL.md` — safe Bash and Unix shell usage for inspection, scripting, and automation
- `skills/browser-qa/SKILL.md` — browser-driven QA, screenshots, and user-visible web defect evidence
- `skills/ci-cd-and-automation/SKILL.md` — CI/CD workflows and automation gates for verified delivery
- `skills/code-review-and-quality/SKILL.md` — review changes for correctness, maintainability, scope compliance, tests, and proof sufficiency
- `skills/code-simplification/SKILL.md` — simplify code or documentation while preserving behavior and compatibility
- `skills/context-engineering/SKILL.md` — shape minimum useful context for grounded, narrow, recoverable agent sessions
- `skills/data-table/SKILL.md` — columnar shell tables for LiNKaios UI
- `skills/database-design/SKILL.md` — schema, migration, index, data access, and database safety guidance
- `skills/deprecation-and-migration/SKILL.md` — migrate, archive, or retire old systems safely while preserving compatibility
- `skills/deployment-procedures/SKILL.md` — plan, execute, verify, and roll back deployments with explicit gates
- `skills/documentation-and-adrs/SKILL.md` — durable documentation and decision records for architecture, APIs, workflows, and operations
- `skills/frontend-ui-engineering/SKILL.md` — production-quality frontend UI using the repo's centralized component system, responsive layout, accessibility, and visual proof
- `skills/git-safeguard/SKILL.md` — repository safety checks before staging, committing, pushing, or publishing
- `skills/i18n-localization/SKILL.md` — internationalization, localization, locale files, formatting, and RTL readiness
- `skills/incremental-implementation/SKILL.md` — implement larger changes in small verified slices
- `skills/intelligent-routing/SKILL.md` — select the smallest appropriate command, skill, artifact path, and agent role
- `skills/lint-and-validate/SKILL.md` — focused lint, build, type, test, and artifact validation after changes
- `skills/mcp-builder/SKILL.md` — MCP servers and tool interfaces as optional adapters
- `skills/mobile-design/SKILL.md` — mobile-first interfaces, touch interactions, navigation, and platform-sensitive behavior
- `skills/nodejs-best-practices/SKILL.md` — practical Node.js, JavaScript, and TypeScript runtime patterns
- `skills/observability-and-instrumentation/SKILL.md` — logs, metrics, traces, and diagnostics for explainable runtime behavior
- `skills/parallel-agents/SKILL.md` — coordinate safe parallel work from dependency-ready issue sets
- `skills/performance-optimization/SKILL.md` — diagnose, measure, and improve performance with evidence
- `skills/persistent-qa/SKILL.md` — independent QA with evidence, defect tracking, and regression concerns
- `skills/personal-information-forms/SKILL.md` — shared form system and personal data entry patterns
- `skills/plan-writing/SKILL.md` — turning a request into an implementation-ready plan
- `skills/powershell-windows/SKILL.md` — safe PowerShell and Windows shell usage for Windows-targeted tasks
- `skills/python-patterns/SKILL.md` — practical Python project, typing, async, testing, and packaging patterns
- `skills/release-readiness/SKILL.md` — assess whether integrated work is shippable or blocked
- `skills/repository-manager/SKILL.md` — repository hygiene, handoffs, artifact placement, and workspace organization
- `skills/retrospective-learning/SKILL.md` — capture lessons from completed work, blockers, failed reviews, and system friction
- `skills/rust-pro/SKILL.md` — practical Rust ownership, error handling, testing, async, and crate organization patterns
- `skills/security-and-hardening/SKILL.md` — security, privacy, authorization, input, dependency, and operational hardening
- `skills/server-management/SKILL.md` — server processes, runtime configuration, health checks, logs, and diagnostics
- `skills/skill-template/SKILL.md` — golden template for IDE Development skills
- `skills/source-driven-development/SKILL.md` — ground implementation decisions in authoritative local or official sources
- `skills/spec-driven-development/SKILL.md` — convert unclear or significant work into a concise specification before planning or coding
- `skills/systematic-debugging/SKILL.md` — reproduce, isolate, root-cause, fix, and verify bugs or failures
- `skills/tailwind-patterns/SKILL.md` — Tailwind CSS patterns with project tokens, responsive constraints, and maintainable classes
- `skills/task-decomposition/SKILL.md` — decompose complex work into atomic, dependency-aware issues
- `skills/test-driven-development/SKILL.md` — use tests as proof for behavior changes and bug fixes
- `skills/testing-patterns/SKILL.md` — choose and structure unit, integration, e2e, and regression tests
- `skills/tool-architect/SKILL.md` — design small CLI-first helper tools or scripts that agents can run safely
- `skills/webapp-testing/SKILL.md` — browser/user-flow testing for web application behavior and frontend proof

## Pending Skill Migration

This catalog lists skills already stabilized or normalized into the shared core.

Repository-specific skills, including any older skills referred to as `g skills`, should be inventoried and evaluated before import. Do not add them directly without checking for overlap with existing skills and deciding whether the right action is import, merge, rewrite, or leave repository-local.

Known source systems for future migration review:

- `LiNKtrend-System/LiNKdev/skills/gstack`
- `LiNKskills/skills`
- `link-antigravity-kit/.codex/skills`
- `addyosmani/agent-skills/skills`
- `anthropics/skills`
- curated awesome lists for discovery only
