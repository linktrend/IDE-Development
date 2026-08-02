# IDE Development — Build Log

Append-only engineering build log for **active** Work Packet progress. Prefer this file plus [`OPEN-ISSUES.md`](./OPEN-ISSUES.md) when asking “what was proven in this wave?”

Historical long-form OPEN-ISSUES entries remain authoritative for older waves; this file starts with **Work Packet 1** entries.

---

## WP1-001 — Work Packet 1 opened (Issue #67) — 2026-08-02

**Issue:** #67
**Branch:** `issue/67-work-packet-1-production-readiness-proof-and-rel`
**Plan:** `docs/work-packets/2026-08-02-work-packet-1-production-readiness.md` (do not edit; already committed)
**Models:** Lead + subagents `cursor-grok-4.5-high` only. Claude excluded.

**Outcome sought:** Independently testable portable managed-core v2 release candidate with installer, migration, Cursor/Codex adapters, packaging, recovery, security, and read-only GitHub external-state verification across macOS, Linux, and Windows.

**Explicitly deferred from WP1 (clarified for WP2/WP03):**

- Touching frozen PR #49 heads (WP2 must preserve frozen heads; may incorporate required content into the new lineage)
- Integration into `development` / promotion to `staging` or `main` → **Work Packet 3**
- Git tag / GitHub Release / registry publish → **Work Packet 3 / later approval**
- Real consumer repository install or update → **separately Principal-gated (not WP2)**
- Live GitHub App/settings **apply** on IDE Development → allowed in **WP2 only** under packet constraints; consumer apply remains deferred

**Lane map:** A cross-platform matrix · B clean-room install/migration · C external-state plan/verify · D RC packaging · E security/fail-closed · F production docs (this log + runbooks/acceptance) · G integrated review after A–F.

---

## WP1-002 — Lane F documentation baseline — 2026-08-02

**Lane:** F (production documentation and operator handoff)
**Commit policy:** Subagent writes only; lead integrates/commits.

**Added / updated (Lane F owned paths):**

- Root `README.md`, `SETUP.md` — operator entrypoints, RC vs source install, Claude exclusion, system-source vs consumer
- `docs/runbooks/release-candidate.md`, `docs/runbooks/rollback.md`
- `docs/acceptance/acceptance-matrix.md`
- `docs/BUILD-LOG.md` (this file)
- Clarifications in Intent / Operations Manual / Technical PRD
- `docs/GITOPS-CONSUMER-ROLLOUT.md` — WP1 deferral + WP2 boundary
- Doc clarifications: `docs/contracts/MANAGED-CORE-V2.md`, `docs/contracts/EXTERNAL-STATE-AUDIT.md`
- Status pointer: `docs/OPEN-ISSUES.md` (Issue #67 / WP1)
- `docs/runbooks/LANE_F_RESULT.md`

**CLI accuracy note at Lane F write time:**

```text
python3 scripts/ide-development.py {plan,install,update,drift,verify,version,rollback,release-candidate}
python3 scripts/ide-development.py release-candidate create|verify
```

`release-candidate` is present on this branch (Lane D). Production RC create requires a clean worktree; `--allow-dirty` is for local proofs only.

**Consumer rollout:** Deferred. Inventory and Principal-gated order remain in `GITOPS-CONSUMER-ROLLOUT.md`; WP1 must not mutate real consumers.

---

## Template for later WP1 entries

```markdown
## WP1-NNN — <title> — YYYY-MM-DD

**Lane / owner:**
**SHA:**
**Commands run + exit codes:**
**Artifacts / checksums:**
**Platforms:**
**Result:** pass | blocked | partial
**Blockers:**
```

## WP1-003 — Integrated checkpoint + three-OS CI green — 2026-08-02

**Branch tip before evidence commit:** `d8f117c8cb12eec808ed5c41a2e795764f417349`
**CI matrix:** run 30728657317 conclusion success on ubuntu/macOS/windows for `d8f117c`
**Evidence path:** `docs/validation/wp1-evidence/`
**RC:** rebuilt after evidence commit on clean tip (see companion JSON)

**Remaining blockers recorded:** H5 stale-cleanup script absent (deferred); live external-state not ready (read-only unknowns/missing).

**Hard stops honored:** no PR / Bugbot / review-ready / merge / promote / consumer / settings apply / tag / release / credentials / cleanup apply.

---

## WP02-001 — Work Packet 2 opened (Issue #68) — 2026-08-02

**Issue:** #68
**Branch:** `issue/68-work-packet-02-integration-lineage-stale-cleanup`
**Plan:** `docs/work-packets/2026-08-02-work-packet-02-integration-lineage-and-live-readiness.md`
**Models:** Lead + subagents `cursor-grok-4.5-high` only. Claude excluded.
**Startup SHA (packet commit):** `9cd3fec75075c6910b5a3bbb09b582e4cb3c94e4`

**Outcome sought:** Canonical issue-branch lineage combining `origin/development`, WP01 checkpoint, and cleanup tip; stale-cleanup controls restored/hardened with coexistence tests; IDE Development live external state verified ready (or blocked with concrete external cause); evidence-bound pushed checkpoint.

**Explicitly NOT claimed by WP02:**

- Integration merge into `development` (WP03)
- Promotion to `staging` / `main` (WP03)
- Git tag / GitHub Release / registry publish
- Real consumer repository install or update
- Cleanup apply / closing frozen PRs / deleting branches or worktrees
- `review-ready`, Packager PR, Bugbot trigger

**Lane map:** A reconciliation ledger · B lineage construction · C stale-cleanup hardening · D live external-state readiness · E manifests/docs/evidence (this log pointer) · F independent Cursor reviews after A–E integration.
