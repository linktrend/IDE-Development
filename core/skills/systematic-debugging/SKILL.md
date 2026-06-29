---
name: systematic-debugging
description: Debug failures through reproduction, isolation, root cause analysis, fix, and verification.
version: 1.0.0
status: active
tags: [debugging, root-cause, verification, bugs]
source_adapted_from:
  - link-antigravity-kit/.codex/skills/systematic-debugging
  - addyosmani/agent-skills/skills/debugging-and-error-recovery
---

# Systematic Debugging

Use this skill when behavior is broken, tests fail, builds fail, or an observed result does not match expected behavior.

## Use When

- a bug report needs investigation
- a test or build failure appears
- logs show an unexplained error
- behavior differs across environments
- a previous fix did not hold

## Workflow

### Phase 1: Reproduce

Establish the failure before changing code.

- record exact steps
- capture expected versus actual behavior
- identify frequency: always, often, sometimes, rare
- preserve logs, screenshots, or test output when available

### Phase 2: Isolate

Narrow the problem.

- check recent changes
- identify affected boundaries
- reduce to the smallest failing case
- separate symptom from cause
- avoid broad rewrites while isolating

### Phase 3: Understand

Find the root cause.

- explain why the failure happens
- name the code path, data path, config, or dependency involved
- identify whether similar code may share the problem
- record assumptions separately from verified facts

### Phase 4: Fix

Make the smallest correction that addresses the root cause.

- avoid speculative cleanup
- preserve unrelated behavior
- add or update regression protection where practical

### Phase 5: Verify

Prove the fix.

- rerun the reproducer
- run focused tests
- run relevant regression checks
- record results in proof

## Anti-Patterns

- changing code before reproducing the bug
- treating a symptom as the root cause
- making many unrelated changes at once
- deleting failing tests instead of fixing behavior
- declaring completion without verification evidence

## Output

- reproduction evidence
- isolated cause
- fix summary
- verification commands and results
- residual risk or blockers

## Progressive Disclosure

Read the active issue, failing output, relevant source files, and nearby tests. Do not scan unrelated systems unless isolation points there.
