# Streamlined delivery operator runbook

This runbook is for Terra/operator work after repository verification. A
packet executor may implement and test repository code, but must not install a
service, mutate GitHub, open or merge a PR, promote a branch, tag, release,
rollback live state, or remove shared resources.

## Repository verification

1. Confirm the exact Phase/W3 base and a clean worktree.
2. Run the combined W3 test list from the W3 packet, including manifest and
   `git diff --check` verification.
3. Regenerate with `env PYTHONPATH=scripts python3 -m ide_development.build_manifest`
   and verify with `--verify`; do not hand-edit `MANIFEST.json`.
4. Create the release candidate with
   `python3 scripts/ide-development.py release-candidate create --json`.
   The ignored output is under `build/release-candidate/`; retain the metadata,
   archive, and `SHA256SUMS.json` paths as evidence.
5. Verify the archive with the exact tarball using the CLI `verify` operation.
   The disposable consumer must prove v2 configuration, both workflow
   profiles, no nested system installation, no absolute source path, and
   install/update idempotence plus rollback.

## Live canary gate

Terra snapshots the installed checkout, service, rulesets, credentials state,
containers, and rollback version before a canary. The canary registers only
IDE Development and proves protected-default policy loading, container-only
candidate execution, 300-second fast timing, two-fast/one-heavy admission,
pressure pause, cancellation, restart recovery, two-attempt stop/one-alert,
stable status contexts, and scoped cleanup. Any trust, identity, cleanup, or
protection failure stops the sequence and rolls back immediately.

## Promotion and rollback

After exact candidate gates pass, Terra opens one Phase PR, permits at most one
corrected seal, merges to development, and applies the receipt-bound staging
and main sequence. Main approval binds staging source, main base, promotion
head, and receipt. Verify protections and content/tree identity after each
branch operation. Rollback uses the retained previous coordinator/package
version and the consumer transaction journal; stop if rollback cannot prove
exact restoration.
