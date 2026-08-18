# Packet WP-I6-PHASE-PREP — Item 6 pre-rollout Phase candidate

## Identity

| Field | Value |
|---|---|
| Packet ID | WP-I6-PHASE-PREP |
| Lane | non-core Item 6 consumer-integration only |
| Repository | `linktrend/IDE-Development` |
| Phase branch | `phase/item6-consumer-integration-pre-rollout` |
| Base | `origin/development` `741e58922e7413c1097f4a58ea25e94a934af903` / tree `1affbab9035df799fdb7d723d8518e54fa6a1c00` |
| Accepted Item 6 tip | `issue/321-item-6-s6-cross-cutting-integration` `b07f8eb23220915093d7cff873e9837db6b9f504` / tree `982831f544bb65d25e883c04d2bbdbe47b9468a1` |
| Docs authority | `issue/311-item-6-connect-ide-development-five-provider-con` `128f5f2abd004f71a09f2ff630369326cb370150` / tree `e45fae62967b10bd212d909f4bf442f5f8996f6c` |
| Owned content | `core/link-integrations/**`, `tests/link-integrations/**`, Item 6 PRD/plan, this evidence directory |

## Accepted predecessor ledger

See `predecessor-ledger.json`. Independently verified:

- Exact issue/321 head/tree identity
- S0–S5 tip novel commits patch-id equal to layered commits on issue/321
- WP-I6-DOCS tip commits patch-id equal to cherry-picks on this Phase branch
- Owned-path purity vs `origin/development` (Item 6 paths only before evidence docs)
- Focused `tests/link-integrations/*.mjs` all pass; `git diff --check` clean
- Full suite not run (forbidden for this packet)

## Post-v2.4.0 gates (do not execute now)

| Packet | Gate |
|---|---|
| WP-I6-MANIFEST | Managed-core materialization for nine consumers — only after `v2.4.0` is on protected lines |
| WP-I6-INTEGRATE | Packager opens Phase PR of Item 6 novel commits into `development` — only after `v2.4.0` Packager era |
| WP-I6-HOSTED | Fast on that Phase PR; reuse the single final-combined exact-tree Full — no standalone Item 6 Full |

Do not create or mutate `phase/next-ide-development-v2.4.0` from this lane. Do not materialize managed core, publish, promote, merge, or open/update a PR from this checkpoint.

## Topology

1. Create Phase from `origin/development`
2. Fast-forward exact accepted issue/321 tip (preserves Item 6 novel commit range)
3. Cherry-pick WP-I6-DOCS from issue/311
4. Record evidence + future Packager handoff
5. Checkpoint = commit + push only

## Rollback

See `ROLLBACK.md`. Leave this Phase branch unmerged. Prefer deleting the remote Phase tip or resetting only this branch after founder authorization. Never prefer-incoming onto active v2.4.0 core branches.
