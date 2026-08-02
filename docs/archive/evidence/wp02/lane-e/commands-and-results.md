# WP02 Lane E — Commands and results

Lane E executed read-only inspection commands only. No commit, push, review-ready, PR, Bugbot, merge, promote, cleanup apply, or consumer mutation.

| # | Command | Exit | Result summary |
|---|---|---|---|
| 1 | `git rev-parse --abbrev-ref HEAD` | 0 | `issue/68-work-packet-02-integration-lineage-stale-cleanup` |
| 2 | `git rev-parse HEAD` | 0 | `9cd3fec75075c6910b5a3bbb09b582e4cb3c94e4` |
| 3 | `git cat-file -t 89956878c54ff45e4aef1ff42883d209221b7a30` | 0 | `commit` (WP01) |
| 4 | `git cat-file -t 5cf099155d9f7b5d95e094f74b288af7aec766af` | 0 | `commit` (cleanup) |
| 5 | `git cat-file -t 991abc319782008ef93af95002be0d7f3d5a937c` | 0 | `commit` (development) |
| 6 | `git merge-base --is-ancestor 89956878… HEAD` | 1 | WP01 **not** ancestor of branch tip yet |
| 7 | `git merge-base --is-ancestor 5cf0991… HEAD` | 1 | cleanup **not** ancestor of branch tip yet |
| 8 | `git merge-base --is-ancestor 991abc3… HEAD` | 0 | development **is** ancestor |
| 9 | `git grep -i 'WP02\|Work Packet 2' <SHAs> -- docs…` | 0 | WP02 “future/wrong scope” statements located primarily on WP01 SOT docs + HEAD packet status |
| 10 | Manifest presence compare (python/`git show`) across WP01/cleanup/development/HEAD | 0 | `core/managed-core/**` and `.agents/skills-manifest.json` **ABSENT** on development/cleanup/HEAD; present on WP01. `managed-runtime/MANIFEST.json`, `VENDOR-MANIFEST.json`, `SKILLS_CATALOG.md` **IDENTICAL**. Root `VERSION` WP01=`v2.0.0` vs others=`v1.2` |
| 11 | `gh issue view 68 --repo linktrend/IDE-Development --json number,title,state` | 0 | OPEN · title matches WP02 packet |
| 12 | Seed + edit files under `docs/evidence/wp02/lane-e/**` only | 0 | Proposed docs + evidence artifacts written |

## Placeholders for lead final bind (fill after validation)

| # | Command | Exit | Notes |
|---|---|---|---|
| L1 | `bash scripts/tests/test-stale-cleanup-controls.sh` | `__` | After combined lineage |
| L2 | `bash scripts/tests/test-external-state-wp1.sh` | `__` | |
| L3 | `bash scripts/tests/test-external-state-audit.sh` | `__` | |
| L4 | `bash scripts/tests/test-repository-protection.sh` | `__` | |
| L5 | `bash scripts/tests/test-gitops-behavioral.sh` | `__` | |
| L6 | `bash scripts/tests/test-gitops-lifecycle.sh` | `__` | |
| L7 | `bash scripts/tests/test-gitops-review-packager.sh` | `__` | |
| L8 | `bash tests/test-portable-v2-integration.sh` | `__` | |
| L9 | `SKIP_LOCAL_ARCHIVE_CHECKS=1 bash scripts/verify-ide-development.sh` | `__` | |
| L10 | Three-OS CI on exact pushed tip | `__` | Bind run URL/conclusion (no secrets) |
| L11 | RC create/verify reproducibility | `__` | |
| L12 | `git rev-parse HEAD` == `git rev-parse origin/<branch>` | `__` | Final checkpoint |
