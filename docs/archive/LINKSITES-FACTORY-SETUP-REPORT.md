# LiNKsites Factory Setup Report

**Date:** 2026-07-10  
**Mission:** Post–Stage 1b workspace setup (Phases 1–4)  
**Principal:** Carlos | **Reviewer:** Lisa

---

## Summary

Phases 1–4 of the post–Stage 1b setup mission are complete. Phase 5 (Website Factory workflow spec) was **not** written under the prior agent prompt — the correct approach is the **Factory Operations Common Blueprint** (`docs/FACTORY-OPERATIONS-BLUEPRINT.md`), locked in Carlos/Lisa alignment session. Website variant detail is the next deliverable.

---

## Commits

| Hash | Message |
|---|---|
| `505e832` | Stage 1a/1b docs (prior session) |
| `af9174b` | Stage 1b bootstrap rename + gstack provenance relabels |

---

## Phase 1 — Stage 1b code commit

**Status:** Done (`af9174b`)

- Renamed `00-linkdev-bootstrap.mdc` → `00-bootstrap.mdc`
- Updated `.cursor/README.md`, `.cursor/INDEX.yaml`
- Relabeled three skills to `LiNKdev-internal-gstack` provenance

---

## Phase 2 — LiNKdeveloper workspace

**Status:** Done (updated 2026-07-10)

**Path:** `/Users/linktrend/Projects/Workspaces/LiNKdeveloper.code-workspace`

| Folder | Purpose |
|---|---|
| IDE Development | LiNKdeveloper Stage 1 |
| LiNKsites | Website Factory product |

**Removed:** LiNKtrend-System (LiNKaios deferred — was wrongly added by prior agent).

**Action for Carlos:** Reload workspace in Cursor.

---

## Phase 3 — LiNKsites `.cursor` adoption

**Status:** Stopped — selective merge required (correct decision)

| Item | Result |
|---|---|
| Backup | `docs/adoption-backups/LiNKsites/.cursor-backup-20260710/` (21 files) |
| Symlink | **Not applied** |
| Reason | Mixed directory: repo-specific rules (`10-foundation`, `11-sites-apps`, `12-linksites-ui-policy`, `15-release-deploy`), unique generic rules with no IDE Development equivalent (`03-quality`, `04-testing`, `05-agent-behavior`, `06-troubleshooting`, `07-cross-ide-handoff`), and `agents/README.md` pointing at abandoned LiNKdev — trips `LEGACY-CLEANUP.md` stop condition |

**Next:** Carlos decides selective merge (keep LiNKsites-specific rules local; symlink shared paths only if added later).

---

## Phase 4 — Locked Q&A

| # | Decision | Applied |
|---|---|---|
| Q1 | Stale `00-linkdev-bootstrap` in `core/prompts/execution/*.md` | **Deferred** — 7 files listed; fix later |
| Q2 | Stage 1a historical bootstrap mentions | **Done** — one-line note in `LINKDEVELOPER-STAGE1A-SPEC.md` §D.3 |
| Q3 | LiNKsites `.cursor` symlink | **Stopped** — backup exists; selective merge pending |

---

## Phase 5 — Website Factory workflow spec

**Status:** Superseded by blueprint-first approach

- Prior agent prompt incorrectly mapped Website Factory onto LiNKdeveloper dev workflow (`Intent → …`)
- **Correct sequence:** Factory Operations Common Blueprint (locked) → Website variant spec (next)
- **Next file:** `docs/LINKSITES-FACTORY-WORKFLOW-SPEC.md`

---

## Open questions

1. LiNKsites `.cursor` selective merge — which rules stay local vs shared?
2. VPS path for hot artifact storage (`/data/factories/` vs MinIO)?
3. Odoo sync triggers — which gates write back to `crm.lead` / `sale.order`?
4. First Website Factory niche/city for P1 bootstrap?

---

## Self-assessment

**Pass with planned follow-ups.** Infrastructure setup (commit, workspace, backup, Q&A) is complete. Factory blueprint is locked. Website variant spec and schema migration are the next build steps.
