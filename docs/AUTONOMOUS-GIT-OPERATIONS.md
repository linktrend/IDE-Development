# Git operations doctrine

**Status:** Active system-source doctrine. This repository is the
IDE Development source and is not a consumer install target.

## Normal flow

Implementers work on short-lived `issue/*` branches, checkpoint with one
focused commit, and stop. Accepted issue commits are integrated serially on a
`phase/*` branch. The Phase Packager/Coordinator
(`scripts/gitops/packager_coordinator.py`) opens one Phase PR into
`development`; retained `packager_discover.py` is not that component. The
delivery controller and promotion gates evaluate exact PR heads. No implementer
opens, merges, or promotes a PR.

Checkpoints do not trigger managed CI. The Phase PR runs hosted ARM64 fast
checks. Only an exact final seal may trigger Bugbot and the full suite. A
successful receipt is reused for promotion only when all frozen identity
digests match. Main promotion requires Carlos's explicit approval.

## Stop conditions

Stop on a changed sealed head, missing or stale evidence, failed protection or
source policy, an unresolved conflict, a third infrastructure attempt, or a
third sealed candidate. Preserve the prior evidence and report the reason;
never repair by choosing one side automatically.

## Independent-review convergence

Pre-land independent review is governed by
`scripts/gitops/independent_review_convergence.py`. One session tracks one
exact repository, base, candidate, tree, scope, and reviewer policy. Findings
keep a durable ledger and stable identity. One review produces one
consolidated repair batch and one observational repair cycle. There is no
arbitrary terminal cycle cap. Unattended work pauses after three cycles. A
recorded founder `continue until clean` instruction authorizes further
progressing cycles without repeated approval. Stop only for repeated
unresolved findings, two no-progress cycles, repair reintroduction,
redesign/new authority, infrastructure retry exhaustion, or an explicit
resource limit. Those stops publish a truthful HOLD / `review_stalled`
founder packet. Implementers never review their own work. Reviewer silence
or timeout is never clean. A later source change invalidates prior review
and Full evidence. Full does not run until required independent review is
clean unless repository policy explicitly requires Full first.

## External boundary

This doctrine does not perform GitHub, host, Docker, consumer, release, or
billing operations. W3 operators use the redacted inventory and cleanup plan
under `scripts/external/cleanup_plan.py`, with separate repository and host
scopes. The default is a plan with zero external mutation; live apply is
outside this repository executor's authority.
