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
(`verified: true` plus a trusted `source`). Free-text heuristics must not
convert `conclusion=failure` into gate success.

## Structured findings (no free-text pass)

Genuine `review-findings` require trustworthy structured signals only:
GitHub check `annotations_count > 0`, `conclusion=action_required`, or an
explicit classifier `--findings-present` flag. Free-text check summaries and
candidate prose must never authorize pass, findings, or advisory success.
Missing or neutral-alone remain `review-unknown` (blocking).

## Default-branch script trust boundary

The managed `check_run` workflow must checkout and execute classifier scripts
only from the protected repository default branch. Candidate head, tree,
receipts, and provider-error files are data (API) only — never a checkout
source for executable scripts. A PR cannot rewrite the classifier or
self-approve by changing candidate scripts.

## Full receipt before success

Publishing a successful `Linktrend Review Gate` status requires an exact-head
Full Suite success receipt/check. The receipt-provided `gitTree` is preserved
and compared independently to the live exact tree; never overwrite receipt tree
with live `TREE`. Missing, wrong-head, wrong-tree, or non-success Full evidence
fails closed.

## Infrastructure attempt accounting

Infrastructure retry markers must be read and persisted fail-closed. Paginated
marker comment reads use `gh api --paginate --slurp` piped through
`flatten-comment-bodies --slurp-json -` (stdin; never argv). Do not swallow
read failures with `2>/dev/null || echo []` (that resets or undercounts
attempts). Do not swallow marker publication failures with `|| true`. Shell
`pipefail` must preserve upstream `gh` failures as HOLD.
