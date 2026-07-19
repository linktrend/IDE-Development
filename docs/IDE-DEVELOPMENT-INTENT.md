# IDE Development — Intent

**Status:** Confirmed Intent for the IDE Development repository itself (this repository), written in the same spirit as a Module 1 confirmed Intent artifact — a plain-English statement of what is being built, why, for whom, and what "done" means. Grounded in what the filesystem, verification scripts, and git history actually deliver today (through 2026-07-19), not in aspirational Stage 2/3 autonomy language.

**Audience:** The Principal (sole human authority) and any agent or Integrator that needs to understand *why this repository exists* before reading the Technical PRD.

**Companion document:** [`IDE-DEVELOPMENT-TECHNICAL-PRD.md`](./IDE-DEVELOPMENT-TECHNICAL-PRD.md) — exhaustive how-it-works reference.

---

## 1. Problem

LiNKtrend is an AI-native venture studio that builds digital ventures with AI agents doing nearly all day-to-day execution. That model still needs a **shared, human-assisted development operating system** that every product repository can consume:

- Every product needs the same doctrine (laws, gates, proof/review/integration), the same command surface, the same skill catalog, and the same model-routing policy — otherwise each repo invents its own process and quality drifts.
- Agents need a durable, progressive-disclosure knowledge base (`core/`) that is not reinvented per IDE, plus a Cursor-compatible runtime surface (`.cursor/`) that product repos can adopt via symlink.
- Prior LiNKtrend experiments either coupled factory autonomy into this shared surface (creating identity confusion with the separate LiNKdeveloper Program), left hybrid skills as “reference only,” or let descriptive docs drift ahead of what the filesystem actually wires.

The problem IDE Development solves is: **give every LiNKtrend product repository one installable, verified Application Factory operating system — doctrine, artifacts, hybrid skills, model routes, and pipeline gates — that a human Principal plus Cursor/Codex agents can run session-by-session without depending on a persistent autonomous VPS factory.**

---

## 2. Who it is for

| Role | Relationship to IDE Development |
|---|---|
| **Principal (Carlos)** | Sole human authority. Approves Intent + Technical PRD at Module 1 of an application Program, holds Module 6 pre-deploy / Release OK, and reviews briefings when repair budgets exhaust. Does not write code or manage day-to-day execution. |
| **LiNKtrend studio (agent roles)** | Planners, executors, reviewers, and Integrators operate under this repo’s Laws, pipeline validator, and gates when a product repo is wired to this runtime. |
| **Downstream product repositories** | Consumers. They install this system via `.cursor` → IDE Development symlink (`scripts/wire-repo.sh`). Once wired, they hold the product code; this repo holds the shared how-to-build operating system. |
| **LiNKdeveloper (separate Program)** | Sibling, not a runtime dependency. LiNKdeveloper is the VPS-hosted autonomous application factory. It may be *authored* using this repo’s `.cursor` surface like any other product, but it does not depend on IDE Development at runtime. Process-shape parity exists; mechanical runtime parity does not. |

IDE Development is **not** a customer-facing product and **not** the autonomous factory. It is LiNKtrend’s shared, human-assisted Application Factory core.

---

## 3. What "done" looks like (repository-level)

This repository is “done enough for daily use” when:

1. **`core/` is the canonical knowledge asset** and `.cursor/` is a working compatibility runtime (mostly symlinks into `core/`, plus Cursor-only adapter files such as `rules/` and `mcp.json`).
2. Product repos can be **wired once** with `scripts/wire-repo.sh` and then consume the same rules, skills, commands, templates, and execution doctrine.
3. The **fixed six-Module application pipeline** is defined, templated, validated fail-closed (`validate-application-pipeline.mjs`), and enforced by local git hooks when `PIPELINE-STATE.json` is present.
4. **Hybrid skills are physically vendored and hash-verified** (gstack + mattpocock), with command entrypoints under `core/commands/hybrid-*.md` — not stubs and not sibling-path dependencies.
5. **Six model-routing subagents** exist under `.cursor/agents/route-*.md` with Cursor bracket-param model pins, ported from LiNKdeveloper’s router criteria.
6. **Verification passes:** `scripts/verify-ide-development.sh` (and the scripts it invokes) exit 0.

That is **not** the same as: a persistent autonomous orchestrator, Telegram executive routing, live VPS deployment of this system, or automatic `development` → `staging` → `main` promotion of *product* work without Principal Release OK. Those belong elsewhere (chiefly LiNKdeveloper) or remain deliberately deferred.

---

## 4. Scope — inputs and outputs

### Inputs (what IDE Development takes)

- A **Principal / operator** who can open Cursor, answer interview checkpoints, and approve named gates.
- A **target product repository** (or this repo itself) to wire and/or run an application Program against.
- Optional **candidate Intent / PRD-shaped text** for Module 1 entry classification.
- Optional access to **LiNKlibraries** (`https://github.com/linktrend/LiNKlibraries.git`) for Module 2 library query and Module 5 contribution.
- Optional local clones of upstream hybrid skill sources when refreshing the vendor (`scripts/vendor-hybrid-skills.sh`).

### Outputs (what IDE Development produces)

- An **installable operating system** (`core/` + `.cursor/`) that product repos share.
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
| Automatic product promotion without Principal | Module 6 ends at `release_ready` with **Principal pre-deploy / Release OK**. No LAW-06 auto-promotion here. |
| Own product-specific factory operations | Website/automation/content factory ops belong in each product’s own specification — not in this shared core. |
| Decide which venture to build | Intent comes from the Principal / studio strategy. |
| Ship a Principal phone/web approval dashboard | Operator surface is Cursor + this Operations Manual. |
| Depend on LiNKdeveloper at runtime | Independence is intentional. Route criteria are *ported*, not live-imported. |

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
| Shared core is installable | `scripts/wire-repo.sh` wires a consumer; `.cursor` resolves into this repo’s surface |
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
| `docs/OPEN-ISSUES.md` | Append-only build log — what was verified, deferred, and limited. Prefer over stale prose elsewhere. |
| `docs/IDE-DEVELOPMENT-TECHNICAL-PRD.md` | Exhaustive technical reference for how the system works. |
| `docs/IDE-DEVELOPMENT-OPERATIONS-MANUAL.md` | Plain-English handbook for the Principal. |
| `docs/HYBRID-SKILLS-REGISTRY.md` | Live operational map of gstack/mattpocock commands (kept because verify + command entrypoints cite it). |
| `core/execution/*` | Operative doctrine (Laws, runtime model, autonomous module behavior, application pipeline). **Not archived.** |
| `docs/ARCHIVE-INDEX.md` + `docs/archive/` | Retired systems and superseded descriptive docs. |
| LiNKdeveloper Intent / Technical PRD / Operations Manual | Sibling Program docs — process-shape reference, not authority over this repo. |

---

## 8. One-sentence Intent

**IDE Development is LiNKtrend’s shared, human-assisted Application Factory operating system: a `core/` + `.cursor/` install that wires product repos to one doctrine, one six-Module pipeline, vendored hybrid skills, pinned model routes, and fail-closed gates — so the Principal approves Intent and release while agents execute the rest session-by-session in Cursor/Codex.**
