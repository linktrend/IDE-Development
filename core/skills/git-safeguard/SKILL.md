---
name: git-safeguard
description: "Applies a mandatory safety checklist before git push operations to prevent accidental or unsafe repository publication."
usage_trigger: "Use when preparing any git push or remote branch publication."
version: 1.1.0
release_tag: v1.1.0
created: 2026-02-24
author: LiNKskills Library
tags: [git, safety, release]
engine:
  min_reasoning_tier: balanced
  preferred_model: gpt-4.1
  context_required: 64000
tooling:
  policy: cli-first
  jit_enabled_if: generalist_or_gt10_tools
  jit_tool_threshold: 10
  require_get_tool_details: true
tools: [write_file, read_file, list_dir, get_tool_details]
dependencies: [git]
permissions: [fs_read, fs_write, shell_exec]
scope_out: ["Do not run git push without checklist completion", "Do not skip staged diff review"]
format_profile: simple
last_updated: 2026-07-15
---

# git-safeguard

> **Profile: `simple`.** This is a single-pass, stateless safety gate. It carries no task
> ledger, no `{{task_id}}` state machine, and no resumable multi-phase workflow — it runs a
> mandatory checklist once per push and returns a decision. Telemetry (the Phase 5 ledger
> append) is still mandatory.

## Preconditions (Fail-Fast)
1. Intelligence floor check: confirm the active runtime satisfies `frontmatter.engine`.
2. Tooling policy check: plan must follow the CLI-first protocol below.
3. Confirm a concrete push target (branch + remote) is provided; otherwise stop and request it.

## Safety Checklist (Mandatory Before `git push`)
1. Run `git status` and verify intended branch/files only.
2. Run `git diff --cached` and review exact staged content.
3. Confirm no prohibited artifacts or secrets are staged.
4. Confirm branch naming policy and remote target.
5. Only then permit `git push`. Block the push on any unresolved checklist item and report the exact remediation.

## Tooling Protocol (CLI-First)
1. **Level 1 - Native CLI**: native cli commands (`git status`, `git diff --cached`) are primary.
2. **Level 2 - CLI Wrapper Scripts**: a cli wrapper under `scripts/` may automate checklist execution.
3. **Level 3 - Direct API**: direct api is exception-only.
4. **Level 4 - MCP**: mcp applies only to persistent session operations.
- When the skill is Generalist or has >10 tools, call `get_tool_details` and cache capability summaries before use.

## Ledger (Telemetry — mandatory)
On completion, append `{ "timestamp", "skill", "task_id", "status", "summary" }` to the
root `execution_ledger.jsonl`. Telemetry is required for every skill regardless of profile.
`task_id` here is a lightweight ledger correlation id, not a resumable state handle.

## Contracts
| Direction | Schema Reference | Purpose |
| :--- | :--- | :--- |
| **Input** | `./references/schemas.json#/definitions/input` | Pre-flight validation of push target. |
| **Output** | `./references/schemas.json#/definitions/output` | Push-readiness decision integrity check. |
