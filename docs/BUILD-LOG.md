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

**Explicitly deferred to Work Packet 2 / separate approval:**

- Touching frozen PR #49
- Integration into `development` / promotion to `staging` or `main`
- Git tag / GitHub Release / registry publish
- Real consumer repository install or update
- Live GitHub App, secret, variable, Bugbot, or ruleset **apply**

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

## WP02-001 — Work Packet 02 complete for stated scope (Issue #68) — 2026-08-02

**Issue:** #68
**Branch:** `issue/68-work-packet-02-integration-lineage-stale-cleanup`
**Accepted partial checkpoint:** `712675614014abdf6e180915e07aa21e1a983324`
**Packet:** `docs/work-packets/2026-08-02-work-packet-02-integration-lineage-and-live-readiness.md`
**Evidence:** `docs/evidence/wp02/WORK-PACKET-02-EVIDENCE.md` + `EXTERNAL-CONFIGURATION-CLOSURE.md`

**Proven:** canonical lineage (DEV + WP01 + cleanup + #28 handoff); stale-cleanup tests (no apply); three-OS CI green; RC bound; live external readiness closed (App mint on dry-run `30730954742`; staging/main rulesets `20218450`/`20218451`; development `19728531` preserved; Bugbot Manual Only via Principal UI evidence SHA-256 recorded).

**Result:** COMPLETE for stated WP02 scope (checkpoint only).

**Not claimed:** production acceptance; consumer rollout; WP03 integration; review-ready on this tip; tag/Release.

**Hard stops honored:** no PR / Bugbot trigger / review-ready publish / Integrator / promote / consumer mutation / frozen-head edit / close-delete / force push / cleanup apply / credential exposure.
