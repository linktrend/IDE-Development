# Lane F — Docs truth review (independent reviewer #1)

**Role:** Lane F independent reviewer #1 (docs truth)
**Model:** cursor-grok-4.5-high
**Worktree:** `issue-72-pre-launch-ide-development-codebase-cleanup-arch`
**Date:** 2026-08-02
**Mode:** READ-ONLY (findings only under this path; no commit/push)

## Verdict: **FAIL**

Primary operator surfaces (`docs/CURRENT-STATUS.md`, README, SETUP, Intent status header, Technical PRD, Ops Manual current-status table, GITOPS-CONSUMER-ROLLOUT, WP04 packet, BUILD-LOG WP03/WP04/ISSUE72 entries, runbooks, acceptance-matrix status boundary, contract **status lines**) correctly state:

- WP1 / WP2 / WP03 **COMPLETE**
- WP03 PRs **#69 → development, #70 → staging, #71 → main** and tree `43b1333ae21f43a34c3bdcccb2aac96f3d6e007f`
- WP04 **PREPARED / NOT EXECUTED** (approval pending)
- Claude **excluded**; IDE Development **system source / not consumer**
- Issue **#72 in progress**
- Archive stubs for completed packets/evidence present

FAIL is driven by **major** residual contradictions that still live in active docs and can reverse operator truth for “what is real now” / WP numbering — not by missing `CURRENT-STATUS` or Claude/consumer regressions on the Start-here set.

**Blockers:** none
**Majors:** 3
**Minors:** 4

---

## Checklist vs verified facts

| Verified fact | Active-doc reflection | Notes |
|---|---|---|
| WP1, WP2, WP03 COMPLETE | Pass on Start-here + CURRENT-STATUS + PRD/Ops/GITOPS/BUILD-LOG/WP04 | Residual false-active text in OPEN-ISSUES #15 (major) |
| WP03 PRs #69/#70/#71 + tree `43b1333…` | Pass on CURRENT-STATUS, README, GITOPS, OPEN-ISSUES #17, BUILD-LOG, PRD, WP04 | ARCHIVE-INDEX / archive README understate PRs as “#69” only (minor) |
| WP04 prepared / not executed | Pass across reviewed set | — |
| Claude excluded; system source ≠ consumer | Pass | No re-inclusion of Claude as supported; nested self-install forbidden |
| Issue #72 cleanup in progress | Pass on CURRENT-STATUS, README, OPEN-ISSUES #17, BUILD-LOG | Intent status header omits #72 (minor) |
| `docs/CURRENT-STATUS.md` = concise operator surface | Present and accurate | OPEN-ISSUES intro still claims prefer-this-file for “what is actually real?” (major) |
| Completed packets/evidence under archive + stubs | Pass | Stubs at `docs/work-packets/2026-08-0{1,2}-*` and `docs/evidence/wp02/README.md`, `docs/runbooks/LANE_F_RESULT.md` |

---

## Findings

### F1 — major — OPEN-ISSUES intro competes with CURRENT-STATUS as operator truth

**Path:** `docs/OPEN-ISSUES.md:3`

> Prefer this file over stale prose elsewhere when asking “what is actually real?”

**Why:** Verified requirement is that `docs/CURRENT-STATUS.md` is the concise operator surface. This sentence trains agents/operators to treat the append-only log (which still contains obsolete WP boundaries in #15) as the live board.

**Suggested fix:** Replace with something like:

```markdown
Append-only engineering build log. For “what is true **now**,” prefer `docs/CURRENT-STATUS.md`. This file records history and open/deferred items; later entries supersede earlier wording when they explicitly correct it.
```

Also align Intent §7 (`docs/IDE-DEVELOPMENT-INTENT.md:122`) which still says prefer OPEN-ISSUES over stale prose for what was verified — keep OPEN-ISSUES as history, CURRENT-STATUS as current board.

---

### F2 — major — OPEN-ISSUES #15 still labels completed WP1 as active and WP2 as integration/publication

**Paths / quotes:**

- `docs/OPEN-ISSUES.md:186` — `**Status pointer (active):** Issue #67 · branch \`issue/67-...\``
- `docs/OPEN-ISSUES.md:195` — `**Work Packet 2** is the integration/publication stage.`

**Why:** WP1 is COMPLETE; integration/promote was WP03 (not WP2). Item #17 (`docs/OPEN-ISSUES.md:220`) correctly marks #15–#16 obsolete, but an agent that stops at #15 still sees a false-active issue and wrong WP boundary.

**Suggested fix (append-only-safe):** Immediately under the #15 heading, add a one-line banner:

```markdown
**SUPERSEDED for current status (see item #17 + `docs/CURRENT-STATUS.md`):** WP1 complete; WP2 ≠ integration/publication; do not treat Issue #67 / this branch pointer as active.
```

Optionally change “Status pointer (active)” → “Status pointer (historical at writing)” in a new correcting append (do not silently rewrite history if append-only policy forbids it — banner is enough).

---

### F3 — major — MANAGED-CORE-V2 Wave-internal “WP3” / “WP4” collide with Work Packet 03 / 04

**Paths:**

- `docs/contracts/MANAGED-CORE-V2.md:77` — `platforms/  # Codex/Cursor adapter sources (WP3 fills bodies)`
- `docs/contracts/MANAGED-CORE-V2.md:78` — `migrations/  # reviewed supersession catalog (WP4)`
- `docs/contracts/MANAGED-CORE-V2.md:241` — `not executed in this wave`
- `docs/contracts/MANAGED-CORE-V2.md:278` — `` `core/managed-core/migrations/` (WP4 catalog) ``

**Why:** Active status line correctly says WP1–WP03 complete and WP04 prepared/not executed, but body labels still use bare `WP3`/`WP4` for **Wave 1 ADR slice** work (adapters / migration catalog — see ADR 0004). Operators reading post-WP03 vocabulary will map these to **Work Packet 03 / WP04 consumer rollout**.

**Suggested fix:** Disambiguate everywhere in this contract (and twin under `core/managed-core/content/doctrine/MANAGED-CORE-V2.md` if kept in sync):

- `WP3` → `Wave-1 slice WP3 (platform adapter bodies)` or `ADR-0004 WP3`
- `WP4` → `Wave-1 slice WP4 (migration catalog)` — never bare `WP4` next to consumer-rollout prose
- Line 241: `not executed in this wave` → `not executed (Work Packet 04 / Principal gate)`

---

### F4 — minor — ARCHIVE-INDEX / archive README understate WP03 promote set

**Paths:**

- `docs/ARCHIVE-INDEX.md:10` — `**WP03 (#69)** integrated on \`development\` …`
- `docs/archive/README.md:21` — `after WP03 (#69)`

**Why:** Tree hash is correct, but verified fact requires PRs **#69/#70/#71** (development/staging/main). Naming only #69 invites “staging/main not promoted” misreads.

**Suggested fix:**

```markdown
- **WP03 complete:** PR #69 → `development`, #70 → `staging`, #71 → `main`; trees equal `43b1333ae21f43a34c3bdcccb2aac96f3d6e007f` (issue branch tip starts at `e6301fc`).
```

---

### F5 — minor — Intent status header omits Issue #72 in progress

**Path:** `docs/IDE-DEVELOPMENT-INTENT.md:3`

Grounds WP1/WP2/WP03 but does not state Issue #72 cleanup is in progress (CURRENT-STATUS does).

**Suggested fix:** Append to Status line: `Issue #72 pre-launch cleanup in progress; see docs/CURRENT-STATUS.md.`

---

### F6 — minor — EXTERNAL-STATE-AUDIT SOT omits CURRENT-STATUS; present-tense “Lane C expands”

**Paths:**

- `docs/contracts/EXTERNAL-STATE-AUDIT.md:6` — SOT list has no `docs/CURRENT-STATUS.md`
- `docs/contracts/EXTERNAL-STATE-AUDIT.md:7` — `WP1 Lane C expands inventory...` (present tense for completed WP1)

**Suggested fix:** Add CURRENT-STATUS to SOT; past-tense the Lane C sentence (`expanded` / `expanded under WP1`).

---

### F7 — minor — BUGBOT-MENTION-ONLY “This PR” / PR #19 section reads as live current work

**Path:** `docs/contracts/BUGBOT-MENTION-ONLY.md:63-65`

**Why:** Status line correctly gates WP04; body “This PR” / PR #19 is historical spend-limit context and can look like an open operational freeze.

**Suggested fix:** Retitle to `## Historical note (PR #19 spend-limit period)` and point operators to CURRENT-STATUS / WP04 for rollout gate.

---

## Surfaces reviewed (no additional majors)

| File | Result |
|---|---|
| `README.md` | Pass — post-WP03/pre-WP04, Claude excluded, system source, CURRENT-STATUS pointer |
| `SETUP.md` | Pass — WP04 prepared/not executed; no nested self-install |
| `CHANGELOG.md` | Pass — Issue #72 Lane A unreleased note matches board |
| `docs/CURRENT-STATUS.md` | Pass — authoritative board matches verified facts |
| `docs/IDE-DEVELOPMENT-TECHNICAL-PRD.md` | Pass — complete WP1–03; WP04 not executed; #72; Claude excluded; anti-drift table |
| `docs/IDE-DEVELOPMENT-OPERATIONS-MANUAL.md` | Pass — companion CURRENT-STATUS; consumer rollout not started / WP04 prepared |
| `docs/GITOPS-CONSUMER-ROLLOUT.md` | Pass — WP1–03 complete; WP04 prepared; system source absent from consumer table |
| `docs/BUILD-LOG.md` | Pass — WP03-001 / WP04-001 / ISSUE72-001 correct (earlier WP1 rows are historical narrative) |
| `docs/work-packets/2026-08-02-work-packet-04-consumer-rollout.md` | Pass — PREPARED / NOT EXECUTED |
| `docs/work-packets/README.md` + stubs | Pass — completed packets archived; thin stubs resolve |
| `docs/runbooks/release-candidate.md` / `rollback.md` | Pass — status boundaries correct; Claude excluded |
| `docs/acceptance/acceptance-matrix.md` | Pass — historical WP1 checklist + post-WP03 status boundary |
| `docs/contracts/MANAGED-CORE-V2.md` | Status line Pass; body numbering Fail → **F3** |
| `docs/contracts/EXTERNAL-STATE-AUDIT.md` | Status line Pass; SOT/tense → **F6** |
| `docs/contracts/BUGBOT-MENTION-ONLY.md` | Status line Pass; historical “This PR” → **F7** |
| `docs/ARCHIVE-INDEX.md` / `docs/archive/README.md` | Mostly Pass; PR understatement → **F4** |

---

## Explicit non-findings (charter focus)

- No active Start-here claim that WP1/WP2/WP03 are still pending.
- No claim that WP04 consumer mutation has been executed.
- No Claude re-inclusion as a supported v2 platform on reviewed active docs.
- No instruction to nest-install `.ide-development/` into IDE Development on reviewed active docs.
- `docs/CURRENT-STATUS.md` exists and is correctly linked from README, SETUP, Ops Manual, GITOPS, WP04, runbooks, acceptance-matrix.

---

## Recommended close-out order (for implementer lane, not this reviewer)

1. Fix **F1** + **F2** (operator truth pointer + OPEN-ISSUES #15 supersession banner).
2. Fix **F3** (disambiguate Wave-1 WP3/WP4 vs Work Packet 03/04).
3. Apply **F4–F7** polish.
4. Re-run this checklist; expect **PASS** when majors clear.

Companion machine-readable summary: `docs-truth-review.json`.
