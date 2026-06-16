# Compatibility Matrix

## Purpose

This document defines what is canonical, compatibility-only, optional, or legacy across the assembled system.

## Canonical

Canonical assets are the primary source of truth for new work.

Canonical categories include:

- execution doctrine files
- canonical execution templates
- active control and delivery agent roles
- active execution commands
- runtime specifications
- canonical workflow specifications
- contract specifications
- state specifications
- system assembly specifications

## Pre-Execution

Pre-execution assets are canonical for formation work before executable program work begins.

Examples:

- `INTENT.md`

## Optional

Optional assets remain valid but are not required in every execution path.

Examples:

- `COUNCIL-SUMMARY.md`
- phase review where not explicitly required

## Compatibility-Only

Compatibility assets are retained because older repositories, runtimes, or human expectations may still reference them.

Examples:

- `AGENT-REPORT.md`
- `MODULE-README.md`
- `INTENT-VERDICT.json`
- legacy flat agent roles still retained for continuity

## Legacy

Legacy assets remain present for continuity but are not preferred for new work.

Examples:

- `linkdev-*` command family
- retained older workflow notes such as `dispatch-v2.md` and `planning-lifecycle.md`

## Deprecated

Deprecated assets remain only for backward compatibility and should not be selected for new work unless compatibility explicitly requires them.

Examples:

- deprecated compatibility alias commands already classified as such in the command layer

## Compatibility Guarantee

The assembled system guarantees that:

- canonical assets remain the source of truth
- compatibility assets may coexist without redefining canonical behavior
- legacy assets do not override canonical execution semantics

## Read Next

1. `EXTENSION-MODEL.md`
2. `V1-BUILD-ORDER.md`
