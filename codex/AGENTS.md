# Codex Consumption Guide

## Purpose

Use the shared development core as a portable knowledge asset while preserving compatibility with the existing `.cursor` runtime surface.

**Do not assume `.cursor` is automatically read.** Prefer the paths below for GitOps work.

## Canonical Storage

- canonical knowledge asset: `../core/` (from this folder: `core/` at repo root)
- compatibility runtime surface: `.cursor/`
- GitOps doctrine: `docs/AUTONOMOUS-GIT-OPERATIONS.md`
- Completion: `docs/contracts/AGENT-COMPLETION.md`
- Repair: `docs/contracts/REPAIR-DISPATCHER.md`

## Recommended Read Path

1. Read `../.cursor/README.md` (or `core/` equivalents when `.cursor` is unavailable)
2. Read `../.cursor/bootstrap/START-HERE.md`
3. If the work is greenfield or materially ambiguous, read `../.cursor/discovery/INDEX.yaml`
4. Read `../.cursor/commands/INDEX.yaml`
5. Follow the one command wrapper that matches the task
6. For GitOps: `docs/AUTONOMOUS-GIT-OPERATIONS.md` + `docs/contracts/AGENT-COMPLETION.md`

## GitOps rules (Codex)

- Bootstrap: `scripts/gitops/create_issue_branch.py` + `/agentsetup` — do **not** ask the Principal for issue id/slug; do **not** invent local IDs.
- Ship / session save = **checkpoint only** (commit + push). Implementers do **not** open PRs.
- Finished work = run appropriate tests/checks; auto-repair ordinary failures with at most 3 bounded repair cycles; write machine-readable evidence with `scripts/gitops/completion_gate.py write-evidence`; then call `scripts/gitops/completion_gate.py review-ready`. The gate is authoritative, fail-closed, and publishes **Linktrend Review Ready**. Do not call `scripts/mark-review-ready.sh` as a pre-gate publisher; it is only a compatibility wrapper that requires evidence and delegates to the gate. The Phase Packager/Coordinator (`scripts/gitops/packager_coordinator.py`) opens the Phase PR; retained `packager_discover.py` is not that component.
- If validation or repair cannot complete, call `scripts/gitops/completion_gate.py blocked` so `.linktrend/completion-blocker.json` records the durable blocker and the branch stays ineligible.
- Repair: durable GitHub tasks; Lisa ACP Repair Dispatcher; max 3; no prefer-incoming; GitHub never spawns Cursor.
- Hard stops: no self-merge, no self-review, no staging/main promotion.

## Consumption Rules

- Treat `core/` as canonical storage for portable knowledge.
- Treat `.cursor/` as the operational compatibility surface for existing paths and references.
- Do not rewrite doctrine, command names, or internal references as part of ordinary use.
- Prefer progressive disclosure over scanning the entire repository.

## Scope

This file does not replace doctrine. It explains how Codex should enter and consume the packaged system, including GitOps completion rules when `.cursor` is not loaded.
