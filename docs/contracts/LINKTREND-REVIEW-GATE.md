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
