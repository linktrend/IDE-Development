# Lane F independent review #3 — Git hygiene disposition

**Reviewer:** Lane F #3 (Git hygiene disposition)  
**Model:** cursor-grok-4.5-high  
**Mode:** READ-ONLY (no GitHub mutation; no stash/branch/worktree apply)  
**Reviewed:** `docs/evidence/issue-72/lane-e/`  
**Captured subject:** Lane E @ `2026-08-02T05:06:20Z`  
**Review written:** 2026-08-02 (Asia/Taipei)  
**Subject tip (caller):** `e6301fc920a4bf841f6bb4d27c15dc4e1f655ef2`  
**Machine JSON:** `docs/evidence/issue-72/lane-f/git-hygiene-review.json`

## Verdict: **PASS**

Lane E is PLAN ONLY, preserves hard DO-NOT-TOUCH objects, marks Issue #72 KEEP-ACTIVE, leaves stash untouched, refreshes post-WP03 vs the archived cleanup plan (including new promote leftovers + tree equality), and is sufficiently machine-readable for a later Codex apply session. Non-blocking evidence gaps are listed below; none fail the must-confirm set.

---

## Must-confirm checklist

| # | Requirement | Result | Evidence |
|---|-------------|--------|----------|
| 1 | PLAN ONLY — no `applyAuthorized: true`; no closes/deletes/prunes/stash ops in Issue #72 implementation | **PASS** | Top-level `mode: PLAN_ONLY`, `applyAuthorized: false`; **88/88** object rows `applyAuthorized: false` (0 true/missing). `commands-and-results.md` §9–12 dry-run only; §Explicit non-actions forbids close/delete/prune/stash/push. `DISPOSITION.md` apply sequence is fully commented. Grep: no live `--apply`, `gh pr/issue close`, `worktree remove/prune`, or stash mutate in Lane E evidence. |
| 2 | PR #36 / #37 / #49 DO-NOT-TOUCH | **PASS** | `disposition.json` PRs 36/37/49: `class: DO-NOT-TOUCH`, `proposedAction: none`, `applyAuthorized: false`. Mirrored in `DISPOSITION.md` / `SUMMARY.md` hard tables. Spot-check commands §14 recorded CONFLICTING / MERGEABLE / CONFLICTING respectively without mutation. |
| 3 | Issue #72 branch KEEP-ACTIVE | **PASS** | Issue object id 72, local branch `issue/72-pre-launch-ide-development-codebase-cleanup-arch`, and worktree `issue-72-…` all `class: KEEP-ACTIVE`, `proposedAction: none`. Local dry-run KEEP noted in commands §10. Not on origin (commands §6) — still correctly protected as active caller work. |
| 4 | Stash must not be modified | **PASS** | `stashes[0]` `stash@{0}` → `DO-NOT-TOUCH` / `none` / `applyAuthorized: false`. Commands §5 inventory only; §Explicit non-actions forbids drop/apply. Live `git stash list` still shows the same Cursor cloud-agent entry on `issue/ide-pull-wave-test`. |
| 5 | Post-WP03 refresh vs old cleanup plan (promote leftovers, tree equality) | **PASS** | Prior plan `docs/archive/evidence/wp02/lane-c/cleanup-plan-post-wp03.md` carried 5 remote WOULD_DELETE candidates. Lane E retains those and adds **NEW** `promote/main/8ac0afdc55fe`, `promote/staging/e6301fc920a4` after #70/#71. `postWp03Context` + commands §3/#7: merged #69/#70/#71; trees equal `43b1333ae21f43a34c3bdcccb2aac96f3d6e007f` — **reconfirmed live** this review (`origin/{development,staging,main}^{tree}` all match). `changedSincePriorPlan` documents issue/68 merge + Issue #72 KEEP-ACTIVE + dirty remote dry-run EXIT 1. |
| 6 | Disposition machine-readable & actionable for later Codex apply | **PASS** | Schema'd `disposition.json` (`schemaVersion: 1`) with per-object `class` / `proposedAction` / `applyAuthorized`, `dryRunSummary`, `applyBlockers`, `changedSincePriorPlan`, and human twin `DISPOSITION.md` §F commented apply sequence. Action vocabulary is closed-set and usable: `none` (66), `delete-remote-after-codex-verify` (7), `close-pr-after-codex-verify` (6), `lisa-local-worktree-remove-after-codex-verify` (9). |

---

## Independent rechecks (read-only)

Performed in the Issue #72 worktree only (no GitHub writes):

1. `git rev-parse HEAD` = `e6301fc…` on `issue/72-pre-launch-ide-development-codebase-cleanup-arch` — matches Lane E caller tip.
2. Tree equality `43b1333…` on `origin/development`, `origin/staging`, `origin/main` — matches `postWp03Context.equalTreeSha`.
3. `git stash list` still shows `stash@{0}` on `issue/ide-pull-wave-test` (unchanged inventory claim).
4. Parsed `disposition.json`: zero `applyAuthorized: true`; PRs 36/37/49 DO-NOT-TOUCH; issue/branch/WT #72 KEEP-ACTIVE; stash DO-NOT-TOUCH.

---

## Concrete non-blocking gaps (evidence improvements only)

These do **not** flip the verdict. Suggest Lane E / Codex apply prep tighten:

1. **Abbreviated tip SHAs** — 20 localBranches/worktrees entries use short tips (e.g. `011e85c`, `bba98ba`). Codex apply should require full 40-char SHAs for tip-match deletes; expand in a refresh or attach a `tipShaFull` field.
2. **`stash@{0}.tipSha: null`** — inventory should record `git rev-parse stash@{0}` (or equivalent) so DO-NOT-TOUCH can be tip-pinned without re-parsing stash list.
3. **Action label mismatch on local-only branches** — `issue/31`, `issue/35`, `promote/main/a1c3444a8447`, `promote/staging/0ac31136b8c` use `lisa-local-worktree-remove-after-codex-verify` though they are local branch deletes (local dry-run WOULD_DELETE), not worktree removals. Prefer `delete-local-after-codex-verify` (or split WT vs branch actions) so an apply agent does not call `git worktree remove` on bare local refs.
4. **Remote dry-run EXIT 1** — correctly blocked (`caller checkout changed`), but WOULD_DELETE list was taken from a failing run. Before Codex `--apply`, require a **clean-checkout** dry-run EXIT 0 artifact (stdout path + exit code) reconfirming the same 7 remotes.
5. **Raw command transcripts absent** — `commands-and-results.md` summarizes EXIT/key output only. Optional: store truncated stdout under `lane-e/raw/` for audit (redact secrets).
6. **PR #52 close vs preserve issue 51** — `close-pr-after-codex-verify` on #52 while `preserveIssueNumbers` includes 51 and remote `issue/51-*` is KEEP-FROZEN is consistent (close PR ≠ delete preserved branch), but JSON should add an explicit `constraints: ["preserve-branch-issue-51"]` on that PR row so apply cannot cascade to branch delete.
7. **No ordered apply queue in JSON** — human §F sequence is good; a machine `applyQueue: [{step, action, targets[], preconditions[]}]` would make Codex execution less dependent on markdown parsing.
8. **Class layering (SUPERSEDED PR + KEEP-OPEN remote)** for #54–#62 is correct (open PR blocks delete) but easy to misread; a `blockedBy: ["open-pr"]` field would harden actionability.

---

## What was intentionally not done by this reviewer

- No `gh` mutations, no cleanup `--apply`, no stash/worktree/branch deletes, no push/commit.
- Did not re-run full remote cleanup dry-run (would only restate EXIT 1 on dirty caller); tree/stash/HEAD spot-checks suffice for disposition review.

---

## Bottom line for Codex / Principal

**Lane E disposition is safe to treat as the post-WP03 PLAN ONLY authority.** Hard preserves (#36/#37/#49, Issue #72, stash, permanent branches) are correct. Apply remains blocked until Codex verify + Principal OK + clean-checkout dry-run EXIT 0. Address abbreviated tips / local-action labels before any live delete window.
