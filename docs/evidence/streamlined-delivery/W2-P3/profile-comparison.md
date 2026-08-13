# W2-P3 profile comparison

Base: `9e9abf4da7361e765f8c276d708035be261f8359`

The managed templates remain the GitHub Actions compatibility source. The sync
script renders two explicit profiles:

- `github-actions`: preserves the existing schedule, workflow-run, check-run,
  and promotion PR fallback behavior.
- `local-coordinator`: removes schedule, check-run, workflow-run, and
  pull-request-target cascades from Packager, Integrator, repair, staging, and
  main promotion; retains bounded `workflow_dispatch` recovery; documents the
  frozen status contexts.

Both profiles retain pinned external actions and normal-token credential
boundaries. No live workflow was dispatched.
