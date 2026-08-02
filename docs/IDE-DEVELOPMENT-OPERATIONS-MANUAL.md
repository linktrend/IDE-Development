# IDE Development Operations Manual

**Who this is for:** you — LiNKtrend’s Principal. You make strategic decisions and approve a small number of checkpoints. You do not write code, run technical commands, or manage servers day to day.

**What this is:** a plain-English handbook for how IDE Development works *today*, and what your role in it is. It is not a technical design document.

**Honesty rule:** everything below describes what is actually installed and verified in this repository right now. Where something is planned but not available yet, it is labeled under [Current status](#current-status-what-is-not-available-yet).

**Companion docs:** [`IDE-DEVELOPMENT-INTENT.md`](./IDE-DEVELOPMENT-INTENT.md) (why this exists) · [`IDE-DEVELOPMENT-TECHNICAL-PRD.md`](./IDE-DEVELOPMENT-TECHNICAL-PRD.md) (full technical reference) · [`OPEN-ISSUES.md`](./OPEN-ISSUES.md) (build log).

---

## What IDE Development is

IDE Development is LiNKtrend’s shared “how we build software with AI” operating system. It lives in one GitHub repository (the **system source**) and is installed into the **product / consumer** repositories you care about so every agent follows the same rules. This system repository itself is **not** a consumer install target and must not receive a nested installed copy of itself.

Think of it as the factory floor instructions and tools — not the autonomous factory machine itself. The separate **LiNKdeveloper** Program is the mostly-automatic factory that can run on a server. This repository is what you and Cursor agents use day to day: doctrine, skills, commands, checks, and a fixed six-stage build pipeline.

When a product repo is installed with IDE Development, agents in that repo read the same playbook: plan carefully, build in small checked pieces, prove the work, review it independently, integrate it, and only then treat it as done. Locked consumer install order (and Principal approval gates) live in [`GITOPS-CONSUMER-ROLLOUT.md`](./GITOPS-CONSUMER-ROLLOUT.md) — including `LiNKtrading-codebase`, excluding IDE Development.

---

## Your role today

### Where a new build starts

A serious application build starts with an **Intent** — a short, plain-English statement of what is actually being built. Agents run a guided interview: they ask questions, summarize, and at a few points you must explicitly confirm “yes, that summary is right” before they continue.

That interview happens inside **Cursor** (or with a technical person relaying your answers). There is no phone dashboard yet.

### Moments when a human decision is required

| When | What you are asked | What happens if you say no |
| --- | --- | --- |
| During the interview | Confirm analysis, priority ranking (must / should / could / won’t), and the final Intent | The interview does not advance; vague “sounds fine” is not treated as approval |
| After the interview (formal gate) | Approve the confirmed Intent plus the full **Technical PRD** (the detailed “what we’re building” document), along with an independent second opinion | Rejecting stops serious development on that plan; agents must not quietly reuse a rejected plan |
| Before ship (Module 6) | **Release OK / pre-deploy** — is this ready to go live? | Work stays at “release ready” or blocked; this system does **not** deploy past your refusal |

Day-to-day coding, proof collection, independent review, and merge into the integration branch are designed to run without asking you at every step — as long as those gates pass.

### What you do **not** need to do

- Write code
- Run terminal commands yourself
- Pick skill names or model names
- Approve every small coding task
- Manage servers or cloud accounts day to day

Someone technical (or an AI agent following this playbook) handles those mechanics. Your job is direction and the checkpoints above.

---

## The six stages (plain names ↔ technical names)

Every application build walks through the same six stages, in order.

| # | Plain-English name | Technical Module name | What happens in plain terms |
| --- | --- | --- | --- |
| 1 | Understanding the request | `intake_and_definition` | Interview → Intent → Technical PRD → independent review → your formal approval |
| 2 | Planning how to build it | `assembly_planning` | Features, reusable pieces, technical design, work list (starter template optional) |
| 3 | Building it | `execution` | Piece-by-piece construction, each piece proved, reviewed, and integrated |
| 4 | Testing and hardening it | `verification_and_hardening` | Tests, audits, and a whole-product check against what you approved |
| 5 | Saving reusable pieces | `library_contribution` | Harvests useful pieces into the shared LiNKlibraries catalog |
| 6 | Preparing to ship | `shipment` | Final checks, proof fingerprint, and your Release OK — **does not deploy by itself** |

Commands agents use: `run-application-pipeline` / `resume-application-pipeline`. Doctrine lives under `.cursor/execution/` (especially `APPLICATION-PIPELINE.md`).

---

## Walkthrough: starting a new build (as things work today)

### 1. Open the workspace

1. Open **Cursor**.
2. Open your multi-repo workspace (historically saved as the LiNKdeveloper workspace file under `~/Projects/Workspaces/`).
3. Confirm **IDE Development** appears in the sidebar. Start system questions there.

### 2. Make sure the product repo is installed (one-time, then updates)

Each **consumer** product repo should receive a **physical** managed install of this system (committed `.ide-development/` plus Cursor/Codex adapters) — not a symlink back to this checkout, and never a nested self-install into IDE Development. Preferred method — someone technical runs, from IDE Development (system source), after a read-only drift report and your separate approval for that consumer:

```bash
python3 scripts/ide-development.py plan --repo /path/to/ProductRepo
python3 scripts/ide-development.py install --repo /path/to/ProductRepo
```

You do not need to run this yourself. You only need to know: if a product repo is not installed, agents there will not see the shared playbook.

### 3. Say what you want in plain language

You do not need magic phrases. Agents recognize intent. Examples:

- *"I have an idea for [product]. It should do [X]. Help me turn this into a spec."*
- *"Here is a PRD for [product]. Review it, ask what’s missing, then get it ready to build."*
- *"Look at [repo/feature] and tell me what’s there, what’s missing, and what you’d do next."*
- *"Resume this application build."* (agents read saved pipeline state — not chat memory)

### 4. The interview and your formal approval (stage 1)

Roughly what you will experience:

1. Open-ended questions.
2. An **analysis** summary — you must confirm it.
3. A **priority** recommendation — you must confirm it.
4. A short **Intent** — you must confirm it. Your confirmation *is* the validation of the Intent.
5. Agents (not you) draft the full **Technical PRD**, get an independent second opinion, then ask for your formal yes/no.

Until you decide, serious construction should **block**. That decision is meant to be recorded in the Program’s durable artifacts so a later session can see you already approved (or rejected).

### 5. What happens automatically after you approve

Once you approve stage 1, agents continue through planning, building, testing, library harvest, and ship preparation — checking themselves as they go, with limited automatic retries when a check fails.

They should stop and brief you if retry limits are used up, or when they reach your Module 6 Release OK gate.

### 6. What the end result is meant to be

When a Program completes successfully:

- A real application codebase built and checked in pieces
- Durable artifacts (Intent, Technical PRD, proofs, reviews, pipeline state)
- A release-ready proof package (including a fingerprint of what was produced)
- Optionally, reusable library contributions for the next product

**Important honesty:** this repository is verified as an installable operating system (automated checks pass). It is a **session-scoped** Cursor playbook, not a always-on factory robot. The always-on factory is LiNKdeveloper’s job.

---

## What happens when something goes wrong

The system is designed to catch mistakes — and to **stop** rather than paper over them.

- Work is supposed to be checked by an independent reviewer (not only the agent that did the work).
- Empty or placeholder “proof” is rejected.
- If a check fails, agents can automatically redo the work within a **retry budget** (by default, three attempts).
- When the budget is used up, work is flagged blocked with a trail — not retried forever.
- For application builds, a mechanical validator refuses illegal stage transitions. Local git hooks and CI reinforce that so a broken pipeline state cannot be quietly committed.

So a failure is usually: “tried, failed a check, tried again within limits, then asked for help” — not “spent forever” and not “silently shipped something broken.”

---

## The spirit of the Laws (one sentence each)

Technical wording lives in `.cursor/execution/CANONICAL-LAWS.md`. Spirit only:

1. **Small units of work** — real construction happens as Issues, not vague module vibes.
2. **Order comes from dependencies** — work starts when prerequisites are actually met.
3. **Readiness is proven** — saying “ready” is not enough.
4. **Done means evidence** — confidence is not proof.
5. **Proof must be real** — empty checklists do not count.
6. **Blocked work leaves a trail** — stoppages are explained.
7. **Someone else checks the work** — the builder is not the final judge.
8. **Checked work is not yet integrated** — merging into the active line is a separate step.
9. **Integrated work is not yet released** — release needs its own validation and your ship gate.
10. **Blocking failures stop the line** — gates halt progress; they do not merely warn.

---

## Skills and models (what you can ignore)

Agents choose skills and models. You describe outcomes.

Three skill sources are installed and active:

1. **Local domain skills** in this repository (APIs, UI, testing patterns, deployment procedures, and so on).
2. **gstack** — big-picture help: specification, plan review, health checks, ship verdicts, session context.
3. **mattpocock skills** — detailed craft: clarifying a PRD, slicing work, test-driven loops, debugging, architecture improvement.

Model choice is pinned to named routes (default coding model, escalation model, independent reviewer, cheaper model for tiny safe tasks, and so on). You do not pick these by name unless a technical helper asks you to.

---

## Current status (what is not available yet)

| Topic | Status today |
| --- | --- |
| Phone / web approval dashboard | **Not built.** Approvals run through Cursor (or a technical person recording your decision). |
| Always-on autonomous factory in *this* repo | **Not this repo’s job.** That is LiNKdeveloper. |
| Automatic deploy after Module 6 | **Not built here.** You keep Release OK; this pipeline stops at release-ready. |
| OpenClaw / Telegram executive operators | **Not live for this system.** Older manuals that promised Stage 2/3 OpenClaw for *this* repo are historical framing only. |
| Claude Code as a supported platform | **Not in current v2 support or roadmap.** Historical files may remain; Cursor and Codex are the supported platforms. |
| Dollar spend dashboard | **Not computed** here. |

---

## FAQ

**Can I approve things from my phone?**
Not yet.

**What if I don’t like the plan?**
Reject the Module 1 formal gate (Intent + Technical PRD). Do not confirm interview checkpoints until the wording matches what you mean.

**What if I don’t like what it built later?**
After early approval, construction is meant to be self-checking. You still hold Release OK before ship. If checks fail, agents retry within limits and then escalate rather than shipping past a failed gate.

**Is this the same as LiNKdeveloper?**
No. IDE Development is the shared human-assisted playbook installed into product repos. LiNKdeveloper is the separate autonomous factory Program.

**Do I need to understand TypeScript, git, or APIs?**
No. Your inputs are Intent-level decisions and the named checkpoints above.

**Is the system “done”?**
Done enough for daily installed use under portable v2: doctrine, hybrid skills, pipeline validator, hooks, verification scripts, and the managed install model are in place. Dashboard, always-on autonomy in this repo, Claude Code support, and automatic deploy are not claimed.

**Who installs a product repo?**
Someone technical runs the portable installer once (after a drift report and your approval for that consumer). After that, daily work is conversation + your gates. Updates use the same installer (`update`), still with drift + approval before each consumer.

---

## One-page reminder

1. You describe what you want (via interview or a PRD you already have).
2. You confirm analysis → priorities → Intent.
3. You formally approve (or reject) Intent + Technical PRD.
4. Agents plan, build, test, harvest reusables, and prepare shipment — checking themselves, with limited automatic retries.
5. You give Release OK before anything is treated as cleared to go live.
6. You are not asked to code, pick skills, or approve every merge.
7. This is the shared playbook — not the always-on autonomous factory, and not a phone dashboard (yet).
