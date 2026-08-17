# Packet Issue #328 — Combined-phase validation repair

## Identity

| Field | Value |
|---|---|
| Issue | 328 |
| Branch | issue/328-repair-ide-development-v2-4-0-combined-phase-val |
| Authority plans | 3a5d15231d65b8549d64971960b2aeb617b58838 |
| Start commit | 70acec9871cd23598b1db264946b4f0c00291ac3 |
| Start tree | cc1f666dccce26545884f87dc065f7cfcd86a235 |
| Content head/tree | fce4018d97b639fd1712f2ee2bdeea65126472d4 / 5834a95d72daea8212dba2336101bab16f45ca5f |
| Evidence head/tree | cf356fddf0e58cef9e5ad542c50ee079ac8ecf52 / 46cb697648893340931e3333139586be5e104694 |
| Scope | Repair only PR #326 combined-phase Fast / Verify IDE / installer matrix failures |

## Failures repaired

| Defect | Source runs | Repair |
|---|---|---|
| A secret_scan stale fixtures + high-entropy literal | Fast 32058396059 | Refresh `candidateTree` binding; declare publisher `ltfx.` fixture; replace `ghs_DOCUMENTED_…` at `test-review-ready-publisher.sh:431` |
| B vendored skill hash mismatch | Verify IDE 32058396209 | Update `VENDOR-MANIFEST.json` hashes for `gstack/qa/SKILL.md` and `gstack/review/SKILL.md` to on-disk adapted copies |
| C package_v2 missing `repository_ci_contract.py` | Matrix 32056985170 (ubuntu/macos/windows) | Add self-contained installer-audit stub at fixture `scripts/gitops/repository_ci_contract.py` |

## Exclusions

Full suite, phase PR update, implementer PR, merge, promote, publish, deploy, rollout, protection changes, GitHub CI re-run, self-review, review-ready publish.

## Rollback

Leave issue branch unmerged. Do not prefer-incoming. Do not weaken secret-scan or vendored-skill verification.
