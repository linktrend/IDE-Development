# Future Phase PR body (after v2.4.0 — do not open now)

Use only when WP-I6-INTEGRATE is authorized after `v2.4.0` is on IDE Development protected lines. Packager opens the draft PR; implementers do not.

## Title

`Phase: Item 6 five-provider consumer integration (pre-rollout source)`

## Body

```markdown
## Summary

- Integrates accepted Item 6 pre-rollout consumer boundary (`core/link-integrations/`, `tests/link-integrations/`) plus WP-I6-DOCS PRD/plan.
- Source tip verified independently clean: issue/321 `b07f8eb23220915093d7cff873e9837db6b9f504` / tree `982831f544bb65d25e883c04d2bbdbe47b9468a1`.
- Predecessor ledger (S0–S6 + DOCS) recorded under `docs/evidence/item6-pre-rollout/` with patch-id preservation proofs.
- WP-I6-MANIFEST remains a separate post-v2.4.0 packet (no managed-core / MANIFEST edits in this PR unless that packet is explicitly included later).

## Post-v2.4.0 gate status

- [ ] WP-I6-MANIFEST (nine-consumer managed materialization) — separate or follow-on
- [x] WP-I6-INTEGRATE — this Phase PR
- [ ] WP-I6-HOSTED — Fast on this exact head; reuse final-combined exact-tree Full (no standalone Item 6 Full)

## Test plan

- [ ] Focused: `node tests/link-integrations/test-*.mjs`
- [ ] `git diff --check` on owned paths
- [ ] Hosted Fast on exact Phase PR head (WP-I6-HOSTED)
- [ ] Reuse single final-combined exact-tree Full receipt when identity digests match
- [ ] Confirm no nested `.ide-development/` self-install and no Issue 244 pin SHAs

## Out of scope / hard stops

- No provider-repository edits
- No prefer-incoming conflict resolution
- No promotion to staging/main from this PR
- Do not treat this PR as `phase/next-ide-development-v2.4.0`
```

## Base / head (fill at open time)

| Field | Value |
|---|---|
| Base | `development` at post-v2.4.0 protected tip (record exact SHA) |
| Head | then-current `phase/item6-consumer-integration-pre-rollout` tip after any required post-v2.4.0 rebase/layer (record exact SHA/tree) |
| Draft | yes |
| Bugbot | only after Packager fast-gate on that exact SHA |
