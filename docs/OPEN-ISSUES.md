# IDE Development — Open Issues

Append-only engineering build log for this repository. Prefer this file over stale prose elsewhere when asking “what is actually real?”

---

## Open / deferred (seeded 2026-07-19 from filesystem + docs audit)

1. **Same-session Cursor Desktop verification of all six `route-*.md` model pins** — bracket-param frontmatter is on disk and transcribed from LiNKdeveloper’s live-checked catalog; invoking each `/route-*` agent in Cursor to confirm the responding model matches the pin is still an open operator check (noted in Operations Manual / Technical PRD).

2. **Embedded legacy factory-folder cleanup in product repos** — deferred until Principal schedules per-repo adoption cleanup (`docs/ARCHIVE-INDEX.md`). Stage 1 posture: wire `.cursor` to IDE Development; do not treat those embedded trees as active.

3. **Principal phone/web approval dashboard** — not built; approvals via Cursor / technical relay.

4. **Persistent autonomous orchestrator in this repo** — deliberately out of scope (belongs to LiNKdeveloper).

5. **Automatic product deploy / LAW-06-style promotion from Module 6** — deliberately not ported; Module 6 ends at `release_ready` + Principal Release OK. **Note (2026-07-24):** Git branch promote (`development`→`staging` auto; `staging`→`main` Principal Telegram Approve) is in scope via ADR 0003 — that is not Module 6 live deploy.

6. **Dollar-cost accounting UI** — not present.

7. **Pre-existing dangling path in `.cursor/rules/01-identity.mdc`** — historically cited `docs/LINKDEVELOPER-OPERATIONS-MANUAL.md` (wrong name for this repo). Corrected to `docs/IDE-DEVELOPMENT-OPERATIONS-MANUAL.md` during item 8; broader identity prose that still sounds like LiNKdeveloper branding may need a separate cleanup pass.

8. ~~Documentation source-of-truth cleanup~~ — see item below (2026-07-19).

---

## 8. Documentation cleanup — four source-of-truth documents, legacy docs archived, OPEN-ISSUES created — 2026-07-19

Following the same playbook as LiNKdeveloper OPEN-ISSUES item #43 (2026-07-18), performed the Principal-requested documentation source-of-truth cleanup for **IDE Development** (`linktrend/IDE-Development`).

**New / rewritten source-of-truth documents:**

- `docs/IDE-DEVELOPMENT-INTENT.md` — why this repository exists, scope, out-of-scope, success criteria.
- `docs/IDE-DEVELOPMENT-TECHNICAL-PRD.md` — exhaustive technical reference (architecture, terminology, six-Module pipeline, doctrine, hybrid skills, model routing, git hooks/CI, LiNKlibraries, directory map, deferred gaps, doc-drift table).
- `docs/IDE-DEVELOPMENT-OPERATIONS-MANUAL.md` — **rewritten** plain-English handbook for the Principal (replaced the 2026-07-10/15 manual that still carried Stage 2/3 OpenClaw framing as if it were this repo’s roadmap).
- `docs/OPEN-ISSUES.md` — **created** (this file). No prior `NEXT-STEPS.md` / `TODO.md` / `BACKLOG.md` existed at repo root or under `docs/`.

**Legacy documentation archived to `docs/archive/`** (moved via `git mv`, not deleted):

| Source | Destination |
|---|---|
| `docs/IDE-DEVELOPMENT-STAGE1.md` | `docs/archive/IDE-DEVELOPMENT-STAGE1.md` |
| `docs/workspace-reports/2026-07-13-linksites-wire.md` | `docs/archive/workspace-reports/2026-07-13-linksites-wire.md` |
| `docs/validation/CROSS-SYSTEM-CONTRACT-REPORT.md` | `docs/archive/validation/CROSS-SYSTEM-CONTRACT-REPORT.md` |
| `docs/validation/UNIFICATION-E2E-REPORT.md` | `docs/archive/validation/UNIFICATION-E2E-REPORT.md` |
| `docs/validation/UNIFICATION-E2E-REAL-APP-REPORT.md` | `docs/archive/validation/UNIFICATION-E2E-REAL-APP-REPORT.md` |
| `docs/validation/unification-baseline.md` | `docs/archive/validation/unification-baseline.md` |
| `docs/planning/ide-development-linkdeveloper-unification-build-plan-prd.md` | `docs/archive/planning/ide-development-linkdeveloper-unification-build-plan-prd-live-2026-07-19.md` (differs from the earlier archive copy already at `docs/archive/planning/ide-development-linkdeveloper-unification-build-plan-prd.md`) |

**Explicitly NOT archived (judgment calls):**

- `core/execution/*` — operative doctrine (Laws, runtime model, pipeline); actively cited by name.
- `.cursor/`, `core/commands/`, `.githooks/*`, `tests/fixtures/**`, `docs/adoption-backups/**` — operative runtime / fixtures / backups, not descriptive docs about this repo.
- `docs/HYBRID-SKILLS-REGISTRY.md` — still required by `scripts/verify-ide-development.sh` and cited by many hybrid command/skill entrypoints; remains the live command-level routing map. Technical PRD summarizes architecture and points here.
- `docs/handoff/` — operational session handoff template + README; cited by `core/session/*`.
- `docs/adr/0002-shared-component-template-asset-library.md` — accepted ADR still cited by `core/commands/INDEX.yaml` library entries; Technical PRD covers the relationship.
- `docs/validation/GATE-STOP-001-report.md` — cited by Law 16 in `CANONICAL-LAWS.md` (doctrine must not be edited in this pass).
- `docs/validation/fixed-pipeline-feasibility-report.md` — cited by `scripts/feasibility/run-fixed-pipeline-feasibility.sh`.
- `docs/ARCHIVE-INDEX.md` — required by verify script; updated in place.

**`README.md` rewritten** (not archived) to point at the four documents as source of truth and correct stale claims.

**Archive indexes updated:** `docs/archive/README.md` and `docs/ARCHIVE-INDEX.md` reconciled to point at the new quartet and list what moved.

**Verification after structural changes:** `scripts/verify-ide-development.sh`, `scripts/verify-vendored-skills.sh`, `scripts/verify-pipeline-states.sh` (expected: pure documentation/file-organization pass; no code changes required for green).

**What this deliberately does NOT do:** delete archived documents; rewrite `core/execution/*`; change pipeline/validator/hooks behavior; invent completeness for deferred autonomy features.

---

## 9. Retire hybrid-skills refresh script and sibling gstack/skills clones — 2026-07-23

Principal decision: vendored hybrid skills inside this repo are authoritative and already adapted; do not refresh from upstream sibling clones.

**Removed:** `scripts/vendor-hybrid-skills.sh`.

**Updated:** `docs/HYBRID-SKILLS-REGISTRY.md`, Intent/Technical PRD, `SKILLS_CATALOG.md`, CI workflow comments; Lisa personality notes under `openclaw_prime` now point at vendored paths.

**Deleted from disk (not git):** optional sibling warehouses formerly named `gstack` and `skills` under the operator Projects tree. GitHub forks `linktrend/gstack` and `linktrend/skills` were not deleted.

**Kept:** in-repo vendored trees under `core/runtime/skills/{gstack,mattpocock}/` and `scripts/verify-vendored-skills.sh`.

---

## 10. Autonomous ship / pull / promote + wire inheritance (Layer A+B) — 2026-07-24

Principal go-ahead: system lives in IDE Development; wired repos inherit agent doctrine (`.cursor` symlink) and managed GitHub workflows (sync on wire/backfill); IDE Development itself in scope; Bugbot as Reviewer; Lisa Telegram for one-line status + main Approve.

**Added:** ADR 0003, `docs/AUTONOMOUS-GIT-OPERATIONS.md`, `docs/CURSOR-AUTOMATIONS-SETUP.md`, `core/github/managed-workflows/`, `core/checklists/BUGBOT-INHERITANCE.md`, rules `01-git-branching` / `02-autonomous-ship-pull`, `scripts/sync-managed-workflows.sh`, `scripts/backfill-managed-workflows.sh` (wire-repo extended).

**Clock (amended 2026-07-25):** Lisa Option A is the primary Ship/Pull clock (cron → Cursor ACP on Mini). Cursor Automations are optional backup only (`docs/CURSOR-AUTOMATIONS-SETUP.md`). Bugbot already ON — skip enablement. Lisa ship/pull procedures live in openclaw_prime.

**Skills (2026-07-25):** `/agentsetup` and `/agentcomply` land under `core/skills/` + `core/commands/` for short-lived `issue/*` bootstrap and migration.
