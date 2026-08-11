# Normal GitHub credentials for Mac Mini GitOps

**Status:** required external configuration

Managed workflows do not use a GitHub App, App ID, or App private key. Private
repository jobs execute on the Mac Mini runners; trusted jobs use a normal GitHub
automation credential stored as the masked repository secret
`LINKTREND_AUTOMATION_TOKEN`.

The token must be a fine-grained GitHub token for the repository with only the
permissions needed for Contents, Pull requests, Checks, Statuses, Issues, and
Actions read access. It is available only to trusted, default-branch workflow
jobs. It must never be emitted to job outputs, artifacts, summaries, or files.

`LINKTREND_BUGBOT_USER_TOKEN` supplies the identity that creates the Bugbot
review comment. It may be the same normal automation identity when no separate
review identity is configured. Neither secret is available to untrusted PR code.

If `LINKTREND_AUTOMATION_TOKEN` is absent, the trusted workflow fails closed as
`automation_credentials_blocked`; it must never report a successful review,
merge, or promotion. Required review, exact-head checks, branch protection, and
the isolated untrusted runner remain mandatory.

## Repository setup

1. Add `LINKTREND_AUTOMATION_TOKEN` as a repository secret.
2. Add `LINKTREND_BUGBOT_USER_TOKEN` if Bugbot review comments are enabled.
3. Do not configure `LINKTREND_GITOPS_APP_ID` or
   `LINKTREND_GITOPS_APP_PRIVATE_KEY`.
4. Verify trusted jobs run on `linktrend-privileged`; untrusted PR jobs run on
   `linktrend-ci-isolated` for private repositories.
