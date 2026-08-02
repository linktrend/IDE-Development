# Lane A link-fix requests (Issue #72 Lane B)

Lane B did **not** edit these Lane A–owned / SOT surfaces. Thin stubs keep most historical paths resolvable; please update citations to canonical archive paths when convenient.

## Exact patches requested

### `docs/BUILD-LOG.md`

| Line / context | Current | Prefer |
|----------------|---------|--------|
| WP1 plan pointer | `docs/work-packets/2026-08-02-work-packet-1-production-readiness.md` | `docs/archive/work-packets/2026-08-02-work-packet-1-production-readiness.md` (stub remains at old path) |
| Lane F result | `docs/runbooks/LANE_F_RESULT.md` | `docs/archive/runbooks/LANE_F_RESULT.md` (pointer stub at old path) |
| WP1 evidence path | `docs/validation/wp1-evidence/` | **KEEP** — intentionally retained active (Lane B) |
| WP02 packet | `docs/work-packets/2026-08-02-work-packet-02-integration-lineage-and-live-readiness.md` | `docs/archive/work-packets/2026-08-02-work-packet-02-integration-lineage-and-live-readiness.md` |
| WP02 evidence | `docs/evidence/wp02/WORK-PACKET-02-EVIDENCE.md` + `EXTERNAL-CONFIGURATION-CLOSURE.md` | `docs/archive/evidence/wp02/WORK-PACKET-02-EVIDENCE.md` + same dir (pointer README at `docs/evidence/wp02/`) |

### `docs/OPEN-ISSUES.md`

| Context | Current | Prefer |
|---------|---------|--------|
| Wave 2 packet | `docs/work-packets/2026-08-01-wave-2-app-backed-completion.md` | `docs/archive/work-packets/2026-08-01-wave-2-app-backed-completion.md` |
| WP1 plan status pointer | `docs/work-packets/2026-08-02-work-packet-1-production-readiness.md` | archive path above |
| WP02 evidence | `docs/evidence/wp02/WORK-PACKET-02-EVIDENCE.md`, `EXTERNAL-CONFIGURATION-CLOSURE.md` | `docs/archive/evidence/wp02/…` |

### `docs/GITOPS-CONSUMER-ROLLOUT.md`

| Context | Current | Prefer |
|---------|---------|--------|
| SOT work-packet cite | `docs/work-packets/2026-08-02-work-packet-1-production-readiness.md` | archive path |
| WP02 status evidence | `docs/evidence/wp02/WORK-PACKET-02-EVIDENCE.md` | `docs/archive/evidence/wp02/WORK-PACKET-02-EVIDENCE.md` |

### `docs/contracts/EXTERNAL-STATE-AUDIT.md` (SOT / status header — Lane B left untouched)

| Context | Current | Prefer |
|---------|---------|--------|
| SOT line work-packet | `docs/work-packets/2026-08-02-work-packet-1-production-readiness.md` | `docs/archive/work-packets/2026-08-02-work-packet-1-production-readiness.md` |

### `docs/work-packets/2026-08-02-work-packet-04-consumer-rollout.md` (WP04 — Lane A)

| Context | Current | Prefer |
|---------|---------|--------|
| Related WP1 link | `./2026-08-02-work-packet-1-production-readiness.md` (resolves via stub) | `../archive/work-packets/2026-08-02-work-packet-1-production-readiness.md` |
| Related WP02 link | `./2026-08-02-work-packet-02-integration-lineage-and-live-readiness.md` | `../archive/work-packets/2026-08-02-work-packet-02-integration-lineage-and-live-readiness.md` |

### No change needed (verified)

- `README.md` / `SETUP.md` — already point at active WP04 only.
- `docs/CURRENT-STATUS.md` — no stale WP1/WP02/evidence/wp02 path hits found at Lane B audit time.
- `docs/validation/wp1-evidence/` — retained active; keep BUILD-LOG / acceptance cites as-is.

## Stub coverage (temporary discoverability)

Until the patches above land, these historical paths still resolve:

- `docs/work-packets/2026-08-01-wave-*.md`, `…work-packet-1…`, `…work-packet-02…` → relocate stubs
- `docs/evidence/wp02/README.md` → archive tree
- `docs/runbooks/LANE_F_RESULT.md` → archive copy
