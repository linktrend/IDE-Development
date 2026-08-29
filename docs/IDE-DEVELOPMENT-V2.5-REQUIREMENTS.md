# IDE Development v2.5.1 completed baseline and v2.5.2 requirements queue

**Status:** v2.5.1 COMPLETED; provisional v2.5.2 requirements collection STARTED but not frozen, released, or authorized for rollout
**Baseline issue:** #339
**Successor requirements issue:** #427
**Comprehensive post-rollout reconciliation:** #433
**Baseline date:** 2026-08-19 (Asia/Taipei)
**Successor queue opened:** 2026-08-25 (Asia/Taipei)
**Supersedes for v2.5 planning:** any interpretation that offline contract validation alone constitutes a deployed provider connection

**Successor status (2026-08-27):** v2.5.1 is completed and is the current released package. The v2.5 baseline below is retained as the requirements record that drove that release family. Sections 15–18 contain the reconciled provisional v2.5.2 requirements queue; they do not define, publish, or authorize rollout of version 2.5.2.

## 1. Purpose

IDE Development v2.5 must correct the two material shortcomings exposed during the v2.4 rollout:

1. The installed product must give supported Codex and Cursor sessions real, authenticated access to the LiNK providers they are meant to use. Shipping validators without the transport and application adapters is not a complete deployment.
2. The development and promotion system must be materially simpler, faster, and cheaper. It must retain meaningful protection without repeating equivalent tests, checks, reviews, publications, or promotion work.

The release is complete only when the package, installed consumer experience, delivery workflow, tests, documentation, rollback, and live acceptance evidence all work together. Source code that has not been materialized, configured, and proven in the first designated canary repository from the existing nine consumers is not a deployed feature.

## 2. Required release outcome

Before v2.5 is published or rolled out:

- IDE Development is promoted through `development`, `staging`, and `main` using the v2.5 workflow itself.
- The published package is installed first into one designated repository from the existing nine consumers. That repository is the rollout canary; a separate disposable repository is not required.
- Both the Codex macOS app and Cursor macOS app can discover and call the approved LiNKbrain and LiNKskills read surfaces from that installed repository.
- Both apps can create and read a bounded LiNKbrain handoff in an isolated test namespace.
- Both apps can perform a read-only LiNKplatform capability/identity canary through the supported application adapter.
- Provider denial, unavailability, expired identity, missing credentials, and incompatible contract versions fail clearly and safely.
- No acceptance step depends on undeclared operator knowledge, an unverified repository secret, or a source-repository file that is absent from the installed package.
- The complete Fast path finishes in less than five minutes under normal GitHub capacity.
- One final Full validation is run for the final integrated exact tree. The same unchanged tree is not tested again during promotion or rollout.
- Promotion reuses the exact-tree evidence and does not rerun equivalent suites at `development`, `staging`, and `main`.

## 3. Fully functioning provider access

### 3.1 Installed product, not source-only code

The provider integration must be included in `core/managed-core/`, declared in the managed manifest, installed by the official installer, and present in every supported consumer install. Keeping it only under `core/link-integrations/` is insufficient.

The installed package must contain everything required for supported provider use except secret values and environment-specific endpoints. It must not reference test fixtures, source-repository-only paths, or undeployed files.

### 3.2 Codex and Cursor equivalence

IDE Development must provide native, documented adapters for both applications:

- **Codex:** managed discovery/instructions and the supported connector or MCP configuration required to expose provider tools.
- **Cursor:** managed discovery/instructions and the supported connector or MCP configuration required to expose the same provider capabilities.

The two adapters may differ technically, but their user-visible capabilities and failure behaviour must be equivalent. Installing v2.5 must not silently leave either application with documentation but no callable tools.

### 3.3 LiNKbrain

From an installed consumer, Codex and Cursor must be able to:

- search/read advisory Brain information;
- create, read, and accept bounded handoffs where the actor is authorized;
- receive a clear denied or unavailable result when the action cannot be performed;
- preserve Brain as advisory and never treat it as execution authority.

### 3.4 LiNKskills

From an installed consumer, Codex and Cursor must be able to:

- discover approved skills;
- retrieve an exact qualified release;
- load the appropriate progressive-disclosure material;
- report use through the supported bounded telemetry surface when required;
- reject unpublished, unqualified, incompatible, or mutable aliases.

IDE Development v2.5 must not ship its own workflow skills. Existing IDE Development skills—including setup, compliance, delivery, review, repair, promotion, and rollout skills—must be migrated to LiNKskills as qualified, immutable releases. Managed core may retain only the minimal provider loader and discovery instructions needed to authenticate to LiNKskills and retrieve the first approved skill; that loader is infrastructure, not a workflow skill.

Codex and Cursor must resolve IDE workflow skills exclusively from an IDE-owned, version-pinned LiNKskills namespace and allowlist. They must not silently select similarly named global, repository-local, marketplace, cached, stale, or model-invented skills. Retrieved releases must be verified before use, caches must be digest-bound and disposable, and provider unavailability must fail clearly rather than falling back to an unapproved copy.

Migration must avoid a bootstrap deadlock: the v2.5 installer first installs and proves the minimal LiNKskills loader, then retrieves and verifies the required v2.5 workflow-skill set, and only then removes the old physical IDE workflow skills. Rollback restores the prior complete package and skill set atomically.

### 3.5 LiNKplatform

The installed application adapters must use LiNKplatform for the identity, organization, permission, and capability decisions required by provider access. A direct Supabase development connector is not a substitute for the supported IDE application path.

### 3.6 Other providers

LiNKlibraries and LiNKautowork must retain their approved consumer contracts. Where a live service is available, v2.5 acceptance must include a real read-only application canary. Where a provider is not deployed, the release must prove a faithful local or staged adapter and record the live test as an explicit post-deployment hold rather than claiming production interoperability.

### 3.7 Complete agent-facing capability set

The installed adapters must expose the complete previously defined provider functionality, not merely generic connectivity:

| Provider | Required Codex and Cursor capabilities |
|---|---|
| LiNKplatform | Resolve the acting identity, organization, audience, service scope, permissions, and capabilities; refuse expired, forged, wrong-audience, wrong-organization, or insufficient-capability claims; never mint identity inside IDE Development |
| LiNKlibraries | Discover and retrieve verified revision-2 entries by exact immutable commit, tree, release digest, and receipt; refuse quarantined, metadata-only, superseded, mutable, or unpinned material; never execute a library payload merely because it was retrieved |
| LiNKbrain | Search/read advisory projections; use coordination references; create, read, accept, and track bounded handoffs; never expose raw prompts/transcripts or grant Brain execution authority |
| LiNKskills | Search/discover approved skills; validate and retrieve exact published, qualified, available releases; load progressive-disclosure fragments; let the requesting agent execute locally; report bounded use telemetry; refuse `latest`, unpublished, unqualified, unavailable, or incompatible releases |
| LiNKautowork | Submit an authorized bounded request; read status; exchange handoffs; read receipts and results; distinguish accepted, completed, failed, denied, and unavailable; never let a receipt grant Git, Ledger, Gate, or deployment authority |

All advertised modern provider connections must use the accepted sessionless MCP boundary and refuse silent downgrade to an obsolete protocol. The public agent-facing tools, names, inputs, result shapes, error codes, timeouts, and redaction rules must be documented and equivalent across Codex and Cursor.

### 3.8 Credentials and configuration

- Secret values remain outside Git.
- Required secret names, app installations, endpoints, scopes, and repository/environment placement are declared in a machine-readable preflight specification.
- Preflight runs before expensive tests and before promotion begins.
- Missing or invalid credentials fail immediately with one actionable diagnosis.
- The supported bootstrap must create, install, rotate, or restore every IDE-owned automation credential and repository/environment binding that can be provisioned through the authorized GitHub App or operator identity. Merely detecting that an IDE-owned credential is missing is not an acceptable steady state.
- Credentials that require a one-time founder or external-provider authorization must be requested once through a documented setup step, stored in the correct protected scope, and then maintained by the system. Routine releases must not repeatedly ask for the same credential.
- The Review Ready publisher must have one durable supported authentication route. Bootstrap must prove that route with a harmless write/read/delete canary before any work relies on it, and must repair missing repository bindings or installation permissions automatically when authorized.
- Review Ready publication failure must not be discovered only after implementation and testing are complete. If the credential cannot be provisioned or repaired, the release must stop at bootstrap with the exact external action genuinely required.
- The normal supported path must not depend on a credential that the installer, bootstrap, or release procedure failed to provision or verify.
- No built-in token may be silently substituted where a privileged application credential is required.
- Configuration migrations must remove or reject obsolete settings before runtime activation.

## 4. Simplified development workflow

### 4.1 One ordinary path

The normal path is:

1. Work is committed and pushed on `issue/*`.
2. Accepted issue commits are collected into one `phase/*` candidate.
3. One Phase PR targets `development`.
4. Fast runs once for the candidate.
5. Independent review examines the exact candidate head.
6. Full runs once only on the final integrated exact tree when the change risk requires Full.
7. The delivery controller merges the accepted candidate into `development`.
8. Temporary promotion PRs move the identical tree to `staging` and then `main`, reusing the existing evidence.

There must not be multiple ordinary publishers, coordinators, readiness mechanisms, or merge authorities competing for the same transition.

### 4.2 Clear ownership

- Implementers own code and checkpoint evidence; they do not open or merge delivery PRs.
- One packager owns Phase composition and the Phase PR.
- One delivery controller owns protected merges and promotion orchestration.
- Independent review remains independent from implementation.
- Founder approval is requested only for decisions explicitly reserved to the founder, normally the final production/main approval—not for routine recoverable mechanics.

### 4.3 Bounded recovery

- Ordinary code/test repair is limited to three focused cycles.
- Infrastructure retry is limited to two attempts.
- After the bound, stop that lane and publish one concise blocker containing the exact failure, owner, and safe recovery action.
- A stalled agent or workflow is detected automatically, cancelled when safe, and replaced without retaining false active capacity.
- Cancellation, skipped checks, missing checks, and unavailable reviewers never count as passing.

## 5. Test and check simplification

### 5.1 Test by risk and change

Tests must be selected from the files and contracts changed, not by automatically running every available suite at every branch transition.

- **Focused tests:** run during implementation and repairs.
- **Fast:** one bounded PR gate covering formatting, static validation, affected unit/contract tests, secrets, and workflow integrity. Target: under five minutes.
- **Full:** one final integration suite for the final exact tree when required by the release risk profile. It is never an automatic per-branch ritual.
- **Live canaries:** small provider/application checks run only where live behaviour must be proven. They do not duplicate the source suite.

### 5.2 No redundant execution

- An unchanged tree with matching dependency, workflow, and environment identities reuses its signed evidence.
- Promotion does not rerun Fast or Full merely because the branch name changed.
- Rollout verification checks installed identity, drift, configuration, and a small functional canary; it does not copy and execute source-repository test suites inside consumers.
- Multiple workflows must not perform the same secret scan, policy validation, build, or test under different names.
- Expensive suites use path/risk selection and concurrency cancellation so obsolete runs stop promptly.

### 5.3 Truthful fixtures

Tests installed in consumers must be self-contained. A managed test must not reference a file that exists only in IDE Development source. Fixtures must model actual supported interfaces, and passing fixtures must not be presented as live interoperability evidence.

## 6. GitHub Actions and check topology

- Maintain the minimum number of required checks necessary to make a safe decision.
- Prefer one Fast workflow and one conditional Full workflow over chains of small workflows that repeat checkout, setup, scanning, and publication.
- Review Ready is a state derived from validated evidence; it must not require a second publisher to repeat the gate.
- Merge readiness and promotion readiness must have one authoritative result each.
- Required check names and rulesets are installed atomically with their workflows so a rollout cannot require checks that the repository cannot produce.
- GitHub-hosted compute may run independent repository work in parallel, but parallelism must not duplicate validation of the same tree.
- Usage/cost reporting remains available, while cost controls must not silently block an authorized release.

### 6.1 GitHub App authentication cutover

Replacing a long-lived automation token with GitHub App authentication must not create a new delivery blockage. Before cutover, v2.5 must inventory every operation performed by the existing credential and prove permission parity for repository contents, pull requests, checks/statuses, Actions dispatch/read, issues, metadata, and any required administration surface.

The cutover must account for:

- App installation on IDE Development and every intended consumer repository;
- repository-selection drift when a new consumer is added or an installation is narrowed;
- one-hour installation-token expiry, including refresh before long operations and safe retry after an authentication expiry;
- least-privilege token minting for the exact repository and operation;
- GitHub primary and secondary rate limits, bounded backoff, request consolidation, and a clear rate-limit hold rather than a retry storm;
- workflow-trigger differences between the built-in workflow token and an App installation token;
- required-check and ruleset recognition of statuses/checks published by the App identity;
- fork/untrusted-event rules where protected credentials must not be exposed;
- App suspension, removal, permission changes, private-key rotation, webhook/configuration drift, and GitHub outages;
- token-format changes: code must not assume a fixed token length or persist a minted installation token;
- audit logs that identify the App, repository, exact operation, and sanitized failure without exposing credentials.

Migration uses a canary repository and an atomic cutover. The existing route remains recoverable until the App path proves bootstrap, Review Ready publication, Phase PR creation/update, required-check production, merge, and promotion for an exact test tree. Rollback restores the former route without changing product code or weakening protection. After acceptance, the old long-lived credential is revoked and its repository references are removed so two competing authentication routes cannot remain active.

## 7. Bootstrap, publication, and rollout

### 7.1 Bootstrap

Bootstrap is a declared, repeatable operation that installs and verifies:

- repository variables and non-secret configuration;
- required secret names and availability without exposing values;
- GitHub App installation and permissions;
- required rulesets/check mappings;
- managed workflows and controller configuration;
- Codex and Cursor provider adapters.

Bootstrap owns the lifecycle of IDE-managed credentials and bindings; it does not merely inventory them. Its report must distinguish `present`, `provisioned`, `repaired`, `externally blocked`, and `invalid`, and must prove the Review Ready publisher path before accepting implementation work.

Bootstrap must be idempotent and produce a concise pass/fail report before release work continues.

### 7.2 Publication

Publication must bind the version, source commit, Git tree, manifest, package digest, and rollback identity. The published artifact must be byte-for-byte the artifact validated before promotion.

### 7.3 Consumer rollout

Rollout must support all configured consumer repositories with repository-scoped isolation. It starts with one real canary repository selected from the existing nine; no separate disposable repository is required. The remaining eight begin only after the canary repository passes installation, app discovery, provider access, failure, and rollback checks. For every consumer it must:

1. install the exact published package;
2. apply configuration migrations;
3. verify all managed-file hashes and remove obsolete managed files safely;
4. verify Codex and Cursor discovery;
5. run the small provider-access canaries applicable to that repository;
6. create a normal rollout PR and promote the accepted identical tree without redundant suites;
7. record a rollback commit/package identity.

A repository is not counted as rolled out merely because `.ide-development/` exists or its version file says `2.5.0`.

### 7.4 Repeatable macOS application canaries

The release must provide a supported non-interactive acceptance harness for the Codex and Cursor macOS applications. It must be able to select the canary repository, start an isolated test session, invoke the named read and handoff tools, capture sanitized results, and terminate the session without depending on coordinate clicking or an already-focused window.

If application automation is unavailable, the app canary fails. The release may not replace it with inspection of configuration files, a direct provider call outside the app, or a statement that the connector appears installed.

The harness must use a narrow tool allowlist and per-operation read/write policy. It must not require Cursor's blanket `--force` permission in ordinary use. A read-only canary may approve only the named provider discovery/read tools; a handoff canary may additionally approve only the isolated test-namespace handoff operations.

Baseline finding on 2026-08-19: Cursor CLI in the real LiNKplatform repository reported the Supabase MCP server ready. `--approve-mcps` still rejected `supabase-list_projects`, while a separately authorized read-only run with `--force` successfully queried `linkplatform-prod` (`sedmbicfstnntmkczpvd`): `platform.capabilities` and `platform.organizations` existed with row counts 2 and 1. Therefore Cursor-to-Platform application access is proven, but the current approval mechanism is too broad for the v2.5 production harness and must be replaced by the narrow policy above.

## 8. Required acceptance evidence

v2.5 cannot be released until one concise acceptance matrix proves:

| Area | Required proof |
|---|---|
| Package | Manifest and installed files match the published artifact |
| Codex | Real Brain read, Skills discovery/retrieval, Brain handoff, and Platform capability canaries from the first upgraded repository among the nine consumers |
| Cursor | The same real canaries from the Cursor macOS app in that consumer |
| Failure | Denied, unavailable, expired identity, missing credential, incompatible provider, and obsolete configuration fail clearly and safely |
| Workflow | Checkpoint does not start expensive CI; one Phase PR; Fast under five minutes; one final exact-tree Full when required |
| Promotion | `development`, `staging`, and `main` have the accepted tree and reuse its evidence |
| Rollout | Installed identity, configuration, discovery, functional canaries, and rollback evidence are recorded per repository |
| Cleanup | No obsolete managed workflows, stale controller runs, abandoned rollout branches, or duplicate required checks remain |

Fixture-only, source-only, configuration-presence, health-only, or installation-only evidence cannot satisfy a live application criterion.

## 9. Compatibility and migration

- v2.4 consumers must be upgradeable without losing repository-owned files.
- Obsolete v2.4 workflow/check definitions and provider-validator-only surfaces must be migrated or retired explicitly.
- v2.5 must distinguish managed files from repository-owned customizations and never delete unowned work.
- Provider pins and contract versions are checked during upgrade. An incompatible provider blocks activation with a clear repair path.
- Rollback restores the prior package, configuration, workflow/ruleset mapping, and provider adapter state.

## 10. Explicit exclusions

This requirements document does not authorize:

- implementation, deployment, publication, promotion, or consumer mutation;
- weakening repository protection or treating missing evidence as passed;
- granting Brain execution authority;
- putting secret values in Git;
- deploying LiNKlibraries or LiNKautowork runtime services that are not otherwise authorized;
- unrelated product changes in consumer repositories.

## 11. Implementation order

1. Freeze these requirements and inventory the current v2.4 workflow/check/provider surfaces.
2. Design the single-path workflow and provider adapter architecture together so delivery cannot publish an incomplete package.
3. Implement provider transport, Codex/Cursor adapters, configuration preflight, and self-contained focused tests.
4. Implement the reduced Fast/conditional-Full topology and exact-tree evidence reuse.
5. Remove or migrate redundant workflows, publishers, checks, and obsolete configuration.
6. Run focused source and contract validation.
7. Install into one selected repository among the nine consumers and complete the Codex, Cursor, failure, handoff, and Platform live canaries.
8. Run one final combined Full on the exact release tree if required by the accepted risk profile.
9. Promote and publish the identical artifact.
10. After that real repository passes, roll out to the remaining eight consumers and prove installed functionality, not merely installed files.

## 12. Definition of done

IDE Development v2.5 is done only when a normal coding agent can enter an upgraded consumer repository, use either Codex or Cursor, discover and use the authorized LiNK providers and handoffs without manual undocumented setup, complete work through the simplified workflow, and reach `main` without redundant validation—while genuine failures still stop safely with one clear explanation.

## 13. Cross-repository failure audit requirements

The following requirements come from failures observed across IDE Development, LiNKplatform, LiNKskills, LiNKbrain, LiNKlibraries, LiNKautowork, OpenClaw Prime, LiNKsites, and LiNKdeveloper tasks. They are release requirements, not optional future improvements.

### 13.1 Checks, review, and repository protection

- Required-check names, workflow job names, repository variables, and rulesets must be generated from one versioned contract and installed atomically. A repository must never require a name its installed workflow cannot produce.
- Integrators, packagers, promoters, and rulesets must consume the managed review outcome, not hard-code obsolete raw names such as an external reviewer or an old default verification job.
- External review services must have a defined `available`, `unavailable`, and `failed` outcome. An outage must not be recorded as passed, but it must not permanently deadlock an otherwise independently reviewed exact candidate.
- The bootstrap must discover the repository plan and the management APIs actually available before attempting ruleset or branch-protection operations. It must not repeatedly probe an unavailable API or assume a protection object exists.
- Read-only inspection commands must be technically incapable of dispatching a workflow. Status/probe and mutation/dispatch interfaces must be separate so an inspection cannot accidentally start Full or another expensive run.
- `skipped`, `queued`, `cancelled`, `missing`, and `unavailable` are distinct from `passed` and must remain distinct in every controller decision and report.
- A promotion must not rerun generic repository CI or serial application suites when the exact accepted tree already has valid evidence.

### 13.2 Promotion markers and evidence

- Promotion markers and receipt bindings must be generated by one schema-validating tool. Operators and agents must not hand-write JSON markers, placeholders, quoted JSON, candidate heads, or receipt coordinates.
- The tool must validate the exact source head/tree, target base, retained receipt, and PR body before opening the promotion PR, and must reread them before merge.
- Squash and merge commits may have different commit identities; equality decisions must compare the intended Git tree and retained evidence rather than falsely requiring ancestry.
- An optional cache, artifact upload, analytics step, or post-job cleanup must never turn successful required application proof into failure. Cache keys must be fixed before workspace mutation, and cache restore/save remains advisory.

### 13.3 Truthful and maintainable tests

- Time-sensitive fixtures use a controlled clock or relative future/past values. A fixture intended to be valid must not silently expire as the calendar advances.
- The canonical Full inventory must automatically include every declared required test package and fail if a new required test is omitted. A green Full that never executed new tests is not acceptance evidence.
- When canonical catalogues, manifests, or other inputs change, dependent fixture digests and disposable caches must be rebuilt through the authoritative generator; stale derived fixtures must not be edited manually.
- Generated managed mirrors and manifests have one canonical source and one deterministic generator. Agents must not manually edit generated copies or allow source/mirror drift.
- Tests must distinguish provider source commit/tree, selected release source, artifact tree, payload identity, and receipt identity. Similar-looking hashes must not be treated as interchangeable.
- Cross-platform tests must normalize legitimate macOS path aliases such as `/var` and `/private/var`, while still rejecting traversal and unsafe paths.

### 13.4 Real delivery components

- Files called Packager, Integrator, Controller, Review Ready, or Promoter must actually perform the named bounded operation or be renamed. Validation-only workflows must not masquerade as callable delivery components.
- Bootstrap acceptance must invoke each installed delivery component in a harmless dry run and prove that the expected Phase PR, state transition, check, or promotion package can actually be produced.
- Source-only adapters, documentation, fixtures, workflow filenames, or package entries do not establish callable functionality.

### 13.5 Agent, model, worktree, and host reliability

- Before dispatch, the coordinator verifies the requested model's exact supported identifier, reasoning level, execution location, and approval/sandbox compatibility. One invalid model slug must not launch or strand multiple repository workers.
- Agent startup must prove it can read and write the assigned isolated worktree, including linked-worktree Git metadata required for fetch, merge, commit, and push, before implementation begins.
- Agents publish bounded heartbeats containing state (`starting`, `researching`, `editing`, `testing`, `waiting`, `blocked`, `complete`) and last material progress. A run that remains busy without progress is cancelled and replaced after the configured bound.
- Completed, failed, cancelled, and abandoned agents are closed so stale sessions cannot consume capacity or be mistaken for active work.
- The coordinator enforces repository-scoped concurrency and host memory/CPU limits. Heavy typecheck, build, Full, and browser jobs run serially when host pressure requires it; unrelated processes are never killed.
- Tool and shell preflight must detect unsupported option combinations and remote shell differences before a release or deployment command starts.

### 13.6 Automated change safety

- Security scanners, formatters, migration tools, generators, and bulk repair scripts must declare whether they are read-only or mutating before execution.
- A mutating automated tool runs first on an isolated canary and must stop when changed-file or changed-line limits are exceeded.
- Unexpected broad mutation—such as thousands of modified source, test, or asset files—automatically aborts the packet and preserves the last known-good tree for rollback. It must not be “repaired” file by file without identifying the introducing operation.
- Before merge, the controller compares the candidate's path and size profile with the approved scope and requires explicit review of unexpected mass changes.
- Deployment/cutover scripts use the target host's actual shell or explicitly invoke the required interpreter, check permissions before mutation, retain the old release, and automatically restore it if health checks fail.

### 13.7 Acceptance canaries derived from these failures

Before v2.5 publication, the canary repository must prove all of the following without special manual repair:

1. Bootstrap provisions and proves authentication, installed components, check-name/ruleset parity, and repository-plan compatibility.
2. A checkpoint push starts no expensive CI.
3. The Packager creates one Phase candidate and PR.
4. Fast runs once and finishes within the target.
5. External review unavailability is recorded truthfully and follows the approved independent-review fallback without deadlock.
6. One final Full executes every declared required component exactly once.
7. Promotion markers are generated automatically and accepted unchanged by staging and main gates.
8. Promotions reuse evidence and do not rerun equivalent application suites.
9. A deliberately unavailable cache remains non-blocking while a deliberately failed required test remains blocking.
10. A time-controlled fixture remains deterministic across simulated dates.
11. Codex and Cursor retrieve only the approved IDE workflow skills from LiNKskills and perform the live provider canaries.
12. Stalled-agent, expired-App-token, rate-limit, unsupported-model, and host-pressure simulations stop or recover within their bounds without losing the candidate.
13. A simulated broad automated mutation is rejected and rolled back.
14. Rollback restores the previous installed IDE package, app adapters, workflow/check contract, credentials/bindings, and provider-skill set.

## 14. Audit traceability

| Repository/task family inspected | Workflow lesson carried into v2.5 |
|---|---|
| IDE Development release, compute, and provider-connection tasks | stale required statuses, unavailable credentials, invalid model identifiers, source-only provider delivery, obsolete package-version expectations, and workers exiting during startup |
| LiNKplatform production delivery | missing trusted-publisher configuration, repository-plan API limitations, stale-base conflicts, linked-worktree metadata permissions, and malformed promotion markers |
| LiNKskills production delivery | external-review outage, missing receipt markers, placeholder promotion identities, skipped-versus-passed ambiguity, and repeated branch promotion checks |
| LiNKbrain production delivery | hard-coded obsolete review/check names, inaccessible protection controls, accidental workflow dispatch during inspection, and redundant promotion CI |
| LiNKlibraries production delivery | missing callable Packager/Integrator, privileged Review Ready dependency, omitted tests from the canonical Full command, and derived fixture digests becoming stale |
| LiNKautowork production delivery | calendar-expired fixtures, check-name/ruleset mismatch, infrastructure-only CodeQL failures, and review workflows restricted to the wrong branch type |
| OpenClaw Prime and Lisa delivery | stalled/dirty coordination state, whole-repository automated corruption, parser/build recovery, target-shell incompatibility, permission preflight, and guarded runtime rollback |
| LiNKsites CI and provider-consumer work | optional cache post-save falsely failing successful Full evidence, duplicate managed/application Full execution, cancellation scoping, and missing CMS build coverage |
| LiNKdeveloper provider-consumer work | duplicate fixture trees, incomplete native-contract validation, resource contention, unsupported model slug, worktree-local dependency/tool gaps, and macOS path normalization |

## 15. Provisional IDE Development 2.5.2 successor requirements queue

**Status:** CANDIDATE ONLY — not a defined release, not implemented as a release, not approved for publication, and not approved for consumer rollout.

All consumer repositories remain on their valid installed IDE Development 2.5.1 package until a later release is fully defined, implemented, independently audited, protected-integrated, packaged, and explicitly approved for rollout by the Principal.

### 15.1 Candidate intent

The provisional 2.5.2 patch is the next central collection point for IDE tooling maintenance discovered after the 2.5.1 rollout. Candidate work may be developed and protected-integrated in this repository without creating a release. The release boundary stays open so other compatible IDE corrections can be assessed before the Principal decides the final scope.

IDE Development remains the sole source of truth for managed IDE tooling. Consumer repositories use the released package; they do not independently author or release variants of managed IDE files.

### 15.2 Candidate queue

| Candidate | Requirement | Current treatment |
|---|---|---|
| Managed-upgrade conflict resolution | Accept only an explicitly allowed, exact, non-empty observed subset of managed-file differences; preserve fail-closed validation for every other difference. Candidate source: Issue #424. | Central IDE candidate. Do not copy or release it as 2.5.2 yet. |
| Generated secret-scan fixture binding | Ensure generated closure fixtures bind to the exact governed candidate and cannot become stale across protected assembly or promotion. Candidate source: Issue #425. | Central IDE candidate. Do not copy or release it as 2.5.2 yet. |
| Consumer managed-file immutability | In the future 2.5.2 release, enforce that installed managed files are read-only between official installer transactions and byte-identical to that installed package. This enforcement is not part of 2.5.1 and must not be retrofitted into 2.5.1 consumer code. | Candidate requirement for 2.5.2 only; all consumers remain on 2.5.1. |
| Immutable released-package identity | Publish one immutable tag/release, source commit/tree, manifest digest, and archive digest for every rollout. Protected `development` and `main` must never expose different managed bytes under the same package version. Consumer verification and cleanup must bind to the released identity, not merely the text in `VERSION`. | Candidate requirement for 2.5.2; closes the ambiguity discovered because 2.5.1 has no published tag/release while protected branches contain different manifests. |
| Unreleased post-2.5.1 change inventory | Reassess the central changes currently present only after protected `main`: adaptive Cursor capacity, exact Cursor environment/run binding, completion evidence stored outside candidate trees, obsolete review-gate removal, promotion Full-receipt binding, managed-upgrade conflict handling, generated-transaction closure, and change-scoped secret-scan/parser/migration handling. Each accepted behaviour must become an explicit 2.5.2 requirement and later receive a correctly versioned implementation; it must not be distributed while still claiming 2.5.1. | Candidate inventory derived from `origin/main..origin/development`; no release or consumer rollout authorized. |
| Completion-gate remote parser | Assess the LiNKskills-local enhancement to `scripts/gitops/completion_gate.py` for robust remote parsing. If accepted, specify its fail-closed inputs, tests, and portability centrally before implementation. | Candidate intent extracted from LiNKskills during 2.5.1 cleanup; the consumer-local implementation is removed and receives no application DoD credit. |
| Explicit repository-bound Cursor Cloud dispatch | Default every Cursor Cloud dispatch to an explicit `repos[]` binding carrying the exact repository URL and requested starting ref. Treat a saved display-name environment as provenance only until an authenticated API smoke readback confirms the repository/ref. Accept temporary `dev/cloudcursor/*` branches only when API readback proves the worker repository is correct and its HEAD commit/tree exactly equals the requested starting-ref commit/tree; fail closed on any repository or commit/tree mismatch. Maintain one central program-to-repository routing registry and never fall back to the shared `IDE Development 2.5.1` named environment for application repositories. | Candidate requirement for IDE Development 2.5.2; central documentation/contract only, queued and unreleased. Do not alter installed 2.5.1 files or publish a 2.5.2 package. |
| Product/tooling lifecycle separation | An unreleased central IDE maintenance candidate must not block a product repository's integration or promotion when that repository's installed released IDE version is valid and its own required protected checks pass. | Required governance rule. |
| Review Ready publisher import repair | Queue the accepted Issue #428 repair and its tests for a future 2.5.2 revision candidate. The repair changes only `scripts/gitops/issue_checkpoint.py` and `tests/github_auth/test_issue_checkpoint.py`; it must remain central and must not be integrated into the released 2.5.1 package or any consumer. | Candidate evidence: accepted checkpoint `b9e993592984fe5ffda1308d97318bcd134f9fbc` (tree `4018c67d3b8cafd62507354286e5b6eac4cf748a`), independently audited as accepted (receipt digest `sha256:331824f08e35546602161bc070fca69bb08213fd9e39a968c769e6a97597f37a`), and referenced by closed PR [#429](https://github.com/linktrend/IDE-Development/pull/429). PR #429 was closed by Principal direction without integration. |

### 15.2.1 Current 2.5.1 cleanup and future 2.5.2 enforcement

Until a separately defined and approved 2.5.2 release exists:

1. Version 2.5.1 did not technically enforce read-only managed files. The current portfolio cleanup is a Principal-directed remediation: classify consumer-local IDE changes, retain valid change intent in this central requirements queue, and restore consumers to the official 2.5.1 package without treating tooling drift as application work.
2. Preserve repository-owned application work required by the application's definition of done. Preserve IDE change intent only when it is a valid 2.5.2 candidate. Unneeded work in neither category may be discarded after classification.
3. Restore 2.5.1 managed bytes through the official 2.5.1 installer/manifest transaction. Do not hand-edit a consumer into apparent conformity or copy tooling from another consumer.
4. Proposed managed-file changes are central 2.5.2 revision candidates. They may later be implemented, audited, and protected-integrated centrally, but they are not 2.5.1 changes and do not authorize a consumer update.
5. Read-only enforcement is itself a 2.5.2 candidate requirement. It is not being implemented or rolled out during the 2.5.1 cleanup.
6. The Issue #428 Review Ready publisher import repair and its tests are queued under this rule. The accepted checkpoint and closed PR #429 are evidence for candidate provenance only; they are not 2.5.1 release or rollout evidence.

Queue membership does not mean acceptance. Each item still requires bounded implementation, its required validation, exactly one independent audit for its checkpoint, and protected integration before it can enter a release candidate.

### 15.3 Required successor-release behaviour

1. **No in-place consumer authorship.** IDE-managed files installed in a consumer repository are read-only except while the official installer performs a verified install, update, or rollback transaction.
2. **Central changes require a new identity.** Any change to managed package bytes must be authored in this repository and shipped under a new package version with a matching immutable manifest and digest. Changed bytes must never continue claiming to be version 2.5.1.
3. **Consumers stay on 2.5.1 for now.** OpenClaw Prime and every other consumer retain their current released 2.5.1 installation. No 2.5.2 installation, label, manifest, or rollout is authorized by these requirements.
4. **Installed helpers remain installed.** Repository-local IDE helpers that support agent setup, evidence, packaging, checks, and controlled integration remain present. They are development tools, not product runtime code, and a future approved release may supersede them through the installer.
5. **Product promotion is independent.** A consumer product may proceed through its governed development, staging, and main promotion using its valid installed 2.5.1 tooling. Pending central IDE candidate work is not a product-engineering blocker.
6. **Official rollout only.** If 2.5.2 is later approved, each consumer is updated through a dedicated IDE-maintenance change using the official installer. The transaction must preserve repository-owned product files and prove rollback to the prior released IDE installation.

### 15.4 Release-definition gate

The provisional 2.5.2 release may be defined only after the Principal reviews the complete candidate queue. Definition requires:

- a frozen and explicit scope;
- protected-integrated central implementation for every included item;
- required focused and package-level validation;
- exactly one independent audit per checkpoint;
- an immutable package manifest and reproducible package proof;
- disposable-consumer install, update, verification, and rollback proof;
- confirmation that consumer product/runtime files are untouched; and
- separate Principal approval to publish and roll out the release.

Until that gate is satisfied, the repository version, installer version, package manifest, saved Cursor environment identity, and all installed consumer identities remain 2.5.1.

## 16. Post-2.5.1 execution findings

This section reconciles the problems observed while v2.5.1 was used to coordinate and finish the nine-program portfolio. It records both the temporary recovery used at the time and the permanent behaviour required from a future 2.5.2 release. A temporary recovery is evidence for a requirement; it is not automatically the required implementation.

### 16.1 What worked and must be preserved

- Short-lived `issue/*` checkpoints, one independent audit per checkpoint, Phase assembly, and controller-owned protected integration preserved scope and review separation when exact identities were used consistently.
- Focused packet tests plus one exact-tree Phase Full gave useful protection without requiring a whole-application audit for every packet.
- Exact repository URL, commit, tree, branch, model, effort, and run readback made remote-worker claims deterministic.
- Identical-tree promotion evidence successfully separated content equality from merge-commit identity when the receipt contract supported it.
- Isolated worktrees and exact protected-ref audit checkouts allowed investigation without touching dirty shared checkouts.
- Fail-closed provider and consumer handoff receipts prevented synthetic or stale evidence from being counted as accepted.
- Bounded retries followed by one declared fallback prevented ordinary service failures from becoming unlimited retry loops.
- Generated-output closure, clean-tree checks, and deterministic rebuilds exposed stale catalogues and fixtures that ordinary tests had masked.
- Separating repository-owned pre-deployment engineering from provider, consumer, VPS/live, canary, and founder acceptance prevented external operations from being misreported as source completion.

### 16.2 Failure and recovery ledger

| Observed problem | Temporary recovery or bootstrap used | 2.5.2 requirement |
|---|---|---|
| Cursor workers were reported as running from PREPARED records, local processes, mocks, fabricated IDs, or terminal runs. | The dashboard and authenticated API readback became the only runtime authority; stale agents were archived. | CUR-01 through CUR-05 and OBS-01. |
| Saved Cursor environment names routed work to the wrong repository or were not recognized by the API. | Dispatches used explicit `repos[]` bindings and verified the worker repository plus starting commit/tree; mismatches were archived. | CUR-01 through CUR-04. |
| Cursor-created `dev/cloudcursor/*` branches were incorrectly rejected because their branch name was not `development`. | Acceptance was corrected to verify repository and starting commit/tree rather than require the protected branch name. | CUR-03. |
| Orchestrators stopped after a status response, ordinary failure, or worker completion, leaving safe work idle. | The coordinator manually woke orchestrators, processed terminal events, and dispatched successors. | ORC-01 through ORC-07. |
| Packet audits expanded into whole-application audits and delayed large repositories. | Audits were narrowed to owned changed paths, affected contracts, and focused tests; Full stayed at Phase integration. | AUD-01 through AUD-05. |
| Full evidence became stale after a protected merge changed the commit but not the tree. | Ad hoc promotion receipts rebound Phase identity to the protected merge identity. | RCP-01 through RCP-05. |
| A checked-in OpenClaw baseline receipt invalidated itself every time its own rebind was committed. | Several narrow receipt/controller rebinds proved the loop but did not remove the structural cause. | RCP-06 through RCP-09. |
| LiNKsites Phase PRs emitted CodeQL but not the required application workflows. | A one-time, narrow, independently audited workflow bootstrap temporarily required only an actually emitted check, merged the repair, restored the original ruleset, and verified with a disposable PR. | WFL-01 through WFL-07. |
| Rulesets required obsolete or impossible check names. | Rulesets were read back, minimally corrected, and restored after bootstrap. | WFL-02 and WFL-03. |
| GitHub jobs raced prerequisites, remained queued, returned startup failures, or were blocked by exhausted hosted-compute funds. | The exact run/check-suite state was inspected; one clean retry was used only after prerequisites or budget were healthy. | WFL-08 through WFL-11 and CAP-01 through CAP-04. |
| OpenClaw checkout fetched the repository's complete ref population and timed out. | Checkout was restricted to the exact candidate and protected base refs. | WFL-12. |
| IDE 2.5.1 managed files were edited independently in consumer repositories and then confused with application work. | Useful IDE changes were queued centrally for 2.5.2; irrelevant changes were discarded after classification; consumers were restored to the released 2.5.1 package. | MNG-01 through MNG-09. |
| Dirty shared checkouts, retained worktrees, local branches, open PRs, and uncommitted files contradicted DONE claims. | Exact-main audit checkouts and manual reconciliation distinguished product work, IDE candidate work, post-deployment work, duplicates, and obsolete residue. | CLS-01 through CLS-08. |
| Completion percentages counted Issues, optional packets, partial work, or tranche results. | Denominators were reconstructed from committed canonical PRD packets; partial and unintegrated work received zero credit. | DOD-01 through DOD-07. |
| Aggregate completion ledgers contradicted detailed HOLD evidence or stale execution manifests. | Detailed packet evidence and current protected refs took precedence pending reconciliation. | DOD-08 through DOD-10. |
| CI rebuilt a catalogue before checking it, so a stale committed catalogue appeared green. | A clean isolated checkout ran the freshness check before mutation and compared the post-generator tree. | GEN-01 through GEN-05. |
| Generated secret-scan fixtures became stale during assembly and promotion. | Narrow generated-fixture closure repairs regenerated the authoritative fixture for the exact candidate. | GEN-02 through GEN-06. |
| Missing Python, PostgreSQL, Docker, Node dependencies, or architecture-specific runners caused skipped checks or misleading failures. | Disposable environments and targeted preflight distinguished source defects from unavailable tooling. | ENV-01 through ENV-06. |
| Cross-repository handoffs such as LiNKsites to LiNKharness and LiNKsites to Master Website Template stalled for hours. | Immutable provider/consumer receipts were passed manually and downstream work was restarted after acceptance. | DEP-01 through DEP-06. |
| Scheduled Update messages failed, targeted a retired coordinator, or reported before terminal worker results were processed. | Automations were recreated or manually triggered and the live coordinator was explicitly handed ownership. | AUT-01 through AUT-06 and HND-01 through HND-05. |
| Status reports inferred progress from tests, manifests, or source integration without proving protected promotion and repository cleanliness. | Reports were corrected to use protected refs, accepted receipts, worker readback, and a fixed definition of done. | OBS-01 through OBS-07. |

## 17. Detailed v2.5.2 candidate requirements

These are normative candidate requirements. The identifiers are stable planning references; inclusion in a future release still requires the release-definition gate in section 15.4.

### 17.1 Cursor dispatch and remote-worker truth

- **CUR-01 — Explicit repository routing.** Every Cursor Cloud request must carry the exact GitHub repository URL and requested starting ref in the API/SDK request. A saved environment display name must never be the sole routing input.
- **CUR-02 — Central routing registry.** IDE Development must own one versioned program-to-repository routing registry. Shared multi-repository entries are allowed only for declared cross-repository tasks and must list every permitted repository.
- **CUR-03 — Starting-identity verification.** After creation, readback must prove the actual repository and the worker branch HEAD commit/tree equal the requested starting-ref commit/tree. A service-created branch name is acceptable; a repository or identity mismatch is not.
- **CUR-04 — Fail-closed mismatch handling.** Wrong-repository, wrong-ref, install-failed, unauthenticated, or identity-incomplete runs must be cancelled or archived and must not be counted as workers.
- **CUR-05 — Exact model policy.** Dispatch evidence records provider, model, reasoning effort, and fast mode. Unsupported model aliases fail during preflight before capacity is consumed.
- **CUR-06 — SDK/API equivalence.** The official SDK may be the orchestration client, but its create, status, archive, and evidence semantics must be identical to direct API use.
- **CUR-07 — Routing canary.** Release acceptance must create a harmless read-only worker for every configured repository, verify exact starting identity, archive it, and retain a sanitized routing receipt.

### 17.2 Durable orchestration and maximum safe parallelism

- **ORC-01 — Durable lane state.** Each executable lane has a durable state machine: `PREPARED`, `RUNNING`, `WAITING_DEPENDENCY`, `TERMINAL_ACCEPT`, `TERMINAL_REJECT`, `INTEGRATING`, `COMPLETE`, or `BLOCKED`.
- **ORC-02 — Leases and heartbeats.** Remote and local workers publish bounded leases, last-material-progress time, and a meaningful state. A busy process without material progress is not healthy.
- **ORC-03 — Terminal event processing.** A finished worker immediately triggers archive, result classification, evidence preservation, and the next dependency-ready action before a status report is produced.
- **ORC-04 — Bounded recovery.** Ordinary repair and infrastructure retries follow declared limits. Recovery uses the same immutable checkpoint when only infrastructure failed and a successor checkpoint when source changed.
- **ORC-05 — No duplicate ownership.** One owner may mutate a scope. Independent scopes may run concurrently, including separate repositories and non-overlapping packet lanes.
- **ORC-06 — Dependency scheduler.** The coordinator maintains a machine-readable dependency graph, prioritizes work that unblocks other repositories, and automatically dispatches downstream work when an accepted handoff arrives.
- **ORC-07 — Capacity use.** If dependency-ready work exists and safe capacity is available, the system must dispatch it or record a concrete reason why it cannot.
- **ORC-08 — Coordinator restart recovery.** On restart or takeover, the coordinator reconstructs live workers, protected refs, leases, terminal results, and ready lanes without relying on conversational memory.

### 17.3 Audit and validation scope

- **AUD-01 — One audit per checkpoint.** Exactly one independent audit is permitted for an immutable checkpoint. A rejected checkpoint may receive one fresh audit only after a new repair checkpoint exists.
- **AUD-02 — Narrow checkpoint audit.** The audit covers cumulative changed paths against the protected base, declared ownership, affected contracts, focused tests, generated closure, and negative cases. It does not rerun the entire application by default.
- **AUD-03 — Phase Full once.** The complete required integration suite runs once for the final assembled Phase tree.
- **AUD-04 — Promotion evidence reuse.** Staging and main verify and reuse the accepted Phase Full evidence when the candidate tree, dependency lock, workflow profile, and environment contract are unchanged.
- **AUD-05 — No double auditing.** Cursor and Codex must not both audit the same checkpoint. A fallback is allowed only after the original auditor is unavailable or exceeds the bounded stall rule and is cancelled.
- **AUD-06 — Required negative proof.** Missing, skipped, cancelled, stale, changed-scope, changed-dependency, and wrong-environment evidence must be proven to reject.

### 17.4 Receipt architecture and promotion

- **RCP-01 — Content and transition identity.** A receipt separately records source commit, Git tree, dependency lock, workflow/profile version, environment class, and artifact digests.
- **RCP-02 — Protected-merge transition.** After Phase merge, the controller automatically issues an authenticated transition receipt binding the audited Phase commit/tree to the resulting protected-development commit/tree.
- **RCP-03 — Identical-tree reuse.** Different merge commits with the same accepted tree may reuse Full evidence only through the authenticated transition receipt; tree equality alone is insufficient.
- **RCP-04 — Deterministic invalidation.** Evidence becomes stale only when a bound code tree, dependency lock, workflow/profile, required environment, or declared contract changes.
- **RCP-05 — Generated promotion markers.** One schema-validating tool creates and rereads promotion markers. Agents must not hand-write run IDs, candidate heads, receipt coordinates, or JSON markers.
- **RCP-06 — No self-invalidating receipts.** A checked-in file must not be required to attest the commit that contains that file.
- **RCP-07 — External receipt store.** Integration and promotion receipts should be stored in an authenticated external or Git-common-dir evidence store and referenced by immutable digest from the candidate.
- **RCP-08 — Receipt-maintenance transition.** If a receipt/controller-only correction is necessary, one bounded transition may admit the exact predecessor identity, exact authorized maintenance paths, unchanged failure contract, and current protected base without reopening product scope.
- **RCP-09 — Loop detector.** Two consecutive receipt-only successors for the same unchanged product tree trigger a structural receipt diagnosis and stop further rebind attempts.
- **RCP-10 — Current-run truth.** Baseline-failure receipts bind exact failed job identities from the current run and reject aggregates, duplicates, omissions, additions, or substitutions.

### 17.5 Workflow and ruleset recovery

- **WFL-01 — Workflow emission contract.** Tests must prove that every protected Phase event emits the required workflow and exact context names.
- **WFL-02 — Atomic ruleset installation.** Required contexts and producing workflows are generated from one versioned contract and installed atomically.
- **WFL-03 — Drift preflight.** Before Phase admission, verify that every required context can be produced by the current workflow on the target event.
- **WFL-04 — Recovery bootstrap.** The release must provide a governed workflow-recovery operation for the case where protection requires checks that cannot emit.
- **WFL-05 — Minimal temporary protection.** Recovery may temporarily require only an actually emitted, independently audited check for an exact workflow-only repair; application or runtime code is forbidden from that repair.
- **WFL-06 — Automatic restoration.** Recovery captures the complete before-state, applies a time-bounded change, merges only the audited repair, restores the ruleset byte-for-byte, and verifies restoration.
- **WFL-07 — Disposable proof PR.** After restoration, a disposable exact-scope PR proves all required contexts emit before product work resumes.
- **WFL-08 — Prerequisite ordering.** Full must not start until its exact Fast, catalogue, or other declared prerequisites are terminal and accepted.
- **WFL-09 — Infrastructure retry.** Startup failure, missing runner, service outage, or funding block permits at most the declared clean retry after the cause is healthy; it does not create a source repair.
- **WFL-10 — Suite-level interpretation.** Controllers reconcile workflow, check-suite, and job conclusions so a queued or startup-failed suite cannot be misreported from one green job.
- **WFL-11 — Cost-aware fanout.** Obsolete runs are cancelled, repeated checkouts and duplicate suites are removed, and hosted compute availability is preflighted before expensive work.
- **WFL-12 — Exact-ref checkout.** Large repositories fetch only the candidate ref, protected base, and explicitly required history by default.

### 17.6 Managed-core ownership and consumer cleanup

- **MNG-01 — Central authority.** `core/managed-core/` in IDE Development is the only authoring source for managed IDE files. The IDE Development source repository must never install a nested consumer copy.
- **MNG-02 — Read-only consumers.** Installed managed files are read-only outside a verified installer install, upgrade, repair, or rollback transaction.
- **MNG-03 — Ownership manifest.** Every installed path has an owner, package version, source digest, installed digest, mutability policy, and removal policy.
- **MNG-04 — Drift classifier.** The installer classifies a consumer difference as exact package, valid repository-owned extension, candidate central IDE improvement, obsolete/duplicate residue, or unknown.
- **MNG-05 — Candidate export.** A useful managed-file change discovered in a consumer is exported as evidence and a requirement candidate to IDE Development before the consumer copy is removed.
- **MNG-06 — No application credit.** Consumer-local managed IDE changes never count toward application PRD completion and do not block product promotion when the released installation is otherwise valid.
- **MNG-07 — Repair transaction.** Cleanup restores exact released bytes using the official package and manifest; it does not copy tooling between consumers or hand-edit files into conformity.
- **MNG-08 — Safe obsolete removal.** Obsolete managed files are removed only when the manifest proves ownership and the operation preserves repository-owned files.
- **MNG-09 — Version integrity.** Different managed bytes must never claim the same package version. Release identity includes tag, source commit/tree, manifest digest, archive digest, and rollback identity.
- **MNG-10 — Installed capability closure.** Managed tests and workflows may reference only components present in the same installed manifest. Removing or renaming a delivery component must atomically migrate its callers and tests so a consumer cannot inherit tests for an absent tool.

### 17.7 Repository consolidation and definition of done

- **CLS-01 — One-time classification.** Every uncommitted file, local-only commit, branch, PR, and worktree is classified as required pre-deployment product work, central IDE candidate, post-deployment work, duplicate/obsolete work, or unknown.
- **CLS-02 — Preserve required work.** Unique repository-owned work required by the committed PRD must be integrated through the governed path before completion.
- **CLS-03 — Quarantine before deletion.** Unknown or potentially unique work is preserved in an immutable quarantine receipt before any destructive cleanup.
- **CLS-04 — Branch convergence.** Repository completion requires `development`, `staging`, and `main` to resolve to the accepted content tree.
- **CLS-05 — Clean local state.** The canonical local checkout matches `origin/main`, is clean, and contains no untracked application or managed-system residue.
- **CLS-06 — Resource cleanup.** No open application PR, retained issue/Phase/promotion branch, or extra worktree remains unless explicitly classified as post-deployment work with an owner.
- **CLS-07 — Installed-version verification.** The released managed package version and every managed-file digest are verified after cleanup.
- **CLS-08 — Consolidation receipt.** A final machine-readable receipt records remote refs/trees, local identity, branches, PRs, worktrees, dirty state, managed version, and quarantined or post-deployment exceptions.

- **DOD-01 — Canonical denominator.** Completion denominator comes only from canonical required work packets in the committed PRD; Issues, receipts, subtasks, optional packets, and external gates are excluded.
- **DOD-02 — Zero partial credit.** Prepared, partial, rejected, unaudited, or unintegrated packets receive zero packet credit.
- **DOD-03 — Milestone accounting.** Development, staging, and main are explicit additional milestones after canonical packet completion.
- **DOD-04 — Fixed boundary.** Pre-deployment completion includes all repository-owned engineering, required validation, audit, package, configuration templates, migrations, backup/recovery/rollback, and offline rehearsal. Actual host installation, live deployment, canary, provider qualification, and founder acceptance remain separate unless a PRD explicitly places them before deployment.
- **DOD-05 — No tranche completion.** A green suite, manifest subset, source merge, or phase completion cannot establish full-program completion.
- **DOD-06 — Machine-readable ledger.** The repository generates its packet ledger from the committed PRD and binds each completed packet to protected integration evidence.
- **DOD-07 — Stable reporting.** Percentage rules and denominator cannot change during execution without an explicit PRD amendment.
- **DOD-08 — Contradiction gate.** Aggregate completion, packet evidence, final reconciliation, execution manifest, and protected refs must agree. A detailed `HOLD` cannot be overwritten by a later unsupported aggregate claim.
- **DOD-09 — Manifest lifecycle.** Packet and execution manifests automatically advance from planned through integrated and promoted states using accepted receipts.
- **DOD-10 — Exact closeout.** DONE requires the full pre-deployment boundary, protected main promotion, and consolidation receipt; it does not claim live VPS or Mac installation.

### 17.8 Generated artifacts and runtime preflight

- **GEN-01 — Check before generation.** Freshness checks run against a clean checkout before any generator mutates the tree.
- **GEN-02 — One canonical generator.** Catalogues, managed mirrors, manifests, indexes, and synthetic secret fixtures each have one authoritative source and deterministic generator.
- **GEN-03 — Post-generation cleanliness.** CI fails if a required generator changes tracked files that were expected to be current.
- **GEN-04 — Dependency closure.** Changing a canonical input regenerates and validates every dependent digest, fixture, cache key, and receipt in the same governed checkpoint.
- **GEN-05 — No masking.** A workflow must not regenerate a stale committed artifact and then check only the regenerated output.
- **GEN-06 — Synthetic fixture isolation.** Synthetic secret fixtures are explicitly marked, scoped, deterministic, and excluded from real-secret findings without weakening actual secret scanning.

- **ENV-01 — Toolchain manifest.** Each required check declares supported OS, architecture, Python/Node/package-manager versions, system tools, services, and runner class.
- **ENV-02 — Preflight before work.** Worker startup verifies the toolchain, repository write access, linked-worktree metadata, network policy, and required non-secret configuration.
- **ENV-03 — Truthful skips.** A skipped native PostgreSQL, browser, Docker, or platform test is recorded as `NOT_RUN` or `ENVIRONMENT_BLOCKED`, never PASS.
- **ENV-04 — Source versus infrastructure.** Missing tools, unavailable runners, quota, and external outages are classified separately from source defects.
- **ENV-05 — Disposable proof.** Migration, backup, restore, rollback, installer, and package rehearsals run in disposable environments that cannot mutate the host or production.
- **ENV-06 — Resource safety.** Memory-heavy builds and browser/database suites obey host capacity limits; unrelated processes are never killed to manufacture capacity.

### 17.9 Cross-repository handoffs

- **DEP-01 — Typed receipt.** Every provider-to-consumer handoff uses a versioned schema with producer repository/commit/tree, consumer repository/commit/tree, artifact and contract digests, verdict, and lifecycle state.
- **DEP-02 — Protected acceptance.** Downstream admission requires an independently accepted, protected-integrated receipt; preparatory or local evidence cannot unblock it.
- **DEP-03 — Latest protected identity.** Consumers reject stale/frozen provider pins and identify the exact current protected handoff required.
- **DEP-04 — Event-driven unblock.** Acceptance publishes an event that automatically wakes every dependent lane and dispatches the next safe work.
- **DEP-05 — Parallel preparation.** Downstream work that does not consume the missing artifact may proceed in parallel, but final admission remains fail closed.
- **DEP-06 — Dependency visibility.** Portfolio status names the blocking repository, exact missing handoff class, active owner, and next automatic action.

### 17.10 Reporting, scheduled automation, and handover

- **OBS-01 — Runtime authority.** A worker is RUNNING only when the authoritative provider readback says so. Prepared, install-failed, terminal, local mock, and archived records are excluded.
- **OBS-02 — Protected truth first.** Status refreshes remote protected refs/trees, accepted receipts, open PRs, worktrees, and live workers before calculating progress.
- **OBS-03 — Deterministic language.** Reports use `ISSUED`, `RUNNING`, `FINISHED`, or `NOT ISSUED`; they do not use ambiguous future-progress wording.
- **OBS-04 — Required fields.** Each program reports percentage to its fixed done boundary, completed canonical packets, active partial packets, exact current work, next work, blockers/dependency, actual worker provider, and whether maximum safe parallelism is in use.
- **OBS-05 — Action before report.** An Update cycle processes terminal results, archives workers, restarts stopped safe work, and dispatches dependency-ready lanes before reporting.
- **OBS-06 — No evidence-ID noise.** Founder-facing reports omit low-level IDs unless needed to resolve a discrepancy; durable machine evidence retains them.
- **OBS-07 — No stale coordinator claims.** A retired coordinator cannot issue work or report current portfolio status.

- **AUT-01 — Target identity.** A scheduled automation binds the immutable coordinator task ID, not only a display title.
- **AUT-02 — Delivery receipt.** Every scheduled invocation records scheduled time, actual delivery time, target task, result, retry count, and remaining runs.
- **AUT-03 — Bounded retry.** Missed delivery retries within a declared window and reports a permanent failure rather than silently disappearing.
- **AUT-04 — Finite-run correctness.** Hourly-for-N-runs automation decrements only after confirmed delivery.
- **AUT-05 — Handover retargeting.** Coordinator handover atomically retargets or disables related automations.
- **AUT-06 — Update protocol version.** The automation includes the current report scope and protocol version so an old scheduled message cannot revive obsolete reporting rules.

- **HND-01 — Single live owner.** A handover designates one live coordinator and marks the predecessor historical/read-only.
- **HND-02 — Durable handoff schema.** Handoff includes program/task IDs, protected refs, canonical packet ledgers, active workers, blockers, dependency graph, authorizations, routing registry version, and outstanding automation.
- **HND-03 — Live re-verification.** The successor treats handoff data as provisional until protected refs and worker APIs are refreshed.
- **HND-04 — Terminal-event transfer.** Results arriving in the retired task are forwarded once to the successor and cannot restart retired coordination.
- **HND-05 — Compaction safety.** Coordinator state must be reconstructable from repository and provider evidence after conversational compaction.

### 17.11 Security and evidence integrity

- **SEC-01 — No credential discovery.** Agents must not search for, extract, print, or persist credentials. They use injected authority and sanitized availability diagnostics.
- **SEC-02 — Evidence schema.** Worker evidence includes repository URL, starting ref, commit/tree, resulting checkpoint, provider/model/effort/fast mode, authoritative run identity/status, scope, tests, verdict, and receipt digest.
- **SEC-03 — Trusted provenance.** Handwritten IDs, SDK mocks, local session IDs, and unverified status text cannot satisfy cloud or audit evidence.
- **SEC-04 — Mutation declaration.** Every tool declares read-only or mutating behaviour before execution; unexpected broad mutation stops and preserves the last known-good identity.
- **SEC-05 — Scope enforcement.** Before integration, the controller compares cumulative paths and size against packet ownership and inherited failure contracts.

## 18. v2.5.2 acceptance matrix

A future 2.5.2 candidate cannot be called ready for publication until all applicable rows pass on the exact release candidate.

| Area | Required acceptance proof |
|---|---|
| Cursor routing | Read-only dispatch canary for every configured repository proves exact repository and starting commit/tree; deliberate wrong binding is rejected and archived. |
| Orchestration | Restart and takeover simulation reconstructs lanes; terminal workers are archived; every safe ready lane is dispatched; stalled-worker replacement obeys its bound. |
| Audit scope | A packet receives one narrow independent audit; the final Phase receives one Full; unchanged staging/main promotions reuse it. |
| Receipt transitions | Phase-to-development merge with a changed commit and identical tree produces a valid transition receipt; changed-tree, changed-lock, changed-profile, and stale receipts reject. |
| Receipt loop prevention | A receipt/controller-only maintenance transition succeeds once; a second unchanged-product rebind is stopped by the loop detector. |
| Workflow recovery | A fixture repository with an impossible required context is repaired through the captured, time-bounded bootstrap; original protection is restored and a disposable PR emits every context. |
| GitHub infrastructure | Startup failure, queued runner, budget exhaustion, and prerequisite race are classified correctly and recover within the retry bound without source mutation. |
| Managed-core integrity | Consumer edits to a managed file are detected; useful intent exports centrally; exact released bytes restore transactionally; repository-owned files remain untouched; installed tests reference only manifest-present components. |
| Consolidation | A fixture with dirty files, extra worktree, stale branch, open PR, IDE drift, and unique application work is classified, preserved or integrated correctly, and ends with a truthful consolidation receipt. |
| Completion accounting | Generated ledger uses only canonical required packets plus milestones, gives zero partial credit, and fails on contradictory detailed HOLD evidence. |
| Generated outputs | Stale catalogue and stale secret fixture both fail before mutation; authoritative regeneration restores a clean tree and exact dependent digests. |
| Runtime preflight | Missing PostgreSQL, Docker, browser, Python, Node, or architecture support is reported as environment-blocked, not PASS or source failure. |
| Dependency handoff | Accepted provider receipt automatically wakes the dependent consumer lane; stale receipt and wrong provider identity reject. |
| Scheduled Update | A finite hourly automation delivers exactly N confirmed invocations, survives one transient failure, and retargets correctly after coordinator handover. |
| Security | No secret is exposed; fabricated run identity is rejected; unexpected scope and broad mutation abort before integration. |
| Rollback | Installer, workflow/ruleset recovery, promotion, and managed-core cleanup each restore their exact recorded predecessor state. |

### 18.1 Release evidence package

The release evidence package must contain:

- the frozen included requirement IDs and explicit excluded/deferred IDs;
- exact source commit/tree, version, manifest, archive, dependency, workflow/profile, and rollback digests;
- focused checkpoint receipts and exactly one independent audit per checkpoint;
- one final Phase Full receipt and authenticated Phase-to-protected transition receipt;
- Cursor routing-canary results for every configured repository;
- workflow/ruleset before/after recovery proof;
- managed-core install, drift detection, candidate export, repair, upgrade, and rollback proof;
- orchestration restart, stall, dependency-unblock, automation, and handover simulations;
- disposable consumer proof on macOS for both Codex and Cursor;
- generated-artifact freshness and clean-tree proof;
- consolidation proof showing that release-owned temporary branches, PRs, workers, and worktrees are closed; and
- a plain-English list of every remaining external or post-deployment gate.

### 18.2 Non-goals preserved

These requirements do not:

- authorize a 2.5.2 implementation, publication, rollout, or consumer mutation;
- make consumer-local IDE drift part of application engineering;
- weaken branch protection, independent audit, fail-closed provider admission, or founder-reserved approval;
- require full-application validation for each packet;
- treat provider qualification, consumer live proof, VPS/Mac installation, production canary, or founder acceptance as pre-deployment source work unless the owning PRD explicitly says so; or
- permit the IDE Development source repository to install or maintain a nested consumer copy of itself.
