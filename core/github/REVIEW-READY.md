# Review-ready record (branch-local)

Committed on a task branch when work is finished and eligible for the Tue/Fri Review Packager.

## Path

`.linktrend/review-ready.json`

## Design (non-self-referential)

1. Finish functional work and commit it. That commit is **`contentSha`**.
2. Run `scripts/mark-review-ready.sh` — writes the JSON with `contentSha` = current HEAD (functional tip). Does **not** commit.
3. Run `scripts/commit-review-ready.sh` — creates a **marker-only** commit that changes only approved readiness paths.
4. Push. The marker commit’s tip SHA is the proposed PR/review SHA.

### Validity rules

Valid only when all are true:

- `contentSha == HEAD^` (parent of tip is the functional commit)
- Tip commit changes only `.linktrend/review-ready.json` (and optional `.linktrend/review-freeze.json`)
- Tip includes `.linktrend/review-ready.json`
- `deterministicGate` is `pass`

Any later commit makes the record stale automatically.

The Packager uses the **marker tip** as the PR head / review SHA. It does **not** require `contentSha == HEAD`.

## Schema

```json
{
  "schemaVersion": 2,
  "issueId": "<issue-id>",
  "branch": "issue/<id>-<slug>",
  "contentSha": "<40-char lowercase hex of final functional commit>",
  "recordedAt": "<ISO-8601>",
  "deterministicGate": "pass",
  "notes": "<optional>"
}
```

Legacy `commitSha` (self-referential) is **rejected**.

## Agent checklist before writing

1. Approved scope and acceptance criteria satisfied
2. Implementation complete; no further functional changes planned
3. Required `PROOF.md` (or equivalent proof) exists
4. Inexpensive deterministic checks pass locally
5. Working tree clean
6. `scripts/mark-review-ready.sh` then `scripts/commit-review-ready.sh`
7. Push; set issue status to `review_ready`

## Packager behavior

See `scripts/gitops/packager_runner.py` and `linktrend-review-packager.yml`:

1. Discover allowed work branches with a valid marker tip
2. Open a **draft** PR (no Bugbot yet)
3. Wait for named **fast-gate** on that exact PR head
4. Only then mark ready and comment the configurable Bugbot command (default `cursor review`)
5. Write the hidden “requested” marker **only in that comment after it succeeds**
