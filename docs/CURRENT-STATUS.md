# IDE Development — Current status

**Audience:** Principal and operators who need the truth without reading historical build logs.
**Date:** 2026-08-03
**Package:** portable managed-core **v2.1.0** (identity in `VERSION`; no Git tag / GitHub Release claimed)
**Platforms:** Cursor + native Codex supported; **Claude Code excluded**

This page is the concise launch-readiness / current-status surface. Historical detail lives in [`BUILD-LOG.md`](./BUILD-LOG.md), [`OPEN-ISSUES.md`](./OPEN-ISSUES.md), and work packets under [`work-packets/`](./work-packets/).

---

## One-line verdict

**Pre-rollout cleanup complete.** The v2.1 system source is integrated and promoted across protected lines. Consumer rollout is **prepared and not executed** — Principal approval is still required.

---

## Work-packet board

| Packet | Issue | Outcome | Status |
|---|---|---|---|
| **WP1** | #67 | Proved RC on disposable targets (installer, migration, Cursor/Codex adapters, packaging, recovery, security, read-only external-state, OS matrix expectations) | **Complete** |
| **WP2** | #68 | Built canonical lineage + IDE Development live readiness (checkpoint; no consumer mutation) | **Complete** |
| **WP03** | integration/promote | PR #69 → `development`, #70 → `staging`, #71 → `main` | **Complete** |
| **Issue #72** | pre-launch cleanup | System-repo active-doc truth, archive, tooling hygiene | **Complete** |
| **Issue #81** | v2.1 phase delivery | PR #82 → `development`, #85 → `staging`, #86 → `main` | **Complete** |
| **WP04** | consumer rollout | Locked-order consumer installs/updates | **Prepared — NOT EXECUTED** (approval pending) |

---

## Protected-line equality

After PR #86, `origin/development`, `origin/staging`, and `origin/main` shared content tree:

```text
fb1eb79a6a0e2b7990c13b6a16f90682bb7b2a77
```

The final pre-rollout reconciliation is promoted through the same governed path; operators must verify live equality before WP04 execution.

---

## Boundaries that remain true

| Boundary | Rule |
|---|---|
| System vs consumer | IDE Development is **system source / self-verification** — not a consumer rollout entry; **no nested self-install** of `.ide-development/` into this repo |
| Claude | **Excluded** from v2 support and roadmap |
| WP04 | Packet prepared at [`work-packets/2026-08-02-work-packet-04-consumer-rollout.md`](./work-packets/2026-08-02-work-packet-04-consumer-rollout.md); **no consumer mutation authorized** until Principal approval |
| Locked consumer order | `openclaw_prime` → LiNKplatform → LiNKskills → LiNKbrain → LiNKsites → LiNKdeveloper → LiNKlibraries → LiNKautowork → LiNKtrading-codebase ([`GITOPS-CONSUMER-ROLLOUT.md`](./GITOPS-CONSUMER-ROLLOUT.md)) |
| Tag / Release | Still not claimed as published for `v2.1.0` unless separately approved |

---

## Start here next

1. This page (current truth)
2. [`GITOPS-CONSUMER-ROLLOUT.md`](./GITOPS-CONSUMER-ROLLOUT.md) — inventory + gates
3. [`work-packets/2026-08-02-work-packet-04-consumer-rollout.md`](./work-packets/2026-08-02-work-packet-04-consumer-rollout.md) — WP04 prepared packet
4. [`runbooks/release-candidate.md`](./runbooks/release-candidate.md) · [`runbooks/rollback.md`](./runbooks/rollback.md)
5. Intent / Technical PRD / Operations Manual / `SETUP.md` for deeper doctrine and install commands
