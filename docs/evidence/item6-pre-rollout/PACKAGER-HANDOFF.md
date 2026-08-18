# Packager handoff — Item 6 Phase candidate (after v2.4.0)

## Authority

Packager opens the draft Phase PR into `development`. This packet only prepares the candidate and evidence. Do not open/update PR, merge, promote, materialize managed core, publish, or roll out from the pre-rollout checkpoint.

## Candidate

| Field | Pre-rollout value |
|---|---|
| Phase branch | `phase/item6-consumer-integration-pre-rollout` |
| Accepted content tip | issue/321 `b07f8eb23220915093d7cff873e9837db6b9f504` / tree `982831f544bb65d25e883c04d2bbdbe47b9468a1` |
| Evidence | `docs/evidence/item6-pre-rollout/` |
| Future PR body | `FUTURE-PR.md` |
| Rollback | `ROLLBACK.md` |
| Predecessor ledger | `predecessor-ledger.json` |

## When authorized (post-v2.4.0)

1. Confirm `v2.4.0` is on protected IDE Development lines and Packager of that era exists.
2. Rebase or deliberately layer this Phase tip onto then-current `origin/development` if needed. Repair conflicts deliberately; never prefer-incoming.
3. If WP-I6-MANIFEST is in the same Phase, layer it only after post-v2.4.0 `MANIFEST.json` authority exists.
4. Open one draft Phase PR using `FUTURE-PR.md` (WP-I6-INTEGRATE).
5. Run hosted Fast on the exact PR head (WP-I6-HOSTED). Reuse the single final-combined exact-tree Full; do not start a standalone Item 6 Full without founder exception.
6. Request Bugbot only after fast-gate success on that exact SHA.
7. Integrator merges only when named gates + Bugbot succeed.

## Do not

- Package onto `phase/next-ide-development-v2.4.0` from Item 6
- Touch unrelated active core implementation branches (WP-U03/U04/U08/U01/etc.) while preparing this lane
- Publish Review Ready / managed Fast / Full from pre-rollout checkpoints
- Materialize `.ide-development/` into this system repository
