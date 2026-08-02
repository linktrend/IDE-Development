# IDE Development — Intent

**Status:** Confirmed Intent for the IDE Development repository itself (this repository), written in the same spirit as a Module 1 confirmed Intent artifact — a plain-English statement of what is being built, why, for whom, and what "done" means. Grounded in the portable managed-core v2 model (version **v2.0.0**; Wave 1 / Issue #43), WP1 production-readiness proof (Issue #67), WP2 lineage + live readiness (Issue #68), and post-WP03 promotion (PR #69/#70/#71). Issue #72 pre-launch cleanup in progress; see `docs/CURRENT-STATUS.md`. Describes what the filesystem + verification scripts deliver, not aspirational Stage 2/3 autonomy language.

**Audience:** The Principal (sole human authority) and any agent or Integrator that needs to understand *why this repository exists* before reading the Technical PRD.

**Companion document:** [`IDE-DEVELOPMENT-TECHNICAL-PRD.md`](./IDE-DEVELOPMENT-TECHNICAL-PRD.md) — exhaustive how-it-works reference.

---

## 1. Problem

LiNKtrend is an AI-native venture studio that builds digital ventures with AI agents doing nearly all day-to-day execution. That model still needs a **shared, human-assisted development operating system** that every product repository can consume:

- Every product needs the same doctrine (laws, gates, proof/review/integration), the same command surface, the same skill catalog, and the same model-routing policy — otherwise each repo invents its own process and quality drifts.
- Agents need a durable, progressive-disclosure knowledge base (`core/`) that is not reinvented per IDE, plus portable Cursor and Codex discovery adapters installed as **physical files** inside each consumer (committed `.ide-development/` managed core — no consumer-to-system checkout symlinks).
- Prior LiNKtrend experiments either coupled factory autonomy into this shared surface (creating identity confusion with the separate LiNKdeveloper Program), left hybrid skills as “reference only,” depended on Mac-local `.cursor` symlinks, or let descriptive docs drift ahead of what the filesystem actually wires.

The problem IDE Development solves is: **give every LiNKtrend product repository one versioned, portable, verified Application Factory operating system — doctrine, artifacts, hybrid skills, model routes, and pipeline gates — that a human Principal plus Cursor/Codex agents can run session-by-session without depending on a persistent autonomous VPS factory or absolute external symlinks.**

---

## 2. Who it is for

| Role | Relationship to IDE Development |
|---|---|
| **Principal (Carlos)** | Sole human authority. Approves Intent + Technical PRD at Module 1 of an application Program, holds Module 6 pre-deploy / Release OK, and reviews briefings when repair budgets exhaust. Does not write code or manage day-to-day execution. |
| **LiNKtrend studio (agent roles)** | Planners, executors, reviewers, and Integrators operate under this repo’s Laws, pipeline validator, and gates when a product repo is wired to this runtime. |
| **Downstream product repositories** | Consumers. They install this system via the portable installer (`scripts/ide-development.py`) as a committed `.ide-development/` tree plus physical Cursor/Codex adapters. Once installed, they hold the product code; this repo holds the shared how-to-build operating system. |
| **LiNKdeveloper (separate Program)** | Sibling, not a runtime dependency. LiNKdeveloper is the VPS-hosted autonomous application factory. It may be *authored* using this system’s guidance like any other product, but it does not depend on IDE Development at runtime. Process-shape parity exists; mechanical runtime parity does not. |

IDE Development is **not** a customer-facing product, **not** the autonomous factory, and **not** a consumer rollout entry. It is the system source and internal self-verification target for LiNKtrend’s shared, human-assisted Application Factory core.

---

## 3. What "done" looks like (repository-level)

This repository is “done enough for daily use” when:

1. **`core/` is the canonical knowledge asset**; `core/managed-core/` is the portable package source; this system repo’s `.cursor/` remains a compatibility authoring surface. Consumers receive physical managed files under `.ide-development/` and physical discovery adapters — not a symlink back to this checkout.
2. Product repos can be **installed or updated** with `scripts/ide-development.py` (`install` / `update` / `plan` / `drift` / `verify` / `version` / `rollback`, plus `release-candidate create|verify` for packaging proof) and then consume the same rules, skills, commands, templates, and execution doctrine. Real consumer mutation remains Principal-gated (WP04 prepared / not executed); WP1 proved disposable/RC installs only.
3. The **fixed six-Module application pipeline** is defined, templated, validated fail-closed (`validate-application-pipeline.mjs`), and enforced by local git hooks when `PIPELINE-STATE.json` is present.
4. **Hybrid skills are physically vendored and hash-verified** (gstack + mattpocock), with command entrypoints under `core/commands/hybrid-*.md` — not stubs and not sibling-path dependencies.
5. **Six model-routing subagents** exist under `.cursor/agents/route-*.md` with Cursor bracket-param model pins, ported from LiNKdeveloper’s router criteria.
6. **Verification passes:** `scripts/verify-ide-development.sh` (and the scripts it invokes) exit 0.

That is **not** the same as: a persistent VPS factory orchestrator, or live product deployment without Module 6 Principal Release OK. **Git** ship/pull/promote (Bugbot review, Integrator merge into `development`, scheduled `development`→`staging`, Principal Telegram Approve for `staging`→`main`) **is** in scope for this system and is inherited by wired repos — see `docs/AUTONOMOUS-GIT-OPERATIONS.md` and ADR 0003.

---

## 4. Scope — inputs and outputs

### Inputs (what IDE Development takes)

- A **Principal / operator** who can open Cursor, answer interview checkpoints, and approve named gates.
- A **target product repository** (or this repo itself) to wire and/or run an application Program against.
- Optional **candidate Intent / PRD-shaped text** for Module 1 entry classification.
- Optional access to **LiNKlibraries** (`https://github.com/linktrend/LiNKlibraries.git`) for Module 2 library query and Module 5 contribution.
- Hybrid gstack/mattpocock skills as already-vendored, adapted copies under `core/runtime/skills/` (not sibling-repo dependencies).

### Outputs (what IDE Development produces)

- An **installable operating system** (managed core + Cursor/Codex adapters) that product repos share as physical committed files.
- For each application Program in a target repo: durable artifacts under `docs/development/<program-id>/` (Intent, Technical PRD, Technical Design, Program, Module trees, `PIPELINE-STATE.json`, proof manifest).
- **Proof → independent review → integration** artifacts for Issues, plus Module gates.
- Optional **Library contribution PRs** into LiNKlibraries (Librarian merges; this client does not self-merge).
- A **verified hybrid skill surface** (vendored gstack/mattpocock + local domain skills + Module composite skills under `runtime/skills/linktrend/`).

### Explicit out of scope (deliberate — not forgotten)

| Out of scope | Why / status |
|---|---|
| Be the autonomous VPS factory | That is **LiNKdeveloper**. This repo stays human-assisted / session-scoped. |
| Persist a Program Ledger / poll loop | No Postgres Ledger, no unattended crash recovery, no heartbeat. State lives in repo artifacts + `PIPELINE-STATE.json`. |
| Mandatory Starter Kit / environment_bootstrap Module | LiNKdeveloper has seven Modules including `environment_bootstrap`. IDE Development has **six** Modules; Starter Kit is optional; light git/CI sanity is not a seventh Module. |
| Automatic **product live deploy** without Principal | Module 6 ends at `release_ready` with **Principal pre-deploy / Release OK**. Git branch promote is separate (ADR 0003). |
| Own product-specific factory operations | Website/automation/content factory ops belong in each product’s own specification — not in this shared core. |
| Decide which venture to build | Intent comes from the Principal / studio strategy. |
| Ship a Principal phone/web approval dashboard | Operator surface is Cursor + this Operations Manual. |
| Depend on LiNKdeveloper at runtime | Independence is intentional. Route criteria are *ported*, not live-imported. |
| Claude Code as a supported runtime | **Excluded.** Outside current v2 support and roadmap. Historical packaging archived under `docs/archive/platform-entrypoints/claude/`; no new Claude entrypoints. |
| Nested self-install into this repository | IDE Development is system source / self-verification only — not a consumer rollout target. |
| Real consumer rollout before WP04 Principal approval | Deferred. Inventory + order live in `docs/GITOPS-CONSUMER-ROLLOUT.md`; each consumer needs separate Principal approval. WP04 packet is prepared / not executed (`docs/work-packets/2026-08-02-work-packet-04-consumer-rollout.md`). |
| Git tag / GitHub Release as part of WP1 | WP1 may build a release-candidate **archive** for proof; tag/Release publication remains separately approval-gated (not claimed by WP03 tree promotion alone). |

---

## 5. Guiding governance principles

Full law text lives in `core/execution/CANONICAL-LAWS.md` (20 laws). Spirit for operators:

1. **The Issue is the atomic executable unit** — Modules/Phases organize; Issues execute (Laws 1–2).
2. **Readiness is computed, not declared** — dependencies and gates must actually be satisfied (Law 4).
3. **Completion requires non-vacuous proof** — confidence is not evidence (Laws 9–10).
4. **Review is separate from execution; integration is separate from review; release is separate from integration** (Laws 12–14).
5. **Quality gates stop progression** — fail-closed validator; no warn-only mode for application pipeline transitions (Law 16).
6. **Progressive disclosure** — read only what the current unit needs (Law 19).
7. **Tool-independent doctrine** — Laws live in artifacts so Cursor/Codex/future tools can share them (Law 20).
8. **Human gates where judgment must stay human** — Module 1 Intent + Technical PRD approval; Module 6 Principal Release OK.

---

## 6. Success criteria

| Criterion | Evidence that counts |
|---|---|
| Shared core is installable | `scripts/ide-development.py` installs physical `.ide-development/` + Cursor/Codex adapters into a disposable/approved consumer; no outbound checkout symlink |
| Doctrine is live | `core/execution/*` cited by commands, rules, and validator |
| Hybrid skills are real | Vendored trees + `VENDOR-MANIFEST.json` hashes; `verify-vendored-skills.sh` passes |
| Pipeline is fail-closed | Validator + pre-commit/pre-push hooks reject invalid `PIPELINE-STATE.json` |
| Model routing is wired | Six `route-*.md` agents with bracket-param pins |
| Verification is green | `scripts/verify-ide-development.sh` ALL CHECKS PASSED |
| Live autonomous factory | **Not claimed.** That is LiNKdeveloper’s job. |

---

## 7. Relationship to other documents

| Document | Role |
|---|---|
| `docs/CURRENT-STATUS.md` | Concise current status / launch readiness (post-WP03 / pre-WP04). |
| `docs/OPEN-ISSUES.md` | Append-only engineering history and open/deferred items. Prefer `docs/CURRENT-STATUS.md` for what is true now. |
| `docs/BUILD-LOG.md` | Active Work Packet build log (WP1+). |
| `docs/runbooks/` · `docs/acceptance/` | Operator release-candidate / rollback runbooks and acceptance matrix. |
| `docs/IDE-DEVELOPMENT-TECHNICAL-PRD.md` | Exhaustive technical reference for how the system works. |
| `docs/IDE-DEVELOPMENT-OPERATIONS-MANUAL.md` | Plain-English handbook for the Principal. |
| `docs/GITOPS-CONSUMER-ROLLOUT.md` | Consumer inventory; rollout = WP04 (approval pending / not executed). |
| `docs/work-packets/2026-08-02-work-packet-04-consumer-rollout.md` | WP04 prepared packet — no mutation until Principal approval. |
| `docs/HYBRID-SKILLS-REGISTRY.md` | Live operational map of gstack/mattpocock commands (kept because verify + command entrypoints cite it). |
| `core/execution/*` | Operative doctrine (Laws, runtime model, autonomous module behavior, application pipeline). **Not archived.** |
| `docs/ARCHIVE-INDEX.md` + `docs/archive/` | Retired systems and superseded descriptive docs. |
| LiNKdeveloper Intent / Technical PRD / Operations Manual | Sibling Program docs — process-shape reference, not authority over this repo. |

---

## 8. One-sentence Intent

**IDE Development is LiNKtrend’s shared, human-assisted Application Factory operating system: a versioned portable managed core that installs into product repos as physical files so every consumer shares one doctrine, one six-Module pipeline, vendored hybrid skills, pinned model routes, and fail-closed gates — so the Principal approves Intent and release while agents execute the rest session-by-session in Cursor/Codex.**
