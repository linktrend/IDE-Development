---
name: persistent-qa
description: "Independent quality assurance skill that audits outputs and maintains recurring defect memory in Supabase-backed BUG_HISTORY.md artifacts."
usage_trigger: "Use when validating delivered work independently and tracking recurring technical debt across projects and sessions."
version: 1.0.0
release_tag: v1.0.0
created: 2026-02-25
author: LiNKskills Library
tags: [qa, auditing, memory]
engine:
  min_reasoning_tier: high
  preferred_model: gpt-5
  context_required: 128000
tooling:
  policy: cli-first
  jit_enabled_if: generalist_or_gt10_tools
  jit_tool_threshold: 10
  require_get_tool_details: true
tools: [write_file, read_file, list_dir, get_tool_details]
dependencies: [memory]
permissions: [fs_read, fs_write, api_access]
scope_out: ["Do not self-approve unverified outputs", "Do not overwrite bug history without append-only audit record"]
persistence:
  required: true
  state_path: ".workdir/tasks/{{task_id}}/state.jsonl"
last_updated: 2026-02-25
---

# persistent-qa

## Decision Tree (Fail-Fast & Persistence)
0. Resume from `.workdir/tasks/*/state.jsonl` if task exists.
1. Require target artifact and acceptance criteria.
2. Load existing BUG_HISTORY context from Supabase-backed memory.
3. Run intelligence floor check.
4. Enforce tooling protocol sequence: native cli, cli wrapper, direct api, mcp.
5. Classify specialist or generalist QA path.
6. If generalist or >10 tools, call `get_tool_details` and cache schemas.
7. Fail if audit cannot produce evidence-backed verdict.

## Rules

### Scope-In
- Run independent QA checks on delivered artifacts.
- Capture defects with reproducible evidence.
- Append recurring issue signals to BUG_HISTORY.md in memory storage.

### Scope-Out
- Do not downgrade severity without evidence.
- Do not replace historical bug context; append changes.
- Do not skip contract validation.

### Tooling Protocol (CLI-First)
1. Level 1: native cli for deterministic local checks.
2. Level 2: cli wrapper scripts for repeatable validations.
3. Level 3: direct api only for exception workflows.
4. Level 4: mcp for persistent background sessions.

### Internal Persistence (Zero-Copy / Flat-File)
- Save QA phase checkpoints to `.workdir/tasks/{{task_id}}/state.jsonl`.
- Save defect evidence as flat files under task path.
- Seek specific bug keys and run slices during resume.

### Smart JIT Tool Loading (Mitigated)
- JIT enabled only for generalist or >10 tool workflows.
- `get_tool_details` required for schema-aware QA planning.

## Workflow

### Phase 1: Ingestion & Checkpointing
1. Load target artifacts, test expectations, and issue history.
2. Determine specialist/generalist QA profile.
3. Initialize JIT cache where required.
4. Validate Input Contract.
5. Checkpoint `INITIALIZED`.

### Phase 2: Audit Logic
6. Execute QA checks and capture defects with evidence.
7. Classify defects by severity and recurrence probability.
8. Update in-memory BUG_HISTORY.md draft.
9. Checkpoint `IN_PROGRESS`.

### Phase 3: Drafting & Asynchronous Gate
10. Draft QA verdict and remediation plan.
11. If critical unresolved risk exists, set `PENDING_APPROVAL`.

### Phase 4: Finalization
12. Finalize verdict and persist BUG_HISTORY updates.
13. Validate Output Contract.
14. Checkpoint `COMPLETED`.

### Phase 5: Self-Correction & Auditing
15. Append summary to `execution_ledger.jsonl`.
16. Save audit trace under task directory.
17. Update `references/old-patterns.md` with recurring failure signatures.

## Tools
| Tool Name | Workflow Scope | Critical Execution Rule |
| :--- | :--- | :--- |
| `memory` | Phases 1-4 | Store and retrieve BUG_HISTORY context using isolated agent/project keys. |
| `write_file` | All | Persist checkpoints and QA evidence summaries. |
| `get_tool_details` | Phase 1+ | Mandatory for generalist/JIT profile. |

## Contracts
| Direction | Artifact Name | Schema Reference | Purpose |
| :--- | :--- | :--- | :--- |
| **Input** | `qa_request` | `./references/schemas.json#/definitions/input` | Validate audit targets and acceptance criteria. |
| **Output** | `qa_report` | `./references/schemas.json#/definitions/output` | Validate defect summary and recurrence tracking. |
| **State** | `execution_state` | `./references/schemas.json#/definitions/state` | Persist resumable QA flow. |

## Progressive Disclosure References
- Complex QA branches: `./advanced/advanced.md`
- Tool references: `./references/api-specs.md`
- Recurring anti-patterns: `./references/old-patterns.md`
- Change history: `./references/changelog.md`
