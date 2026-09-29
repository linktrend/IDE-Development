# Program Run Rollout Boundary Implementation Plan

> **For Codex:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Remove portfolio-specific rollout data from the reusable IDE Development package and publish the focused correction as v2.5.1.

**Architecture:** Keep the existing generic rollout engine unchanged. Program Run configuration remains the sole authority for one-or-many targets, canaries, cohorts, and concurrency. Remove only stale package content that violates that boundary, regenerate package identity, and verify the installed artifact.

**Tech Stack:** Python 3 standard-library tests, JSON/YAML package metadata, shell acceptance checks, GitHub-protected Git delivery.

---

### Task 1: Add the package-boundary regression test

**Files:**
- Modify: `scripts/ide_development_tests/test_build_manifest.py`

1. Replace the cleanup-plan packaging assertion with assertions that the managed package contains no known portfolio repository names and does not package `external-cleanup-plan.json`.
2. Run the focused unit test and confirm it fails for the current package content.

### Task 2: Remove execution-specific content

**Files:**
- Modify: `docs/contracts/MANAGED-CORE-V2.md`
- Modify: `core/managed-core/content/doctrine/MANAGED-CORE-V2.md`
- Modify: `scripts/ide_development/build_manifest.py`
- Delete: `core/managed-core/migrations/external-cleanup-plan.json`

1. Replace the fixed consumer role/order with generic Program Run language covering one or many configured targets.
2. Remove the cleanup-plan identity entry and file.
3. Run the focused unit and rollout tests and confirm they pass.

### Task 3: Version and regenerate

**Files:**
- Modify: `VERSION`
- Modify: `core/managed-core/VERSION`
- Regenerate: `core/managed-core/MANIFEST.json`
- Regenerate package indexes or generated closure records when the official generator requires them.

1. Set package identity to v2.5.1.
2. Run the official manifest generator and verifier.
3. Run `git diff --check` and focused package, rollout, and portable acceptance checks.
4. Install into a disposable repository and verify the extracted package contains no portfolio-specific names.

### Task 3A: Close the installed execution-contract gap

**Files:**
- Modify: `core/execution/protocol.py`
- Modify: `core/execution/CODING-EXECUTION-PROTOCOL.md`
- Modify: `core/managed-core/content/doctrine/CODING-EXECUTION-PROTOCOL.md`
- Modify: `scripts/ide_development/build_manifest.py`
- Modify: `scripts/ide_development_tests/test_build_manifest.py`
- Modify: `tests/execution_protocol/test_protocol.py`

1. Package the canonical protocol, control contract, and execution-manifest schema.
2. Resolve discovery from either the system-source layout or `.ide-development/`
   consumer layout without requiring consumer-owned `core/` directories.
3. Audit all required discovery surfaces and run a real v2.5.0-to-v2.5.1 upgrade
   canary that loads the installed schema.

### Task 4: Deliver and roll out

1. Commit and push issue 364 with exact evidence.
2. Integrate through the Phase/delivery controller and promote the accepted tree through `development`, `staging`, and `main` under the user's explicit approval.
3. Use this execution's Program Run target inventory to update the consumer repositories without adding it to reusable package content.
4. Verify `.ide-development/`, native Codex/Cursor discovery files, version, and package identity in every configured consumer; record exact before/after refs and rollback points.
