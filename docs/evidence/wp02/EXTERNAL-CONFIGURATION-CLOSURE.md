# WP02 — External configuration closure (Issue #68)

**Status:** CLOSED for WP02 stated scope
**Recorded:** 2026-08-02T03:46:00Z (Asia/Taipei wall ~11:46)
**Base partial checkpoint:** `712675614014abdf6e180915e07aa21e1a983324`
**Authoritative tip:** `git rev-parse` of pushed `issue/68-work-packet-02-integration-lineage-stale-cleanup`
**Recorder:** Cursor Grok 4.5 High evidence-closure (single-writer; no product/GitOps code mutation)

## Scope of this record

Documents Principal-supplied and already-verified live facts that close the live external-state gaps left open at the verified partial checkpoint. This makes **WP02 COMPLETE for its stated scope** (lineage + cleanup plan + IDE Development live readiness → pushed checkpoint).

This record does **not** mean:

- production acceptance of the system;
- consumer rollout authorization;
- WP03 integration into `development`;
- tag/Release publication;
- review-ready publication on this tip.

## Principal-supplied Bugbot UI evidence (external; not committed)

Two Principal-supplied screenshots were inspected in place. Images were **not** copied into the repository. Absolute local paths are **not** recorded.

| Ref | Portable identity | SHA-256 |
|-----|-------------------|---------|
| Screenshot 1 | Principal-supplied external evidence — Bugbot Active + Manual Only | `3738e1c84a2e556649d532ff39f9c28678e69069b4eb8f8aaefeed4ecad8aefa` |
| Screenshot 2 | Principal-supplied external evidence — linktrend provider repos enabled | `109aecf276118d99422e656dde2e8b35c0e23b775cf7c7b97f35495d073c1138` |

### Observed (non-secret)

- **Bugbot Active** (green Active indicator).
- **Trigger Mode** explicitly **Manual Only**.
- Page states Bugbot runs only when explicitly triggered with `bugbot run` or `@cursor review`.
- Screenshot 2: GitHub provider **linktrend** shows **10/82 Repositories Enabled**.

## Already-verified live facts (non-secret)

### GitHub App credentials (names only)

- Repository **variable** for GitHub App ID: present (value omitted).
- Repository **secret name** for App private key: present (value never read/printed).

### Review Ready Publisher dry-run — Actions run `30730954742`

- Trusted default-branch Review Ready Publisher **dry-run** successfully minted an App token with `AUTOMATION_TOKEN_SOURCE=github_app`.
- The run then failed **solely** because the WP02 tip lacks review-ready completion evidence — expected for this checkpoint-only packet (no `review-ready` publication attempted).

### Owner-authorized admin bootstrap — rulesets

| Branch | Ruleset ID | Posture |
|--------|------------|---------|
| `development` | `19728531` | Preserved unchanged |
| `staging` | `20218450` | Created and post-verified |
| `main` | `20218451` | Created and post-verified |

- Post verification returned `ok: true`.
- `staging` / `main` require **Verify IDE Development** plus **Enforce allowed PR source branches** (no Bugbot on promote/release branches).

### Carlos restricted user token

- Repository secret **name** `LINKTREND_BUGBOT_USER_TOKEN` exists.
- GitHub intentionally does not allow reading stored secret scopes — **scope is non-observable**, not a remaining configuration blocker.
- Code contract and tests restrict its use to Packager feature-PR creation and the exact Bugbot trigger comment only.

## Residual non-blockers (observability limits)

- Workflow `permissions:` blocks remain non-observable via Actions list API (`workflows.permissions_posture` historically `unknown`). Not treated as an open WP02 configuration blocker after App mint proof + ruleset post-verify + Manual-Only UI proof.
- This tip intentionally has no review-ready evidence; publisher dry-run failure for that reason is expected.

## Prohibited actions (this closure session and recorded live work)

All remain false / did not occur:

- credentials or secret values exposed;
- PR opened;
- review-ready publication;
- Packager;
- Bugbot trigger;
- Integrator merge;
- promotion;
- consumer mutation;
- frozen-head edit;
- close/delete of PRs/issues/branches/worktrees;
- force push / history rewrite;
- cleanup apply;
- tag/Release.

## Lane D historical note

Lane D packet under `docs/evidence/wp02/lane-d/` remains the accurate **session** record of the earlier blocked apply (`NOT READY` at `9cd3fec…`). This closure file supersedes that readiness *verdict* for WP02 completion without rewriting Lane D history.
