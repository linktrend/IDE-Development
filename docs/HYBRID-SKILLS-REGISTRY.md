# Hybrid Skills Registry

**Date:** 2026-07-10  
**Status:** Installed and wired — local clones present  
**Owner:** IDE Development

This registry is the authoritative map for gstack macro-orchestration and mattpocock micro-execution skills integrated into **IDE Development**. Historical layered model detail: [`docs/archive/LINKDEVELOPER-STAGE1A-SPEC.md`](archive/LINKDEVELOPER-STAGE1A-SPEC.md) Section C.

---

## Fork URLs

- **gstack (macro):** https://github.com/linktrend/gstack — upstream `garrytan/gstack`
- **mattpocock (micro):** https://github.com/linktrend/skills — upstream `mattpocock/skills`

Both forks were created 2026-07-10 under the `linktrend` account. LiNKtrend owns the fork; upstream updates are pulled deliberately, not automatically.

---

## Vendored skill paths (authoritative at runtime)

Physical copies live in-repo (not sibling-path dependencies, not cross-repo symlinks):

- **gstack:** `.cursor/runtime/skills/gstack/`
- **mattpocock:** `.cursor/runtime/skills/mattpocock/`

Manifest: `core/runtime/skills/VENDOR-MANIFEST.json`. Refresh with `scripts/vendor-hybrid-skills.sh`; verify with `scripts/verify-vendored-skills.sh`.

IDE Development command entrypoints under `core/commands/hybrid-*.md` point agents at these vendored paths.

For retired skill systems and historical provenance, see [`docs/ARCHIVE-INDEX.md`](ARCHIVE-INDEX.md).

---

## gstack commands

Representative macro-orchestration slash commands. Invoke via `core/commands/hybrid-*.md` or read the skill file directly.

- **`/spec`** — Turn vague intent into a structured specification. Primary path for **Trigger 1 (New idea)** after the interview phase and before Carlos approves the spec/PRD.
- **`/plan-ceo-review`** — CEO-level product and architecture review of a plan or spec. Use when a significant program or module plan needs executive-style scrutiny before decomposition.
- **`/health`** — Project health checks and repair loops. Use under **Trigger 3 (Existing software)** during assess/plan when the codebase shows drift, failing gates, or unclear readiness.
- **`/ship`** — Release and shipping workflow. Decides shippable vs blocked; **subordinate to IDE Development integration and release gates** — gstack does not bypass proof, review, or integration in IDE Development.
- **`/context-save`** and **`/context-restore`** — Session context persistence and handoff across long runs. Pair with `context-engineering` (IDE Development read-order) — gstack persists session state; IDE Development shapes what to read.

Additional gstack skills (`/review`, `/qa`, `/retro`, `/learn`) exist in the fork for extended orchestration; route via `intelligent-routing` when macro QA or retro is needed after module completion.

Skill paths (examples):

- `.cursor/runtime/skills/gstack/spec/SKILL.md`
- `.cursor/runtime/skills/gstack/plan-ceo-review/SKILL.md`
- `.cursor/runtime/skills/gstack/health/SKILL.md`
- `.cursor/runtime/skills/gstack/ship/SKILL.md`
- `.cursor/runtime/skills/gstack/context-save/SKILL.md`
- `.cursor/runtime/skills/gstack/context-restore/SKILL.md`

---

## mattpocock commands

Micro-execution skills for clarification, PRD synthesis, issue slicing, TDD, debugging, and architecture improvement.

- **`/grill-with-docs`** — Relentless interview against documentation; clarifies gaps. Primary path for **Trigger 2 (PRD in hand)** step 1 (clarify gaps).
- **`/to-prd`** — Implemented as **`to-spec`** in the fork. Synthesizes conversation or clarified intent into a PRD/spec and publishes to the issue tracker.
- **`/to-issues`** — Implemented as **`to-tickets`** in the fork. Slices work into atomic issues with dependencies.
- **`/tdd`** — Test-driven implementation loop (failing test → fix → pass → regression proof).
- **`/diagnosing-bugs`** — Systematic debugging for blocked or failing issues.
- **`/improve-codebase-architecture`** — Architecture refactor guidance during **Trigger 3** plan or large refactor work.

Skill paths:

- `.cursor/runtime/skills/mattpocock/grill-with-docs/SKILL.md`
- `.cursor/runtime/skills/mattpocock/to-spec/SKILL.md` (command label: `/to-prd`)
- `.cursor/runtime/skills/mattpocock/to-tickets/SKILL.md` (command label: `/to-issues`)
- `.cursor/runtime/skills/mattpocock/tdd/SKILL.md`
- `.cursor/runtime/skills/mattpocock/diagnosing-bugs/SKILL.md`
- `.cursor/runtime/skills/mattpocock/improve-codebase-architecture/SKILL.md`

One-time setup skill (vendored): `.cursor/runtime/skills/mattpocock/setup-matt-pocock-skills/SKILL.md`

---

## Trigger routing (prose)

Carlos operates with three triggers only. Agents map hybrid skills inside each trigger; Carlos does not pick skill names.

**Trigger 1 — New idea:** Interview with Carlos → gstack `/spec` (and optionally `/plan-ceo-review` for large bets) → mattpocock `/grill-with-docs` if docs need sharpening → `/to-prd` when ready to formalize → Carlos approves spec/PRD → route app vs factory → IDE Development commands (`plan-program`, `plan-module`, …) for decomposition and execution.

**Trigger 2 — PRD in hand:** mattpocock `/grill-with-docs` to clarify gaps → Carlos approves clarified PRD → `/to-issues` for issue graph → IDE Development execution (`execute-issue`, proof, review, integration). Use `/tdd` and `/diagnosing-bugs` during issue execution as needed.

**Trigger 3 — Existing software:** Assess codebase → gstack `/health` when health is uncertain → plan (IDE Development `plan-module` or `/improve-codebase-architecture` for structural work) → Carlos approves if high-impact → develop with `/tdd`, domain skills, and IDE Development gates. Use gstack `/ship` only after IDE Development integration passes; it does not replace review or integration.

**Session continuity:** Long runs may use gstack `/context-save` and `/context-restore` plus IDE Development `context-engineering` for read order.

**Internal artifact commands** (`plan-program`, `execute-issue`, `review-issue`, `integrate-issue`, …) apply when work is decomposed into the canonical artifact graph — not as Carlos's primary UI.

---

## Sunset skills (removed from IDE Development)

These eight local skills were removed — hybrid replaces them with no wrappers:

- `release-readiness` → gstack `/ship`
- `browser-qa` → gstack `/health` and QA flows; fallback `webapp-testing`
- `retrospective-learning` → gstack `/retro` and `/learn`
- `spec-driven-development` → gstack `/spec` + mattpocock `/grill-with-docs`
- `plan-writing` → mattpocock `/to-prd` + gstack `/spec`
- `task-decomposition` → mattpocock `/to-issues`
- `test-driven-development` → mattpocock `/tdd`
- `systematic-debugging` → mattpocock `/diagnosing-bugs`

Details: [`docs/archive/SKILLS-SUNSET-REPORT.md`](archive/SKILLS-SUNSET-REPORT.md)

---

## Verification

Trigger 2 hybrid smoke test completed 2026-07-10. Artifacts (archived): `docs/archive/pilots/hybrid-smoke/`. Outcome: [`docs/archive/LINKDEVELOPER-STAGE1-HYBRID-REPORT.md`](archive/LINKDEVELOPER-STAGE1-HYBRID-REPORT.md).

Automated re-check: `scripts/verify-ide-development.sh`

---

## Related documents

- [`docs/IDE-DEVELOPMENT-INTENT.md`](IDE-DEVELOPMENT-INTENT.md) — why this repository exists
- [`docs/IDE-DEVELOPMENT-TECHNICAL-PRD.md`](IDE-DEVELOPMENT-TECHNICAL-PRD.md) — exhaustive technical reference (§5 covers hybrid skills)
- [`docs/IDE-DEVELOPMENT-OPERATIONS-MANUAL.md`](IDE-DEVELOPMENT-OPERATIONS-MANUAL.md) — day-to-day operator instructions
- [`docs/OPEN-ISSUES.md`](OPEN-ISSUES.md) — build log / deferred items
- [`docs/ARCHIVE-INDEX.md`](ARCHIVE-INDEX.md) — retired systems and historical reference
- `core/skills/SKILLS_CATALOG.md` — agent routing catalog
- `core/skills/intelligent-routing/SKILL.md` — hybrid routing hub
