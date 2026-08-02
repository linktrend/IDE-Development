# WP02 Lane ownership (disjoint writes)

Lead worktree: issue-68-work-packet-02-integration-lineage-stale-cleanup
Startup SHA: 9cd3fec75075c6910b5a3bbb09b582e4cb3c94e4
Model: cursor-grok-4.5-high for all subagents

| Lane | Write paths only | Read surfaces |
|------|------------------|---------------|
| A | docs/evidence/wp02/lane-a/** | git/gh read-only; before-state |
| B | docs/evidence/wp02/lane-b/** | git read-only ancestry/diff |
| C | docs/evidence/wp02/lane-c/** | CLEAN tip 5cf0991; WP01 tree read-only |
| D | docs/evidence/wp02/lane-d/** | live GET audit; no apply without lead |
| E | docs/evidence/wp02/lane-e/** | manifests/docs read; propose edits only |

Subagents MUST NOT: commit, push, modify frozen PR heads, alter files outside their write path, call review-ready, open PRs, trigger Bugbot, mutate consumer repos, expose secrets.
Lead alone integrates, commits, pushes.
