# Lead prep merge-tree notes

## Facts
- `git merge-tree --write-tree WP01 CLEAN` fails with **content conflict only in `docs/OPEN-ISSUES.md`**.
- For LISA-LOCAL-CLEANUP-HANDOFF, REPAIR-DISPATCHER, cleanup-merged-branches.sh, repair_task.py, test-gitops-behavioral.sh: WP01 blob == development blob; CLEAN has the only delta. Ordinary merge takes CLEAN versions (no content conflict).
- HEAD+WP01 merge-tree succeeds (clean tree OID available).

## Intended lead integration order
1. `git merge --no-ff 8995687` (WP01) into issue/68
2. `git merge --no-ff 5cf0991` (cleanup); resolve OPEN-ISSUES by append-union of both suffixes after shared prefix
3. Apply Lane C integration tests + any hardening beyond cleanup tip
4. Apply Lane E doc/manifest proposed updates
5. Act on Lane D apply decision only if App-authorized

## OPEN-ISSUES strategy
Append-only log: keep shared DEV prefix, then WP01-only entries, then CLEAN-only entries not already present, then WP02/#68 entry.
