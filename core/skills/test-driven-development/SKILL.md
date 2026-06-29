---
name: test-driven-development
description: Use tests as proof for new behavior, bug fixes, and behavior-changing refactors.
version: 1.0.0
status: active
tags: [testing, tdd, proof, bugs]
source_adapted_from:
  - addyosmani/agent-skills/skills/test-driven-development
  - link-antigravity-kit/.codex/skills/tdd-workflow
---

# Test-Driven Development

Use this skill when changing behavior or fixing bugs.

## Use When

- implementing new logic
- fixing a bug
- changing existing behavior
- adding edge-case handling
- proving a regression is fixed

Do not force TDD for pure documentation, static content, or configuration-only changes with no behavior impact.

## Core Loop

1. Write or identify a test that should fail before the fix.
2. Run it and confirm the failure is meaningful.
3. Implement the smallest change that makes the test pass.
4. Run the focused test again.
5. Run broader relevant tests for regression confidence.
6. Record test commands and outcomes in proof.

## Bug Fix Pattern

For bug fixes:

1. Reproduce the bug.
2. Add a test or documented reproduction check.
3. Confirm the test/check fails before the fix.
4. Fix the root cause.
5. Confirm the test/check passes.
6. Check nearby behavior for regressions.

## Rules

- A test that never failed is weak proof for a bug fix.
- If a test cannot be added, explain why and provide another concrete verification method.
- Do not rewrite unrelated tests to make failures disappear.
- Do not declare done until test evidence is captured in proof.

## Output

- failing test or reproduction evidence
- implementation change
- passing test output
- regression check
- proof-ready summary

## Progressive Disclosure

Read the active issue, relevant source files, and nearby tests. Do not inspect unrelated test suites unless failures or dependencies require it.
