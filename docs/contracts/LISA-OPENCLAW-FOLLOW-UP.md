# Lisa / OpenClaw follow-up contract (GITOPS-01)

**Status:** Follow-up only — **no Lisa or openclaw_prime edits in GITOPS-01**
**Date:** 2026-07-28
**Timezone:** Asia/Taipei (no DST)

This document is the binding follow-up contract for a future PR in `openclaw_prime` (and any Lisa personality sync). IDE Development is the **source of truth** for autonomous Git ops doctrine.

**Authoritative SOT (read first):**

- `docs/AUTONOMOUS-GIT-OPERATIONS.md`
- `docs/adr/0003-autonomous-ship-pull-promote.md` (incl. 2026-07-28 commit-status amendment)
- `core/github/CI-GATE-CONTRACTS.md`
- `core/github/REVIEW-READY.md` (**commit status only** — never a readiness file in the diff)
- `docs/contracts/LISA-MAIN-APPROVE-DISPATCH.md`

---

## Scope of this follow-up

Align Lisa Option A (OpenClaw cron → Cursor ACP) with the **Review Packager redesign**:

| Topic | Required change |
|---|---|
| Ship waves | **Checkpoint only:** commit + push on work branch. **No PR. No Bugbot.** |
| Pull waves | Merge `origin/development` into unfinished work branches; **skip frozen reviewed SHAs** |
| Review Packager | GitHub-owned Tue/Fri **08:00** — Lisa reports status lines only |
| Staging promote | GitHub-owned Tue/Fri **10:00** — Lisa reports status lines only |
| Implementer finish | Push tip → publish successful commit status `Linktrend Review Ready` on that exact SHA; Packager opens PR |

Do **not** claim Lisa/openclaw files were edited in GITOPS-01. Implement this contract in openclaw_prime when scheduled.

---

## Authoritative clock (Asia/Taipei)

| Event | Time | Owner | Lisa role |
|---|---|---|---|
| Ship 05 | **05:00** | Lisa cron → ACP shipper | Run checkpoint shipper; Telegram + email one-liner |
| Pull 07 | **07:00** | Lisa cron → ACP puller | Run puller; skip frozen reviewed SHAs |
| Review Packager | Tue & Fri **08:00** | GitHub Action | Report `Review Packager (Tue|Fri): Clear\|Issues` after workflow outcome |
| Staging promote | Tue & Fri **10:00** | GitHub Action | Report `Staging promote (Tue|Fri): Clear\|Issues` after workflow outcome |
| Ship 16 | **16:00** | Lisa cron → ACP shipper | Same as Ship 05 (checkpoint only) |
| Pull 18 | **18:00** | Lisa cron → ACP puller | Same as Pull 07 |
| EOD checkpoint | ~17:00 | Agent / operator | Checkpoint only — not a review request |
| Main package | Mon **08:00** | GitHub Promoter | Report `Main ready (Mon): Clear\|Issues` |
| Morning digest | **08:30** | Lisa cron | Pipeline section D; Mon Main Approve when Clear |
| Main Approve | Mon **08:30** | Lisa digest + Telegram | See `LISA-MAIN-APPROVE-DISPATCH.md` |

**Why Packager 08:00 / Staging 10:00:** Pull 07 completes first; review, CI, integration, and repair get a two-hour window before staging promotes only what is already safely on `development`.

**Wave labels:** Use **Ship 05**, **Pull 07**, **Ship 16**, **Pull 18** — local hour names, not A/B letters and not `Ship 05:00`.

---

## Ship waves — checkpoint only (mandatory)

On every Ship 05 and Ship 16 wave, the ACP **Shipper** prompt must:

1. Process **one repo at a time** in the locked studio order (below).
2. On each repo with local changes or unpushed commits on a work branch (`issue/*` preferred; also `cursor/*`, rare `dev/*`):
   - Commit with conventional commits if there are changes (never secrets).
   - Push the branch.
3. **STOP.** Do **not** open or update a PR. Do **not** request Bugbot. Do **not** merge. Do **not** touch `staging` or `main`.

EOD (~17:00) follows the same checkpoint rule.

When work is **finished** (proof, local gates, clean tree): implementer **pushes first**, then marks review-ready via `scripts/mark-review-ready.sh` (publishes `Linktrend Review Ready` on the exact tip SHA) — still **no PR** from the implementer and **no** `.linktrend/review-ready.json`. Tue/Fri 08:00 Review Packager opens the PR and requests Bugbot once.

---

## Pull waves — skip frozen reviewed SHAs

On every Pull 07 and Pull 18 wave, the ACP **Puller** prompt must:

1. Process one repo at a time in studio order.
2. On each checked-out work branch (not `development` / `staging` / `main` as dump targets):
   - `git fetch origin`
   - Merge `origin/development` into the work branch (unless repo mandates rebase).
3. **Skip** branches whose tip SHA is **frozen under active review**:
   - Exact branch-tip SHA has successful GitHub commit status **`Linktrend Review Ready`**, **or**
   - Open review PR into `development` whose head equals that tip, **or**
   - Explicit operator freeze.
   - Do **not** consult `.linktrend/review-ready.json` (that file must not be used).
4. Do **not** merge into `staging` or `main`.
5. Unfinished work on skipped branches rolls forward on the next Pull wave.

Pull is **not** hard-gated on all PRs being merged.

---

## Repo order (sequential — Principal locked)

Process exactly **one repo at a time**, skipping missing paths:

1. IDE Development (`/Users/linktrend/Projects/IDE Development`)
2. openclaw_prime
3. LiNKplatform
4. LiNKskills
5. LiNKbrain
6. LiNKsites
7. LiNKdeveloper
8. LiNKlibraries
9. LiNKautowork

---

## Lisa one-line status contract (exact formats)

Telegram announce bodies, Ship/Pull emails, heartbeat/digest pipeline lines, and `memory/pipeline-status.md` result lines must use **exactly** these shapes — no lists, no links, no extra words:

| Checkpoint | Clear | Issues |
|---|---|---|
| Ship 05 | `Ship 05: Clear` | `Ship 05: Issues` |
| Pull 07 | `Pull 07: Clear` | `Pull 07: Issues` |
| Ship 16 | `Ship 16: Clear` | `Ship 16: Issues` |
| Pull 18 | `Pull 18: Clear` | `Pull 18: Issues` |
| Review Packager (Tuesday) | `Review Packager (Tue): Clear` | `Review Packager (Tue): Issues` |
| Review Packager (Friday) | `Review Packager (Fri): Clear` | `Review Packager (Fri): Issues` |
| Staging promote (Tuesday) | `Staging promote (Tue): Clear` | `Staging promote (Tue): Issues` |
| Staging promote (Friday) | `Staging promote (Fri): Clear` | `Staging promote (Fri): Issues` |
| Main package (Monday) | `Main ready (Mon): Clear` | `Main ready (Mon): Issues` |

**ACP shipper/puller final reply:** exactly `WAVE: Clear` or `WAVE: Issues` (e.g. `Ship 05: Clear`) — Lisa maps to the table above for status file and channels.

**Detail:** only when Carlos asks. Operational detail lives in `memory/pipeline-status.md` (Lisa workspace), not in Telegram one-liners.

**GitHub-owned checkpoints:** After Tue/Fri 08:00 Packager and 10:00 Staging workflows complete (or fail), Lisa (or a dedicated cron) should read workflow conclusion / step summary and write the matching Clear/Issues line with the correct `Staging date` / freshness markers per `agents/pipeline-status.md`.

---

## ACP prompt deltas (Shipper — replace in ship-pull-clock.md)

Remove steps that open/update PRs or mention Bugbot. Required Shipper body:

```text
WAVE (Asia/Taipei). You are the Implementer shipper under IDE Development autonomous Git ops (Lisa Option A clock).

CHECKPOINT ONLY — no PR, no Bugbot, no merge.

Process ONE REPO AT A TIME in this exact order (skip missing paths):
1) /Users/linktrend/Projects/IDE Development
2) /Users/linktrend/Projects/openclaw_prime
3) /Users/linktrend/Projects/LiNKplatform
4) /Users/linktrend/Projects/LiNKskills
5) /Users/linktrend/Projects/LiNKbrain
6) /Users/linktrend/Projects/LiNKsites
7) /Users/linktrend/Projects/LiNKdeveloper
8) /Users/linktrend/Projects/LiNKlibraries
9) /Users/linktrend/Projects/LiNKautowork

For each repo that has local changes or unpushed commits on a work branch (prefer issue/*; also cursor/*, rare dev/*):
1) Commit with conventional commits if there are changes (never commit secrets).
2) Push the branch.
3) STOP. Do not open or update a PR. Do not request Bugbot. Do not merge. Do not touch staging/main.

When work is finished (separate session): mark review-ready per IDE Development core/github/REVIEW-READY.md — Packager opens PR Tue/Fri 08:00.

Do not edit pipeline-status.md; Lisa owns the shared status writer.

Reply with exactly one line only: WAVE: Clear or WAVE: Issues.
```

## ACP prompt deltas (Puller — add skip rule)

Add explicit skip-frozen-reviewed-SHA rule to Puller prompt (see Pull section above). Remove any implication that Pull waits for all PRs merged.

---

## openclaw_prime checklist (future PR)

Update these files in `openclaw_prime` — **not in GITOPS-01**:

- [ ] `linkbots/lisa/Personality files/agents/ship-pull-clock.md` — Shipper checkpoint-only; Puller skip frozen SHAs; doctrine pointers
- [ ] `linkbots/lisa/Personality files/agents/pipeline-status.md` — Review Packager lines; Staging **10:00**; exact status formats; Packager Tue/Fri 08:00
- [ ] `linkbots/lisa/Personality files/agents/morning-digest.md` — Section D includes Review Packager lines when dated; Staging 10:00 not 08:00
- [ ] `linkbots/lisa/Personality files/HEARTBEAT.md` — Tue/Fri 08:00 Packager + 10:00 Staging checkpoints
- [ ] `linkbots/lisa/Personality files/AGENTS.md` — Ship = checkpoint only; Packager owns PR+Bugbot
- [ ] `linkbots/lisa/Personality files/memory/pipeline-status.md` — Template example lines for Packager + Staging 10:00
- [ ] `linkbots/lisa/docs/SHIP-PULL-CLOCK-INSTALL.md` — Cross-link redesign SOT
- [ ] Live sync: `~/.openclaw-lisa/workspace/` mirrors for edited personality files
- [ ] `docs/handoffs/` — dated note when follow-up PR lands

**Main Approve store (IDE #23 SOT):** `docs/contracts/LISA-MAIN-APPROVE-DISPATCH.md` +
`scripts/gitops/main_approve_package_discover.py`. Store = GitHub `promote/main/*`→`main`
PR marker (`<!-- linktrend-promote: … -->`). Lisa must pass **all three** bindings on
`approve-merge`: `expected_sha`, `expected_main_sha`, `expected_promote_head`.
Do **not** use OpenClaw JSON/Markdown sidecars. After this interface exists on the
consumer, Lisa may flip `MAIN_APPROVE_RUNTIME_STORE.available` in openclaw_prime.

---

## Runtime prerequisites (ops — not code secrets)

- Mac Mini awake (Keep Awake / Remote Control) for Lisa ACP spawn.
- Lisa gateway profile `lisa`; ACP/`acpx` healthy.
- Four cron jobs: `lisa-ship-05`, `lisa-pull-07`, `lisa-ship-16`, `lisa-pull-18`.
- Cursor Automations remain **backup only** (`docs/CURSOR-AUTOMATIONS-SETUP.md`).

---

## Validation

Future openclaw PR is done when:

1. Ship ACP prompt never opens PRs or triggers Bugbot.
2. Pull ACP prompt skips frozen reviewed SHAs and documents the rule.
3. Status file and digest use exact one-line formats including Review Packager and Staging 10:00.
4. All doctrine links point to IDE Development SOT paths above.
5. Live Mini personality matches Personality files after sync.
