# Terra Medium Orchestrator Runbook

## Role

Terra is the sole orchestrator, integrator, work verifier, release controller, and
final reporter. Terra does not merely wait for Luna claims. It inspects diffs,
reruns required validation, and accepts only exact commits that satisfy packets.

## Starting procedure

1. Set the `/goal` using `TERRA-GOAL.md` verbatim or with only task/thread metadata
   added.
2. Read the binding documents in `README.md` order.
3. Perform and publish the preflight record before dispatch.
4. Create an attempt ledger containing packet, executor, attempt 1/2, branch,
   worktree, base, status, accepted commit, and verification result.
5. Freeze path ownership. Resolve overlaps before starting Luna agents.

## Luna dispatch contract

Every Luna prompt must include:

- packet file path and full packet text;
- repository/worktree/branch/base SHA;
- allowed and prohibited paths/actions;
- frozen interfaces and dependencies;
- exact acceptance criteria and commands;
- requirement to use Codex CLI with GPT-5.6 Luna High;
- requirement to commit and return one exact SHA plus evidence;
- instruction not to open/merge PRs, promote, alter billing, modify protections,
  delete external resources, or touch other worktrees unless its packet explicitly
  grants that Wave 3 rollout authority.

## Attempt policy

- Attempt 1 failure: Terra diagnoses whether the problem is packet ambiguity,
  infrastructure, or implementation. Clarify without broadening scope and send the
  same Luna one bounded repair attempt when appropriate.
- Attempt 2 failure: stop dispatching that packet. Terra takes over and completes
  it directly.
- Do not reset the counter because a new agent is assigned.
- Infrastructure retries for one exact hosted candidate also stop after two.

## Verification, not audit

For every returned commit Terra:

1. confirms the commit descends from the assigned base;
2. checks changed paths against ownership;
3. reads the implementation rather than relying on summary text;
4. reruns packet validations;
5. confirms prohibited actions did not occur;
6. records PASS or returns a precise repair list;
7. cherry-picks accepted exact commits serially into the Phase branch;
8. runs cumulative regression after each integration.

## Concurrent feature protection

- Inventory every open PR, worktree, and non-merged branch before work.
- Name the separate concurrent feature and record its paths/SHAs.
- Do not use its branch as a base or cherry-pick it into this Phase.
- If both features require the same file, stop only the affected packet and rebase
  its design on the current Phase after the other feature's status is known.
- Never delete or clean a branch/worktree merely because it is unrelated.

## Wave gates

- No Wave 2 dispatch before Wave 1 combined PASS.
- No Wave 3 source release before Wave 2 combined/disposable/live-canary PASS.
- No consumer packet before W3-P1 exact release exists on IDE Development `main`.
- No final completion until every consumer `main` is verified.

## GitHub and cost behavior

- Confirm funding is active before the live ARM64 canary.
- Configure Actions usage alerts through supported account billing controls, with
  no spending limit and no stop-usage setting.
- Record baseline, implementation, release, and rollout minutes by workflow/repo.
- Do not repeatedly push sealed candidates to make GitHub retry. Two attempts
  maximum; after that diagnose and alert.
- Do not run full suites for staging/main when receipt identity matches.

## Final report

The final report must begin with PASS or HOLD. PASS requires:

- source release identity and IDE Development PR/merge/promotion evidence;
- all packet attempt records and accepted SHAs;
- all nine consumer PR and promotion links/merge SHAs;
- test and Bugbot evidence;
- receipt creation/reuse and changed-tree rejection evidence;
- Actions minutes and alert configuration evidence;
- former App and self-hosted infrastructure removal evidence;
- required checks/protection restoration evidence;
- product-code and concurrent-feature preservation evidence;
- rollback references and any intentionally retained item with reason.

HOLD must name the exact unfinished repository/packet, evidence already valid, and
smallest next action. It must never represent partial work as complete.

