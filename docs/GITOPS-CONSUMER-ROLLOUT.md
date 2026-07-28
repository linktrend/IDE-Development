# GitOps consumer rollout (GITOPS-01)

**Status:** Rollout plan — read-only drift posture until wired
**Date:** 2026-07-28
**PR:** `issue/GITOPS-01-review-packager-pipeline` on IDE Development

**SOT:** `docs/AUTONOMOUS-GIT-OPERATIONS.md` · `docs/adr/0003-autonomous-ship-pull-promote.md`

This PR updates **IDE Development only**. It does **not** edit consumer repositories.

---

## What this PR does

- Review Packager workflow (`linktrend-review-packager.yml`)
- Staging promote window Tue/Fri **10:00** Asia/Taipei (was 08:00 in older ADR table)
- Named CI gates: `core/github/CI-GATE-CONTRACTS.md`
- Review-ready record: `core/github/REVIEW-READY.md` + helper scripts
- Lisa/OpenClaw **follow-up contracts** (no openclaw edits here)
- Consumer rollout plan (this document)

---

## What this PR does NOT do

- Edit `openclaw_prime` Lisa personality or cron jobs
- Run `wire-repo.sh` or `sync-managed-workflows.sh` on consumers
- Change consumer `ci.yml` or repo-specific workflows
- Enable Bugbot on consumers
- Set `LINKTREND_INTEGRATOR_REQUIRED_CHECKS` on consumers
- Apply development merge rulesets on consumers
- Modify LiNKplatform / LiNKskills / LiNKbrain / LiNKsites / LiNKdeveloper / LiNKlibraries / LiNKautowork branches or workflows

Consumer adoption is **staged** only after:

1. this change reaches IDE Development’s **default branch (`main`)** and first-adopter smoke passes, and
2. **Bugbot mention-only** (`manualTriggerOnly`) is confirmed per repository (`docs/contracts/BUGBOT-MENTION-ONLY.md`).

Merging to `development` alone does **not** activate new scheduled workflows. Code alone does **not** enforce mention-only.

---

## Consumer repos (locked order)

Drift reports and Ship/Pull waves use this **exact sequential order** (one repo at a time):

| # | Repo (disk) | GitHub slug (typical) | Notes |
|---|---|---|---|
| 1 | IDE Development | `linktrend/IDE-Development` | **First adopter** — same regime as consumers |
| 2 | openclaw_prime | `linktrend/openclaw_prime` | Lisa runtime; follow-up PR for personality |
| 3 | LiNKplatform | `linktrend/LiNKplatform` | |
| 4 | LiNKskills | `linktrend/LiNKskills` | |
| 5 | LiNKbrain | `linktrend/LiNKbrain` | |
| 6 | LiNKsites | `linktrend/LiNKsites` | |
| 7 | LiNKdeveloper | `linktrend/LiNKdeveloper` | |
| 8 | LiNKlibraries | `linktrend/LiNKlibraries` | |
| 9 | LiNKautowork | `linktrend/LiNKautowork` | |

**Read-only drift report posture:** Before wiring, operators may compare each consumer against IDE Development managed templates (`cmp` / `scripts/sync-managed-workflows.sh --dry-run`) and record gaps without mutating consumer repos.

---

## Activation constraint (GitHub default branch)

GitHub loads **scheduled** workflows and reliable `workflow_dispatch` definitions from the repository’s **default branch** (for IDE Development: `main`).

Therefore:

1. Merging PR #19 **only into `development` does not activate** the new Review Packager cron (or other new workflow files) for the org.
2. The corrected central change must pass IDE Development **`development` → `staging` → `main`** first.
3. Only after the workflows exist on the **default branch (`main`)** can Packager/promote schedules run reliably and be manually smoked with confidence.
4. **Only after that first-adopter smoke on `main`** should consumer rollout (Stage 2+) begin.

A one-time administrator bootstrap merge may be used to land this PR into `development` while Bugbot is unavailable due to spending limits — that is **not** a permanent product bypass.

---

## Staged rollout (after GITOPS-01 reaches default branch)

### Stage 0 — Promote through IDE Development protected branches

1. Independent non-Bugbot review of PR #19 (or successor) into `development`.
2. Integrator or documented one-time admin bootstrap merge into `development` (Bugbot may be unavailable; do not add a permanent Bugbot bypass).
3. Tue/Fri staging promote (or manual) of the combined candidate via `promote/staging/*` PR after staging-gate on that PR head.
4. Monday main package + Principal Approve of exact staging SHA **and** promote PR head; merge via `promote/main/*` only.
5. Confirm workflows are present on `main` (default branch).

### Stage 1 — IDE Development smoke on default branch

1. Confirm managed workflows in `.github/workflows/` on `main` match `core/github/managed-workflows/`.
2. Run `scripts/verify-ide-development.sh`.
3. Set repo variables on IDE Development as needed:
   - `LINKTREND_INTEGRATOR_REQUIRED_CHECKS` (e.g. `Verify IDE Development`)
   - `LINKTREND_BUGBOT_REVIEW_COMMAND` (default `cursor review` if unset)
   - `LINKTREND_STAGING_GATE_CHECKS` / `LINKTREND_RELEASE_GATE_CHECKS` if non-default
4. Apply development merge ruleset: `./scripts/apply-development-merge-ruleset.sh`
5. Smoke: functional commit → mark/commit review-ready → Packager `workflow_dispatch` → draft PR → fast-gate → ready + Bugbot (when funded) → Integrator.

### Stage 2 — Wire sync managed workflows

After Stage 1 smoke is green on IDE Development **default branch**:

```bash
# Per consumer (from IDE Development repo root):
./scripts/wire-repo.sh /Users/linktrend/Projects/<ConsumerRepo>
# or sync workflows only:
./scripts/sync-managed-workflows.sh /Users/linktrend/Projects/<ConsumerRepo>
```

Follow consumer order 2–9. **Never overwrite** consumer `ci.yml`.

Verify each consumer:

```bash
cmp core/github/managed-workflows/linktrend-review-packager.yml \
  /path/to/consumer/.github/workflows/linktrend-review-packager.yml
# repeat for other managed files
```

### Stage 3 — `LINKTREND_INTEGRATOR_REQUIRED_CHECKS` per repo

For each wired consumer:

1. Identify primary verify workflow job display name(s) on PRs to `development`.
2. Set GitHub Actions repository variable `LINKTREND_INTEGRATOR_REQUIRED_CHECKS` (comma-separated).
3. Map job names to gate ids in consumer docs or workflow comments (`fast-gate` / `staging-gate` / `release-gate` per `CI-GATE-CONTRACTS.md`).
4. Optionally set `LINKTREND_STAGING_GATE_CHECKS` and `LINKTREND_RELEASE_GATE_CHECKS`.
5. Optionally set `LINKTREND_BUGBOT_REVIEW_COMMAND` (exact default if unset: `cursor review`).

Example (IDE Development):

```
Verify IDE Development
```

### Stage 4 — Bugbot checklist

Per repo, complete `core/checklists/BUGBOT-INHERITANCE.md`:

1. Enable Bugbot on Cursor dashboard for the repo.
2. Confirm `Cursor Bugbot` check on test PR to `development`.
3. Apply ruleset via `apply-development-merge-ruleset.sh`.
4. Record `Bugbot: enabled | blocked:<reason>` in wire/adoption report.

Integrator merges only when `Cursor Bugbot` = **success** and `fast-gate` checks = success.

---

## GitHub plan limitations

Plan for these constraints when rolling out to nine repos:

| Limitation | Impact | Mitigation |
|---|---|---|
| **Actions minutes** | Five managed workflows × cron schedules × 9 repos adds recurring minute usage (Packager Tue/Fri, Staging Tue/Fri, Integrator on PR events, branch policy, staging-to-main Mon) | Monitor org usage; stagger manual dispatches during rollout; use `workflow_dispatch` smoke sparingly |
| **Rulesets** | `apply-development-merge-ruleset.sh` requires org/repo admin and GitHub ruleset availability | Run from operator account with admin; document repos where rulesets blocked |
| **Bugbot availability** | Bugbot requires Cursor team + GitHub integration; not all repos may be connected day one | Complete checklist per repo; Integrator must not force-merge without Bugbot or alternate review path |
| **Concurrent workflow limits** | Burst of Packager + Integrator on same repo | Managed workflows use concurrency groups; Lisa processes repos sequentially |
| **Private repo Actions** | Minutes count against plan quotas | Prioritize IDE Development + openclaw_prime before lower-activity repos |
| **Org workflow permissions** | `GITHUB_TOKEN` may need explicit permissions for PR create/merge | Templates already set `permissions:`; verify org default token policy |

---

## Drift detection (read-only)

Before Stage 2, optional drift report per consumer:

| Check | Command / action |
|---|---|
| Managed files present | `ls consumer/.github/workflows/linktrend-*.yml` |
| Byte match templates | `cmp` vs `core/github/managed-workflows/*` |
| `.cursor` symlink | `readlink consumer/.cursor` → IDE Development |
| Integrator variable | `gh api repos/linktrend/REPO/actions/variables/LINKTREND_INTEGRATOR_REQUIRED_CHECKS` |
| Bugbot on PR | Manual or last PR check list |
| Review-ready helpers | `scripts/mark-review-ready.sh` available via wired `.cursor` |

Record gaps in adoption notes; do not auto-fix consumers from GITOPS-01 PR.

---

## Related documents

- `docs/GITOPS-CONSUMER-ROLLOUT.md` (this file)
- `docs/contracts/LISA-OPENCLAW-FOLLOW-UP.md`
- `docs/contracts/LISA-MAIN-APPROVE-DISPATCH.md`
- `core/github/managed-workflows/README.md`
- `core/checklists/BUGBOT-INHERITANCE.md`
- `scripts/wire-repo.sh`, `scripts/sync-managed-workflows.sh`, `scripts/backfill-managed-workflows.sh`
