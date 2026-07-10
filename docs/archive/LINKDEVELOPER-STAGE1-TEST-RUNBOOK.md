# LiNKdeveloper Stage 1 — Test Runbook

**Audience:** Carlos (Principal)  
**Duration:** 30–45 minutes  
**Repository:** `/Users/linktrend/Projects/IDE Development`  
**Purpose:** Supervised operational validation before v1.0 tag and Stage 1 sign-off  
**Output:** Completed checklist + filled verification report at `docs/LINKDEVELOPER-STAGE1-VERIFICATION-REPORT.md`

---

## Before You Start

| Item | Path / action |
|------|----------------|
| Workspace | Open `~/Projects/Workspaces/LiNKdeveloper.code-workspace` or this repo directly in Cursor |
| Branch | Stay on `development` (or create `dev/carlos-stage1-verify` if you prefer an isolated branch) |
| Session | Start a **fresh** Cursor chat — do not resume an old thread |
| Timer | Block 45 minutes; stop at 45 even if incomplete and record blockers in the verification report |

**Do not commit or push during this runbook unless you explicitly choose to afterward.** The runbook is validation-only.

---

## Recommended Smoke Test Path

**Use the SMALL-CHANGE path** (not full authentication re-validation).

| Path | Verdict |
|------|---------|
| **SMALL-CHANGE** (recommended) | Primary smoke test |
| Authentication pilot re-validation | Optional 10-minute spot-check only |

### Rationale

1. **V1 checklist item 10** asks for a *supervised real repository test* using the **current** bootstrap and command surfaces — not a re-read of an existing simulation.
2. **Time budget:** Authentication pilot has 6 issues plus module-level artifacts (~35+ files). Walking it end-to-end exceeds the 30–45 minute window. SMALL-CHANGE completes proof → review → integration in one issue (~20 minutes).
3. **Bootstrap currency:** The authentication pilot report references `00-linkdev-bootstrap.mdc` (renamed to `00-bootstrap.mdc` in Stage 1b). SMALL-CHANGE exercises the live bootstrap rule and `START-HERE.md` decision path.
4. **Fresh evidence:** A new operator run produces artifacts Carlos can sign off today. The auth pilot already passed on 2026-06-12; re-validation adds little new signal.
5. **Same gates:** SMALL-CHANGE still enforces issue atomicity, `review_ready`, separate proof/review/integration, and anti-incompletion — the behaviors V1 items 4–6 require.

**Optional auth spot-check (10 min max):** After the SMALL-CHANGE smoke, skim `core/pilots/authentication-module-smoke-test/PILOT-REPORT.md` and confirm `review/AUTH-004-REVIEW-v1.md` rejected insufficient proof. This reinforces item 6 without re-running the full pilot.

---

## Phase 1 — V1 Readiness Checklist (Items 1–10)

Work top to bottom. Check each box only when you have **verified** the expected outcome (not merely read the file title).

### D.1 — Root entrypoints for first-time use

- [ ] **1.** Confirm the root entrypoints for first-time use are:
  - [ ] `.cursor/README.md` — opens and describes read order + `core/` / `.cursor/` split
  - [ ] `.cursor/bootstrap/START-HERE.md` — opens and lists minimum read order + decision path
  - [ ] `.cursor/commands/INDEX.yaml` — opens and lists preferred commands including `small-change`

**How to verify:** Open each file. Confirm START-HERE routes tiny changes to `SMALL-CHANGE -> PROOF -> REVIEW -> INTEGRATION`.

**Expected outcome:** All three files exist, are readable, and agree on startup order.

---

### D.2 — Every canonical layer remains indexed

- [ ] **2.** Confirm every canonical layer remains indexed and discoverable.

**How to verify:** Confirm each `INDEX.yaml` exists and is non-empty:

| Layer | Index path |
|-------|------------|
| Bootstrap | `.cursor/bootstrap/INDEX.yaml` |
| Discovery | `.cursor/discovery/INDEX.yaml` |
| Execution | `.cursor/execution/INDEX.yaml` |
| Templates | `.cursor/templates/INDEX.yaml` |
| Commands | `.cursor/commands/INDEX.yaml` |
| Agents | `.cursor/agents/INDEX.yaml` |
| Workflows | `.cursor/workflows/INDEX.yaml` |
| Contracts | `.cursor/contracts/INDEX.yaml` |
| State | `.cursor/state/INDEX.yaml` |
| Runtime | `.cursor/runtime/INDEX.yaml` |
| System | `.cursor/system/INDEX.yaml` |
| Session | `.cursor/session/INDEX.yaml` |
| Workspace | `.cursor/workspace/INDEX.yaml` |
| Examples | `.cursor/examples/INDEX.yaml` |

**Also run wire checklist structure section** (`core/checklists/wire-checklist.md`):

- [ ] `.cursor/README.md` exists
- [ ] `rules/`, `skills/`, `prompts/`, `agents/`, `templates/`, `commands/` exist under `.cursor/`
- [ ] `workflows/` and `checklists/` exist under `core/` (canonical) and resolve via `.cursor/` symlink

**Expected outcome:** No missing index; wire checklist structure boxes checked.

---

### D.3 — Canonical execution command surface

- [ ] **3.** Confirm the canonical execution command surface remains:
  - [ ] `plan-program` → `.cursor/commands/plan-program.md`
  - [ ] `plan-module` → `.cursor/commands/plan-module.md`
  - [ ] `complete-module` → `.cursor/commands/complete-module.md`
  - [ ] `execute-issue` → `.cursor/commands/execute-issue.md`
  - [ ] `review-issue` → `.cursor/commands/review-issue.md`
  - [ ] `integrate-issue` → `.cursor/commands/integrate-issue.md`
  - [ ] `small-change` → `.cursor/commands/small-change.md` (lightweight path; still preferred)

**How to verify:** Open `.cursor/commands/INDEX.yaml` and confirm each entry has `status: active` (or `preferred` tag). Open one command file and confirm it points to a prompt under `.cursor/prompts/execution/`.

**Expected outcome:** Six core commands + `small-change` are present and marked active/preferred. Legacy `linkdev-*` commands are compatibility-only.

---

### D.4 — Issue remains the atomic executable unit

- [ ] **4.** Confirm issue remains the atomic executable unit everywhere.

**How to verify:**

1. Read Law 1 in `.cursor/execution/CANONICAL-LAWS.md` — *"The issue is the atomic executable unit."*
2. Open `.cursor/templates/ISSUE.md` — confirm `issue_id`, `status`, `acceptance_criteria`, `proof_requirements`, `review_requirements`, `integration_requirements`.
3. Open `.cursor/state/STATE-MODEL.md` — confirm issue states include `ready`, `in_progress`, `review_ready`, `done`.

**Expected outcome:** Doctrine, template, and state model all treat the issue as the smallest executable unit.

---

### D.5 — `review_ready` remains mandatory

- [ ] **5.** Confirm `review_ready` remains mandatory for issues.

**How to verify:**

1. `.cursor/templates/ISSUE.md` — Gate Guidance: issues must pass through `review_ready`; no jump from `in_progress` to `done`.
2. `.cursor/execution/MINIMUM-RUNTIME-MODEL.md` — confirm review handoff is required before integration.
3. `.cursor/workflows/ISSUE-WORKFLOW.md` — confirm terminal execution state is `review_ready`, not `done`.

**Expected outcome:** All three sources require `review_ready` before review; `done` only after integration.

---

### D.6 — Proof, review, and integration remain separate gates

- [ ] **6.** Confirm proof, review, and integration remain separate completion gates.

**How to verify:**

1. Laws 12–13 in `.cursor/execution/CANONICAL-LAWS.md` — review separate from execution; integration separate from review.
2. Confirm three distinct templates exist:
   - `.cursor/templates/PROOF.md`
   - `.cursor/templates/REVIEW.md`
   - `.cursor/templates/INTEGRATION.md`
3. Optional auth spot-check: `core/pilots/authentication-module-smoke-test/review/AUTH-004-REVIEW-v1.md` — verdict `fail` on insufficient proof; integration only after `AUTH-004-REVIEW-v2.md` passes.

**Expected outcome:** Three templates, three workflows, no single artifact claiming all three gates.

---

### D.7 — Module completion semantics

- [ ] **7.** Confirm module completion semantics are explicit in doctrine and templates.

**How to verify:**

1. `.cursor/templates/MODULE.md` — `module_definition_of_done` and note that module completion requires mandatory module review.
2. `.cursor/workflows/MODULE-WORKFLOW.md` — exit requires module review complete.
3. Auth pilot evidence (read-only): `core/pilots/authentication-module-smoke-test/review/AUTH-MODULE-REVIEW.md` and `integration/AUTH-MODULE-INTEGRATION.md` exist.

**Expected outcome:** Template and workflow state module-level completion; pilot demonstrates module review + integration artifacts.

---

### D.8 — Compatibility assets explicitly marked

- [ ] **8.** Confirm compatibility assets are explicitly marked and do not override canonical semantics.

**How to verify:**

1. `.cursor/commands/INDEX.yaml` — `linkdev-go`, `linkdev-dispatch`, `wire-linkdev` entries have `status: compatibility-archive` or `not-preferred` tags.
2. `.cursor/templates/INDEX.yaml` — `AGENT-REPORT.md`, `MODULE-README.md`, `COUNCIL-SUMMARY.md` marked optional/compatibility where applicable.
3. `.cursor/rules/00-bootstrap.mdc` — states *"Do not depend on LiNKdev"* (not the reverse).

**Expected outcome:** Legacy commands/templates are labeled; canonical path is clearly preferred.

---

### D.9 — Canonical examples teach read order

- [ ] **9.** Confirm canonical examples still teach the intended read order and command path.

**How to verify:**

1. Read `.cursor/examples/README.md` — confirm read order: INDEX → example dir → INTENT → PROGRAM → MODULE → PHASE → ISSUE → PROOF → REVIEW → INTEGRATION.
2. Open `.cursor/examples/EXAMPLE-BUGFIX/ISSUE.md` — confirm `read_first`, `read_forbidden`, and command usage note (`execute-issue` → `review-issue` → `integrate-issue`).
3. Open `.cursor/examples/INDEX.yaml` — three examples listed with purpose tags.

**Expected outcome:** Examples demonstrate progressive disclosure and command path without requiring a full scan.

---

### D.10 — Supervised real repository test

- [ ] **10.** Run one supervised low-risk real repository test using the current bootstrap and command surfaces.

**This is Phase 2 below.** Do not check this box until the SMALL-CHANGE smoke test completes and the verification report is drafted.

---

## Phase 2 — Stage 1 Smoke Test (SMALL-CHANGE)

**Estimated time:** 20–25 minutes  
**Workspace folder for artifacts:** `core/pilots/stage1-operator-smoke/`  
**Command:** `.cursor/commands/small-change.md` → `.cursor/prompts/execution/SMALL-CHANGE.md`

### Step 2.1 — Bootstrap (5 min)

Follow `.cursor/rules/00-bootstrap.mdc` read order:

1. `.cursor/README.md`
2. `.cursor/rules/00-bootstrap.mdc` (and any other applicable rules you see attached)
3. `.cursor/bootstrap/START-HERE.md` — choose **tiny low-risk change** path
4. `.cursor/commands/INDEX.yaml` — select `small-change`
5. `.cursor/prompts/execution/SMALL-CHANGE.md`
6. Templates: `ISSUE.md`, `PROOF.md`, `REVIEW.md`, `INTEGRATION.md`

**Expected outcome:** You reached the SMALL-CHANGE prompt without scanning unrelated trees. Note in the verification report whether progressive disclosure felt sufficient.

### Step 2.2 — Define the issue (3 min)

Create a compact issue record. Suggested scope (pick one if you have no preference):

| Option | Change | Risk |
|--------|--------|------|
| **A (default)** | Add a "Verification" subsection to `docs/LINKDEVELOPER-STAGE1-CLOSURE.md` linking this runbook and the verification report path | Doc-only, reversible |
| **B** | Add a one-line cross-reference from `core/checklists/wire-checklist.md` to this runbook under Verification | Doc-only |
| **C** | Fix a typo or stale path you noticed during Phase 1 | Doc-only, must still be small |

**Artifact path:** `core/pilots/stage1-operator-smoke/issues/STAGE1-SMOKE-001.md`

Minimum fields (use `.cursor/templates/ISSUE.md` as guide):

- `issue_id`: `STAGE1-SMOKE-001`
- `status`: start `ready`, move through `in_progress` → `review_ready` → `done`
- `objective`, `scope`, `acceptance_criteria` (2–3 bullets)
- `proof_requirements`, `review_requirements`, `integration_requirements`
- `read_first`: list only files needed for the change

**Expected outcome:** Issue is executable immediately (no dependencies).

### Step 2.3 — Execute the change (5 min)

1. Set issue status to `in_progress`.
2. Make the doc change in the repo.
3. Do **not** mark `done` yet.

**Expected outcome:** File diff matches acceptance criteria. Change is small and reviewable in under 2 minutes.

### Step 2.4 — Proof (3 min)

**Artifact path:** `core/pilots/stage1-operator-smoke/proof/STAGE1-SMOKE-001-PROOF.md`

Include:

- What file(s) changed
- Before/after summary (one sentence each)
- How you verified (e.g. opened file, confirmed link resolves)
- Set issue status to `review_ready`

**Expected outcome:** Proof is concrete and non-vacuous. Issue is `review_ready`, not `done`.

### Step 2.5 — Review (3 min)

Act as an independent reviewer (fresh lens or a second Cursor agent).

**Artifact path:** `core/pilots/stage1-operator-smoke/review/STAGE1-SMOKE-001-REVIEW.md`

- Verdict: `pass`, `fail`, or `blocked`
- Reference proof and acceptance criteria
- If `fail`: return to proof step; do not integrate

**Deliberate gate test (optional, +5 min):** Submit intentionally weak proof first, confirm you would verdict `fail`, then correct proof. Skip if time is tight — auth pilot already proved this.

**Expected outcome:** Review verdict `pass` only when proof closes all acceptance criteria.

### Step 2.6 — Integration (3 min)

**Artifact path:** `core/pilots/stage1-operator-smoke/integration/STAGE1-SMOKE-001-INTEGRATION.md`

- Record that the change is integrated
- Note downstream effect (e.g. "closure doc now points operators to runbook")
- Set issue status to `done`

**Expected outcome:** Issue reaches `done` only after proof + passing review + integration record.

### Step 2.7 — Smoke pass criteria

The smoke test **passes** when all are true:

| # | Criterion |
|---|-----------|
| 1 | Bootstrap read order followed `00-bootstrap.mdc` without LiNKdev dependency |
| 2 | SMALL-CHANGE command/prompt was sufficient without `plan-module` |
| 3 | Issue never skipped `review_ready` |
| 4 | Proof, review, and integration are three separate artifacts |
| 5 | Doc change is visible in the working tree |
| 6 | Total smoke time ≤ 25 minutes (or blockers documented) |

---

## Phase 3 — Write the Verification Report (5–10 min)

Fill in `docs/LINKDEVELOPER-STAGE1-VERIFICATION-REPORT.md` using the template in the next section (or create the file from the template if it does not exist yet).

**Required contents:**

1. Date, operator name (Carlos), duration
2. Checkbox results for V1 items 1–10
3. Smoke test path used and pass/fail
4. Artifact paths created under `core/pilots/stage1-operator-smoke/`
5. Blockers or doctrinal gaps (if any)
6. Recommendation: ready for v1.0 tag / not ready (with reasons)

---

## Phase 4 — Optional Authentication Pilot Spot-Check (10 min max)

Only if time remains after Phase 3.

| Step | Path | Look for |
|------|------|----------|
| 1 | `core/pilots/authentication-module-smoke-test/PILOT-REPORT.md` | Overall verdict `pass` |
| 2 | `core/pilots/authentication-module-smoke-test/modules/authentication/MODULE.md` | Module definition of done |
| 3 | `core/pilots/authentication-module-smoke-test/review/AUTH-004-REVIEW-v1.md` | `fail` on insufficient proof |
| 4 | `core/pilots/authentication-module-smoke-test/review/AUTH-004-REVIEW-v2.md` | `pass` after corrected proof |
| 5 | `core/pilots/authentication-module-smoke-test/review/AUTH-MODULE-REVIEW.md` | Module-level review exists |
| 6 | `core/pilots/authentication-module-smoke-test/integration/AUTH-MODULE-INTEGRATION.md` | Module marked complete |

Record spot-check notes in the verification report appendix.

---

## Artifact Path Summary

| Artifact | Path |
|----------|------|
| This runbook | `docs/LINKDEVELOPER-STAGE1-TEST-RUNBOOK.md` |
| Verification report (output) | `docs/LINKDEVELOPER-STAGE1-VERIFICATION-REPORT.md` |
| Smoke issue | `core/pilots/stage1-operator-smoke/issues/STAGE1-SMOKE-001.md` |
| Smoke proof | `core/pilots/stage1-operator-smoke/proof/STAGE1-SMOKE-001-PROOF.md` |
| Smoke review | `core/pilots/stage1-operator-smoke/review/STAGE1-SMOKE-001-REVIEW.md` |
| Smoke integration | `core/pilots/stage1-operator-smoke/integration/STAGE1-SMOKE-001-INTEGRATION.md` |
| Auth pilot (reference) | `core/pilots/authentication-module-smoke-test/` |
| V1 checklist source | `core/reports/V1-READINESS-ASSESSMENT.md` § D |
| Wire checklist | `core/checklists/wire-checklist.md` |
| Bootstrap rule | `.cursor/rules/00-bootstrap.mdc` |

---

## Appendix A — Verification Report Template

Copy the block below into `docs/LINKDEVELOPER-STAGE1-VERIFICATION-REPORT.md` and fill it in after the run.

```markdown
# LiNKdeveloper Stage 1 — Verification Report

**Date:** YYYY-MM-DD  
**Operator:** Carlos  
**Reviewer:** Lisa (optional)  
**Duration:** __ minutes  
**Repository:** /Users/linktrend/Projects/IDE Development  
**Runbook:** docs/LINKDEVELOPER-STAGE1-TEST-RUNBOOK.md

---

## Executive Summary

| Field | Value |
|-------|-------|
| Overall verdict | pass / fail / blocked |
| Smoke test path | SMALL-CHANGE / auth re-validation / other |
| Ready for v1.0 tag | yes / no / yes-with-caveats |
| Ready for Stage 1 final sign-off | yes / no |

One paragraph: what was tested, what passed, what failed.

---

## V1 Readiness Checklist (Section D, Items 1–10)

| # | Item | Result | Notes |
|---|------|--------|-------|
| 1 | Root entrypoints | pass / fail | |
| 2 | Layer indexes discoverable | pass / fail | |
| 3 | Canonical command surface | pass / fail | |
| 4 | Issue = atomic unit | pass / fail | |
| 5 | review_ready mandatory | pass / fail | |
| 6 | Separate proof/review/integration gates | pass / fail | |
| 7 | Module completion semantics | pass / fail | |
| 8 | Compatibility assets marked | pass / fail | |
| 9 | Examples teach read order | pass / fail | |
| 10 | Supervised real repo test | pass / fail | |

---

## Smoke Test Detail

### Path chosen

- [ ] SMALL-CHANGE (recommended)
- [ ] Authentication pilot full re-validation
- [ ] Other: ___________

### Issue executed

- **ID:** STAGE1-SMOKE-001
- **Objective:**
- **Files changed:**

### Artifacts produced

| Gate | Path | Verdict |
|------|------|---------|
| Issue | core/pilots/stage1-operator-smoke/issues/STAGE1-SMOKE-001.md | |
| Proof | core/pilots/stage1-operator-smoke/proof/STAGE1-SMOKE-001-PROOF.md | |
| Review | core/pilots/stage1-operator-smoke/review/STAGE1-SMOKE-001-REVIEW.md | |
| Integration | core/pilots/stage1-operator-smoke/integration/STAGE1-SMOKE-001-INTEGRATION.md | |

### Bootstrap observations

- Progressive disclosure sufficient? yes / no
- LiNKdev dependency encountered? yes / no
- Commands/prompts sufficient without legacy path? yes / no

### Gate discipline

- Issue skipped review_ready? yes / no (must be **no**)
- Proof before review? yes / no
- Review before integration? yes / no
- Done only after all three? yes / no

---

## Wire Checklist Results

| Section | Pass | Notes |
|---------|------|-------|
| Structure | yes / no | |
| Guidance | yes / no | |
| Verification (no LiNKdev runtime dep) | yes / no | |

---

## Blockers and Gaps

| ID | Severity | Description | Recommended action |
|----|----------|-------------|-------------------|
| | critical / important / optional | | |

---

## Authentication Pilot Spot-Check (optional)

| Check | Result | Notes |
|-------|--------|-------|
| PILOT-REPORT verdict | | |
| AUTH-004 proof rejection | | |
| Module-level review/integration | | |

---

## Recommendation

**v1.0 tag:** proceed / defer — reason:

**Stage 1 closure:** confirm / reopen — reason:

**Next operator action:**

---

## Sign-off

| Role | Name | Date | Verdict |
|------|------|------|---------|
| Operator | Carlos | | |
| Reviewer | Lisa | | |
```

---

## Appendix B — Time Budget Guide

| Phase | Target | Stop if over |
|-------|--------|--------------|
| Phase 1 (items 1–9) | 15 min | Skip optional depth; note in report |
| Phase 2 (smoke test) | 20–25 min | Document partial completion |
| Phase 3 (report) | 5–10 min | Required — minimum deliverable |
| Phase 4 (auth spot-check) | 0–10 min | Optional |

**Total:** 30–45 min

---

## Appendix C — Failure Handling

If any item fails:

1. Do **not** check the box.
2. Record exact file path and what was missing in the verification report Blockers table.
3. Continue the runbook if the failure does not block later steps.
4. Item 10 fails if the smoke test does not complete with separate proof, review, and integration.

If bootstrap feels broken (cannot find commands, LiNKdev required, or must scan entire repo):

- Stop the smoke test.
- Mark item 10 `fail`.
- File blocker as **critical** in the verification report.
