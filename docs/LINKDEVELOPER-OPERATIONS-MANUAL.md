# LiNKdeveloper Operations Manual

**Audience:** Carlos (Principal) and future OpenClaw operators  
**Date:** 2026-07-10  
**Status:** Active — Stage 1 operational; Stage 2/3 in preparation

This manual is the canonical operator reference for LiNKdeveloper. It replaces the workspace operator guide for day-to-day use.

---

## 1. System identity

**LiNKdeveloper is IDE Development.** The local folder is `IDE Development` at `/Users/linktrend/Projects/IDE Development`. The GitHub repository remains `linktrend/IDE-Development`. The product name and folder name are intentionally aligned in meaning, not spelling.

LiNKdeveloper is the unified development system for planning and building venture software with AI assistance. It holds rules, skills, templates, doctrine, and execution commands. Product repositories hold the code and content being built.

Earlier experiments and duplicate runtimes are retired. They are not part of daily operation. See [`docs/ARCHIVE-INDEX.md`](ARCHIVE-INDEX.md) for retired systems, archive paths, and when you may read from archive. Do not add archived folders to the workspace or wire product repos to them.

**One system, three installed sources:**

1. **IDE Development core** — canonical knowledge in `core/` and the Cursor runtime surface in `.cursor/` (mostly symlinks into `core/`). Doctrine, gates, proof/review/integration, and domain skills live here.
2. **gstack (macro)** — cloned at `/Users/linktrend/Projects/gstack`, fork https://github.com/linktrend/gstack. Handles specification, executive plan review, health checks, shipping verdicts, and session context.
3. **mattpocock/skills (micro)** — cloned at `/Users/linktrend/Projects/skills`, fork https://github.com/linktrend/skills. Handles PRD clarification, issue slicing, test-driven development, debugging, and architecture improvement.

You operate one system. Agents route across all three sources through the hybrid registry — you do not manage separate sources manually.

The saved workspace file **LiNKdeveloper** groups the system repo with product repos you are actively building. Add product folders to the workspace when you need them; remove them when work pauses.

---

## 2. Autonomy evolution — three stages, one gate structure

LiNKdeveloper evolves through three stages of autonomy. The **gate structure stays the same** across all stages. What changes is **who executes** between gates: Carlos in Stage 1, OpenClaw executives and executors in Stages 2 and 3.

**Shared lifecycle spine (Application Factory):**

```
Intent → Program → Module → Phase → Issue → Proof → Review → Integration → Complete
```

**Stage 1 — Semi-manual (now).** Carlos holds the primary human gates. Cursor agents do detailed work — planning, implementation, proof, review, integration — but stop at approval points. Carlos approves spec/PRD before serious development, and holds program, module, and launch gates when formal program work is in scope. This stage is complete and verified for use.

**Stage 2 — Mostly autonomous OpenClaw (next).** OpenClaw executive agents replace Carlos as the primary executor between gates. Carlos retains policy gates — especially spec/PRD approval and release — but day-to-day module execution, issue dispatch, and proof collection run through OpenClaw orchestration. Stage 2 preparation reads design concepts from the archived autonomous runtime; that archive is reference material only, not an active dependency.

**Stage 3 — Fully autonomous OpenClaw (future).** OpenClaw runs the full lifecycle continuously. Human involvement reduces to policy-only decisions: strategic direction, protected side effects, and explicit overrides. Gates remain; the system computes readiness from artifacts and state rather than assuming progress.

The executor handoff is the main delta: **human → OpenClaw**. Gate names, proof requirements, and review discipline do not change.

---

## 3. Three triggers only

Every session starts with exactly one of three triggers. Choosing application versus factory is **not** a fourth trigger — it is a routing decision inside each trigger, after the spec or PRD is clear.

You do not need exact wording — agents recognize intent, not a magic phrase. The examples below just show the kind of thing you can type to start each trigger.

### Trigger 1: New idea

You have a product concept but no written spec yet.

**Say something like:** *"I have an idea for [product]. It should do [X]. Help me turn this into a spec."*

1. **Interview** — work with an agent to explore the idea, constraints, and success criteria.
2. **Spec or PRD** — the agent produces a written specification or product requirements document.
3. **You approve** — review and approve the spec/PRD before development begins. This is your primary human gate.
4. **Route and develop** — based on what the product is:
   - **Normal application** — say *"scaffold this from the LiNKapps starter kit and start developing."* The agent copies the starter kit at `/Users/linktrend/Projects/LiNKapps` into the new product location and begins building on top of it — you do not run any setup commands yourself.
   - **Factory product** — agents use `docs/FACTORY-OPERATIONS-BLUEPRINT.md` as the planning reference for how the factory should operate, then develop.

### Trigger 2: PRD in hand

You already have a product requirements document (from you, a stakeholder, or a prior session).

**Say something like:** *"Here is a PRD for [product]. Review it, ask me what's missing, then get it ready to build."* (paste or attach the PRD)

1. **Clarify gaps** — the agent reads the PRD, asks targeted questions, and fills missing detail.
2. **You approve** — confirm the clarified spec/PRD is acceptable.
3. **Route and develop** — same application-or-factory decision as Trigger 1, then build.

### Trigger 3: Existing software

You have working code that needs work — refactor, finish incomplete features, customize, or extend.

**Say something like:** *"Look at [repo/feature] and tell me what's there, what's missing, and what you'd do next."* or *"There's a bug: [describe what's wrong]."*

1. **Assess** — the agent inspects the codebase and states what exists, what is missing, and what risks apply.
2. **Plan** — for larger changes, the agent proposes a short plan; you approve if direction is unclear or high-impact.
3. **Develop** — implement, test, and deliver. Factory products still reference the Factory Operations blueprint when operational behavior is in scope.

**Application versus factory — one short note.** Normal applications start from the LiNKapps starter kit. Factory products (revenue production lines such as website, automation, or content factories) use `docs/FACTORY-OPERATIONS-BLUEPRINT.md` as a planning reference. That blueprint describes how factory operations should eventually run autonomously. It is design-only until you explicitly start factory ops work.

---

## 4. Human gates — Stage 1 (Carlos)

Agents do most detailed work. **You** hold the gates that matter for direction and release.

### You approve (human gates)

1. **Spec / PRD approval** — Is the written product intent and requirements document acceptable before serious development begins? This is the **primary** gate in Stage 1. Nothing substantial starts without it.
2. **Program gate** — Is the program plan and scope right before large autonomous execution runs? Applies when work is organized as a formal program.
3. **Module gate** — Is the module decomposition right before agents execute a module end-to-end?
4. **Launch / release gate** — Is integrated work ready to ship or go live?

When an agent reaches one of these gates, it stops and presents the artifact for your decision — it does not assume approval.

### Agents handle (with your oversight available)

1. Issue implementation and proof collection
2. Independent review — checks proof against acceptance criteria, not gut feel
3. Integration recording — only after review passes

**Key rule:** readiness is computed from artifacts and state, not assumed. Every issue must pass through **review-ready** before integration. Review inspects **proof**, not confidence.

If something feels wrong at any point, you can stop, redirect, or reject. That is the intended operating model.

---

## 5. OpenClaw operator path — Stage 2 preparation

Stage 2 is not live yet. This section describes what to read and assume when OpenClaw orchestration comes online.

### What to read first (Stage 2 prep)

1. This manual — triggers, gates, and workspace wiring
2. `docs/LINKDEVELOPER-STAGE1.md` — Stage 1 declaration and verified scope
3. `docs/HYBRID-SKILLS-REGISTRY.md` — hybrid skill routing
4. `.cursor/skills/intelligent-routing/SKILL.md` — how agents pick skills from triggers
5. Archived autonomous runtime design docs — read-only reference for lifecycle model, executor routing, and work-packet shape. See [`docs/ARCHIVE-INDEX.md`](ARCHIVE-INDEX.md). Stage 2 reads the archive for concepts; it does not wire or extend that code.

### Assume Carlos gates until explicitly migrated

During Stage 2 rollout, treat spec/PRD approval and release gates as Carlos-held until a written migration says otherwise. OpenClaw may execute modules and issues autonomously, but policy gates remain human until Stage 3 policy automation is proven.

### Telegram and executive agent model

Stage 2 introduces OpenClaw **executive agents** — not one OpenClaw per product, but a small set of executives with distinct roles:

1. **Development executive** — orchestrates Application Factory work: program planning, module dispatch, gate presentation to Carlos.
2. **Factory orchestrator** (Stage 2+, when factory ops begins) — one executive oversees all operations factories, per the Factory Operations blueprint.
3. **Principal overseer** — policy channel; presents gates, briefings, and protected-action approvals to Carlos.

**Telegram** is the intended executive notification and approval surface for Stage 2. Carlos receives gate requests, briefings, and override prompts there. Executors (Agent Zero, sub-agents, automation, scripts) do the atomic work; executives coordinate and escalate.

Executors write proof; executives verify gate readiness and route the next unit of work. The same proof → review → integration discipline from Stage 1 applies.

---

## 6. Workspace and repo wiring

### Open the workspace

1. Open **Cursor**.
2. Go to **File → Open Workspace from File…**
3. Select:

   ```
   ~/Projects/Workspaces/LiNKdeveloper.code-workspace
   ```

4. If Cursor already has the workspace open but folders look stale, use **File → Reload Window**.

**What you should see:** at minimum, `IDE Development` in the sidebar. Always start there when opening a new chat or session about how work should run.

### IDE Development is the system

Everything agents need to behave consistently lives in **IDE Development**:

- **`core/`** — canonical knowledge (the master copy)
- **`.cursor/`** — what Cursor reads at runtime (mostly symlinks back into `core/`)

When you improve the system, edits usually go into `core/` and flow through to `.cursor/` automatically.

### Product repos adopt the system via symlink

Each product repo can share the same runtime by pointing its local `.cursor` folder at the system:

```
ProductRepo/.cursor  →  ../IDE Development/.cursor  →  ../IDE Development/core
```

This is a **one-time wiring step**, not something you do every session.

**Preferred wiring command** (from `IDE Development`):

```bash
./scripts/wire-repo.sh /path/to/ProductRepo
```

The script backs up an existing `.cursor`, creates the symlink, verifies required runtime paths, and is safe to re-run when already wired. Agents should use this script for natural-language requests like "wire this repo" rather than improvising symlink commands.

Full adoption sequence and manual fallback when judgment is needed first: `core/workspace/WORKSPACE-ADOPTION.md` and `core/workspace/REPO-WIRING.md`.

**Rules of thumb:**

1. Do **not** copy the whole system into each product repo when a symlink is enough.
2. Always inspect an existing `.cursor` before replacing it — some repos have local rules worth keeping.
3. Back up replaceable material before changing anything (the script does this automatically for replaceable `.cursor` state).

### Starting a session — what to read first

When you or an agent starts work, read these in order (agents follow the same list automatically):

1. **`README.md`** (repo root) — what this repository is and how it is structured
2. **`.cursor/rules/00-bootstrap.mdc`** — mandatory read order and operating rules for every task
3. **`.cursor/skills/SKILLS_CATALOG.md`** — which skill to use for a given kind of work

After that, read **only what the current task needs** — a specific command file, template, or doctrine doc. Do not scan the entire system unless the task genuinely requires it.

For a fast path when the task is already clear, agents may also use `.cursor/bootstrap/QUICKSTART.md`.

---

## 7. Skills — hybrid registry

Skills live in `.cursor/skills/SKILLS_CATALOG.md`. Agents read the catalog first, then open only the skill needed for the task.

**Carlos does not pick skill names.** You describe intent through one of the three triggers. Agents route through `docs/HYBRID-SKILLS-REGISTRY.md` and `core/skills/intelligent-routing/SKILL.md` to the correct hybrid or domain skill.

**Three installed sources:**

1. **Local domain skills** in this repository — APIs, UI, deployment execution, routing, and governance.
2. **gstack (macro)** — `/Users/linktrend/Projects/gstack`. Spec, plan review, health, ship, context save/restore.
3. **mattpocock/skills (micro)** — `/Users/linktrend/Projects/skills`. Grill-with-docs, PRD synthesis, issue slicing, TDD, debugging, architecture improvement.

All three are wired and active — not reference-only. Hybrid command entrypoints live under `.cursor/commands/hybrid-*.md` (canonical copies in `core/commands/`).

To extend the system later, add domain skills under `core/skills/`, update the catalog and registry, and run a supervised low-risk test before relying on changes for production work.

---

## 8. Factory operations blueprint — planning only

`docs/FACTORY-OPERATIONS-BLUEPRINT.md` is a **planning document only** — not live factory infrastructure. Its banner states clearly: no Supabase schemas, Postgres factory ledger, n8n factory controller, or factory brain infrastructure is built until you explicitly start factory ops work.

**Factory infrastructure belongs to factory operations — not Stage 1.** Stage 1 is the Application Factory development workflow in this repository. Factory ops is a separate domain for continuous production lines (website, automation, content factories).

Use the blueprint when the product is a **factory**. It describes the common operations skeleton — trigger, program, module, stage, issue, run, gate, output, complete — shared by revenue factories. Agents consult it when designing or building factory behavior; you do not operate it as a day-to-day control panel today.

The **Application Factory workflow** (this manual, IDE Development commands, and the development lifecycle) is separate from factory **operations**. Development builds software; factory operations run production lines once built.

---

## 9. Appendix — internal agent commands

Cursor commands under `.cursor/commands/` are **agent entry points** for structured execution inside IDE Development. You do not type these as your primary workflow — you use natural language and the three triggers in Section 3. Agents invoke commands when the task fits.

### IDE Development execution commands

1. **`plan-program`** — new product idea or objective; produces validated intent, program artifact, and initial module structure
2. **`plan-module`** — program exists; breaks a module into phases and issues with dependencies and acceptance criteria
3. **`complete-module`** — module is planned; recursive execution through proof, review, and integration until done or blocked
4. **`execute-issue`** — one issue ready to implement; code/work output plus proof artifact
5. **`review-issue`** — issue has proof; independent review verdict (pass, fail, or blocked)
6. **`integrate-issue`** — review passed; integration record and updated downstream readiness
7. **`small-change`** — tiny, low-risk fixes that still need proof, review, and integration but not full program or module planning

**Typical agent flow:**

```
plan-program  →  plan-module  →  complete-module
                                      ↓
                              execute-issue  →  review-issue  →  integrate-issue
```

### Hybrid commands (gstack and mattpocock)

Agents select these from triggers; Carlos does not invoke them by name.

1. **`hybrid-spec`** — gstack `/spec`; structured specification for Trigger 1
2. **`hybrid-grill`** — mattpocock `/grill-with-docs`; clarify PRD gaps (Trigger 2)
3. **`hybrid-to-prd`** — mattpocock `/to-prd`; synthesize PRD from clarified intent
4. **`hybrid-to-issues`** — mattpocock `/to-issues`; slice PRD into atomic issues after approval
5. **`hybrid-tdd`** — mattpocock `/tdd`; test-driven implementation loop
6. **`hybrid-diagnosing-bugs`** — mattpocock `/diagnosing-bugs`; systematic debugging
7. **`hybrid-health`** — gstack `/health`; project health checks (Trigger 3 assess)
8. **`hybrid-ship`** — gstack `/ship`; shippable vs blocked verdict (subordinate to IDE Development integration and release gates)
9. **`hybrid-plan-ceo-review`** — gstack `/plan-ceo-review`; executive plan review
10. **`hybrid-context-save`** and **`hybrid-context-restore`** — session context persistence
11. **`hybrid-improve-architecture`** — mattpocock `/improve-codebase-architecture`; refactor guidance

Command definitions live under `.cursor/commands/`. Index: `.cursor/commands/INDEX.yaml`.

---

## 10. What is coming — Stage 2 and Stage 3

**Stage 2 — Mostly autonomous OpenClaw.** OpenClaw executives take over module and issue execution between Carlos gates. Telegram becomes the primary gate and briefing channel. Hybrid skills and IDE Development commands remain the execution substrate. Design concepts migrate from the archived autonomous runtime into a live OpenClaw orchestration layer wired to IDE Development — without reviving legacy folder structures or duplicate system copies.

**Stage 3 — Fully autonomous OpenClaw.** Continuous lifecycle operation with human policy only. Gates persist; readiness stays artifact-driven. Factory operations infrastructure (ledger, automation controller, factory schemas) comes online when Carlos explicitly starts factory ops work — not before.

**What Stage 1 deliberately excludes (unchanged):**

1. Live OpenClaw orchestration and Telegram executive routing
2. Factory operations infrastructure (Postgres ledger, factory controller, factory Supabase schemas)
3. Unsupervised release without Carlos approval at policy gates

**Key reference documents:**

1. Stage 1 overview — `docs/LINKDEVELOPER-STAGE1.md`
2. Hybrid skills registry — `docs/HYBRID-SKILLS-REGISTRY.md`
3. Workspace adoption — `core/workspace/WORKSPACE-ADOPTION.md`
4. Repo wiring — `core/workspace/REPO-WIRING.md` and `scripts/wire-repo.sh`
5. Factory operations (planning) — `docs/FACTORY-OPERATIONS-BLUEPRINT.md`
6. Historical evidence — `docs/archive/`
7. Automated Stage 1 re-check — `scripts/verify-stage1.sh`

Your operating surface today: this manual, the LiNKdeveloper workspace, the three triggers, and your approval at the gates in Section 4.
