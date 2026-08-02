# Issue #72 Lane A — status claims before → after

Representative surgical truth fixes (not an exhaustive diff).

## Board / launch posture

| Before | After |
|---|---|
| WP1 “in flight” / RC packaging ongoing | WP1 **complete** (RC proved on disposable targets) |
| WP2 is the “integration/publication stage” | WP2 **complete** = lineage + live readiness (checkpoint); integration/promote was **WP03** |
| WP03 not claimed / still ahead | WP03 **complete** — PR #69→development, #70→staging, #71→main; tree `43b1333ae21f43a34c3bdcccb2aac96f3d6e007f` |
| Consumer rollout “deferred until after WP2” | Consumer rollout = **WP04 prepared / NOT EXECUTED**; Principal approval pending |
| No single current-status page | **`docs/CURRENT-STATUS.md`** is the concise operator surface |
| No WP04 packet | **`docs/work-packets/2026-08-02-work-packet-04-consumer-rollout.md`** exists; mutation unauthorized until approval |

## README / SETUP

| Before | After |
|---|---|
| “WP1 proves RC; WP2 is integration/publication” | Post-WP03 / pre-WP04 narrative + CURRENT-STATUS + WP04 pointers |
| “Do not nest-install during Wave 1 / WP1” | Do not nest-install (system source) — timeless boundary |
| “Real consumers wait for Principal approval after WP2” | Real consumers wait for **WP04** Principal approval |

## Intent / Technical PRD / Ops Manual

| Before | After |
|---|---|
| Intent out-of-scope: “rollout during WP1”; “tag at WP2 boundary” | Rollout before WP04 approval deferred; tag/Release still separately gated |
| PRD status: WP1 “in flight” | PRD status: WP1–WP03 complete; WP04 prepared; Issue #72 cleanup |
| PRD: “WP2 is the integration/publication stage” | WP04 consumer rollout prepared / not executed |
| Ops: “WP1 proves RC… after WP2 decisions” | WP1–WP03 done; WP04 not started / approval pending |
| Ops FAQ “What is Work Packet 2?” | FAQ “What is Work Packet 4?” with prepared/not-executed framing |

## GITOPS-CONSUMER-ROLLOUT

| Before | After |
|---|---|
| Status: deferred until WP2 decisions | Status: deferred until **WP04** Principal approval; packet not executed |
| WP2 boundary = merge/publication | WP1/WP2/WP03 complete summaries; WP04 = consumer mutation (gated) |
| “Not authorized during WP1” only | Not authorized until WP04 approval; post-WP03 tree equality cited |

## Runbooks / acceptance / contracts (boundary / status lines)

| Before | After |
|---|---|
| RC runbook: WP2 handles merge/publication/rollout | Boundaries: WP1 RC, WP2 lineage, WP03 promote done, WP04 rollout gated |
| Acceptance hand-off: “WP2 owns integration…” | Hand-off: WP2/WP03 complete; WP04 owns consumer rollout |
| MANAGED-CORE / EXTERNAL-STATE / BUGBOT status lines pre-WP03 | Status lines updated to post-WP03 / WP04-not-executed (body left alone where constrained) |

## Boundaries kept crisp

- Claude Code **excluded**
- IDE Development = **system source / self-verification**; **no nested self-install**
- Locked consumer order unchanged; IDE Development absent from table
- WP04 document preparation ≠ authorization to mutate consumers

## Residual (not fully rewritten here)

| Location | Stale residue | Why left |
|---|---|---|
| `docs/contracts/MANAGED-CORE-V2.md` § Self-verification table | “Work Packet 2 handles integration/publication” | Lane A ownership = **status lines only** |
| `docs/contracts/EXTERNAL-STATE-AUDIT.md` agent prohibitions #6 | “those remain WP2 / Principal-gated” | Status lines only |
| `docs/OPEN-ISSUES.md` items #15–#16 | Historical WP1/WP2 “active” / “WP03 not claimed” wording | Append-only; superseded by item #17 + CURRENT-STATUS |
| `docs/BUILD-LOG.md` WP1-002 historical bullet | “WP1 deferral + WP2 boundary” | Append-only history; later WP03/WP04 entries correct board |
| `docs/work-packets/` archived WP1/WP02 bodies | Pre-WP03 framing inside archived packets | Lane B archive; historical artifacts |
| Outside ownership (examples) | `AGENTS.md` managed block consumer `.ide-development/` framing; other contracts/scripts; archive indexes | Other lanes / not Lane A write set |
