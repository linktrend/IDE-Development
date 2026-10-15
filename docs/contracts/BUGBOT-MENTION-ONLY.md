# Bugbot retirement notice

**Status:** Retired from the v3 IDE Development delivery and automation policy.

This file is retained because prior v2.5 workflows, migration fixtures, and audit
records refer to it. Its historical setup and triggering instructions are not
current operating guidance. Do not configure, invoke, require, or spend on Cursor
Bugbot as part of v3 work. Do not create or restore a Bugbot token, check alias,
workflow, reviewer gate, or settings automation from this document.

The v3 package requires an independent exact-head review by a different model
family. That review is performed through the existing reviewer process; it does
not depend on Bugbot.

Removing v3-managed invocations does not prove that the Cursor provider is
disabled in an account or dashboard. GitHub API observations cannot establish
that provider state. Report external provider coverage as unknown until an
owner-side, provider-authoritative readback is available. Do not infer disabled
status from missing secrets, variables, workflows, or branch-protection checks.

Historical references may remain in archived doctrine and negative migration
tests where they identify retired byte patterns or prove cleanup behavior.
