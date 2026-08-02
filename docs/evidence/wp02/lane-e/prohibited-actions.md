# WP02 Lane E — Prohibited-action booleans

All values **must remain `false`** for WP02 scope (checkpoint-only delivery). Lead final bind must not flip these without an explicit Principal scope change outside WP02.

| Action | Boolean | Notes |
|---|---|---|
| Opened a pull request | `false` | Packager only after later review-ready; not WP02 |
| Requested Bugbot | `false` | |
| Published `Linktrend Review Ready` | `false` | |
| Merged into `development` | `false` | WP03 |
| Promoted to `staging` | `false` | WP03 |
| Promoted to `main` | `false` | WP03 |
| Created Git tag | `false` | |
| Created GitHub Release | `false` | |
| Mutated a consumer repository | `false` | Rollout separately Principal-gated |
| Mutated consumer GitHub state | `false` | |
| Applied cleanup deletes | `false` | Plan only in WP02 |
| Altered frozen PR heads (#36/#37/#49/etc.) | `false` | |
| Closed frozen PRs or issues | `false` | Disposition recorded for WP03 |
| Deleted branches or worktrees | `false` | |
| Nested self-install into IDE Development | `false` | System source only |
| Exposed or persisted secrets | `false` | Names/posture only in evidence |
| Force-pushed or rewritten history | `false` | Ordinary history only |
| Prefer-incoming conflict resolution | `false` | |
| Used Claude Code | `false` | Excluded |

Machine-readable twin: `evidence-template.json` → `prohibitedActions.booleans`.
