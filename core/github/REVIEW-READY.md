# Review-ready record (branch-local)

Committed on a task branch when work is finished and eligible for the Tue/Fri Review Packager.

## Path

`.linktrend/review-ready.json`

## Validity rule

The file is valid **only** when `commitSha` equals the current tip SHA of the branch (`HEAD`). Any later functional commit makes the record stale; the agent must rewrite it (or remove it) before packaging.

## Schema

```json
{
  "schemaVersion": 1,
  "issueId": "<issue-id>",
  "branch": "issue/<id>-<slug>",
  "commitSha": "<40-char lowercase hex>",
  "recordedAt": "<ISO-8601>",
  "deterministicGate": "pass",
  "notes": "<optional>"
}
```

## Agent checklist before writing

1. Approved scope and acceptance criteria satisfied
2. Implementation complete; no further functional changes planned
3. Required `PROOF.md` (or equivalent proof) exists
4. Inexpensive deterministic checks pass locally
5. Working tree clean for owned paths
6. Record the exact `git rev-parse HEAD` SHA
7. Set issue status to `review_ready`

## Packager behavior

See `core/github/managed-workflows/linktrend-review-packager.yml`. Invalid or stale records are left queued with a clear reason — never force a PR.
