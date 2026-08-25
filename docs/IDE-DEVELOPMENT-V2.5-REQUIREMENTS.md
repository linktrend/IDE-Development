# IDE Development v2.5.1 completed baseline and v2.5.2 requirements queue

**Status:** v2.5.1 COMPLETED; provisional v2.5.2 requirements collection STARTED but not frozen, released, or authorized for rollout
**Baseline issue:** #339
**Successor requirements issue:** #427
**Baseline date:** 2026-08-19 (Asia/Taipei)
**Successor queue opened:** 2026-08-25 (Asia/Taipei)
**Supersedes for v2.5 planning:** any interpretation that offline contract validation alone constitutes a deployed provider connection

**Successor status (2026-08-25):** v2.5.1 is completed and is the current released package. The v2.5 baseline below is retained as the requirements record that drove that release family. Section 15 starts the provisional v2.5.2 requirements queue; it does not define, publish, or authorize rollout of version 2.5.2.

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
| Consumer managed-file immutability | Treat installed IDE-managed files as read-only consumer artifacts. Improvements must be authored centrally and delivered only by an official versioned installer transaction. | Required for the future release contract. |
| Product/tooling lifecycle separation | An unreleased central IDE maintenance candidate must not block a product repository's integration or promotion when that repository's installed released IDE version is valid and its own required protected checks pass. | Required governance rule. |

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
