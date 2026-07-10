# LiNKdeveloper Workspace — Operator Guide

**Audience:** Carlos (Principal)  
**Date:** 2026-07-10  
**Status:** Active

This guide explains how to open the LiNKdeveloper workspace, how the development system works, and what you do versus what the AI agents do. No technical setup knowledge is required to follow it.

---

## 1. What this workspace is

**LiNKdeveloper** lives in the folder called `IDE Development` on your Mac. It is the unified development system you use to plan and build venture software with AI assistance.

The saved workspace file **LiNKdeveloper** groups the system repo together with the product repos you are actively working on. Add product repos to the workspace when you need them.

**IDE Development** is the system — rules, skills, templates, and doctrine that agents follow. Product repos hold the actual code and content being built.

GitHub names stay unchanged: the repo is still `linktrend/IDE-Development`. The local folder name stays `IDE Development`.

The LiNKdeveloper system combines three sources into one runtime: the IDE Development core (rules, commands, skills, templates), macro-orchestration patterns from gstack (spec, plan review, health checks, shipping), and micro-execution patterns from mattpocock/skills (clarification, PRD generation, issue slicing, TDD, debugging). You operate one system — not separate tiers or layers.

---

## 2. How to open the workspace in Cursor

1. Open **Cursor**.
2. Go to **File → Open Workspace from File…**
3. Select:

   ```
   ~/Projects/Workspaces/LiNKdeveloper.code-workspace
   ```

4. If Cursor already has the workspace open but folders look stale, use **File → Reload Window**.

**What you should see:** at minimum, `IDE Development` in the sidebar. `IDE Development` is always the system repo — start there when you open a new chat or session about how work should run.

---

## 3. How the system repo and product repos connect

### IDE Development is the system

Everything agents need to behave consistently — rules, commands, skills, templates, execution doctrine — is stored in **IDE Development**:

- **`core/`** — canonical knowledge (the master copy)
- **`.cursor/`** — what Cursor reads at runtime (mostly symlinks back into `core/`)

When you improve the system, edits usually go into `core/` and flow through to `.cursor/` automatically.

### Product repos adopt the system via symlink

Each product repo can share the same runtime by pointing its local `.cursor` folder at the system:

```
ProductRepo/.cursor  →  ../IDE Development/.cursor  →  ../IDE Development/core
```

This is a **one-time wiring step**, not something you do every session. Full procedure: `core/workspace/REPO-WIRING.md` and `core/workspace/WORKSPACE-ADOPTION.md`.

**Rules of thumb:**

- Do **not** copy the whole system into each product repo when a symlink is enough.
- Always inspect an existing `.cursor` before replacing it — some repos have local rules worth keeping.
- Back up replaceable material before changing anything.

---

## 4. Starting a session — what to read first

When you or an agent starts work, read these in order (agents follow the same list automatically):

1. **`README.md`** (repo root) — what this repository is and how it is structured
2. **`.cursor/rules/00-bootstrap.mdc`** — mandatory read order and operating rules for every task
3. **`.cursor/skills/SKILLS_CATALOG.md`** — which skill to use for a given kind of work

After that, read **only what the current task needs** — a specific command file, template, or doctrine doc. Do not scan the entire system unless the task genuinely requires it.

For a fast path when the task is already clear, agents may also use `.cursor/bootstrap/QUICKSTART.md`.

---

## 5. Your primary workflow — three triggers

Your work always starts with one of three triggers. **Choosing application versus factory is not a separate trigger** — it is a decision made inside each trigger, after the spec or PRD is clear.

### Trigger 1: New idea

You have a product concept but no written spec yet.

1. **Interview** — work with an agent to explore the idea, constraints, and success criteria.
2. **Spec or PRD** — the agent produces a written specification or product requirements document.
3. **You approve** — you review and approve the spec/PRD before development begins. This is your primary human gate.
4. **Route and develop** — based on what the product is:
   - **Normal application** — scaffold from the LiNKapps starter kit at `/Users/linktrend/Projects/LiNKapps`, then develop.
   - **Factory product** — agents use `docs/FACTORY-OPERATIONS-BLUEPRINT.md` as the planning reference for how the factory should operate, then develop.

### Trigger 2: PRD in hand

You already have a product requirements document (from you, a stakeholder, or a prior session).

1. **Clarify gaps** — the agent reads the PRD, asks targeted questions, and fills missing detail.
2. **You approve** — you confirm the clarified spec/PRD is acceptable.
3. **Route and develop** — same application-or-factory decision as Trigger 1, then build.

### Trigger 3: Existing software

You have working code that needs work — refactor, finish incomplete features, customize, or extend.

1. **Assess** — the agent inspects the codebase and states what exists, what is missing, and what risks apply.
2. **Plan** — for larger changes, the agent proposes a short plan; you approve if direction is unclear or high-impact.
3. **Develop** — implement, test, and deliver. Factory products still reference the Factory Operations blueprint when operational behavior is in scope.

### Application versus factory — one short note

**Normal applications** start from the LiNKapps starter kit at `/Users/linktrend/Projects/LiNKapps`. **Factory products** (revenue production lines such as website, automation, or content factories) use `docs/FACTORY-OPERATIONS-BLUEPRINT.md` as a planning reference for agents — it describes how factory operations should eventually run autonomously. That blueprint is design-only until you explicitly start factory ops work; agents consult it when building or extending a factory, not when building a standard app.

---

## 6. Human gate points — where you approve

Agents do most of the detailed work. **You** hold the gates that matter for direction and release.

### You approve (human gates)

- **Spec / PRD approval** — Is the written product intent and requirements document acceptable before serious development begins?
- **Program gate** — Is the program plan and scope right before large autonomous execution runs? (Applies when work is organized as a formal program.)
- **Module gate** — Is the module decomposition right before agents execute a module end-to-end?
- **Launch / release gate** — Is integrated work ready to ship or go live?

When an agent reaches one of these gates, it should stop and present the artifact for your decision — not assume approval.

### Agents handle (with your oversight available)

- Issue implementation and proof collection
- Independent review — checks proof against acceptance criteria, not gut feel
- Integration recording — only after review passes

**Key rule:** readiness is computed from artifacts and state, not assumed. Every issue must pass through **review-ready** before integration. Review inspects **proof**, not confidence.

If something feels wrong at any point, you can stop, redirect, or reject — that is the intended operating model.

---

## 7. Skills — installed hybrid stack

Skills live in `.cursor/skills/SKILLS_CATALOG.md`. Agents read the catalog first, then open only the skill needed for the task.

LiNKdeveloper combines three installed sources into one runtime:

- **Local domain skills** in this repository — APIs, UI, deployment execution, routing, and governance (40 skills after hybrid sunset).
- **gstack (macro)** — cloned at `/Users/linktrend/Projects/gstack`, fork https://github.com/linktrend/gstack. Handles spec, plan review, health checks, shipping verdicts, and session context.
- **mattpocock/skills (micro)** — cloned at `/Users/linktrend/Projects/skills`, fork https://github.com/linktrend/skills. Handles PRD clarification, issue slicing, TDD, debugging, and architecture improvement.

All three are wired and active — not reference-only. Agents route through your three triggers to the right hybrid or domain skill without you choosing skill names. Registry: `docs/HYBRID-SKILLS-REGISTRY.md`.

To extend the system later, add domain skills under `core/skills/`, update the catalog and registry, and run a supervised low-risk test before relying on changes for production work.

---

## 8. Factory operations blueprint — planning reference

`docs/FACTORY-OPERATIONS-BLUEPRINT.md` is a **planning document only** — not live factory infrastructure. Its banner states: no Supabase, LiNKbrain, LiNKskills, or factory infrastructure in that blueprint is built until you explicitly start factory ops work.

Use it when the product is a **factory** (continuous production line). It describes the common operations skeleton — trigger, program, module, stage, issue, run, gate, output, complete — shared by website, automation, and content factories. Agents consult it when designing or building factory behavior; you do not operate it as a day-to-day control panel.

The **Application Factory workflow** (this guide, IDE Development commands, and the development lifecycle) is separate from factory **operations**. Development builds software; factory operations run production lines once built.

---

## 9. Quick reference

### Open workspace

```
~/Projects/Workspaces/LiNKdeveloper.code-workspace
```

### Session start reads

1. `README.md`
2. `.cursor/rules/00-bootstrap.mdc`
3. `.cursor/skills/SKILLS_CATALOG.md`

### Your three triggers

1. **New idea** → interview → spec/PRD → you approve → app or factory → develop
2. **PRD in hand** → clarify gaps → you approve → app or factory → develop
3. **Existing software** → assess → plan (if needed) → develop

### You approve

Spec/PRD · Program gates · Module gates · Launch/release

### Key docs

- Stage 1 overview — `docs/LINKDEVELOPER-STAGE1.md`
- Stage 1 closure — `docs/LINKDEVELOPER-STAGE1-CLOSURE.md`
- Hybrid skills registry — `docs/HYBRID-SKILLS-REGISTRY.md`
- Workspace adoption — `core/workspace/WORKSPACE-ADOPTION.md`
- Repo wiring — `core/workspace/REPO-WIRING.md`
- Factory operations (planning) — `docs/FACTORY-OPERATIONS-BLUEPRINT.md`
- Command index (agents) — `.cursor/commands/INDEX.yaml`

---

## 10. What Stage 2 is (and is not)

**LiNKdeveloper Stage 2** is a separate repository (`/Users/linktrend/Projects/LiNKdeveloper`) designed for fully autonomous orchestration. It is **reference only** during Stage 1 — do not add it to the workspace or depend on it for daily work.

Your operating surface is this workspace, the three triggers above, and your approval at the gates in Section 6.

---

## Appendix A — Internal commands (agents, not your primary UI)

Cursor commands under `.cursor/commands/` are **agent entry points** for structured execution inside IDE Development. You do not type these as your primary workflow — you use natural language and the three triggers in Section 5. Agents invoke commands when the task fits.

**Primary commands:**

- **`plan-program`** — new product idea or objective; produces validated intent, program artifact, and initial module structure
- **`plan-module`** — program exists; breaks a module into phases and issues with dependencies and acceptance criteria
- **`complete-module`** — module is planned; recursive execution through proof, review, and integration until done or blocked
- **`execute-issue`** — one issue ready to implement; code/work output plus proof artifact
- **`review-issue`** — issue has proof; independent review verdict (pass, fail, or blocked)
- **`integrate-issue`** — review passed; integration record and updated downstream readiness

**Typical agent flow:**

```
plan-program  →  plan-module  →  complete-module
                                      ↓
                              execute-issue  →  review-issue  →  integrate-issue
```

**`small-change`** handles tiny, low-risk fixes that still need proof, review, and integration but not full program or module planning.

Command definitions live under `.cursor/commands/`. Index: `.cursor/commands/INDEX.yaml`.
