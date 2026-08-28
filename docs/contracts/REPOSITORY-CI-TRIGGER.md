# Repository-owned CI trigger contract

**Audience:** Review Packager, Integrator, promotion controllers, installers, CI maintainers.
**Status:** Binding for IDE Development Update 7 / WP-U07.
**Schema:** `core/managed-core/schemas/repository-ci-contract.schema.json`
**Implementation:** `scripts/gitops/repository_ci_contract.py`
**Repo declaration:** `.github/linktrend-repository-ci-contract.json`

---

## Purpose

IDE Development must retain each repository's necessary tests while enforcing the
shared lifecycle:

| Event | Managed compute |
|---|---|
| Issue-branch checkpoint push | None |
| Phase PR update | Fast on the exact head |
| Sealed final candidate | Full once (or trusted-governance when path-limited) |
| Unchanged staging/main promotion | Receipt verification only — no Full / broad PR matrix |

Branch protection requires the stable aggregate context
`Linktrend Full Suite`, never an unconditional raw application-Full context.

The versioned `promotionPolicy` in the repository declaration is the reusable
lean-promotion contract. It identifies `promote/` refs as receipt-only and
retains Fast/Full checks for `phase/` work plus the explicit Branch Source
Policy and Receipt Gate checks for promotion. Accepted checks are reused; a
second broad or local Full suite is not requested.

## Profiles

- `fast` — Phase validation
- `full` — sealed application candidate with mandatory coverage components
- `trusted-governance` — managed workflows/schemas/receipt/policy-only changes
- `promotion` — Branch Source Policy + receipt (+ optional short smoke)
- `scheduled` — repository-owned schedule decisions

Trusted-governance results must never be labelled as application Full.

## Evidence

Successful Full requires a `ci-component-manifest` bound to the exact candidate.
Missing mandatory components, stdout-only artifacts, wrong-schema/wrong-head
files, forged/stale/ambiguous omissions, and wrapper-masked failures fail
closed. Environment preflight failures are infrastructure, retain unrelated
successful component evidence, and resume only the invalidated component.
Caches are advisory: keys are fixed from immutable inputs before workspace
mutation; restore/key/save failures warn without changing correctness.

## Installer audit

`installer_audit_repository_ci_triggers` reports workflows whose broad
`pull_request` / `push` triggers would repeat expensive checks during
promotion. The audit is report-only and has no mutation authority. It emits a
versioned consumer-executable migration plan; a consumer may apply that plan
only under an independently explicit rollout scope. The plan guards expensive
workflows to `phase/*` heads, preserves application test commands, and does
not add a duplicate broad suite. This packet does not apply the plan to any
consumer workflow.

## Related

- `core/github/CI-GATE-CONTRACTS.md`
- `docs/contracts/STREAMLINED-DELIVERY.md`
- `docs/NEXT-IDE-DEVELOPMENT-RELEASE-SPECIFICATION.md` Update 7
