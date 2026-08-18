# Rollback — Item 6 Phase pre-rollout candidate

## Safe default

Leave `phase/item6-consumer-integration-pre-rollout` unmerged. Pre-rollout checkpoints are reversible by abandoning the Phase tip.

## If the Phase tip must be withdrawn

1. Do not merge, promote, or open a PR.
2. Do not rewrite unrelated issue/core branches.
3. After founder authorization, delete or retire only `phase/item6-consumer-integration-pre-rollout` (remote + local).
4. Accepted issue tips remain the durable source:
   - issue/321 `b07f8eb23220915093d7cff873e9837db6b9f504` / tree `982831f544bb65d25e883c04d2bbdbe47b9468a1`
   - predecessors S0–S5 / DOCS recorded in `predecessor-ledger.json`
5. If a future post-v2.4.0 Phase PR was opened by mistake before authorization: close it as draft-abandoned; do not merge; withdraw any Review Ready status via the normal-token publisher `action=withdraw` path only.

## Conflict / repair policy

- No prefer-incoming
- No silent adoption of active v2.4.0 core branches
- Bounded ordinary repairs only on this Phase branch; stop after 3 attempts and record a blocker

## Content recovery

Rebuild the Phase from `origin/development` by fast-forwarding the accepted issue/321 tip and cherry-picking WP-I6-DOCS from issue/311, then restoring this evidence directory from git history.
