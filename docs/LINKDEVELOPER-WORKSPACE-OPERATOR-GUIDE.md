# LiNKdeveloper Workspace — Operator Guide

**Audience:** Carlos (Principal)  
**Date:** 2026-07-10  
**Status:** Active — Stage 1 complete

This guide explains how to open the LiNKdeveloper workspace, how the shared development system works, and what you do versus what the AI agents do. No technical setup knowledge is required to follow it.

---

## 1. What this workspace is

**LiNKdeveloper Stage 1** lives in the folder called `IDE Development` on your Mac. It is the semi-manual **Application Factory** — the system you use to plan and build venture applications with AI assistance.

The saved workspace file **`LiNKdeveloper`** groups the system repo together with the product repos you are actively working on (for example, LiNKsites for the Website Factory).

| Folder in workspace | Role |
|---|---|
| **IDE Development** | The system — rules, commands, skills, templates, and doctrine |
| **LiNKsites** (and others you add later) | Product repos — the actual code and content being built |

GitHub names stay unchanged: the repo is still `linktrend/IDE-Development`. The local folder name stays `IDE Development`.

---

## 2. How to open the workspace in Cursor

1. Open **Cursor**.
2. Go to **File → Open Workspace from File…**
3. Select:

   ```
   ~/Projects/Workspaces/LiNKdeveloper.code-workspace
   ```

4. If Cursor already has the workspace open but folders look stale, use **File → Reload Window**.

**What you should see:** at minimum, `IDE Development` and `LiNKsites` in the sidebar. `IDE Development` is always the system repo — start there when you open a new chat or session about how work should run.

**If the workspace file does not exist yet:** create it once by opening `IDE Development` in Cursor, adding the folders you need via **File → Add Folder to Workspace…**, then saving with **File → Save Workspace As…** as `LiNKdeveloper` under `~/Projects/Workspaces/`.

---

## 3. How the system repo and product repos connect

### IDE Development is the system

Everything agents need to behave consistently — rules, commands, skills, templates, execution doctrine — is stored in **IDE Development**:

- **`core/`** — canonical knowledge (the master copy)
- **`.cursor/`** — what Cursor reads at runtime (mostly symlinks back into `core/`)

When you improve the system, edits usually go into `core/` and flow through to `.cursor/` automatically.

### Product repos adopt the system via symlink

Each product repo (LiNKsites, LiNKapps, etc.) can share the same runtime by pointing its local `.cursor` folder at the system:

```
LiNKsites/.cursor  →  ../IDE Development/.cursor  →  ../IDE Development/core
```

This is a **one-time wiring step**, not something you do every session. Full procedure: `core/workspace/REPO-WIRING.md` and `core/workspace/WORKSPACE-ADOPTION.md`.

**Rules of thumb:**

- Do **not** copy the whole system into each product repo when a symlink is enough.
- Always inspect an existing `.cursor` before replacing it — some repos have local rules worth keeping.
- Back up replaceable material before changing anything.

**Important for this mission:** LiNKsites is **not** symlinked yet. See Section 8.

---

## 4. Starting a session — what to read first

When you or an agent starts work, read these in order (agents follow the same list automatically):

| Order | File | Why |
|---|---|---|
| 1 | `README.md` (repo root) | What this repository is and how it is structured |
| 2 | `.cursor/rules/00-bootstrap.mdc` | Mandatory read order and operating rules for every task |
| 3 | `.cursor/skills/SKILLS_CATALOG.md` | Which skill to use for a given kind of work |

After that, read **only what the current task needs** — a specific command file, template, or doctrine doc. Do not scan the entire system unless the task genuinely requires it.

**Do not depend on:** chat memory, IDE memory, or the old **LiNKdev** system. LiNKdev is abandoned legacy.

For a fast path when the task is already clear, agents may also use `.cursor/bootstrap/QUICKSTART.md`.

---

## 5. The command surface — how work gets done

Commands are entry points in Cursor chat. Type or invoke them when you want structured agent behavior. The six primary commands for Stage 1:

| Command | When to use it | What you get |
|---|---|---|
| **`plan-program`** | You have a new product idea or objective | Validated intent, a program artifact, and initial module structure |
| **`plan-module`** | A program exists and you need to break a module into phases and issues | Module, phase, and issue artifacts with dependencies and acceptance criteria |
| **`complete-module`** | A module is planned and you want it executed end-to-end | Recursive execution through proof, review, and integration until the module is done or blocked |
| **`execute-issue`** | One issue is ready to implement | Code/work output plus a proof artifact; issue moves to review-ready or blocked |
| **`review-issue`** | An issue has proof and needs an independent check | A review verdict (pass, fail, or blocked) with findings |
| **`integrate-issue`** | Review passed and work should be recorded as accepted | Integration record and updated downstream readiness |

**Typical flow:**

```
plan-program  →  plan-module  →  complete-module
                                      ↓
                              execute-issue  →  review-issue  →  integrate-issue
```

There is also **`small-change`** for tiny, low-risk fixes that still need proof, review, and integration — but do not need full program or module planning.

Command definitions live under `.cursor/commands/`. Index: `.cursor/commands/INDEX.yaml`.

**Legacy commands** (`linkdev-go`, `wire-linkdev`, etc.) exist for backward compatibility only. Do not use them for new work.

---

## 6. Human gate points — where you approve

Stage 1 is **semi-manual**. Agents do most of the issue-level work; **you** hold the gates that matter for direction and release.

### You approve (human gates)

| Gate | What you are deciding |
|---|---|
| **Program gate** | Is the product intent and program plan acceptable before serious technical work begins? |
| **Module gate** | Is the module decomposition and scope right before autonomous execution runs? |
| **Blueprint / architecture approval** | Is the product blueprint and technical approach approved? (First hard governance boundary before architecture work.) |
| **Launch / release gate** | Is integrated work ready to ship or go live? |

When an agent reaches one of these gates, it should stop and present the artifact for your decision — not assume approval.

### Agents handle (with your oversight available)

| Step | Who |
|---|---|
| Issue implementation | Agent (via `execute-issue`) |
| Proof collection | Agent |
| Independent review | Agent reviewer role (via `review-issue`) — checks proof against acceptance criteria, not gut feel |
| Integration recording | Agent (via `integrate-issue`) — only after review passes |

**Key rule:** readiness is computed from artifacts and state, not assumed. Every issue must pass through **review-ready** before integration. Review inspects **proof**, not confidence.

If something feels wrong at any point, you can stop, redirect, or reject — that is the intended operating model for Stage 1.

---

## 7. Skills — what is installed vs. reference only

### Layer 1 — installed and active

The skills listed in `.cursor/skills/SKILLS_CATALOG.md` are **local skills** in this repository. Agents read the catalog first, then open only the skill needed for the task. Examples: `intelligent-routing`, `frontend-ui-engineering`, `browser-qa`, `release-readiness`.

These are ready to use today inside the LiNKdeveloper workspace.

### Layer 2 and Layer 3 — reference only, not installed

Two external skill libraries are **mapped in planning documents but not vendored or installed** in Stage 1:

| Layer | Source | Purpose (when installed later) |
|---|---|---|
| **Layer 2** | [`garrytan/gstack`](https://github.com/garrytan/gstack) | Macro-orchestration: spec, plan review, health checks, shipping, context save/restore |
| **Layer 3** | [`mattpocock/skills`](https://github.com/mattpocock/skills) | Micro-execution: clarification, PRD generation, issue slicing, TDD, debugging |

**They are not active in your workspace today.** Agents should not assume `/spec`, `/ship`, `/tdd`, or similar Layer 2/3 commands exist.

**Naming note:** Three existing skills (`release-readiness`, `browser-qa`, `retrospective-learning`) were originally mined from an **internal** LiNKdev folder also called "gstack". That is **not** the same as `garrytan/gstack`. Those skills are labeled `LiNKdev-internal-gstack` in their provenance to avoid confusion.

### How to add Layer 2/3 later (when you decide)

This is future work — not part of Stage 1 closure:

1. Review the layered skills map in `docs/LINKDEVELOPER-STAGE1A-SPEC.md` (Section C).
2. Vendor or install the external packages into an approved location under `core/skills/` or a dedicated adapter path.
3. Register new entries in `SKILLS_CATALOG.md` with clear layer labels.
4. Wire command routing so Layer 2/3 skills complement — not replace — the existing command surface.
5. Run a supervised low-risk test before relying on them for production work.

Until then, treat Layer 2/3 as **read-only reference** for design decisions.

---

## 8. LiNKsites `.cursor` — backup exists, no symlink yet

LiNKsites has its **own copied `.cursor`** folder with a mix of:

- LiNKsites-specific rules (foundation, sites/apps, UI policy, release/deploy)
- Generic rules that do not yet exist in IDE Development (quality, testing, agent behavior, troubleshooting)
- Legacy LiNKdev commands and references

**What was done:**

- A full backup was saved to `docs/adoption-backups/LiNKsites/.cursor-backup-20260710/` (21 files).
- **No symlink was applied** — a blind symlink would have overwritten repo-specific rules.

**What this mission does not do:**

- Symlink LiNKsites `.cursor` to IDE Development
- Delete LiNKsites local rules without a selective merge plan

**Your decision (pending):** selective merge — keep LiNKsites-specific rules local; adopt shared system paths only where it is safe. Details: `docs/LINKSITES-FACTORY-SETUP-REPORT.md`.

---

## 9. Factory operations blueprint — planning only, not active now

There are **two different blueprints**. Do not mix them up.

| Blueprint | Applies to | Status in Stage 1 |
|---|---|---|
| **Application Factory** (LiNKdeveloper Stage 1) | Building venture apps — the workflow in this guide | **Active** — use the commands in Section 5 |
| **Factory Operations Common Blueprint** | Website, Automation, and Content factories — continuous production lines | **Planning document only** — not active implementation |

The Factory Operations blueprint (`docs/FACTORY-OPERATIONS-BLUEPRINT.md`) describes how revenue factories will eventually run autonomously:

```
Trigger → Program → Module → Stage → Issue → Run → Gate → … → Output → Complete
```

That spine, factory controller triggers, Postgres ledger, and OpenClaw orchestrator are **future factory build work**. Stage 1 gives you the development workflow and workspace; the operations blueprint tells agents what to build next — it is not something you operate today.

**Next product work:** finish the Website Factory under that blueprint, starting with a LiNKsites workflow variant spec. See `docs/LINKDEVELOPER-STAGE1-CLOSURE.md`.

---

## 10. Quick reference

### Open workspace

```
~/Projects/Workspaces/LiNKdeveloper.code-workspace
```

### Session start reads

1. `README.md`
2. `.cursor/rules/00-bootstrap.mdc`
3. `.cursor/skills/SKILLS_CATALOG.md`

### Primary commands

`plan-program` · `plan-module` · `complete-module` · `execute-issue` · `review-issue` · `integrate-issue`

### You approve

Program gates · Module gates · Blueprint/architecture · Launch/release

### Do not do in this mission

- Symlink LiNKsites `.cursor`
- Install `garrytan/gstack` or `mattpocock/skills`
- Operate the Factory Operations blueprint as if it were live

### Key docs

| Topic | Path |
|---|---|
| Stage 1 overview | `docs/LINKDEVELOPER-STAGE1.md` |
| Stage 1 closure | `docs/LINKDEVELOPER-STAGE1-CLOSURE.md` |
| Workspace adoption | `core/workspace/WORKSPACE-ADOPTION.md` |
| Repo wiring | `core/workspace/REPO-WIRING.md` |
| LiNKsites setup status | `docs/LINKSITES-FACTORY-SETUP-REPORT.md` |
| Factory operations (future) | `docs/FACTORY-OPERATIONS-BLUEPRINT.md` |
| Command index | `.cursor/commands/INDEX.yaml` |

---

## 11. What Stage 2 is (and is not)

**LiNKdeveloper Stage 2** is a separate repository (`/Users/linktrend/Projects/LiNKdeveloper`) designed for fully autonomous orchestration. It is **reference only** during Stage 1 — do not add it to the workspace or depend on it for daily work.

Stage 1 is complete. Your operating surface is this workspace, these commands, and your approval at the gates above.
