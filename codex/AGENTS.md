# Codex Consumption Guide

## Purpose

Use the shared IDE Development core as a portable knowledge asset. Codex on the orchestrator VM is a **worker**.

**Do not assume `.cursor` is automatically read.** Prefer the paths below.

## Canonical Storage

- canonical knowledge asset: `../core/` (from this folder: `core/` at repo root)
- compatibility runtime surface: `.cursor/`
- current status: `docs/CURRENT-STATUS.md`
- operations: `docs/IDE-DEVELOPMENT-OPERATIONS-MANUAL.md`

## Recommended Read Path

1. Read `../.cursor/README.md` (or `core/` equivalents when `.cursor` is unavailable)
2. Read `../.cursor/bootstrap/START-HERE.md`
3. If the work is greenfield or materially ambiguous, read `../.cursor/discovery/INDEX.yaml`
4. Read `../.cursor/commands/INDEX.yaml`
5. Follow the one command wrapper that matches the task
6. For how v3 runs: `docs/IDE-DEVELOPMENT-OPERATIONS-MANUAL.md`

## Worker rules (Codex)

- You are a worker. Everyday route is Luna High. Hard route is Sol Medium. Use Codex only while more than 25% of the allowance remains in every reported window.
- Work only on the branch you were given. Branch names are `issue/<PREFIX>-<n>-<slug>`.
- Commit small, clear steps and push often.
- Do not open pull requests. The orchestrator packages branches into pull requests.
- Do not merge, and do not promote `development` to `main`.
- Before you finish, run the fast checks named in the Issue.
- End your final reply with a short lessons note.
- When the work is finished, push and stop. The orchestrator moves the Issue to `in_review` in the Ledger.

## Consumption Rules

- Treat `core/` as canonical storage for portable knowledge.
- Treat `.cursor/` as the operational compatibility surface for existing paths and references.
- Do not rewrite doctrine, command names, or internal references as part of ordinary use.
- Prefer progressive disclosure over scanning the entire repository.

## Scope

This file does not replace doctrine. It explains how a Codex worker enters the packaged system and what it is allowed to do with git.
