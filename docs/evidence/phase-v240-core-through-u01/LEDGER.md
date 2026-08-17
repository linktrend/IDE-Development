# Phase v240 core-through-u01 serial integration ledger

- Phase branch: `phase/v240-core-through-u01`
- Immutable base: `741e58922e7413c1097f4a58ea25e94a934af903`
- Integration content head: `6d19995509b40a51edb21b6aa329f9158e5f0ade` tree `ecc7b856ae504e879a5c875fa2fa076d789125cd` (= WP-U01 tip tree)
- Holds: none

## Order and novel commits

### WP-U04
- Accepted tip: `e2aab836ddf7efb67c6299f82a1b239f1470f383` tree `accf5727d0c9901cac8ae60e8360f0058201e8ea`
- Novel commits (1):
  - `e2aab836ddf7` patch `7e88661ca540` — fix(gitops): place trusted Review Ready flag on publish and forward AUTOMATION_TOKEN

### WP-U03
- Accepted tip: `3147d10a96805c1169f737fd350fc6f9a58d5f6f` tree `21463af488c3ff6aa256b16adaf97eab9d412eba`
- Novel commits (2):
  - `7563504cb0b1` patch `f2f91ba0abdc` — feat(gitops): add agent-agnostic Phase Packager and Coordinator
  - `3147d10a9680` patch `3ea1a4ab0a0f` — fix(gitops): fail-closed live Phase Packager assemble

### WP-U08
- Accepted tip: `03100dcaecfc9132672fe0592fa37bd126caaf3a` tree `19696d9e86638d65c815ba2e3db17f9aa69825ec`
- Novel commits (2):
  - `927d0fd98ce2` patch `a5836c73a1f2` — feat(gitops): add safe stale delivery-artifact reconciliation
  - `03100dcaecfc` patch `2073eba3133f` — fix(gitops): stop inventory JSON from authorizing deletion

### WP-U09
- Accepted tip: `36231634601e5580c83d4339acaeef651769ea93` tree `259bc414e753e3d8f9a5b193f8e5bee7c9fa1a75`
- Novel commits (5):
  - `e6295a79e108` patch `f236b40a95c5` — feat(gitops): add progress-based independent-review convergence
  - `24bae9ddf524` patch `eee0738abc2a` — fix(gitops): close independent-review identity and stop-state holes
  - `6108a8fd1c19` patch `7d76cc80e4b8` — fix(gitops): keep HOLD and repair paths fail-closed
  - `e8f503090d24` patch `9a6c17b51c7e` — fix(gitops): require consumed repair batch before empty-ingest correction
  - `36231634601e` patch `ea3d0103caca` — fix(manifest): refresh independent-review sourceHashes for live verify

### WP-U10
- Accepted tip: `f738a94f3db6888968692d617b0b2bcd85024684` tree `1c73c8747ab73ff0c9cc5671740aa1c7c9ec061f`
- Novel commits (5):
  - `cd97055888d6` patch `bf4960ac5d21` — feat(gitops): add fixture-aware secret scanning
  - `ca1d42648460` patch `ae6d04743482` — fix(gitops): close U10 secret-scan review findings
  - `0142b2f0e19c` patch `61e7d7fcf7e4` — fix(gitops): reconcile factory secret-scan findings for WP-U10
  - `0fde823ed770` patch `c66712e5c64a` — fix(gitops): reject duplicate secret-scan fixture ids
  - `f738a94f3db6` patch `71d990ff28e8` — fix(gitops): rebind secret-scan fixture candidateTree

### WP-U07
- Accepted tip: `a926794d7e549a97579f2e1816aca7a893993ccd` tree `53af75c63ad2dc48403ba0c2f3be5adb71d79bd2`
- Novel commits (11):
  - `7c2277d23d03` patch `2a072e32937c` — feat(gitops): add repository-owned CI trigger contract core
  - `72ce7464bc32` patch `39d5753aaca8` — feat(installer): package U07 CI contract and audit triggers on plan
  - `dcb7cfe379e7` patch `c704de3baa95` — docs(evidence): record WP-U07 focused validation checkpoint
  - `c23ada6a248e` patch `005035a57997` — docs(evidence): bind WP-U07 acceptance to checkpoint tip
  - `a831e7f2c5ca` patch `0a93ad8b5b8b` — docs(evidence): distinguish WP-U07 implementation and evidence tips
  - `678a618e1ac5` patch `ccc8cf4ea82e` — fix(gitops): close WP-U07 P1/P2 review findings
  - `12f9c630b7fd` patch `d505035e2571` — docs(evidence): bind WP-U07 acceptance to exact repaired head
  - `b35e816a455d` patch `7be1abdb82d1` — fix(schemas): reconcile ci-evidence with producer fields
  - `5b5306106f33` patch `ef518bd8bde9` — docs(evidence): bind WP-U07 ci-evidence schema repair head
  - `e74bfb032b36` patch `fc7585e4b4b8` — docs(evidence): regenerate WP-U07 focused-test transcript
  - `a926794d7e54` patch `5406bfb56b27` — docs(evidence): bind WP-U07 acceptance to truthful transcript tip

### WP-U01
- Accepted tip: `b9f1ac4b73030e4ea8417fd34fa4987a5f890136` tree `ecc7b856ae504e879a5c875fa2fa076d789125cd`
- Novel commits (28):
  - `2c1448647d96` patch `74c829df870f` — docs(evidence): record WP-U01 predecessor ledger on U07 tip
  - `185e58bb4123` patch `2afb58540fe5` — feat(gitops): add Linktrend Review Gate for WP-U01
  - `d4ed665ab582` patch `214026791d28` — docs(evidence): record WP-U01 focused validation checkpoint
  - `fb0934d02350` patch `f1be2f0ccbfc` — docs(evidence): bind WP-U01 acceptance to checkpoint tip
  - `ff83fe7e0149` patch `ddb67e569615` — docs(evidence): bind WP-U01 tip head and transcript evidence SHAs
  - `4aabf52bd36c` patch `14af3d1c47fe` — docs(evidence): bind WP-U01 acceptance to truthful tip
  - `e86d27beea9c` patch `60b2d936e524` — docs(evidence): bind WP-U01 acceptance head to verified tip
  - `d020b73431af` patch `0dfbb705e9f7` — docs(evidence): clarify WP-U01 packet head/tree bind notes
  - `c11d2586ddd3` patch `e13b95f69a68` — fix(gitops): close WP-U01 review findings for Review Gate
  - `6be0d8ce4e3e` patch `58a79f2897e8` — docs(evidence): record WP-U01 repair validation on content head
  - `a15fa0b5334f` patch `3da1db687d16` — docs(evidence): bind WP-U01 acceptance to content head
  - `b92b10ce29d7` patch `2cc14231046d` — docs(evidence): finalize WP-U01 bind-tip packet range
  - `7eb1c8f55d02` patch `3291ce456134` — fix(gitops): keep provider observation split and bootstrap doctrine
  - `c84abbbe98f5` patch `222dfbe1e455` — docs(evidence): record WP-U01 follow-up validation on content head
  - `300de65f4b73` patch `572906cf05f1` — docs(evidence): bind WP-U01 acceptance to follow-up content head
  - `866965f89b87` patch `c400ebc235f8` — docs(evidence): finalize WP-U01 follow-up bind-tip packet range
  - `a67f2f8f286d` patch `76719270fc96` — docs(evidence): stamp WP-U01 bind tip identity
  - `ee8097ca54a0` patch `5874c91c6160` — docs(evidence): finalize WP-U01 follow-up packet tip bindings
  - `7fee5d9cf423` patch `130ccc5be5ad` — fix(gitops): close U01-R2..R4 review-gate findings
  - `38069d21af6d` patch `a7c64ff1f4da` — docs(evidence): record U01-R1..R4 validation on content head
  - `cc0854788eec` patch `ba6e60581ba6` — docs(evidence): bind U01 content/evidence heads without self-SHA
  - `6ec04c16b675` patch `2dae436bc67c` — fix(gitops): fail-closed paginated slurp for review-gate markers
  - `74fc5ab5503e` patch `4b834e891cb0` — docs(evidence): record pagination fail-closed validation on content head
  - `b0b7051f1b45` patch `23195d6dfb66` — docs(evidence): bind pagination repair content/evidence heads
  - `e07ee73e3e9e` patch `ddb1bcc3a6b8` — fix(gitops): pipe review-gate slurps via stdin, not argv
  - `e4a2ceff2dfc` patch `489436134451` — style(tests): hoist os import for review-gate ARG_MAX test
  - `13d1cb740c58` patch `0c491a56f1e1` — docs(evidence): record stdin-slurp validation on content head
  - `b9f1ac4b7303` patch `3ad6349d5bd5` — docs(evidence): bind stdin-slurp content/evidence heads

## Conflicts reconciled
- WP-U03 `7563504cb0b1`: ['core/managed-core/MANIFEST.json'] → conflict
- WP-U09 `e6295a79e108`: ['core/managed-core/MANIFEST.json'] → regenerated-manifest-via-build_manifest
- WP-U10 `0142b2f0e19c`: ['scripts/tests/test-completion-gate-app-route.sh'] → HOLD-conflict
- WP-U10 `0142b2f0e19c`: ['scripts/tests/test-completion-gate-app-route.sh'] → keep-U04-phase-prefix-and-trusted-publisher-contract; apply-U10-secret-scan-string-split-on-error-literals

## Validation

Combined focused tests + manifest verify + `git diff --check` passed. No Full.
