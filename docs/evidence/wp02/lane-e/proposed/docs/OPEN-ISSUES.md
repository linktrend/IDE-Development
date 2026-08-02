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

---

## 11. GITOPS-01 Review Packager redesign — 2026-07-28

Branch `issue/GITOPS-01-review-packager-pipeline`. Principal-locked amendment to ADR 0003 (Review Packager + promotion window).

**Done in this PR (IDE Development only):**

- **Ship = checkpoint only:** commit + push on work branch; no PR; no Bugbot from Ship waves or EOD.
- **Review Packager:** `linktrend-review-packager.yml` — Tue/Fri **08:00** Asia/Taipei; discover `.linktrend/review-ready.json` where `commitSha == HEAD` → open/ready PR → Bugbot once (`@cursor review` default).
- **Staging promote:** Tue/Fri **10:00** Asia/Taipei (two hours after Packager); promote only work already on `development`; skip + report if not ready.
- **Named CI gates:** `core/github/CI-GATE-CONTRACTS.md` (`fast-gate`, `staging-gate`, `release-gate`).
- **Review-ready contract:** `core/github/REVIEW-READY.md` + `scripts/mark-review-ready.sh`, `validate-review-ready.sh`, `clear-review-ready.sh`.
- **Managed workflow sync list** includes review-packager; development-to-staging cron `0 2 * * 2,5` UTC.
- **Doctrine:** `docs/AUTONOMOUS-GIT-OPERATIONS.md` updated; ADR 0003 amendment 2026-07-28.
- **Follow-up contracts (no Lisa/OpenClaw edits here):** `docs/contracts/LISA-OPENCLAW-FOLLOW-UP.md`, `docs/contracts/LISA-MAIN-APPROVE-DISPATCH.md`.
- **Consumer rollout plan:** `docs/GITOPS-CONSUMER-ROLLOUT.md` (read-only drift posture; staged wire after merge).

**Deferred (explicitly not in GITOPS-01):**

- openclaw_prime Lisa personality / cron updates (`ship-pull-clock.md`, `pipeline-status.md`, `morning-digest.md`, etc.) — checklist in `LISA-OPENCLAW-FOLLOW-UP.md`.
- `wire-repo.sh` / `sync-managed-workflows.sh` on consumer repos (order locked in `docs/GITOPS-CONSUMER-ROLLOUT.md`: openclaw_prime → LiNKplatform → LiNKskills → LiNKbrain → LiNKsites → LiNKdeveloper → LiNKlibraries → LiNKautowork → LiNKtrading-codebase). IDE Development is system source only — not a consumer wire target.
- Per-consumer `LINKTREND_INTEGRATOR_REQUIRED_CHECKS` and Bugbot inheritance checklist runs.
- Lisa reporting lines for Review Packager / Staging 10:00 until openclaw follow-up PR lands.

**Authoritative clock (Asia/Taipei):** Ship 05, Pull 07, Ship 16, Pull 18; Packager Tue/Fri 08:00; Staging Tue/Fri 10:00; Main package Mon 08:00; digest + Approve Mon 08:30.

### Correction — 2026-07-28 (review-ready mechanism)

The bullet above that mentions discovering `.linktrend/review-ready.json` is **obsolete** and must not be followed.

**Authoritative mechanism now:**

1. Push the completed work branch first.
2. Publish successful commit status **`Linktrend Review Ready`** on the exact branch-tip SHA (`core/github/REVIEW-READY.md`, `scripts/mark-review-ready.sh`).
3. A later commit becomes unready automatically.
4. No `.linktrend/review-ready.json` and no readiness marker commit.

**Pull/freeze skip:** successful `Linktrend Review Ready` on the tip SHA, or an open review PR whose head equals that tip, or an explicit operator freeze — never a JSON-file condition.

---

## 12. GitOps lifecycle repair control — 2026-07-30

Branch `issue/23-gitops-lifecycle-repair-control`.

**Corrections (append-only):**

- Implementer / Ship / agentcomply: **checkpoint only** (commit+push). No implementer PR; Packager opens PR after review-ready.
- Staging schedule in branching rule: Tue & Fri **10:00** (aligned with ADR 2026-07-28 amendment).
- Cloud Fix language replaced by **Lisa ACP Repair Dispatcher** + durable GitHub repair tasks (max 3; no prefer-incoming).
- Completion gate, create_issue_branch helper, cleanup workflow, Actions cost controls, platform AGENTS (Cursor/Codex/ChatGPT).

See ADR 0003 amendment 2026-07-30 and `docs/contracts/*`.

---

## 13. App-backed Review Ready publisher + production completion bridge — 2026-08-01

Branch `issue/44-add-app-backed-review-ready-publisher-and-produc` (Issue #44). Wave 2 work packet: `docs/work-packets/2026-08-01-wave-2-app-backed-completion.md`.

**Goal:** A normal local implementer can complete an already-verified `issue/<n>-<slug>` branch without a privileged credential. Only the GitHub App publishes `Linktrend Review Ready`, from a trusted Actions workflow that re-validates branch, immutable SHA, and machine-readable evidence.

**Authoritative docs (this wave):**

- `docs/contracts/AGENT-COMPLETION.md` — fail-closed local gate + App-backed route diagnostics; no readiness file
- `core/github/REVIEW-READY.md` — publisher authority, dispatch contract, rollback
- `docs/AUTONOMOUS-GIT-OPERATIONS.md` — Ship/Packager doctrine aligned to App publish path
- Managed-runtime v2 payloads under `core/github/managed-runtime/` (AGENTS section + gitops bootstrap)

**Still true (supersedes any older file-marker wording above):**

1. Push the completed work branch first.
2. Publish successful commit status **`Linktrend Review Ready`** on the exact tip SHA (App-backed publisher / privileged App token only).
3. A later commit becomes unready automatically.
4. No `.linktrend/review-ready.json` and no readiness marker commit — do not discover or consult that path.
5. Carlos's restricted user identity must not publish this status (Packager/Bugbot scope unchanged).

**Out of this documentation packet:** workflow/script/test implementation, credential creation, consumer wire, PR/Bugbot/promote.

---

## 14. Work Packet 1 — production-readiness proof and release candidate (Issue #67) — 2026-08-02

**Status pointer (active):** Issue #67 · branch `issue/67-work-packet-1-production-readiness-proof-and-rel` · plan `docs/work-packets/2026-08-02-work-packet-1-production-readiness.md` (committed; do not edit from Lane F).

**Build log:** `docs/BUILD-LOG.md` (starts with WP1 entries).
**Operator handoff:** `docs/runbooks/release-candidate.md`, `docs/runbooks/rollback.md`, `docs/acceptance/acceptance-matrix.md`, updated `README.md` / `SETUP.md`.

**WP1 proves (system source only):** installer/migration, Cursor + native Codex discovery, RC packaging, recovery/security, read-only GitHub external-state plan/verify, macOS/Linux/Windows evidence expectations.

**WP1 does not:** touch frozen PR #49; merge/promote; publish tag/Release; install real consumers; apply live GitHub settings; add Claude support.

**Consumer rollout:** Deferred and separately Principal-gated — see `docs/GITOPS-CONSUMER-ROLLOUT.md`. **Work Packet 2** is the integration/publication stage.

**CLI at Lane F documentation time:** `plan|install|update|drift|verify|version|rollback|release-candidate` (`create` / `verify`). Default RC output: `build/release-candidate/`.

### Correction — 2026-08-02 (WP02 scope; do not rewrite above)

The WP1 sentence that called Work Packet 2 the “integration/publication stage” is **obsolete**. Authoritative WP02 packet (`docs/work-packets/2026-08-02-work-packet-02-integration-lineage-and-live-readiness.md`, Issue #68): lineage + stale-cleanup hardening (plan only) + IDE Development live readiness; ends at a pushed issue-branch checkpoint. Integration into `development` / promotion / publication decisions are **Work Packet 3**. Consumer rollout remains separately Principal-gated.

## 15. Work Packet 02 — integration lineage, stale cleanup, and live readiness (Issue #68) — 2026-08-02

**Status pointer (active):** Issue #68 · branch `issue/68-work-packet-02-integration-lineage-stale-cleanup` · packet `docs/work-packets/2026-08-02-work-packet-02-integration-lineage-and-live-readiness.md`.

**Immutable inputs:** WP01 `89956878c54ff45e4aef1ff42883d209221b7a30` · cleanup tip `5cf099155d9f7b5d95e094f74b288af7aec766af` · `origin/development` `991abc319782008ef93af95002be0d7f3d5a937c` · frozen PR #49 tip `0868c0034620c4ccb255457484f0342a12a0c833`.

**WP02 seeks:** one canonical issue-branch lineage; stale-cleanup hardening with tests (cleanup **plan only**); IDE Development live external-state readiness under the approved packet; evidence-bound pushed checkpoint.

**WP02 does not:** merge into `development`; promote; open PR / Bugbot / review-ready; tag/Release; mutate consumers; close/delete frozen PRs/issues/branches/worktrees; alter frozen PR heads; nested self-install; expose secrets.

**Next stage (not claimed here):** Work Packet 3 owns integration into `development` / promotion / publication decisions. Consumer rollout remains separately Principal-gated.

**Build log:** `docs/BUILD-LOG.md` (WP02 entries). Evidence: `docs/evidence/wp02/`.
