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
| `SKILLS-SUNSET-REPORT.md` | Layer 1 skills sunset audit |
| `CORE-CURSOR-EQUIVALENCE-REPORT.md` | core/ vs .cursor/ equivalence audit |
| `COPY-FIRST-UI-RESKIN-POLICY.md` | Copy-first UI reskin policy |

Index for the archive folder: [`docs/archive/README.md`](archive/README.md).

The workspace operator guide (`LINKDEVELOPER-WORKSPACE-OPERATOR-GUIDE.md`) remains in active `docs/` as a redirect stub pointing to the Operations Manual.

---

## What archived on GitHub and local disk

| System | GitHub | `isArchived` | Local snapshot |
|---|---|---|---|
| **LiNKdeveloper Stage 2** | [linktrend/LiNKdeveloper](https://github.com/linktrend/LiNKdeveloper) | `true` | `/Users/linktrend/Projects/Archive/LiNKdeveloper-Stage2-Runtime-20260710/` |
| **LiNKdev** | [linktrend/LiNKdev](https://github.com/linktrend/LiNKdev) | `true` | `/Users/linktrend/Projects/Archive/LiNKdev-legacy-20260710/` |

Neither archived repo is installed, extended, or required for Stage 1 operation. See [`docs/ARCHIVE-INDEX.md`](ARCHIVE-INDEX.md) for when Stage 1 may read from archive.

---

## Grep proof — legacy terms in active docs

Command (as specified):

```bash
grep -ri "linkdev\|/Projects/LiNKdeveloper\|/Projects/LiNKdev\|LiNKaios\|LiNKtrend-System" docs/ --include="*.md" \
  | grep -v archive | grep -v adoption-backups | grep -v ARCHIVE-INDEX
```

**Raw match count:** 29 lines.

**Interpretation:** All 29 matches are **LiNKdeveloper false positives** — the pattern `linkdev` matches as a substring inside the canonical product name `LiNKdeveloper`. No active doc references `/Projects/LiNKdeveloper`, `/Projects/LiNKdev`, `LiNKaios`, or `LiNKtrend-System` outside `ARCHIVE-INDEX.md`.

**True legacy term count** (word-boundary `linkdev` plus path/system names, excluding archive and ARCHIVE-INDEX):

```bash
grep -riE "/Projects/LiNKdeveloper|/Projects/LiNKdev|LiNKaios|LiNKtrend-System|\blinkdev\b" docs/ --include="*.md" \
  | grep -v archive | grep -v adoption-backups | grep -v ARCHIVE-INDEX
```

**Result:** 0 matches.

`scripts/verify-stage1.sh` includes an equivalent active-doc LiNKdev check and reports **PASS**.

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

## Stage 2 team — using the archived LiNKdeveloper repo

When Stage 2 work begins, the team should treat [linktrend/LiNKdeveloper](https://github.com/linktrend/LiNKdeveloper) and `/Users/linktrend/Projects/Archive/LiNKdeveloper-Stage2-Runtime-20260710/` as **read-only design reference**, not as a runtime to install or extend. Consult archived docs for autonomous orchestration concepts — lifecycle stage names, governance gates, executor routing, work-packet schema — and implement those ideas inside **IDE Development** with OpenClaw wiring. Do not copy infrastructure, duplicate folder trees, or add archived paths to the LiNKdeveloper workspace. Gate structure, proof/review/integration discipline, and hybrid skills from Stage 1 remain canonical; Stage 2 changes **who executes** between gates, not the gate model itself.

---

## Verification

`./scripts/verify-stage1.sh` — **PASS** (exit 0, all checks passed on 2026-07-10).
