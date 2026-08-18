# Packet — Repair trusted Review Gate default-branch execution (issue #330)

| Field | Value |
|---|---|
| Issue | 330 |
| Branch | `issue/330-repair-v2-4-0-trusted-review-gate-default-branch` |
| Spec | Post-sealed-Full P1/P2/P3 on trusted Review Gate |
| Base | current `origin/development` via agentsetup `--prefer-worktree` |
| Sealed product candidate (prerequisite) | PR #326 head `2f204781e093acad694b084e7c4ba0652fd17721` / tree `4556fb197c575c64cb1a152c00738c8651a3cb74` / Full run `32071094022` PASS |
| Prerequisite commit (layered blobs) | `c5de34d6e91cf633e998192d8b4ef5e5c2ec31a5` |
| Content head/tree (novel repair) | `bdbdf7fdf8e2911525380aba7526723f6d099f8a` / `91ef31f3f372e9fc1e0c9879c0fc955c7eae736e` |
| Novel packet commit range | `c5de34d6e91cf633e998192d8b4ef5e5c2ec31a5..bdbdf7fdf8e2911525380aba7526723f6d099f8a` (content); evidence bind tip follows without self-SHA |
| Scope | Trust-boundary repair only — no Full, no PR, no ruleset mutation, no merge/promotion/publication/rollout; do not modify phase branch or PR #326 |

## Defects closed

1. **P1 — candidate-controlled execution:** workflow checked out `github.event.check_run.head_sha` and executed candidate scripts with statuses/issues/PR write. Now checks out protected `default_branch` for scripts; candidate SHA is fetched into a detached data worktree only.
2. **P2 — dead CHECK_DETAILS / unwired findings-present:** `detect-findings` consumes trustworthy check_run event evidence (`annotations_count`, title, summary) and wires `--findings-present` so genuine Bugbot findings classify as `review-findings`.
3. **P3 — candidate-forged success evidence:** allowlisted planted `.linktrend/review-gate-provider-error.json` could authorize `advisory-unavailable` / `gateSuccess=true` over failure or neutral Bugbot; candidate `.linktrend/full-suite-receipt.json` lacked trusted provenance. Success-authorizing evidence now requires authenticated provenance; candidate files are ignored; trusted routes preserve operator variable + repair-task usage_limit + Checks API Full receipt.

## Preserved properties

- Exact Full receipt head/tree binding (receipt tree never overwritten by live TREE)
- Verified-unavailability fallback only (`verified: true` + trusted source + authenticated provenance)
- No missing-as-pass / no advisory labeled as Bugbot pass
- Findings-present precedence over provider-unavailability advisory
- Least privilege permissions unchanged (`contents: read` + statuses/issues/PR write on classify job)
- Prior A–F repair invariants retained (stdin slurp, founder-alert dedupe fail-closed, infra marker fail-closed, no heuristic failure→advisory)
- Live workflow bytes == managed template
- Default-branch execution; manifests verify; evidence truthfulness (planted junk does not rewrite real Bugbot failure/neutral)

## Negative coverage

- Candidate malicious classifier claiming `review-passed` does not replace trusted `GATE_PY`
- Each allowlisted planted provider-error source (`repair_observer.usage_limit`, `operator_verified_provider_error`, `provider_status_api`) cannot authorize success without authenticated provenance
- Forged candidate Full receipt (matching head/tree/success, or `candidate.worktree_file` provenance) fails closed
- Findings-present still precedes planted provider-error advisory
- Neutral alone without findings evidence remains `review-unknown` (not pass)
- Legitimate trusted routes still authorize advisory / Full receipt when authenticated

## Validation

| Check | Result | Evidence |
|---|---|---|
| actionlint (live + managed) | PASS | `focused-tests.out` |
| classifier positive/negative + trust-boundary + planted-source + forged-receipt + build_manifest | 32 ran / 3 skipped / 0 fail | `focused-tests.out` |
| manifest verify | PASS | `focused-tests.out` |
| secret scan (changed paths) | 0 findings | `secret-scan.out` |
| Verify IDE Development | ALL CHECKS PASSED | `verify-ide-subset.out` |
| `git diff --check` | PASS | `focused-tests.out` |

## Rollback

Leave issue branch unmerged. Do not prefer-incoming. Do not alter PR #326 sealed head/tree/receipt. Packager may integrate novel range onto the sealed candidate later.

## HOLD

Independent review only. No PR. No Full. No merge. No promotion. No publication. No consumer rollout. No ruleset mutation. No phase/PR #326 modification.
