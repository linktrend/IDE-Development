# Provider consumer boundary

This portable module is the IDE Development consumer-side validation boundary
for LiNKplatform, LiNKbrain, LiNKskills, LiNKautowork, and LiNKlibraries.

- It pins the approved provider commit/tree identities.
- It validates references and sanitized projections before an IDE agent acts.
- It has no credentials, network transport, provider execution, Git, Ledger, or
  Gate mutation functions.
- LiNKbrain remains advisory; Platform-issued identity is required at the
  transport boundary; skills are selected and executed by the requesting agent.
- Skill material is addressed by immutable release and progressive fragments.
  This module does not retain a local skill catalogue or full remote pack.

The managed package materializes this directory under
`.ide-development/providers/`. Provider endpoint configuration and live
stage/E2E/production activation are intentionally external HOLDs.
