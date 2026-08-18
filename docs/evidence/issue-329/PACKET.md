# Packet — Trusted Linktrend Review Gate bootstrap (AC-U05-06/14)

| Field | Value |
|---|---|
| Issue | 329 |
| Branch | `issue/329-bootstrap-trusted-linktrend-review-gate-for-ide` |
| Spec | Update 1 Review Gate + Update 4 bootstrap pattern + Update 5 AC-U05-06/14 |
| Base | current `origin/development` via agentsetup `--prefer-worktree` |
| Sealed product candidate | PR #326 head `2f204781e093acad694b084e7c4ba0652fd17721` / tree `4556fb197c575c64cb1a152c00738c8651a3cb74` / Full run `32071094022` PASS |
| Scope | Trusted-verifier **source package** + imported founder step-1 evidence + independent-review repairs — no further live ruleset mutate from this branch, no PR open/merge, no promote/publish/rollout, no Full |

## Exact candidate blobs (runtime package)

- `.github/workflows/linktrend-review-gate.yml`
- `core/github/managed-workflows/linktrend-review-gate.yml`
- `scripts/gitops/linktrend_review_gate.py`
- `core/managed-core/schemas/linktrend-review-gate.schema.json`
- `docs/contracts/LINKTREND-REVIEW-GATE.md`
- `core/managed-core/content/doctrine/LINKTREND-REVIEW-GATE.md` (synced byte-identical from contract)

## Independent-review repairs (this tip)

- P1: Bind accepted Full/provider check payloads to producer run/job/check-suite identity (reject borrowed details_url + forged summary); require successful producer run/output.
- P2: Provider extractor requires exact check head_sha and workflow_run.head_sha (parity with Full).
- P1: Bind trusted Full Suite / provider-unavailability check evidence to authenticated default-branch workflow/run identity (Actions run id from check URL + allowlisted `workflow_run.path` + Contents API default-branch blob match). Same-app/name collisions fail closed.
- P1: Authenticated evidence channels — candidate `.linktrend` provider-error/Full files cannot authorize success; GitHub Checks / privileged channels only.
- P2: Adversarial tests cover all allowlisted planted sources and forged Full receipt provenance.

- P1: Workflow checkouts protected `default_branch` for scripts only; candidate head/tree/receipt/provider evidence are API data only (never execute candidate scripts).
- P2: Structured Bugbot findings via `annotations_count` / `action_required` → `review-findings`; removed dead free-text `CHECK_DETAILS` path.
- P2: Verify evidence host paths sanitized; changed-path secret scan claims truthful.
- P2: Import attestation includes `local-rollback-snapshot-path.txt` in hashes/`fileCount`.
- Negative tests prove PR cannot rewrite classifier/self-approve and default-branch scripts are used.

## Verify-required wiring only

- `scripts/ide_development/build_manifest.py` (CONTENT_DOCTRINE + schema + HOSTED_TEST_FILES)
- `core/managed-core/MANIFEST.json` (regenerated)
- `core/github/managed-runtime/MANIFEST.json` (gitops script entry)
- `scripts/tests/test_linktrend_review_gate.py` (classifier/workflow focus; three unrelated surface-migration tests skipped)

## Imported founder-authorized bootstrap step 1 (live)

Imported under `docs/evidence/issue-329/bootstrap-step1-source-policy/` from Issue #328 packet `issue-328-bootstrap-step1-source-policy` after an independent secret scan (0 findings; 0 secret values redacted). Original before/after/rollback records preserved.

| Fact | Record |
|---|---|
| Live step 1 | **APPLIED + VERIFIED + HOLD** |
| Cursor Bugbot | Remained required on development |
| PR #326 | Unchanged head/tree `2f204781e093acad694b084e7c4ba0652fd17721` / `4556fb197c575c64cb1a152c00738c8651a3cb74` |

## Preserved properties

- Exact-head Full receipt binding (receipt tree never overwritten by live TREE)
- Bugbot classification into managed `Linktrend Review Gate`
- Verified-unavailability fallback only (`verified: true` + trusted source)
- No missing-as-pass / no advisory labeled as Bugbot pass
- Default-branch trust boundary: scripts from protected default path; live == managed template
- Default-branch workflow/run identity binding for trusted Full/provider GitHub Checks
- Live development ruleset still requires `Cursor Bugbot` (no Review Gate cutover from this packet)

## Rollback

Leave issue branch unmerged. Do not prefer-incoming. Do not alter PR #326. Do not weaken live rulesets from this packet.

## HOLD

Independent review only. No PR. No Full. No merge. No promotion. No publication. No consumer rollout. No additional live ruleset mutation from Issue #329. No Bugbot→Review Gate cutover.
