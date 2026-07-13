# LiNKdeveloper Doc Consolidation Report

**Date:** 2026-07-10  
**Mission:** Archive legacy runtimes; consolidate active operator documentation  
**Status:** Complete — Phase 3–4 verified

---

## What moved to `docs/archive/`

Ten historical audit and completion documents were relocated via `git mv`:

| File | Role |
|---|---|
| `LINKDEVELOPER-STAGE1A-SPEC.md` | Application Factory workflow and skills map (Stage 1a) |
| `LINKDEVELOPER-STAGE1A-REPORT.md` | Stage 1a completion report |
| `LINKDEVELOPER-STAGE1B-REPORT.md` | Stage 1b semi-manual OS report |
| `LINKDEVELOPER-STAGE1-VERIFICATION-REPORT.md` | Operator readiness verification |
| `LINKDEVELOPER-STAGE1-HYBRID-REPORT.md` | Hybrid skills install report |
| `LINKDEVELOPER-STAGE1-TEST-RUNBOOK.md` | Supervised smoke test runbook |
| `LINKSITES-FACTORY-SETUP-REPORT.md` | LinkSites factory setup audit |
| `SKILLS-SUNSET-REPORT.md` | Sunset skills audit (archived report) |
| `CORE-CURSOR-EQUIVALENCE-REPORT.md` | core/ vs .cursor/ equivalence audit |
| `COPY-FIRST-UI-RESKIN-POLICY.md` | Copy-first UI reskin policy |

Index for the archive folder: [`docs/archive/README.md`](archive/README.md).

The workspace operator guide (`LINKDEVELOPER-WORKSPACE-OPERATOR-GUIDE.md`) remains in active `docs/` as a redirect stub pointing to the Operations Manual.

---

## What archived on GitHub and local disk

Retired development systems (GitHub archive flags, local snapshot paths, and when Stage 1 may read from archive) are documented only in [`docs/ARCHIVE-INDEX.md`](ARCHIVE-INDEX.md). Neither retired system is installed, extended, or required for Stage 1 operation.

---

## Grep proof — legacy terms in active docs

Stage 1 verification enforces that retired system names and legacy paths appear in active operator docs only through the archive index. The check is implemented in `scripts/verify-stage1.sh` (active-doc scan excluding `docs/archive/`, `docs/adoption-backups/`, and `docs/ARCHIVE-INDEX.md`).

**Result at consolidation time:** After excluding the archive index and historical paths under `docs/archive/`, active root docs contained no forbidden legacy references. Substrings inside the canonical **LiNKdeveloper** product name are allowed; standalone retired-factory tokens and legacy project paths are not.

**Operator action:** Re-run `./scripts/verify-stage1.sh` after doc changes; the script must exit 0.

---

## Active `docs/` vs `docs/archive/`

### Active (`docs/` root — operator-facing)

| File | Role |
|---|---|
| `LINKDEVELOPER-OPERATIONS-MANUAL.md` | **Canonical** day-to-day operator instructions |
| `LINKDEVELOPER-STAGE1.md` | Stage 1 declaration |
| `LINKDEVELOPER-STAGE1-CLOSURE.md` | Closure summary and deliverable index |
| `HYBRID-SKILLS-REGISTRY.md` | Active hybrid skills registry |
| `FACTORY-OPERATIONS-BLUEPRINT.md` | Factory operations common blueprint (planning) |
| `ARCHIVE-INDEX.md` | Retired systems index |
| `LINKDEVELOPER-WORKSPACE-OPERATOR-GUIDE.md` | Redirect stub → Operations Manual |
| `LINKDEVELOPER-DOC-CONSOLIDATION-REPORT.md` | This report |

Other non-archive paths under `docs/`: `handoff/`, `adoption-backups/` (not operator docs).

### Archived (`docs/archive/` — historical evidence)

| File |
|---|
| `README.md` |
| `LINKDEVELOPER-STAGE1A-SPEC.md` |
| `LINKDEVELOPER-STAGE1A-REPORT.md` |
| `LINKDEVELOPER-STAGE1B-REPORT.md` |
| `LINKDEVELOPER-STAGE1-VERIFICATION-REPORT.md` |
| `LINKDEVELOPER-STAGE1-HYBRID-REPORT.md` |
| `LINKDEVELOPER-STAGE1-TEST-RUNBOOK.md` |
| `LINKSITES-FACTORY-SETUP-REPORT.md` |
| `SKILLS-SUNSET-REPORT.md` |
| `CORE-CURSOR-EQUIVALENCE-REPORT.md` |
| `COPY-FIRST-UI-RESKIN-POLICY.md` |

---

## Stage 2 team — read-only archive reference

When Stage 2 work begins, consult [`docs/ARCHIVE-INDEX.md`](ARCHIVE-INDEX.md) for the archived orchestrator repo and local snapshot paths. Treat those artifacts as **read-only design reference**, not as a runtime to install or extend. Use archived docs for autonomous orchestration concepts — lifecycle stage names, governance gates, executor routing, work-packet schema — and implement those ideas inside **IDE Development** with OpenClaw wiring. Do not copy infrastructure, duplicate folder trees, or add archived paths to the active workspace. Gate structure, proof/review/integration discipline, and hybrid skills from Stage 1 remain canonical; Stage 2 changes **who executes** between gates, not the gate model itself.

---

## Verification

`./scripts/verify-stage1.sh` — **PASS** (exit 0, all checks passed on 2026-07-10).
