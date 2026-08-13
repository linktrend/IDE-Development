# Terra Medium Orchestrator and Verification Runbook

## Role

Terra Medium is the sole orchestrator, integrator, and factual verifier. Verification means proving that the assigned packet was actually completed against its acceptance criteria. It is not a separate architecture, security, or product audit.

## 1. Preflight

1. Work only in `/Users/linktrend/Projects/IDE Development` and isolated worktrees created from it.
2. Read root `AGENTS.md` and this planning directory.
3. Confirm the approved goal exactly matches `TERRA-GOAL.md` or record approved amendments.
4. Run `git fetch origin --prune`.
5. Record:
   - `origin/development` as `B0`;
   - local status;
   - all worktrees and branches;
   - all open PRs;
   - the unrelated concurrent feature branch/worktree/PR inventory;
   - active rulesets and required status contexts;
   - installed coordinator/runner services and rollback state.
6. Stop if the root is dirty or a proposed packet path is already owned by the concurrent feature.
7. Create `phase/streamlined-delivery` from `B0`. Only Terra may update it.

## 2. Issue and worktree creation

For each packet:

1. Create/reuse one GitHub Issue with the packet ID in the title.
2. Use `scripts/gitops/create_issue_branch.py --prefer-worktree`.
3. Confirm branch is `issue/<number>-<slug>` and worktree is clean.
4. Confirm `git rev-parse HEAD` equals the correct wave base.
5. Record issue, branch, worktree, base, and owned paths before dispatch.

Do not create packet PRs.

## 3. Luna dispatch

Resolve the installed Codex CLI model/profile that is actually GPT-5.6 Luna. Do not guess the model ID. Record the resolved model and Codex CLI version.

Use Codex CLI, high reasoning, and the packet worktree. Never use Cursor CLI. Supply the packet file, frozen interfaces, base SHA, branch, owned paths, concurrent-feature warning, and response schema in the prompt.

Command shape:

```text
codex exec -C <worktree> --model <verified-luna-model-id> \
  -c 'model_reasoning_effort="high"' --sandbox danger-full-access -
```

The executor must not open PRs, merge, promote, touch live rulesets, install host services, or edit paths outside the packet.

## 4. Attempt policy

Attempt 1:

- Dispatch the complete packet.
- Wait for a terminal response.
- Terra verifies actual repository state.

If verification fails:

- Produce a short list of exact unmet acceptance criteria, commands, outputs, and paths.
- Send the same Luna session one correction attempt limited to those failures.

Attempt 2:

- Terra repeats full packet verification, not only the corrected command.
- If PASS, continue.
- If FAIL, stop the Luna executor. Do not dispatch a third Luna attempt.
- Terra takes over and completes only that packet in its assigned worktree.

Other packet agents continue unless their work depends on the failed packet or overlaps the takeover paths.

## 5. Packet verification checklist

Terra must independently confirm:

- starting SHA and ancestry;
- only owned paths changed;
- no concurrent-feature files changed;
- every required file exists;
- required positive tests pass;
- every required negative probe rejects correctly;
- `git diff --check` passes;
- evidence exists in the packet's stable directory;
- evidence contains no credentials or secret values;
- final worktree is clean;
- branch is pushed;
- local SHA equals `git ls-remote` for that branch.

Luna's narrative is never proof.

## 6. Wave integration

After every packet in a wave passes:

1. Fetch all packet branches.
2. Recheck changed-path intersections.
3. Merge branches into `phase/streamlined-delivery` serially in packet-number order with non-squashing merges so exact Issue commits remain ancestors.
4. On conflict, inspect both changes. Never use blanket ours/theirs or prefer-incoming.
5. Run every packet test against the combined Phase tree.
6. Run the wave integration gate.
7. Record `B1` or `B2` and push the Phase checkpoint.
8. Do not mark the Phase review-ready and do not open another PR.

## 7. Concurrent unrelated feature

- Never delete, reset, rename, rebase, force-push, or write inside its branch/worktree.
- At each wave boundary compare its changed files with the next wave ownership map.
- If overlap appears, serialize only the affected packet and notify the executing agent of the frozen boundary.
- Before final seal, merge the latest remote `development` into the Phase branch once.
- Preserve both features and rerun all affected tests.
- During final promotion, hold a short branch release lock; the other agent may continue committing to its own branch.

## 8. Current-system override

For this feature:

- packet tips remain checkpoints;
- current Packager/Integrator schedules are not used;
- Terra creates one Phase PR directly with normal GitHub authentication;
- tests and Bugbot cannot be bypassed;
- legacy status-rule bypass is allowed only when the old automation context is the sole blocker and equivalent replacement evidence is green;
- snapshot the exact rule before mutation;
- disable only the blocking target-branch rule;
- merge the exact verified candidate;
- immediately apply and verify the replacement active rule;
- on restore failure, stop before further promotion and report the protection failure.

## 9. Wave 3 operational verification

Terra—not Luna—must verify live facts:

- coordinator installation points to the exact candidate/release;
- launchd service is healthy;
- credentials are masked and absent from artifacts;
- queue/status commands work;
- fast timing target is measured;
- one-heavy/two-fast limits are enforced;
- pressure pause works;
- cancellation removes obsolete containers;
- restart recovery works;
- two failures stop and create one alert;
- GitHub receives the stable status contexts;
- Bugbot applies to the sealed exact candidate;
- staging/main reuse the matching receipt;
- branch rules are active after promotion;
- rollback instructions are tested or dry-run verified.

## 10. Final report

Report:

- `B0`, `B1`, and `B2`;
- every Issue, branch, executor, attempts used, packet SHA, and verification result;
- any Terra takeover and why;
- Phase PR, staging PR, main PR;
- merge SHAs and tree identities;
- release tag and artifact digests;
- test commands/results;
- fast/full/release timing;
- peak resource and concurrency evidence;
- container/worktree cleanup evidence;
- ruleset before/after evidence;
- concurrent-feature preservation evidence;
- installed service version and rollback command;
- unresolved issue or `none`.

