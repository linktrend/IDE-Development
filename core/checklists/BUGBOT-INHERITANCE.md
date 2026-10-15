# Retired: Bugbot inheritance checklist

This checklist is retained only as historical migration context. It is not an
installation procedure, repository adoption requirement, reviewer path, or
current configuration contract. Do not follow the setup, trigger, ruleset, or
credential instructions that may appear in old references to this file.

Bugbot is retired from v3 IDE Development policy and delivery. The current
review requirement is one independent exact-head review by a different model
family. The v3 package does not request or require Cursor Bugbot.

No package or GitHub API readback here establishes account-level Cursor
provider state. Treat that external state as unknown unless the account owner
checks it through an authoritative provider interface. Do not infer that the
provider is disabled from absence of a secret, workflow, or required check.

Historical check names and byte signatures may remain in migration fixtures or
retirement cleanup code so old repositories can be recognized and removed
safely. Those references do not authorize restoring the workflow or policy.
