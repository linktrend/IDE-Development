# Retired Bugbot Review Gate

**Status:** Retired by the Principal's global no-Bugbot policy (issue #500).

`review.bugbot="disabled"` is canonical. Legacy `final-candidate-only` is a
read-time migration input and normalizes to disabled. It never authorizes a
paid request. No workflow listens to Bugbot provider results, requests review,
or publishes `Linktrend Review Gate` success. The retained workflow is an
explicitly failing manual tombstone; it has no credentials or write scopes.
The old pure classifier is historical compatibility code, not delivery proof.

Delivery still requires real exact-head independent narrow review, genuine
Fast/application/Full checks and the sealed Full receipt. The native owned
reviewer route and unavailable-evidence behavior are documented in
`docs/AUTONOMOUS-GIT-OPERATIONS.md`. No actor label, comment, copied report,
requested model or missing provider status can grant approval.

Existing required native GitHub approvals remain in force. If external rules
still require `Cursor Bugbot` or `Linktrend Review Gate`, an authorized operator
must review and apply the protection migration separately. Never emit synthetic
success to satisfy obsolete contexts. This change does not mutate settings,
credentials, subscriptions, general Cursor coding or GitHub integration.
Historical raw evidence and classifier fixtures are retained as history.
