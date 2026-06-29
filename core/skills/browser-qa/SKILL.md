---
name: browser-qa
description: Use browser-driven QA to verify web flows, capture evidence, and report user-visible defects.
version: 1.0.0
status: active
tags: [browser, qa, screenshots, web, verification]
source_adapted_from:
  - LiNKtrend-System/LiNKdev/skills/gstack/qa
  - LiNKtrend-System/LiNKdev/skills/gstack/qa-only
  - LiNKtrend-System/LiNKdev/skills/gstack/browse
---

# Browser QA

Use this skill when web behavior needs real browser verification or screenshot evidence.

## Use When

- validating a web route or user flow
- checking a feature before review
- confirming a bug is fixed in the UI
- capturing evidence for proof
- testing responsive or interaction behavior

## QA Modes

- **Quick**: critical path and obvious regressions.
- **Standard**: critical path plus common edge/error states.
- **Focused**: one specific issue, route, or user flow.

Avoid exhaustive testing unless the issue or release gate requires it.

## Workflow

1. Identify target URL, viewport, and expected behavior.
2. Start or locate the app server if needed.
3. Navigate the flow in a browser.
4. Capture observations, screenshots, console errors, and failures.
5. Retest after fixes.
6. Record proof-ready evidence.

## Rules

- Do not use browser QA as a substitute for automated tests when tests are required.
- Do not claim visual correctness without inspecting the rendered UI.
- Do not broaden into unrelated flows unless a regression is visible.
- If browser tooling is unavailable, report that limitation and use the closest available verification.

## Output

- route or URL tested
- mode used
- screenshots or observations
- failures and reproduction steps
- pass/fail/blocker result

## Progressive Disclosure

Read the issue, acceptance criteria, and run instructions. Inspect only the UI files and routes relevant to the tested flow.
