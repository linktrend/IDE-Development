# Packager reconcile ledger — PR #326 + Issues #329/#330

| Field | Value |
|---|---|
| Role | Independent Packager |
| Phase base HEAD | `2f204781e093acad694b084e7c4ba0652fd17721` |
| Phase base TREE | `4556fb197c575c64cb1a152c00738c8651a3cb74` |
| Issue #329 HEAD | `bc34fd44b13d4271f9b911a2404771415b46cad3` |
| Issue #329 TREE | `01730e4d1ff25b2ed8e88cd585077f45d0bba1a2` |
| Issue #330 HEAD | `fe80e3c763de706ef6f1d06b3fda2027602a65ca` |
| Issue #330 TREE | `cb46d5ccab67fef3f63062fa93fbb6034dac2130` |
| Scope | Security/bootstrap Review Gate only; no Full; no new PR; no merge/promote |

## Semantic overlap resolution

Overlapping runtime files diverged on parallel lineages from the sealed candidate.
Integrated candidate preserves **both** accepted fixes:

1. **#329 producer/default-branch identity binding** for Full + provider Checks (`extract-trusted-*`, suite/job membership, workflow blob match).
2. **#330 default-branch execution + candidate-as-data worktree**.
3. **#330 authenticated provenance** routes (operator variable, repair-task API) **and** #329 evidence channels (dual-accept).
4. **#330 detect-findings** event wiring **and** #329 structured annotations_count path.
5. Both evidence trees imported under `docs/evidence/issue-329/` and `docs/evidence/issue-330/`.

HOLD retained from packets: no Bugbot→Review Gate cutover; no additional live ruleset mutation; no Full in this Packager turn.

## Focused checks (non-Full)

| Check | Result |
|---|---|
| `unittest scripts.tests.test_linktrend_review_gate` | 31 ran / 0 fail |
| actionlint (live + managed Review Gate) | PASS |
| `build_manifest --verify` | PASS |
| `unittest test_build_manifest` | 7 ran / 0 fail |
| `git diff --check` | PASS |
| changed-path secret scan | 0 findings |
| `scripts/verify-ide-development.sh` | ALL CHECKS PASSED |
| Linktrend Full Suite | **not run** (Packager HOLD) |

## Residual HOLD

- No Bugbot → Review Gate cutover
- No additional live ruleset mutation
- No Full Suite in this Packager turn
- No merge / promote / publish / consumer rollout
- No new PR; existing Phase PR #326 head advances only
