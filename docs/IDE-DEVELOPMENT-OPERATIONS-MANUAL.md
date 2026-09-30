# IDE Development Operations Manual

**Who this is for:** Carlos, LiNKtrend’s Principal. You give intent and answer questions. You do not write code, approve merges, or approve releases.

**What this is:** a short handbook for how IDE Development v3 works. It is not a technical design document.

**Companions:** [`CURRENT-STATUS.md`](./CURRENT-STATUS.md) · [`runbooks/project-setup-checklist.md`](./runbooks/project-setup-checklist.md)

---

## What IDE Development is

IDE Development is LiNKtrend’s shared way of building software. It is a System (Program-ready). One repository, `linktrend/IDE-Development`, is the system source. Every other repo gets the same playbook installed under `.ide-development/`, plus Cursor and Codex adapters.

LiNKdeveloper is a different Program and repository: the autonomous application factory. It may be built with this system. It is not this system.

---

## Roles

| Role | Who | Job |
|---|---|---|
| Principal | Carlos | State what you want. Answer questions when the orchestrator asks. One-time Project setup steps are listed in the setup checklist. |
| Orchestrator | One Cursor Project per repo, on the cursor-001 account, frontier model | Plan Phases and Issues, dispatch work, package branches into pull requests, merge when checks pass, promote `development` to `main`. |
| Helpers | Cheap subagents of the orchestrator | Routine lookups and summaries. |
| Workers | Codex CLI on the orchestrator VM, and the cursor-002 account via API | Build the Issue on a branch, commit, and push. They never open pull requests. |

Codex uses Luna High for everyday work and Sol Medium for hard work, and only while more than 25% of the allowance remains in every reported window. cursor-002 uses Grok 4.7 Medium for everyday work and Opus 5.5 Medium for hard work.

---

## The flow

1. **Idea.** You say what you want, in plain language.
2. **Plan.** The orchestrator turns that into a Phase and Issues. One GitHub Issue per Phase is the readable summary. Work IDs look like `IDE-<n>`.
3. **Build.** A worker takes one Issue on a branch named `issue/<PREFIX>-<n>-<slug>`, commits small steps, and pushes often.
4. **Package.** The orchestrator groups accepted Issue checkpoints into one `phase/*` candidate and opens one pull request into `development`. Workers do not open PRs.
5. **Check.** The exact Phase head gets Fast checks, the existing combined Verify suite, and one independent review by a different model family. The Ubuntu/macOS/Windows installer matrix runs when installer, workflow, fixture, or dependency paths change. Issue checkpoints do not start CI. Bugbot is not part of delivery eligibility.
6. **Merge.** The orchestrator merges into `development` when required Phase checks and that review pass, retaining the Phase head tree.
7. **Promote.** The orchestrator promotes the verified development content to `main`. The gate reuses the exact Phase-run inventory; it does not rerun Full. Staging is not in the active path.
8. **Deploy.** After `main`, GitHub Actions deploy automatically. The deploy standard lives in the LiNKops repo. Each deploy has a health check and a rollback.

The ledger (`ide_ledger` in the LiNKplatform Supabase project) is the orchestrator’s record of this work. Only the orchestrator writes it, through RPC. Until that ledger is live, the pilot run log stays in the Project store.

---

## When something fails

The repair ladder is fixed:

1. Retry on the everyday route (Luna or Grok) up to three times.
2. Retry once on the hard route (Sol or Opus).
3. If the work started on the hard route, try the other hard route once.
4. If it still fails, flag Carlos.

The builder is not the reviewer. The review is one exact-head pass by a different model family.

---

## What you do

- Describe the outcome you want.
- Answer questions the orchestrator cannot resolve from the repo.
- Do the one-time setup actions in [`runbooks/project-setup-checklist.md`](./runbooks/project-setup-checklist.md) when asked (Project creation, Codex sign-in, secrets in the Cursor dashboard, spend reports).

You do not approve merges or releases. You do not pick models, open pull requests, or run the repair ladder.

---

## What you can ignore

Agents choose skills and models. Shared skills arrive through a pinned LiNKskills sync. Cursor and Codex are the supported platforms. Claude Code is excluded.

---

## One-page reminder

1. You state the idea and answer questions.
2. The orchestrator plans, dispatches, packages, checks, merges, and promotes.
3. Workers build on `issue/<PREFIX>-<n>-<slug>` and push. They do not open pull requests.
4. `development` and `main` are the only long-lived branches. Deploy follows `main` automatically, with a health check and rollback.
5. If repair is exhausted, you get a flag — not a merge request to approve.
