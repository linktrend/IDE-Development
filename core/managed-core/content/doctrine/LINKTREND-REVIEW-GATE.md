# Linktrend Review Gate

**Status:** Active contract for IDE Development Update 1 / WP-U01
**Managed check context:** `Linktrend Review Gate`
**Observed provider check:** `Cursor Bugbot` (never required after migration)

## Rule

Bugbot remains the final-candidate semantic reviewer after the exact Full Suite
succeeds. The managed gate classifies the provider result and publishes one
required context named **`Linktrend Review Gate`**.

## Outcomes

| Outcome | Gate | Notes |
|---|---|---|
| `review-passed` | success | Exact-head Bugbot completed with no blocking findings |
| `review-findings` | failure | Genuine unresolved findings remain blocking |
| `review-failed` | failure | Provider ran but failed for review/policy reasons |
| `advisory-unavailable` | success (advisory) | Verified quota/spending/outage/provider error; founder alert; never labeled as Bugbot pass |
| `review-unknown` | failure | Missing, malformed, forged, stale, wrong-head, neutral-alone, or ambiguous |

## Hard rules

1. Do not request final-candidate Bugbot before Full Suite success.
2. Bind classification to exact repository, PR, commit, and Git tree.
3. A new commit invalidates the previous gate outcome.
4. Retry infrastructure failures at most twice for the same exact candidate; a third attempt is rejected.
5. Neutral conclusions alone are never `advisory-unavailable`.
6. Replace raw `Cursor Bugbot` required contexts with `Linktrend Review Gate` in Integrator, Packager, Promoters, repair observer defaults, protection planner, ruleset plan, and repository variables.
7. Configured independent-review fallback must not be the implementer and becomes stale after a head change.
8. A same-account review comment never satisfies a required GitHub approving review.
9. Undocumented task-level review HOLDs are forbidden after configured gates pass.

## Rollback

Genuine findings and `review-unknown` remain blocking. Do not prefer-incoming.
Do not claim Bugbot passed under `advisory-unavailable`.

## Durable founder alert

When classification sets `alertFounder`, the managed workflow must publish a
deduplicated GitHub issue (marker `<!-- linktrend-review-gate-alert: <sha> -->`)
with the sanitized alert body. In-memory fields alone are not sufficient.
Dedupe inspects prior alert **issue bodies** via `gh api --paginate --slurp`
piped into `flatten-issue-bodies --slurp-json -` (stdin; never argv) and fails
closed when that state cannot be read or parsed. Alert publish failure is
fail-closed.

## Trusted unavailability evidence

`advisory-unavailable` requires structured verified provider evidence
(`verified: true` plus a trusted `source`) **and** a trusted evidence channel
assigned by the workflow loader — never by candidate-controlled JSON.
Trusted channels: `github_check_run`, `repair_observer_record`,
`operator_privileged_input`, `provider_status_api`.
Candidate repository files (`.linktrend/review-gate-provider-error.json`) and
`candidate_repository_file` provenance never authorize advisory success, even
when they plant an allowlisted source string. Free-text heuristics must not
convert `conclusion=failure` / `neutral` into gate success.

When the channel is `github_check_run`, trust requires an independently
authenticated producer identity that candidate code cannot forge:

1. GitHub-assigned `check_suite.id` must equal the allowlisted workflow run's
   `check_suite_id` (URL fields alone are not membership).
2. A successful Actions job for that run must own the check via
   `check_run_url` / check-run id (rejects borrowed `details_url` with a forged
   summary on a different check object).
3. The producer workflow `path` must be allowlisted
   (`.github/workflows/linktrend-repair-observer.yml`), and either the run
   executed on the repository default branch or the Contents API blob SHA of
   that workflow file at the run head equals the default-branch blob.
4. The producer workflow run and check conclusions must be `success`.
5. Exact `head_sha` is required on both the check and the workflow run.

App slug (`github-actions`) plus check name alone are not provenance. Fail
closed when suite/job membership, successful producer output, run identity, or
default-branch blob identity cannot be established.

## Structured findings (no free-text pass)

Genuine `review-findings` require trustworthy structured signals only:
GitHub check `annotations_count > 0`, `conclusion=action_required`, or an
explicit classifier `--findings-present` flag. Free-text check summaries and
candidate prose must never authorize pass, findings, or advisory success.
Missing or neutral-alone remain `review-unknown` (blocking). Findings take
precedence over provider-unavailability evidence.

## Default-branch script trust boundary

The managed `check_run` workflow must checkout and execute classifier scripts
only from the protected repository default branch. Candidate head/tree are data
(API) only — never a checkout source for executable scripts. A PR cannot rewrite
the classifier or self-approve by changing candidate scripts.

## Full receipt before success

Publishing a successful `Linktrend Review Gate` status requires an exact-head
Full Suite success receipt/check from a **trusted GitHub check run**
(`evidence_channel=github_check_run`) bound to the allowlisted Full producer
workflow (`.github/workflows/linktrend-integrator-merge.yml`) via the same
producer run/job/check-suite identity rule as provider checks (suite id match,
successful job ownership of the check-run id, allowlisted `path`, default-branch
execution or matching Contents API workflow blob SHA, successful run/check
conclusions, exact head on check and run). Candidate-controlled
`.linktrend/full-suite-receipt.json` files never authorize success. App slug
plus check name (`Linktrend Full Suite` / `full` / `full-gate`) and borrowed
`details_url` values alone are not enough. The receipt-provided `gitTree` is
preserved and compared independently to the live exact tree; never overwrite
receipt tree with live `TREE`. Missing, wrong-head, wrong-tree, untrusted
channel, unbound producer identity, or non-success Full evidence fails closed.

## Infrastructure attempt accounting

Infrastructure retry markers must be read and persisted fail-closed. Paginated
marker comment reads use `gh api --paginate --slurp` piped through
`flatten-comment-bodies --slurp-json -` (stdin; never argv). Do not swallow
read failures with `2>/dev/null || echo []` (that resets or undercounts
attempts). Do not swallow marker publication failures with `|| true`. Shell
`pipefail` must preserve upstream `gh` failures as HOLD.
