---
name: release-readiness
description: Assess whether integrated work is ready to ship or requires more validation, rollback planning, or approval.
version: 1.0.0
status: active
tags: [release, ship, readiness, validation]
source_adapted_from:
  - LiNKtrend-System/LiNKdev/skills/gstack/ship
  - LiNKtrend-System/LiNKdev/skills/gstack/land-and-deploy
  - addyosmani/agent-skills/skills/shipping-and-launch
---

# Release Readiness

Use this skill when deciding whether a module, program, PR, or deployment candidate is shippable.

## Readiness Checklist

- required issues are `done`
- proof, review, and integration artifacts exist
- tests and validation are current
- release risks are known
- rollback or recovery path is understood
- user-facing or operator-facing changes are documented when needed
- required human approvals are recorded

## Rules

- Integrated does not automatically mean releasable.
- Do not ship with unresolved blocking review findings.
- Do not hide skipped tests or environmental gaps.
- Prefer explicit residual risk over vague confidence.
- Escalate irreversible, security-sensitive, or high-impact releases.

## Output

- release verdict: ready, not ready, or blocked
- evidence reviewed
- remaining risks
- required follow-up
- rollback or recovery note

## Progressive Disclosure

Read module/program definition of done, integration records, reviews, proof, and release notes. Do not inspect unrelated work unless the release scope includes it.
