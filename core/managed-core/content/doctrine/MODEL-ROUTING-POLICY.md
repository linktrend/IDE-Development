# IDE model-routing protocol-conformance restoration

This is a restoration/backfill of an original **mandatory Coding Execution
Protocol requirement** that was omitted or incorrectly implemented in the
superseded routing baseline. It is conformance restoration, not a new feature,
optional improvement, or rollout-created policy. Historical omission evidence
is the prior IDE baseline `2a0b6db`, whose route table hard-coded the
Sonnet/Sol/Grok pattern without Auto Cost mode proof and effective-model
attestation. The acceptance record must therefore prove the original behavior
end to end: route selection, explicit cost-mode binding, actual model readback,
usage-pool evidence, direct Cursor fallbacks, and documented third-party
exceptions.

The preferred route is Cursor Auto Cost, but only when the Cursor Router selector
is explicitly `auto-smart` with `optimize_for=cost` and the effective selection
is read back. The Cloud API response `id=default`, `displayName=Auto` does not
prove that mode and is rejected for this route.

When Auto Cost cannot be expressed or independently attested, select a direct
Cursor model: Composer 2.5 for fully bounded economical work and Grok 4.6
Medium for complex or long-running work. Fast is always false.

Bulk-document roles are a separate, task-justified route bound to the exact
non-Fast selector `gemini-3.7-flash-medium`. Retired legacy Gemini Flash
selectors are not accepted and must not be substituted into the route binding.

Sol or another third-party model requires a task-specific exception recorded in
the packet (capability, security, independence or actual 1M-context need).
Record the requested route, selector/mode, effective model id/display name and
usage pool. Retry at most one hop; an unrecognized or unavailable route fails
closed without substitution.
