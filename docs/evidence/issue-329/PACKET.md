# Packet — Trusted Linktrend Review Gate bootstrap (AC-U05-06/14)

| Field | Value |
|---|---|
| Issue | 329 |
| Branch | `issue/329-bootstrap-trusted-linktrend-review-gate-for-ide` |
| Spec | Update 1 Review Gate + Update 4 bootstrap pattern + Update 5 AC-U05-06/14 |
| Base | current `origin/development` via agentsetup `--prefer-worktree` |
| Sealed product candidate | PR #326 head `2f204781e093acad694b084e7c4ba0652fd17721` / tree `4556fb197c575c64cb1a152c00738c8651a3cb74` / Full run `32071094022` PASS |
| Scope | Narrowest trusted-verifier **source package** + imported founder-authorized bootstrap **step-1** operator evidence — no further live ruleset mutate from this branch, no PR open/merge, no promote/publish/rollout, no Full |

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

## Imported founder-authorized bootstrap step 1 (live)

Imported under `docs/evidence/issue-329/bootstrap-step1-source-policy/` from Issue #328 packet `issue-328-bootstrap-step1-source-policy` after an independent secret scan (0 findings; 0 secret values redacted). Original before/after/rollback records preserved byte-identical.

| Fact | Record |
|---|---|
| Live step 1 | **APPLIED + VERIFIED + HOLD** (`sanitized/OPERATOR-RESULT.json`, `sanitized/step1-post-verify.json`) |
| Cursor Bugbot | Remained required on development (`Cursor Bugbot`, `Verify IDE Development`, `Linktrend Branch Source Policy`) |
| PR #326 | Unchanged head/tree `2f204781e093acad694b084e7c4ba0652fd17721` / `4556fb197c575c64cb1a152c00738c8651a3cb74` |
| Not done | Bugbot→Review Gate cutover; further bootstrap steps; source/runtime changes for step 1 |

See `bootstrap-step1-source-policy/IMPORT-ATTESTATION.json` and `bootstrap-step1-source-policy/PACKET.md`.

## Preserved properties

- Exact-head Full receipt binding (receipt tree never overwritten by live TREE)
- Bugbot classification into managed `Linktrend Review Gate`
- Verified-unavailability fallback only (`verified: true` + trusted source)
- No missing-as-pass / no advisory labeled as Bugbot pass
- Default-branch trust boundary: `check_run` workflow lives on protected default path; live == managed template
- Live development ruleset still requires `Cursor Bugbot` (no Review Gate cutover)

## Rollback

Leave issue branch unmerged. Do not prefer-incoming. Do not alter PR #326. Do not weaken live rulesets from this packet. Failed trusted install leaves sealed candidate and receipt unchanged (`trusted_gate_version_unavailable` semantics).

Step-1 historical rollback command is preserved in the imported operator packet; local usable snapshot path is documented in `bootstrap-step1-source-policy/local-rollback-snapshot-path.txt` (HOLD — do not execute unless founder-authorized).

## HOLD

Independent review only. No PR. No Full. No merge. No promotion. No publication. No consumer rollout. No additional live ruleset mutation from Issue #329. No Bugbot→Review Gate cutover.
