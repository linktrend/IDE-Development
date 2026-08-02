# Lane C proposed/ provenance

| Path | Source |
|------|--------|
| cleanup controls, shell, stale tests, STALE contract, handoff, repair_task plan-cleanup, behavioral json seed, workflows | `git show 5cf099155d9f7b5d95e094f74b288af7aec766af:<path>` (blob-verified) |
| `scripts/ide_development_tests/fixtures/security/cleanup/wrong-repo-evidence.json` | WP01 `89956878c54ff45e4aef1ff42883d209221b7a30` (reference; skip if already merged) |
| `scripts/tests/test-cleanup-wp01-lineage-coexistence.sh` | NEW (Lane C) |
| `tests/security_acceptance/test_cleanup_wp01_coexistence.py` | NEW (Lane C) |

Lead integrate order: WP01 → cleanup tip → copy NEW tests (+ cleanup-only files if not already applied).
