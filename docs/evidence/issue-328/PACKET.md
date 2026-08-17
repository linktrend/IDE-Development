# Packet Issue #328 — Combined-phase validation repair

## Identity

| Field | Value |
|---|---|
| Issue | 328 |
| Branch | issue/328-repair-ide-development-v2-4-0-combined-phase-val |
| Authority plans | 3a5d15231d65b8549d64971960b2aeb617b58838 |
| Start commit | 70acec9871cd23598b1db264946b4f0c00291ac3 |
| Start tree | cc1f666dccce26545884f87dc065f7cfcd86a235 |
| Prior accepted tip (A–C) | cfa141aced4e4843f7d5f51a0b76c3d64f384b72 / 09eef53c721e0f00a81d048b565352a1a4fc841b |
| Content head/tree (includes D) | 555cba0cceb96b334754a6e9ef28fb9aadf13567 / 0b900215b13088735588eb5ea2563069e634b865 |
| Evidence head/tree (includes D) | 2b9083effb732a4510e6fff8ebf03c0e3a70b836 / 6a7356945a5e3b84b9cdbdcb9c8097e4ec46a4d3 |
| Final tip binding | branch HEAD after bind-metadata commit; tip SHA not self-embedded |
| Scope | Repair only PR #326 combined-phase Fast / Verify IDE / installer matrix failures (+ residual Verify IDE managed-workflow drift) |

## Failures repaired

| Defect | Source runs | Repair |
|---|---|---|
| A secret_scan stale fixtures + high-entropy literal | Fast 32058396059 | Refresh `candidateTree` binding; declare publisher `ltfx.` fixture; replace `ghs_DOCUMENTED_…` at `test-review-ready-publisher.sh:431` |
| B vendored skill hash mismatch | Verify IDE 32058396209 | Update `VENDOR-MANIFEST.json` hashes for `gstack/qa/SKILL.md` and `gstack/review/SKILL.md` to on-disk adapted copies |
| C package_v2 missing `repository_ci_contract.py` | Matrix 32056985170 (ubuntu/macos/windows) | Add self-contained installer-audit stub at fixture `scripts/gitops/repository_ci_contract.py` |
| D managed workflow render drift `linktrend-repair-observer.yml` | Verify IDE 32060954525 | Official `scripts/sync-managed-workflows.sh .` converge live `.github/workflows/` copy to rendered `core/github/managed-workflows/` template (comment wording); verifier unchanged |

## Local verification notes (D)

Narrow local reproductions only. Does **not** claim hosted GitHub CI re-run or pass for tip after D.

## Exclusions

Full suite, phase PR update, implementer PR, merge, promote, publish, deploy, rollout, protection changes, GitHub CI re-run, self-review, review-ready publish.

## Rollback

Leave issue branch unmerged. Do not prefer-incoming. Do not weaken secret-scan, vendored-skill verification, or managed-workflow render checks.
