# Packet WP-U05 — Atomic workflow and ruleset migration

## Identity (fill at execution only)

| Field | Value |
|---|---|
| Packet ID | WP-U05 |
| Spec update | Update 5 |
| PRD acceptance | AC-U05-01–AC-U05-16 (AC-U05-17 deferred to WP-CONSUMERS) |
| Depends on (matrix) | WP-U01, WP-U02, WP-U03, WP-U04, WP-U06, WP-U07 |
| Repository | linktrend/IDE-Development |
| Issue | 325 |
| Branch | issue/325-implement-ide-development-v2-4-0-wp-u05 |
| Parallel lane | serial |
| Docs authority | 3a5d15231d65b8549d64971960b2aeb617b58838 / tree 6b9f73f1e78ae4abda3b78b939adc190b6d0842a |
| Start commit | ccaeae212e448e1c49369cf1fabfc28341476b62 |
| Start tree | 6d296378923a1e5b8ecd7b0ca6b5064ed644b3c4 |
| Prior reviewed tip | ccaeae212e448e1c49369cf1fabfc28341476b62 (independently accepted U02) |
| Content head/tree | 75d4cb07dd330b5aef89fa96421a7bdf91e95941 / 6ec7ba3174f774393d5ebd1c18b5f952185bbd05 |
| Evidence head/tree | (filled after evidence commit; tip SHA not self-embedded) |
| Final tip binding | branch HEAD after bind-metadata commit; tip SHA not self-embedded |
| Phase base at handoff | not used |

## Topology notes

Identity model: content-head / evidence-head / final-bind-tip.

Migrates obsolete managed check `Enforce allowed PR source branches` to active workflow job display `Linktrend Branch Source Policy` across protection tooling, evaluators, variables, fixtures, and contracts. Adds atomic three-branch apply/rollback, capability preflight, managed label reconciliation, evaluator contract migration, and trusted-verifier separation from sealed product candidates.

## Rollback

Leave the issue branch unmerged. Restore archived before-state for ruleset/label work. Do not invent empty commits/PRs. Do not weaken native protection or copy verifier repairs onto sealed candidates. No Full/PR/promotion/publication/consumer rollout in this packet. AC-U05-17 live consumer verification deferred to WP-CONSUMERS.
