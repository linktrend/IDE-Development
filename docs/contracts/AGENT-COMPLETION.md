# Agent Completion Contract

**Status:** Active v3 (IDE-28).
**Owner:** IDE Development

What finished means for a worker on one Issue, and for the orchestrator accepting a pull request.

## Worker done

A worker is done when all of the following are true:

1. The work is on `issue/<n>-<slug>`, committed, and pushed. Commit and push often. Never open a pull request.
2. Fast deterministic checks passed before the push. Run `python3 scripts/gitops/run_delivery_profile.py fast` (the command CI job `Linktrend Fast Checks` runs) plus every check the Issue names.
3. The final reply ends with a short lessons note.

Those local checks do not replace the one Full CI run on the pull request head.

## Orchestrator acceptance

The orchestrator decides whether a Phase is one pull request or several into `development`.

Accept a pull request when all of the following hold on the exact head SHA:

1. `Linktrend Fast Checks` and `Linktrend Branch Source Policy` are green.
2. Exactly one Full CI run, job `Verify IDE Development`, is green on that head.
3. One independent review of that head approves. The reviewer is a model from a different family than the author (a GPT model for Grok or Opus work; a Claude or Grok model for Codex work). Bugbot is optional.
4. A commit after that review has a new review of the new head. The review record states that it covered at least the delta.

Merge when the required checks and the Full run are green on the exact reviewed head and the review approves. Promotion to `main` reuses that result with no re-review. The `main` gate checks that the promoted tree equals a `development` commit whose Full CI was green.

## Blocked / flag Carlos

Review `REQUEST_CHANGES` and CI failures both count as failed attempts on the current repair rung. Until a live ledger exists, `scripts/orchestrator/runlog.py` records the rung in `repair_rung` (`0`, `1`, or `2`). `scripts/orchestrator/watchdog.py` recommends the next rung.

1. Rung 0: a Luna (Codex) or Grok (cursor-002) worker, up to 3 attempts.
2. Rung 1: a stronger model (Sol or Opus), one attempt.
3. Rung 2: when the Issue started on Sol or Opus, the other of those two, one attempt.
4. The orchestrator then flags Carlos with a short plain-language question.

## Retired

Retired, and not part of this contract: Review Ready status and its publisher, completion-gate evidence, the review-gate classifier, the repair observer, promotion receipts, the packager, the delivery controller, Lisa, and staging.
