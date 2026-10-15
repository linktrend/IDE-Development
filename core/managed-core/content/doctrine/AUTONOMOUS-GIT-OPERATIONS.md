# Git operations doctrine

**Status:** Active system-source doctrine. This repository is the
IDE Development source and is not a consumer install target.

## Normal flow

Implementers work on short-lived `issue/*` branches, checkpoint with one
focused commit, and stop. Accepted issue commits are integrated serially on a
`phase/*` branch. The Phase Packager/Coordinator
(`scripts/gitops/packager_coordinator.py`) opens one Phase PR into
`development`; retained `packager_discover.py` is not that component. The
agent-agnostic delivery controller (`scripts/gitops/delivery_controller.py`)
is the merge and promotion actor: it evaluates exact PR heads, merges through
GitHub protection, promotes staging on receipt identity, and completes main
only after explicit founder approval. Review Ready publishes a status for
Packager discovery; it does not itself trigger a merge. No implementer opens,
merges, or promotes a PR.

Checkpoints do not trigger managed CI. The Phase PR runs hosted ARM64 fast
checks. Only an exact final seal may trigger the full suite. Bugbot is disabled. A
successful receipt is reused for promotion only when all frozen identity
digests match. Main promotion requires Carlos's explicit approval.

## v2.5 Issue checkpoint (`V25_BOOTSTRAP_LEAN`)

Issue checkpoints are accepted from exact pushed commit/tree, scoped diff,
focused tests, one provider-independent narrow review bound to that exact
identity, and manifest evidence. Review
Ready publication, `AUTOMATION_TOKEN`, Issue PRs, hosted completion status,
and legacy publisher status are nonrequirements. Legacy publisher/status
outcomes are `WAIVED_LEGACY_GATE`, never PASS, and never bypass substantive
proof. Review Ready does not itself trigger a merge and is not Issue-checkpoint
proof. Administrator recovery is a named exact-head exception after replacement
proof: protection snapshot, `gh pr merge --admin --match-head-commit` first,
minimum temporary exception only if needed, exact authorized merge, immediate
restore and readback.

## Disabled paid review and native independent evidence

Canonical policy is `review.bugbot="disabled"`; legacy `final-candidate-only`
normalizes to disabled and cannot re-enable paid review. No pipeline component
posts a Bugbot trigger or treats its status, absence, quota, or request marker as
approval. General Cursor coding and GitHub integrations remain available.

`NativeReviewerAdapter` in `scripts/gitops/independent_review_convergence.py`
owns a fresh native Codex subprocess with read-only sandbox and approval-never.
It owns fresh authenticated GETs for the same-repository open PR, protected
`development` branch and exact head commit/tree. The complete diff starts at
that current protected base; a supplied handoff base is equality-only diagnostic
data. Local Git ancestry must prove that base is included. PR/head/tree/branch
and protected base must remain unchanged after review and on report verification.
No caller-supplied PR JSON or base flag establishes scope. It also binds
start/end clean HEAD/tree, fresh runtime thread, exact changed paths and
structured clean report. Its in-memory result is the producer boundary; copied
JSON/logs, actor names, requested model names, and prior process output are not
proof. Effective model attestation is not claimed.

The controller's `verify-development --native-review-worktree <clean-checkout>`
(and `merge-development` with the same option plus exact receipt/identity and
baseline inputs) owns this adapter. A trusted in-process orchestrator can run
one review and pass `adapter.verify_report` with that report to
`deliver_phase_to_development`; this preserves a single fresh review through
eligibility and merge. No verifier can be installed by JSON, environment module
path or an accepted flag. Runtime absence, non-clean/moved candidate, failed or
incomplete native turn, stale report, self-review, findings or replay block.
Without the owned producer, candidate review remains unavailable, never green.
No real native/provider smoke is implied by mocked tests.

Required Fast, application CI, Full receipt and all frozen receipt identities
remain mandatory. Native review does not create a GitHub approving review or
satisfy external required-approvals policy. Existing protections retaining
`Cursor Bugbot` or `Linktrend Review Gate` need separately authorized migration;
this source change edits no live settings and fabricates no replacement status.

## Stop conditions

Stop on a changed sealed head, missing or stale evidence, failed protection or
source policy, an unresolved conflict, a third infrastructure attempt, or a
third sealed candidate. Preserve the prior evidence and report the reason;
never repair by choosing one side automatically.

## Independent-review convergence

Pre-land independent review is governed by
`scripts/gitops/independent_review_convergence.py`. One session tracks one
exact repository, base, candidate, tree, scope, and reviewer policy. Findings
keep a durable ledger and stable identity: different nonempty fingerprints
never fuzzy-merge, and only wording variants of the same identity may match.
Ingest requires exact `headSha` and `gitTree` and a nonempty list of nonempty
`paths`. Malformed or non-object findings are `malformed_reviewer_output`
with truthful HOLD and no cycle consumption. One review produces one
consolidated repair batch and one observational repair cycle. There is no
arbitrary terminal cycle cap. Unattended work pauses after three cycles. A
recorded founder `continue until clean` instruction authorizes further
progressing cycles without repeated approval. `apply_repair` fails closed
after that pause without that authority, and after `review_stalled` / HOLD,
preserving the exact stalled identity. `apply_repair` requires `touched_paths`
as a nonempty list of nonempty strings and rejects a string or malformed
paths before changing state. Repair cancels or invalidates any live
reviewer. First-seen findings on touched paths are `introduced_by_repair`
and remain blocking; only untouched paths are
`newly_discovered_in_unchanged_scope`. Same-identity
severity reductions count as measurable progress. Compute units use an
explicit accounting path so `maxComputeUnits` can stall truthfully. Stop only
for repeated unresolved findings, two no-progress cycles, repair
reintroduction, redesign/new authority, infrastructure retry exhaustion, or
an explicit resource limit. Those stops publish a truthful HOLD /
`review_stalled` founder packet. `evaluate_progress` short-circuits HOLD and
`review_stalled` and cannot rewrite timeout, silence, or malformed HOLD to
clean or in-progress. `ingest_review` fails closed on HOLD /
`review_stalled`; empty findings cannot mark pending or stalled identities
corrected or fabricate clean after a stop. Implementers never review their
own work. Reviewer silence or timeout is never clean and cannot authorize
Full or repair until a valid exact-bound review transition explicitly clears
the stop. A narrow repair invalidates only focused and delta evidence for its
touched paths; prior exact review and Full records remain historical, with
unchanged path evidence reusable. The final combined Full is run once for the
sealed candidate and its exact receipt is reused for staging and main.
Full never runs while HOLD or `review_stalled`.

## External boundary

This doctrine does not perform GitHub, host, Docker, consumer, release, or
billing operations. W3 operators use the redacted inventory and cleanup plan
under `scripts/external/cleanup_plan.py`, with separate repository and host
scopes. The default is a plan with zero external mutation; live apply is
outside this repository executor's authority.
