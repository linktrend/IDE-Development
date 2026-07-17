# LiNKdeveloper Stage 1 — Hybrid Skills Report

**Date:** 2026-07-10  
**Mission:** Install hybrid gstack + mattpocock skills; sunset superseded Layer 1 duplicates  
**Verdict:** **READY FOR USE** (hybrid wiring complete)

---

## Fork URLs

| Repo | URL | Local clone |
|---|---|---|
| gstack (Layer 2 macro) | https://github.com/linktrend/gstack | `/Users/linktrend/Projects/gstack` |
| mattpocock/skills (Layer 3 micro) | https://github.com/linktrend/skills | `/Users/linktrend/Projects/skills` |

---

## Deleted skills (8 — no wrappers)

1. `release-readiness` → gstack `/ship`
2. `browser-qa` → gstack `/health` + QA flows; fallback `webapp-testing`
3. `retrospective-learning` → gstack `/retro`, `/learn`
4. `spec-driven-development` → gstack `/spec` + mattpocock `/grill-with-docs`
5. `plan-writing` → mattpocock `/to-prd` + gstack `/spec`
6. `task-decomposition` → mattpocock `/to-issues`
7. `test-driven-development` → mattpocock `/tdd`
8. `systematic-debugging` → mattpocock `/diagnosing-bugs`

---

## Kept skills (40)

37 domain/governance skills + 3 parent-approved ambiguous keeps:

- **Kept ambiguous:** `app-builder` (starter kit routing), `persistent-qa` (Layer 1 criterion QA), `context-engineering` (read order; pairs with gstack context-save/restore)
- **Optional host UI composites:** `data-table`, `action-queue`, `personal-information-forms`

Full list: `core/skills/SKILLS_CATALOG.md`

---

## Wiring completed

| Item | Path |
|---|---|
| Hybrid registry | `docs/HYBRID-SKILLS-REGISTRY.md` |
| Skills catalog rewrite | `core/skills/SKILLS_CATALOG.md` |
| Routing hub | `core/skills/intelligent-routing/SKILL.md` |
| Hybrid commands (12) | `core/commands/hybrid-*.md` |
| Command index | `core/commands/INDEX.yaml` |
| Repair routing reference | `core/contracts/VALIDATION-CONTRACT.md` |
| Operator guide | `docs/LINKDEVELOPER-WORKSPACE-OPERATOR-GUIDE.md` |
| Sunset audit | `docs/SKILLS-SUNSET-REPORT.md` |

No LiNKdev dependency. LiNKdev-internal gstack not restored.

---

## Trigger 2 smoke test

| Step | Result |
|---|---|
| PRD | `core/pilots/hybrid-smoke/PRD.md` |
| mattpocock path | grill → approve → to-issues (simulated) |
| Issue | HYBRID-SMOKE-001 — operator guide Key docs + Section 7 |
| Proof / review / integration | `core/pilots/hybrid-smoke/{proof,review,integration}/` |
| Outcome | **pass** — gate discipline maintained |

---

## Verification script

`scripts/verify-stage1.sh` extended with hybrid checks. Run after structural changes.

---

## Verdict

**READY FOR USE** — Hybrid skills installed, sunset complete, three-trigger routing wired, operator guide updated, smoke test passed.
