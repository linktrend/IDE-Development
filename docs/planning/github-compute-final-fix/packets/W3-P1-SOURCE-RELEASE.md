# W3-P1 — IDE Development Integration, Permanent Release, and Promotion

## Objective

Integrate verified Waves 1–2, prove the permanent design live, use the approved
one-time admin path to promote it through IDE Development, remove source-system
legacy external state, and publish one immutable release for consumers.

## Executor

Terra may assign one Luna High for release preparation, but Terra owns verification,
admin authority, merge, promotion, external cleanup, and final acceptance.

## Dependencies

- Wave 2 combined PASS.
- Disposable fresh/upgrade/idempotence/rollback PASS.
- Funded Actions and successful `ubuntu-24.04-arm` canary.
- Before-state/ruleset/App/runner/host/Docker snapshots.
- Concurrent feature inventory remains preserved.

## Required procedure

1. Rebase/merge no unrelated feature. Bring only exact accepted packet commits and
   approved planning docs into `phase/github-compute-final-fix`.
2. Run complete local verification and record Phase head/tree.
3. Push Phase and open one PR to `development`.
4. Prove checkpoint/no-CI separately without generating redundant suites.
5. Exercise a Phase update to prove obsolete fast run cancellation.
6. Seal the final exact candidate. Trigger one Bugbot review and one full suite on
   hosted ARM64. Never exceed two infrastructure attempts/two sealed candidates.
7. Verify full-suite receipt and negative changed-tree probe.
8. Snapshot rules and confirm exact PR head has not changed.
9. Use admin emergency merge for the verified PR into `development`.
10. Promote by PR `development` -> `staging` and `staging` -> `main`; use receipt/
    source-policy checks, not repeated full suites. Admin-merge exact verified heads.
11. Verify protections and required checks after every merge.
12. Choose/increment the managed-core version according to repository convention;
    create immutable tag/release from remote main; publish artifact and digests.
13. Apply the reviewed source-system external cleanup plan: remove former custom
    App repository access/secrets/variables/workflows/status requirements and
    self-hosted runner registrations; remove positively identified IDE-owned Mac
    services and Docker runner resources. Do not remove the global App until W3-P2
    through P4 prove no consumer needs it.
14. Enable supported Actions usage alerts with no stop limit; record settings and
    minutes used.
15. Install release into a final disposable consumer from remote artifact/digest.

## Acceptance criteria

- IDE Development remote main contains exact permanent release.
- Release/tag/artifact/manifest identities agree.
- Hosted ARM64 live behavior proves no-checkpoint, cancellation, sealing, one full
  suite, receipt reuse, and changed-tree rejection.
- Development/staging/main did not rerun full suite for identical content.
- Rules/protections active; no source-system legacy App/runner dependency remains.
- Mac/Docker cleanup removes only owned resources and records recovery posture.
- Concurrent feature unchanged.
- Consumer packets receive immutable release identity.

## Prohibited

- No product consumer rollout before release publication.
- No bypass of a known test/code failure.
- No global App deletion while any consumer dependency remains.
- No deletion of dirty/unique branches/worktrees or ambiguous external resources.

## Handoff

Return complete source release evidence, immutable release identity, external
cleanup evidence, Actions usage/alerts, and explicit GO authorization for W3-P2–P4.

