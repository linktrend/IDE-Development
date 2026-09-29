---
name: repository-manager
description: "Manages repository hygiene, progress sync handoffs, and safe Git flow enforcement for LiNKskills sessions."
usage_trigger: "Use when a task changes repository files, branches, commits, or requires end-of-session handoff updates."
version: 1.0.0
release_tag: v1.0.0
created: 2026-02-24
author: LiNKskills Library
tags: [repository, git, handoff]
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
scope_out: ["Do not bypass commit safety checks", "Do not push directly from disallowed branch patterns"]
persistence:
  required: true
  state_path: ".workdir/tasks/{{task_id}}/state.jsonl"
last_updated: 2026-02-24
---

# repository-manager

## Decision Tree (Fail-Fast & Persistence)
0. Check for resumable tasks in `.workdir/tasks/*/state.jsonl` and ledger continuity.
1. Validate runtime intelligence floor from frontmatter engine requirements.
2. Validate tooling protocol (native cli, cli wrapper, direct api, mcp).
3. Classify scope as Specialist or Generalist; if Generalist run `get_tool_details`.
4. Validate branch naming and commit safety prerequisites before any git mutation.
5. Validate all session outputs include `PROGRESS.md` update before completion.

## Progress Sync Protocol (Mandatory)
Every session must end by updating `PROGRESS.md` with this JSON schema:
`{ "Status": "Done/Blocked/In-Progress", "Last_Action": "...", "Context_For_Next_Agent": "..." }`

## Branching Protocol
- Allowed feature branch prefixes only:
  - `feat/`
  - `fix/`
  - `refactor/`
- Any other branch prefix is blocked until renamed.

## Tooling Protocol (CLI-First)
1. Native CLI first for git/status/diff checks.
2. CLI wrapper scripts under `scripts/` are the default for enforced safety logic.
3. Direct API is exception-only.
4. MCP only for persistent session tooling.

## Internal Persistence (Zero-Copy / Flat-File)
- Persist checkpoints to `.workdir/tasks/{{task_id}}/state.jsonl`.
- Save structured diffs or command snapshots under task-local flat files.
- Seek precise keys and files rather than reloading full context.

## Smart JIT Tool Loading (Mitigated)
- Enable JIT for Generalist or >10 tools.
- When JIT is enabled, call `get_tool_details`, cache schemas, and use one-sentence capability summaries.

## Workflow
### Phase 1: Ingestion & Checkpointing
- Inspect repo state and branch status.
- Validate input contract.
- Checkpoint `INITIALIZED`.

### Phase 2: Safety Planning
- Apply branch prefix policy (`feat/`, `fix/`, `refactor/`).
- Stage safety checks through script wrappers.
- Checkpoint `IN_PROGRESS`.

### Phase 3: Execution Gate
- Apply/update safeguards and progress handoff artifacts.
- Gate on safety check outcomes.

### Phase 4: Finalization
- Ensure `PROGRESS.md` is updated with required schema.
- Validate output contract and checkpoint `COMPLETED`.

### Phase 5: Self-Correction & Auditing
- Append execution summary to `execution_ledger.jsonl`.
- Write trace log and update `references/old-patterns.md` for new known-bad patterns.

## Contracts
- Input: `./references/schemas.json#/definitions/input`
- Output: `./references/schemas.json#/definitions/output`
- State: `./references/schemas.json#/definitions/state`
