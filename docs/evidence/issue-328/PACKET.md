# Packet Issue #328 — Combined-phase validation repair

## Identity

| Field | Value |
|---|---|
| Issue | 328 |
| Branch | issue/328-repair-ide-development-v2-4-0-combined-phase-val |
| Authority plans | 3a5d15231d65b8549d64971960b2aeb617b58838 |
| Start commit | 70acec9871cd23598b1db264946b4f0c00291ac3 |
| Start tree | cc1f666dccce26545884f87dc065f7cfcd86a235 |
| Prior accepted tip (A–E) | 3d394a50540502da596b20e051451232a871cee0 / fe99a7fbb835035dd533ce6ac14f86e0dd9d1084 |
| Content head/tree (includes F) | 9f82a35cb82bc662e39944ddd997345138a03532 / 6b4f40c0a5e4ad35e5e99a1c7f78c4dae6dd3965 |
| Evidence head/tree (includes F) | set in bind-metadata commit; tip SHA not self-embedded |
| Final tip binding | branch HEAD after bind-metadata commit; tip SHA not self-embedded |
| Scope | Repair only PR #326 combined-phase Verify IDE / Fast / matrix failures and residual Verify IDE defects |

## Failures repaired

| Defect | Source runs | Repair |
|---|---|---|
| A secret_scan stale fixtures + high-entropy literal | Fast 32058396059 | Refresh `candidateTree` binding; declare publisher `ltfx.` fixture; replace `ghs_DOCUMENTED_…` at `test-review-ready-publisher.sh:431` |
| B vendored skill hash mismatch | Verify IDE 32058396209 | Update `VENDOR-MANIFEST.json` hashes for `gstack/qa/SKILL.md` and `gstack/review/SKILL.md` to on-disk adapted copies |
| C package_v2 missing `repository_ci_contract.py` | Matrix 32056985170 (ubuntu/macos/windows) | Add self-contained installer-audit stub at fixture `scripts/gitops/repository_ci_contract.py` |
| D managed workflow render drift `linktrend-repair-observer.yml` | Verify IDE 32060954525 | Official `scripts/sync-managed-workflows.sh .` converge live `.github/workflows/` copy to rendered managed template |
| E behavioral heredoc IndentationError on chained `.replace` | Verify IDE 32063802001 | Restore parenthesized `.replace()` chain in resolver managed/live block; keep Review Gate + Bugbot check-name substitutions |
| F nine-consumer Fast/Full profile portability | Verify IDE 32066562328 | Load package `repository_ci_contract` with `package_root` on `sys.path`; require `installer_audit_repository_ci_triggers`; drop factory-only unittest from managed-core Fast/Full `delivery.json` (py_compile + secret_scan only) |

## Local verification notes (F)

Narrow local reproductions only. Does **not** claim hosted GitHub CI re-run or pass for tip after F.

## Exclusions

Full suite, phase PR update, implementer PR, merge, promote, publish, deploy, rollout, protection changes, GitHub CI re-run, self-review, review-ready publish.

## Rollback

Leave issue branch unmerged. Do not prefer-incoming. Do not weaken secret-scan, vendored-skill verification, managed-workflow render checks, Review Gate behavioral assertions, or the nine-consumer profile matrix checks.
