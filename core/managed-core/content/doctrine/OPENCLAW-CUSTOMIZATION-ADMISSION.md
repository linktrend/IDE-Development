# OpenClaw Prime customization-only admission

**Status:** Active protected IDE `v2.5.2` repair, issue #464.
**Single owner:** `scripts/ide_development/openclaw_customization_admission.py`
**Schema:** `core/managed-core/schemas/openclaw-customization-admission.schema.json`

This is a narrow admission path for `linktrend/openclaw_prime`. It scans the
present files in the validated LiNKtrend-owned customization paths, the
present destinations declared by the protected IDE `v2.5.2` package manifest,
and the explicit v2.5.2 transaction paths. It does not scan, rewrite, or
require repair of untouched `openclaw/openclaw` upstream trees.

The consumer boundary is evidence, not a permission to broaden scope. The
module rejects forbidden paths, scanner findings outside the exact checked
set, missing or mismatched package identity, scanner-supplied baselines, and
target commit/tree drift. The packaged scanner path-scoped result, or the
installer adapter, must bind the real HEAD `candidateCommit`/`candidateGitTree`;
admission does not invent those fields. Missing local destinations are
recorded as omitted; they are not silently treated as scanned.

Admission uses two ordinary issue/Phase calls:

1. Before a managed transaction, capture `preInstallBaseline` from the exact
   target commit/tree and exact checked path set.
2. After the transaction, compare a fresh scoped scan with that baseline.

Only an exact pre-existing finding, including its physical content digest, may
be inherited. A new or changed credential, skipped input, or scanner failure
remains blocking. A scanner cannot provide the accepted baseline itself.

`fullRunReceiptIdentity` is optional pass-through evidence, never synthesized
by this scoped path. When supplied, it must be a schema-version 2,
digest-valid successful `FullSuiteReceipt` for the exact OpenClaw commit/tree;
the local customization scan is never relabeled as Full. Until a real GitHub
Actions run produces that receipt, hosted Full evidence remains a HOLD.

This protocol does not edit LiNKautowork, OpenClaw Prime, or any other
consumer-managed file. Consumer rollout and rerun of PR #115 / PR #287 are
separate downstream Phase work after this protected package candidate is
accepted.
