# Skills Sunset Report — Hybrid Migration Audit

**Status:** Audit only — no skills deleted, no commits made  
**Date:** 2026-07-10  
**Auditor:** Subagent B (LiNKdeveloper hybrid skills mission)  
**Scope:** All 48 skills in `core/skills/`  
**Policy:** Q2 — **hybrid only, no wrappers** (Layer 2 `garrytan/gstack` + Layer 3 `mattpocock/skills`; delete superseded Layer 1 duplicates)

---

## Executive Summary

| Category | Count |
|---|---|
| Skills inventoried | **48** |
| **Delete** (superseded by hybrid) | **8** |
| **Keep** (distinct domain / Layer 1 authority) | **37** |
| **Ambiguous** (parent decision) | **3** |

After approved deletion, the catalog would shrink from 48 → **40** skills. Eight skills are direct duplicates of hybrid commands and must go under Q2. The remaining 37 are domain-specific, Layer-1-governance, or host-UI adjunct skills with no clean hybrid replacement. Three skills sit in a gray zone where hybrid overlap is partial but not total.

**Critical dependency:** Hybrid Layer 2/3 is **not yet installed** (`docs/LINKDEVELOPER-WORKSPACE-OPERATOR-GUIDE.md` §7). Deletion should follow hybrid vendoring and catalog routing updates, not precede them.

---

## Inventory — All 48 Skill Directories

Alphabetical list of `core/skills/*/SKILL.md`:

| # | Skill directory | Sunset verdict |
|---|---|---|
| 1 | `action-queue` | Keep (optional host UI) |
| 2 | `api-patterns` | Keep |
| 3 | `app-builder` | Ambiguous |
| 4 | `architecture` | Keep |
| 5 | `bash-linux` | Keep |
| 6 | `browser-qa` | **Delete** |
| 7 | `ci-cd-and-automation` | Keep |
| 8 | `code-review-and-quality` | Keep |
| 9 | `code-simplification` | Keep |
| 10 | `context-engineering` | Ambiguous |
| 11 | `data-table` | Keep (optional host UI) |
| 12 | `database-design` | Keep |
| 13 | `deprecation-and-migration` | Keep |
| 14 | `deployment-procedures` | Keep |
| 15 | `documentation-and-adrs` | Keep |
| 16 | `frontend-ui-engineering` | Keep |
| 17 | `git-safeguard` | Keep |
| 18 | `i18n-localization` | Keep |
| 19 | `incremental-implementation` | Keep |
| 20 | `intelligent-routing` | Keep |
| 21 | `lint-and-validate` | Keep |
| 22 | `mcp-builder` | Keep |
| 23 | `mobile-design` | Keep |
| 24 | `nodejs-best-practices` | Keep |
| 25 | `observability-and-instrumentation` | Keep |
| 26 | `parallel-agents` | Keep |
| 27 | `performance-optimization` | Keep |
| 28 | `persistent-qa` | Ambiguous |
| 29 | `personal-information-forms` | Keep (optional host UI) |
| 30 | `plan-writing` | **Delete** |
| 31 | `powershell-windows` | Keep |
| 32 | `python-patterns` | Keep |
| 33 | `release-readiness` | **Delete** |
| 34 | `repository-manager` | Keep |
| 35 | `retrospective-learning` | **Delete** |
| 36 | `rust-pro` | Keep |
| 37 | `security-and-hardening` | Keep |
| 38 | `server-management` | Keep |
| 39 | `skill-template` | Keep |
| 40 | `source-driven-development` | Keep |
| 41 | `spec-driven-development` | **Delete** |
| 42 | `systematic-debugging` | **Delete** |
| 43 | `tailwind-patterns` | Keep |
| 44 | `task-decomposition` | **Delete** |
| 45 | `test-driven-development` | **Delete** |
| 46 | `testing-patterns` | Keep |
| 47 | `tool-architect` | Keep |
| 48 | `webapp-testing` | Keep |

Source of truth: `core/skills/SKILLS_CATALOG.md` (48 entries) + filesystem glob (48 `SKILL.md` files). Counts match.

---

## Hybrid Reference Map (Deletion Rationale Baseline)

From `docs/LINKDEVELOPER-STAGE1A-SPEC.md` §C and `docs/LINKDEVELOPER-WORKSPACE-OPERATOR-GUIDE.md` §7:

| Layer | Source | Commands / skills |
|---|---|---|
| **Layer 2** | `garrytan/gstack` | `/spec`, `/plan-ceo-review`, `/health`, `/ship`, `/context-save`, `/context-restore` |
| **Layer 3** | `mattpocock/skills` | `/grill-with-docs`, `/to-prd`, `/to-issues`, `/tdd`, `/diagnosing-bugs`, `/improve-codebase-architecture` |

**Naming collision (resolved in provenance, not in sunset):** Three delete-candidates cite `LiNKdev-internal-gstack` provenance — an abandoned internal folder, **not** `garrytan/gstack`. Under Q2, the external Layer 2 commands supersede the mined Layer 1 copies regardless of provenance label.

### gstack ship / qa / retro overlap (LiNKdev-internal-gstack → garrytan/gstack)

| Legacy LiNKdev-internal source | Current Layer 1 skill | garrytan/gstack replacement | Overlap assessment |
|---|---|---|---|
| `gstack/ship`, `gstack/land-and-deploy` | `release-readiness` | `/ship` | **Full** — readiness checklist, risk/rollback assessment, ship verdict |
| `gstack/qa`, `gstack/qa-only`, `gstack/browse` | `browser-qa` | `/health` (health checks) + QA persona tooling in gstack release-manager/QA role | **Full** — browser-driven evidence, screenshot proof, visible defect confirmation |
| `gstack/retro`, `gstack/learn` | `retrospective-learning` | Post-ship retro flows in gstack macro-orchestration | **Full** — lessons learned, system-improvement follow-ups after completed work |

### mattpocock planning / execution overlap

| Current Layer 1 skill | mattpocock replacement | Overlap assessment |
|---|---|---|
| `spec-driven-development` | `/grill-with-docs` + gstack `/spec` | **Full** — intent clarification, acceptance criteria, spec before code |
| `plan-writing` | `/to-prd` + gstack `/spec` | **Full** — structured plan with scope, assumptions, verification |
| `task-decomposition` | `/to-issues` (+ `/to-prd`) | **Full** — atomic issues, dependency graph, acceptance criteria per issue; maps to Canonical Law 6 artifact model |
| `test-driven-development` | `/tdd` | **Full** — failing test → fix → pass → regression proof loop |
| `systematic-debugging` | `/diagnosing-bugs` | **Full** — reproduce → isolate → root cause → fix → verify |

---

## Delete List (8 skills)

| Skill | Hybrid replacement(s) | Rationale |
|---|---|---|
| **`release-readiness`** | gstack `/ship` | Decides shippable vs blocked; checklist mirrors ship gate. `deployment-procedures` remains for execution/rollback — distinct concern. |
| **`browser-qa`** | gstack QA/release-manager flows (`/health`, browse/qa tooling) | Browser evidence and screenshot QA superseded by gstack macro QA. `webapp-testing` covers remaining user-flow browser checks at Layer 1 if needed. |
| **`retrospective-learning`** | gstack retro/learn flows | Post-completion lesson capture and system-improvement routing owned by Layer 2. |
| **`spec-driven-development`** | gstack `/spec` + mattpocock `/grill-with-docs` | Intent → spec → acceptance criteria before planning. Layer 1 artifact mapping (`INTENT.md`, etc.) moves to hybrid routing docs, not a parallel skill. |
| **`plan-writing`** | mattpocock `/to-prd` + gstack `/spec` | Implementation-ready plan output duplicated by PRD generation path. |
| **`task-decomposition`** | mattpocock `/to-issues` | Issue slicing with dependencies directly overlaps; skill even references `ISSUE.md` templates that hybrid path will own. |
| **`test-driven-development`** | mattpocock `/tdd` | Red-green-refactor proof loop is Layer 3 micro-execution. |
| **`systematic-debugging`** | mattpocock `/diagnosing-bugs` | Five-phase debug workflow is Layer 3 blocked-issue execution. |

### Post-delete catalog actions (not executed in this audit)

1. Remove all eight entries from `core/skills/SKILLS_CATALOG.md` overlap-routing sections.
2. Update `docs/LINKDEVELOPER-WORKSPACE-OPERATOR-GUIDE.md` §7 examples (currently cites `browser-qa`, `release-readiness`).
3. Reconcile `core/reports/SKILL-OVERLAP-AND-UI-AUDIT.md` (2026-06-16 "keep all" recommendation is superseded by Q2 hybrid policy).
4. Wire `intelligent-routing` and command INDEX to point at hybrid commands for the deleted concern areas.
5. Confirm `.cursor/skills/` symlinks or copies reflect `core/skills/` after deletion.

---

## Keep List (37 skills)

Grouped by rationale. None have a **full** hybrid duplicate under Q2.

### Domain — APIs, data, security, architecture

| Skill | Rationale |
|---|---|
| `api-patterns` | API contracts, versioning, errors — no hybrid equivalent |
| `architecture` | Structural tradeoff decisions; distinct from mattpocock `/improve-codebase-architecture` (refactor execution) |
| `database-design` | Schema, migrations, indexes, data safety |
| `security-and-hardening` | Auth, input validation, dependency risk — cross-cutting domain |
| `documentation-and-adrs` | Durable docs and decision records; hybrid does not own ADR output shape |
| `source-driven-development` | Ground implementation in authoritative sources; adjacent to `/grill-with-docs` but execution-grounding, not intent interview |

### Frontend and UI (general)

| Skill | Rationale |
|---|---|
| `frontend-ui-engineering` | Centralized component system, accessibility, layout, visual proof — core domain skill |
| `tailwind-patterns` | Utility/token composition; sub-skill of frontend per catalog routing |
| `mobile-design` | Touch, mobile navigation, small-screen ergonomics |
| `i18n-localization` | Locale files, RTL, formatting — no hybrid equivalent |

### Application scaffolding and execution slices

| Skill | Rationale |
|---|---|
| `incremental-implementation` | Verified vertical slices during execution; not planning or TDD — complements `/tdd`, does not duplicate |
| `code-simplification` | Complexity reduction while preserving behavior |

### Testing, QA, and review (remaining after deletes)

| Skill | Rationale |
|---|---|
| `testing-patterns` | Chooses test *type* and coverage shape; strategy layer above `/tdd` |
| `webapp-testing` | User-flow browser behavior checks; absorbs some `browser-qa` routing after delete |
| `lint-and-validate` | Build/lint/typecheck command execution — Layer 4 validation gateway adjunct |
| `code-review-and-quality` | Layer 1 patch/PR review (Law 12); distinct from gstack `/plan-ceo-review` (plan-level CEO review) |

### Operations, release execution, runtime

| Skill | Rationale |
|---|---|
| `deployment-procedures` | Deploy execute/verify/rollback — execution skill; `/ship` decides, this executes |
| `ci-cd-and-automation` | Pipeline configuration and automated gates |
| `server-management` | Processes, env, logs, health — runtime ops |
| `observability-and-instrumentation` | Logs, metrics, traces in product code |
| `performance-optimization` | Measurement-backed perf improvement |

### Language and shell

| Skill | Rationale |
|---|---|
| `nodejs-best-practices` | Node/TS runtime patterns |
| `python-patterns` | Python project patterns |
| `rust-pro` | Rust ownership, async, crates |
| `bash-linux` | Unix shell scripting |
| `powershell-windows` | Windows PowerShell |

### Tools, agents, governance, meta

| Skill | Rationale |
|---|---|
| `tool-architect` | Small local CLIs/helpers — distinct from `mcp-builder` |
| `mcp-builder` | MCP servers and agent-callable interfaces |
| `parallel-agents` | Multi-agent coordination from dependency-ready issue sets |
| `intelligent-routing` | Layer 1 command/skill/artifact router — becomes hybrid routing hub after wiring |
| `context-engineering` | Progressive disclosure and session context shaping (Law 19) |
| `git-safeguard` | Pre-commit/push safety |
| `repository-manager` | Workspace hygiene, handoffs, artifact placement |
| `deprecation-and-migration` | Safe retirement of old systems — meta skill for this sunset work |
| `skill-template` | Golden template for creating/refactoring core skills |

### LiNKaios host UI composites (optional — host repos only)

Per mission brief: **keep only if documented as optional for host UI work**. These three skills apply to **Class A LiNKaios operator UI** per `core/reports/SKILL-OVERLAP-AND-UI-AUDIT.md`; they should not be required in non-host repos (e.g. LinkSites customer UI).

| Skill | Rationale |
|---|---|
| `data-table` | Columnar shell tables — optional when building LiNKaios catalog/index/log surfaces |
| `action-queue` | Feed-style attention rows — optional for inbox/alert surfaces |
| `personal-information-forms` | Shared PII form patterns — optional for identity/contact forms in host UI |

**Recommendation:** Keep all three as **optional Layer 1 adjuncts** with catalog note: *"Use only when the host repo implements LiNKaios Class A UI."*

---

## Ambiguous List (3 skills — parent decision required)

| Skill | Overlap | Options | Subagent B recommendation |
|---|---|---|---|
| **`app-builder`** | Partial overlap with gstack `/spec` + mattpocock `/tdd` + `/to-issues` for full-stack scaffolding; mission brief mentions **"app-builder → starter kit"** | **A)** Keep as domain scaffold skill **B)** Rename/merge into a "starter kit" skill **C)** Delete and route all scaffolding to hybrid | **A or B** — `app-builder` coordinates multi-layer scaffold (frontend + API + data + tests) using repo templates; hybrid commands decompose and implement but do not encode LiNKtrend stack conventions. If a formal starter-kit skill is planned, rename in same pass as sunset. |
| **`persistent-qa`** | Partial overlap with gstack QA persona and `/health`; also overlaps post-delete routing with `webapp-testing` | **A)** Keep as Layer 1 independent QA evidence mapper **B)** Delete — all QA via gstack **C)** Merge into `webapp-testing` | **A** — `persistent-qa` maps acceptance criteria → evidence across test/browser/log proof types; gstack QA is macro-orchestration. Layer 1 still needs criterion-level verification independent of Layer 2 ship authority. |
| **`context-engineering`** | Partial overlap with gstack `/context-save` and `/context-restore` | **A)** Keep as Layer 1 progressive-disclosure skill **B)** Slim to bridge doc only **C)** Delete after context-save wired | **A** — shapes *what to read* (Law 19); gstack context-save persists *session state*. Different concerns; Stage 1A spec proposes bridge, not replacement. |

### Resolved as keep (not elevated to ambiguous)

These were considered but judged **keep** with documented distinction:

| Skill | Why not ambiguous |
|---|---|
| `architecture` vs `/improve-codebase-architecture` | Decision/tradeoff skill vs refactor execution command |
| `code-review-and-quality` vs `/plan-ceo-review` | Issue/PR review vs program-level plan review |
| `webapp-testing` vs deleted `browser-qa` | Becomes sole Layer 1 browser-flow skill; gstack QA is orchestration layer |
| `testing-patterns` vs `/tdd` | Strategy vs execution loop |
| `incremental-implementation` vs `/tdd` | Slice sizing vs test-driven proof |
| `source-driven-development` vs `/grill-with-docs` | Implementation grounding vs intent clarification interview |
| LiNKaios composites | Clearly optional host-only; no hybrid equivalent |

---

## Catalog Routing Updates (preview — for delete pass)

When the eight deletes execute, `SKILLS_CATALOG.md` overlap sections should read approximately:

| Former routing | New routing |
|---|---|
| `browser-qa` for visual evidence | gstack QA flows; fallback `webapp-testing` for user-flow proof |
| `release-readiness` for ship decision | gstack `/ship` (subordinate to Layer 1 integration gates) |
| `retrospective-learning` after modules | gstack retro flows |
| `spec-driven-development` for unclear intent | gstack `/spec` → mattpocock `/grill-with-docs` |
| `plan-writing` for plans | mattpocock `/to-prd` |
| `task-decomposition` for issue slicing | mattpocock `/to-issues` |
| `test-driven-development` for behavior proof | mattpocock `/tdd` |
| `systematic-debugging` for failures | mattpocock `/diagnosing-bugs` |

---

## Risk Notes

1. **Deletion before install** — Removing the eight skills before hybrid vendoring leaves a routing gap. Install/reference hybrid first, update catalog routing, then delete.
2. **Layer 1 authority preserved** — Hybrid may plan, review, and ship but **may not declare complete** (manual §10.5.4). Skills like `code-review-and-quality`, `git-safeguard`, and `intelligent-routing` remain essential Layer 1 governance.
3. **Host repo variance** — LiNKaios UI composites should stay optional; LinkSites and other suites should not inherit them via blanket catalog routing.
4. **Prior audit superseded** — `core/reports/SKILL-OVERLAP-AND-UI-AUDIT.md` recommended keeping all 48 skills; Q2 hybrid-only policy overrides that recommendation for the eight listed deletes.

---

## Parent Decisions Requested

1. **`app-builder`** — Keep, or rename/merge to "starter kit" in the same sunset pass?
2. **`persistent-qa`** — Keep as Layer 1 criterion-level QA, or fold entirely into gstack QA?
3. **`context-engineering`** — Keep as Layer 1 read-order skill, or reduce to a gstack context-save bridge note only?
4. **LiNKaios UI composites** — Confirm optional-host-only catalog labeling (recommended: yes)?
5. **Delete timing** — Approve delete pass only after hybrid install/reference is complete?

---

## Appendix — Skill Count Reconciliation

```
48 total
 − 8 delete (hybrid superseded)
 − 0 delete (ambiguous — pending parent)
= 40 projected remaining (37 keep + 3 ambiguous if all kept)
```

If parent chooses to delete all three ambiguous skills: **37 remaining**.
