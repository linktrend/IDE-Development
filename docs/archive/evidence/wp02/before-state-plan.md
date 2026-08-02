# WP02 Before-State Plan (deterministic)

**Captured:** 2026-08-02T03:09:43Z
**Repo:** linktrend/IDE-Development
**Authority:** WP02 packet; live apply only via authorized GitHub App path with rollback snapshot

## Immutable inputs

| Name | SHA |
|------|-----|
| origin/development (startup base) | 991abc319782008ef93af95002be0d7f3d5a937c |
| WP01 checkpoint | 89956878c54ff45e4aef1ff42883d209221b7a30 |
| Cleanup tip (#63) | 5cf099155d9f7b5d95e094f74b288af7aec766af |
| Frozen PR #49 tip | 0868c0034620c4ccb255457484f0342a12a0c833 |
| origin/staging | f7829436751b8d5adb01c1a50fc9131a5201d1df |
| origin/main | 80144d391414de603e1c71ab1739da22e24b5684 |

## Allowed live mutations (IDE Development only)

1. Read-only audit first (`external_state_audit.py --live`).
2. Apply ONLY settings proven by repository standard/contracts, through GitHub App path.
3. Require restorable before-state snapshot before any apply.
4. Never use Carlos restricted user token for settings/protection mutations.
5. Never fall back to ambient GH_TOKEN/GITHUB_TOKEN for privileged mutations.
6. Bugbot Manual-Only: verification-only unless approved App/UI route exists without credential exposure.

## Prohibited

- Alter PR #36/#37/#49 heads; close PRs/issues; delete branches/worktrees
- Force push / reset / rewrite; open PR; review-ready; Packager; Bugbot trigger; Integrator; promote; tag/release
- Consumer repository changes; credential exposure
