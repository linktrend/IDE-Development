# Lane F result — production documentation and operator handoff

**Lane:** F
**Issue:** #67
**Work packet:** Work Packet 1 — production-readiness proof and release candidate
**Model:** cursor-grok-4.5-high
**Date:** 2026-08-02
**Commit/push/PR/review-ready:** Not performed (subagent constraint)

---

## Files changed

### Created

| Path | Purpose |
|---|---|
| `docs/runbooks/release-candidate.md` | RC operator runbook; `create`/`verify`; source vs extracted install; WP1/WP2 boundary |
| `docs/runbooks/rollback.md` | Transactional rollback runbook |
| `docs/acceptance/acceptance-matrix.md` | WP1 acceptance gates (installer, OS, external-state, RC, exclusions) |
| `docs/BUILD-LOG.md` | Append-only WP1+ build log |
| `docs/runbooks/LANE_F_RESULT.md` | This result file |

### Updated

| Path | Purpose |
|---|---|
| `README.md` | System source, install surfaces, CLI, RC path, Claude excluded, rollout deferred, OS evidence |
| `SETUP.md` | One-command source + RC install; discovery/precedence; external-state read-only; WP1 hard rules |
| `docs/IDE-DEVELOPMENT-INTENT.md` | WP1/WP2, Claude excluded, rollout deferred, build-log/runbook pointers |
| `docs/IDE-DEVELOPMENT-OPERATIONS-MANUAL.md` | Principal-facing status: deferred rollout, no tag/apply in WP1, WP2 FAQ |
| `docs/IDE-DEVELOPMENT-TECHNICAL-PRD.md` | Install model, RC commands, external-state WP1 boundary, doc-drift table |
| `docs/GITOPS-CONSUMER-ROLLOUT.md` | Explicit deferred consumer mutation; WP1 vs WP2 boundary |
| `docs/contracts/MANAGED-CORE-V2.md` | Doc clarifications: WP1 no-apply, RC, deferred rollout |
| `docs/contracts/EXTERNAL-STATE-AUDIT.md` | Doc clarifications: plan/verify only in WP1; no apply |
| `docs/OPEN-ISSUES.md` | Status pointer item #14 for Issue #67 / WP1 |

### Not edited (per ownership)

- `docs/work-packets/2026-08-02-work-packet-1-production-readiness.md`
- Installer / tests / workflows / packaging code / `.github/**`
- Archived historical evidence (active SOT docs already supersede)

---

## Accuracy notes

Live CLI from `python3 scripts/ide-development.py --help`:

```text
plan | install | update | drift | verify | version | rollback | release-candidate
```

`release-candidate` actions:

- `create` — `--output-dir` (default `build/release-candidate`), `--allow-dirty` (local proofs only), `--skip-install-verify`, `--skip-evidence`
- `verify` — `--archive` required; optional `--expected-version` (default `2.0.0`)

Flags on other commands: `--repo`/`--target`, `--package`, `--json`, `--dry-run`.

---

## Doc gaps waiting on other lanes

| Gap | Waiting on |
|---|---|
| Exact archive member layout / entrypoint path inside `.tar.gz`/`.zip` for manual `--package` install prose | Lane D evidence / schemas |
| Cross-platform matrix command name / CI artifact paths filled into acceptance evidence columns | Lane A |
| Expanded external-state planner/verifier names beyond `external_state_audit.py` | Lane C |
| Disposable-harness paths if they diverge from the plan’s listed suites | Lane B / E |
| Final evidence-bundle path and SHA fill-in for BUILD-LOG | Lead after A–G |
| Confirmation that production `create` without skip flags is green on this SHA | Lane D + Lead |

---

## Blockers for Lane F itself

None for documentation ownership. Remaining production-readiness blockers are implementation/evidence from other lanes (A three-OS matrix green; D production-grade RC create without skip flags; C live/fixture verify; B/E harnesses), not missing owned prose paths.
