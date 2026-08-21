# IDE model-routing policy 2.5.1

The preferred route is Cursor Auto Cost, but only when the Cursor Router selector
is explicitly `auto-smart` with `optimize_for=cost` and the effective selection
is read back. The Cloud API response `id=default`, `displayName=Auto` does not
prove that mode and is rejected for this route.

When Auto Cost cannot be expressed or independently attested, select a direct
Cursor model: Composer 2.5 for fully bounded economical work and Grok 4.6
Medium for complex or long-running work. Fast is always false.

Sol or another third-party model requires a task-specific exception recorded in
the packet (capability, security, independence or actual 1M-context need).
Record the requested route, selector/mode, effective model id/display name and
usage pool. Retry at most one hop; an unrecognized or unavailable route fails
closed without substitution.
