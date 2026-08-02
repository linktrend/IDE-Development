# WP02 Lane E — Manifest & SOT reconciliation

**Lane:** E (manifests, documentation, readiness evidence)
**Model:** cursor-grok-4.5-high
**Written:** 2026-08-02T03:12:45Z (UTC)
**Write root:** `docs/evidence/wp02/lane-e/**` only
**Conceptual combined lineage inputs (immutable):**

| Input | SHA |
|---|---|
| WP01 checkpoint | `89956878c54ff45e4aef1ff42883d209221b7a30` |
| Cleanup tip | `5cf099155d9f7b5d95e094f74b288af7aec766af` |
| `origin/development` | `991abc319782008ef93af95002be0d7f3d5a937c` |
| WP02 branch tip at Lane E write | `9cd3fec75075c6910b5a3bbb09b582e4cb3c94e4` |
| Frozen PR #49 tip (do not alter) | `0868c0034620c4ccb255457484f0342a12a0c833` |

**Ancestry note (at Lane E write):** WP01 and cleanup are **not** ancestors of WP02 `HEAD` yet (`merge-base --is-ancestor` → false). Development **is** an ancestor. Proposed docs assume lead will incorporate WP01+cleanup trees via ordinary history (Lane B).

---

## 1. Classification key

| Code | Meaning |
|---|---|
| `TAKE_WP01` | Content exists only (or authoritatively) on WP01; must land in combined lineage |
| `TAKE_CLEANUP` | Content exists only (or authoritatively) on cleanup tip; must land |
| `IDENTICAL` | Same bytes across compared tips |
| `DEVELOPMENT_BASE` | Present on development/HEAD; keep as base |
| `DOC_UPDATE_WP02` | WP01 prose incorrectly scopes WP02 as merge/publication; proposed edit aligns to approved WP02 packet + WP03 |
| `APPEND_ONLY` | Do not rewrite prior log entries; append correction / new entry |
| `CONFLICT_LEDGER` | Competing append-only entries — lead/Lane A–B must order without rewriting |
| `DEFER_WP03` | Explicitly out of WP02 (integration merge / promote / publish / consumer) |

---

## 2. Managed-core / skills manifests that must remain consistent after WP01+cleanup merge

These surfaces are **package integrity** — after combining trees, hashes/contents must remain coherent with WP01 portable-v2 (cleanup does not author them). Lead must re-run packaging/verify suites after integration.

| Path | WP01 | Cleanup / development / HEAD | Classification | Consistency rule |
|---|---|---|---|---|
| `core/managed-core/MANIFEST.json` | present (`packageVersion` 2.0.0, 227 files) | **ABSENT** | `TAKE_WP01` | Must appear exactly from WP01 package source; do not invent from development |
| `core/managed-core/VERSION` | `2.0.0` | **ABSENT** | `TAKE_WP01` | Must match package + root `VERSION` story (`v2.0.0` on WP01) |
| `core/managed-core/INDEX.yaml` | present | **ABSENT** | `TAKE_WP01` | Keep with managed-core package |
| `core/managed-core/platforms/cursor/materialization-manifest.json` | present (47 entries) | **ABSENT** | `TAKE_WP01` | Must stay aligned with Cursor physical adapters + managed-core skills |
| `core/managed-core/platforms/codex/skills-manifest.json` | present | **ABSENT** | `TAKE_WP01` | Must stay aligned with Codex discovery + `.agents` |
| `.agents/skills-manifest.json` | present | **ABSENT** | `TAKE_WP01` | Native Codex discovery manifest; must match packaged skills |
| `core/github/managed-runtime/MANIFEST.json` | present | present | `IDENTICAL` (sha256 `d018dce8dc41…`) | Keep; no conflict |
| `core/runtime/skills/VENDOR-MANIFEST.json` | present | present | `IDENTICAL` | Keep; hybrid vendor inventory must not drift |
| `core/skills/SKILLS_CATALOG.md` | present | present | `IDENTICAL` | Keep; catalog must remain consistent with agentsetup/agentcomply presence |
| Root `VERSION` | `v2.0.0` | `v1.2` | `TAKE_WP01` / conflict with development | Combined lineage should adopt WP01 `v2.0.0` (portable v2); record resolution in lead bind |
| `core/managed-core/skills/**` + platform skill copies | WP01 only | absent | `TAKE_WP01` | Skill trees must stay byte-consistent with `MANIFEST.json` file list |
| `core/managed-core/platforms/cursor/skills/agentsetup|agentcomply` | WP01 | absent | `TAKE_WP01` | Must match `core/skills/` and Codex/`.agents` counterparts |
| `core/managed-core/platforms/codex/skills/agentsetup|agentcomply` | WP01 | absent | `TAKE_WP01` | Same |
| `.agents/skills/agentsetup|agentcomply` | WP01 | absent | `TAKE_WP01` | Same |
| Cleanup stale-cleanup scripts/contracts | absent / older | present on `5cf0991` | `TAKE_CLEANUP` | Coexist with WP01 portable system (Lane C); do not drop for doc convenience |

**No proposed manifest byte edits in Lane E.** Manifests listed above are reconciliation targets for the lead after Lane B tree integration; Lane E only records required consistency.

---

## 3. Active SOT documents — WP02 “future / wrong scope” statements

WP01 active docs (and the WP02 packet status line on HEAD) contained statements that either (a) treat WP02 as not started, or (b) mis-assign merge/promotion/publication to WP02. Approved packet: WP02 = lineage + cleanup hardening (plan) + IDE live readiness → checkpoint; WP03 = integrate/promote/publish decisions; consumer rollout still separately gated.

| Document (WP01 path unless noted) | Obsolete / wrong statement (summary) | Proposed disposition | Classification |
|---|---|---|---|
| `docs/work-packets/2026-08-02-work-packet-02-…` (HEAD) | Status “Prepared; execution not started” | Status → execution in progress Issue #68 | `DOC_UPDATE_WP02` |
| `README.md` | WP2 = integration/publication (merge/promote) | WP2 = lineage/live readiness; WP3 = integrate/publish | `DOC_UPDATE_WP02` |
| `SETUP.md` | Consumer rollout after WP2 decisions; live apply = WP2/later loosely | Defer consumers to WP03+; IDE live apply may be WP2 under packet | `DOC_UPDATE_WP02` |
| `docs/GITOPS-CONSUMER-ROLLOUT.md` | Status/WP2 boundary = merge/publication | Split WP2 vs WP3; add Issue #68 | `DOC_UPDATE_WP02` |
| `docs/IDE-DEVELOPMENT-INTENT.md` | WP2 handles integration/publication; tag = WP2 | WP2 no consumer/tag; WP3 for publish decisions | `DOC_UPDATE_WP02` |
| `docs/IDE-DEVELOPMENT-OPERATIONS-MANUAL.md` | FAQ “What is WP2?” = merge/promote/publish | Rewrite FAQ; add WP3; update status table | `DOC_UPDATE_WP02` |
| `docs/IDE-DEVELOPMENT-TECHNICAL-PRD.md` | WP2 = integration/publication; tag WP2-gated | WP2 in progress lineage; tag WP03-gated | `DOC_UPDATE_WP02` |
| `docs/runbooks/release-candidate.md` | WP2 merges to development / publication | Split WP2/WP3 boundaries | `DOC_UPDATE_WP02` |
| `docs/acceptance/acceptance-matrix.md` | WP2 hand-off owns promote/publication | WP2 checkpoint vs WP3 hand-off | `DOC_UPDATE_WP02` |
| `docs/contracts/MANAGED-CORE-V2.md` | WP2 handles integration/publication | WP2 lineage/live readiness; WP3 publication | `DOC_UPDATE_WP02` |
| `docs/contracts/EXTERNAL-STATE-AUDIT.md` | Apply remains WP2/Principal (ambiguous vs consumers) | Clarify IDE apply may be WP2 packet; consumers WP03+ | `DOC_UPDATE_WP02` |
| `docs/BUILD-LOG.md` | WP1 deferred list lumps merge+apply into “WP2” | Clarify WP2 vs WP3; append WP02-001 | `DOC_UPDATE_WP02` + `APPEND_ONLY` |
| `docs/OPEN-ISSUES.md` item 14 | “WP2 is the integration/publication stage” | Keep text; append correction + item 15 | `APPEND_ONLY` |
| Cleanup `docs/OPEN-ISSUES.md` item 14 (stale-cleanup) | Competing #14 with WP01 | Lead orders both append-only; then WP02 #15 | `CONFLICT_LEDGER` |

Proposed edited copies: `docs/evidence/wp02/lane-e/proposed/**` (mirrors repo paths).

---

## 4. Explicit non-claims (Lane E)

Lane E proposals do **not** claim:

- WP03 integration into `development` complete
- Promotion, tag, GitHub Release, or registry publish
- Consumer rollout / consumer GitHub mutation
- Cleanup apply or frozen-head mutation
- Final combined-lineage SHA (placeholder in evidence template)

---

## 5. Conflict / resolution placeholders for lead bind

| ID | Conflict | Resolution (placeholder) |
|---|---|---|
| C-VERSION | Root `VERSION` `v2.0.0` (WP01) vs `v1.2` (development/cleanup) | `__RESOLVE__: prefer WP01 v2.0.0 after tree take` |
| C-OPEN-ISSUES-14 | Two distinct item 14 entries (WP01 WP1 vs cleanup stale-cleanup) | `__RESOLVE__: keep both chronologically; renumber if needed; then append #15` |
| C-MANAGED-CORE-ABSENT | managed-core tree absent on development | `__RESOLVE__: take WP01 tree wholesale; verify MANIFEST file list` |
| C-DOC-WP02-SCOPE | WP01 docs call WP2 merge/publication | `__RESOLVE__: apply Lane E proposed/**` |

---

## 6. External-state before/after summary placeholders (no secrets)

| Field | Value |
|---|---|
| Before snapshot dir | `docs/evidence/wp02/before-state-2026-08-02T030943Z/` |
| Before plan | `docs/evidence/wp02/before-state-plan.md` |
| After summary (Lane D bind) | `__PLACEHOLDER__: filled by lead after Lane D` |
| Secrets in evidence | **false** (names/posture only; never values) |
