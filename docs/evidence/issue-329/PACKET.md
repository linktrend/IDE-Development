# Packet — Trusted Linktrend Review Gate bootstrap (AC-U05-06/14)

| Field | Value |
|---|---|
| Issue | 329 |
| Branch | `issue/329-bootstrap-trusted-linktrend-review-gate-for-ide` |
| Spec | Update 1 Review Gate + Update 4 bootstrap pattern + Update 5 AC-U05-06/14 |
| Base | current `origin/development` via agentsetup `--prefer-worktree` |
| Sealed product candidate | PR #326 head `2f204781e093acad694b084e7c4ba0652fd17721` / tree `4556fb197c575c64cb1a152c00738c8651a3cb74` / Full run `32071094022` PASS |
| Scope | Narrowest trusted-verifier **source package** only — no live ruleset mutate, no PR open/merge, no promote/publish/rollout, no Full |

## Exact candidate blobs (runtime package)

- `.github/workflows/linktrend-review-gate.yml`
- `core/github/managed-workflows/linktrend-review-gate.yml`
- `scripts/gitops/linktrend_review_gate.py`
- `core/managed-core/schemas/linktrend-review-gate.schema.json`
- `docs/contracts/LINKTREND-REVIEW-GATE.md`
- `core/managed-core/content/doctrine/LINKTREND-REVIEW-GATE.md` (synced byte-identical from contract)

## Verify-required wiring only

- `scripts/ide_development/build_manifest.py` (CONTENT_DOCTRINE + schema + HOSTED_TEST_FILES)
- `core/managed-core/MANIFEST.json` (regenerated)
- `core/github/managed-runtime/MANIFEST.json` (gitops script entry)
- `scripts/tests/test_linktrend_review_gate.py` (classifier/workflow focus; three unrelated surface-migration tests skipped)

## Preserved properties

- Exact-head Full receipt binding (receipt tree never overwritten by live TREE)
- Bugbot classification into managed `Linktrend Review Gate`
- Verified-unavailability fallback only (`verified: true` + trusted source)
- No missing-as-pass / no advisory labeled as Bugbot pass
- Default-branch trust boundary: `check_run` workflow lives on protected default path; live == managed template

## Rollback

Leave issue branch unmerged. Do not prefer-incoming. Do not alter PR #326. Do not weaken live rulesets. Failed trusted install leaves sealed candidate and receipt unchanged (`trusted_gate_version_unavailable` semantics).
