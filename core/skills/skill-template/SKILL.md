---
name: skill-template
description: "Golden template for creating production-grade LiNKskills skills."
usage_trigger: "Use when creating or updating a standardized skill scaffold."
version: 1.2.0
release_tag: v1.2.0
created: 2026-02-20
author: LiNKskills Library
tags: [template, baseline]
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
dependencies: []
permissions: [fs_read, fs_write]
scope_out: ["Do not execute business workflows from this template", "Do not remove persistence and audit primitives", "Do not implement governance, entitlements, leases, or permission-to-act"]
format_profile: heavy
persistence:
  required: true
  state_path: ".workdir/tasks/{{task_id}}/state.jsonl"
last_updated: 2026-02-20
---

# <Skill Name Identifier>

> **Validation:** Use `python3 scripts/validate_skills.py` (repo root) — canonical
> structural gate in `validator.py`. Do not maintain duplicate validators under
> `skills/*/scripts/`.

## Format Profile (choose before scaffolding)
This file is the **`heavy`** profile of the golden template (`format_profile: heavy`):
resumable, multi-phase, HITL-gated skills that carry a task-state machine. Declare the
profile in frontmatter with `format_profile: heavy | simple`. Default is `heavy` when the
field is absent (backward compatible — no existing skill's validation weakens).

Use the **`simple`** profile instead for genuinely stateless, single-pass skills (≤ a few
tools, no cross-phase state, no HITL resume). The simple profile keeps the same folder
shape, the same core frontmatter, the CLI-first tooling protocol, and the **mandatory
Phase 5 ledger append** (telemetry is universal), but drops the `.workdir/tasks` task
ledger, the `{{task_id}}` state path, the `#/definitions/state` schema, and the full
multi-phase Decision Tree. See [`./references/simple-profile.md`](#) for the simple
authoring shape. The rest of this file is the heavy profile.

## Decision Tree (Fail-Fast & Persistence)
0.  **Audit Check**: Does the user request refer to a previous execution?
    - YES: Read `execution_ledger.jsonl` (at repository root) to find the matching `task_id`, then seek local `state.jsonl`. STOP and EXPLAIN.
1.  **Pending Task Check**: Scan `.workdir/tasks/*/state.jsonl` for tasks with latest `status: "PENDING_APPROVAL"`.
    - IF PENDING TASK FOUND: Is current input a duplicate/continuation?
        - YES: Resume from Phase 4 using existing `task_id`.
        - NO: Generate a **NEW Task ID** and move to Step 2.
    - IF NO PENDING TASK: Generate **NEW Task ID** (format: `YYYYMMDD-HHMM-<SKILLNAME>-<SHORTUNIX>` where SHORTUNIX is the last 6 digits of the current Unix timestamp).
2.  **Intelligence Floor Check**: Does the active model/runtime satisfy `frontmatter.engine` requirements?
    - NO: Fail-fast. Warn user that reasoning reliability/context may be insufficient.
3.  **Tooling Protocol Check**: Does plan follow CLI-first levels and direct API/MCP limits in `frontmatter.tooling`?
    - NO: Refactor plan to comply before execution.
4.  **Prerequisite Check**: Are all tools in `frontmatter.tools` and `dependencies` available?
    - NO: Request creation via `/skills/tool-architect` before execution.
5.  **Old Pattern Check**: Consult [`./references/old-patterns.md`](#). Does the task match a deprecated heuristic?
    - YES: Warn user, propose the current workflow, and await confirmation.
    - NO: Initiate **Phase 1**.

## Rules

### Scope-In
- [Mandatory atomic task 1]
- [Mandatory atomic task 2]
- [Final deliverable requirement]

### Scope-Out
- **CRITICAL**: Do not [forbidden action 1].
- Do not [unauthorized data modification or tool use].
- Avoid [stylistic or procedural anti-pattern].

### Escalation Protocol
- If [tool error/timeout], then [recovery or report action].
- If [missing context/variable], then [stop and request clarification].

### Tooling Protocol (CLI-First)
1. **Level 1 - Native CLI**: Prefer system binaries first.
2. **Level 2 - CLI Wrapper Scripts**: Use local Python/Bash scripts under `scripts/` as default logic layer.
3. **Level 3 - Direct API (Exception Only)**: Allowed only for high-frequency LLM reasoning, complex DB queries with high serialization costs, or real-time streaming.
4. **Level 4 - MCP**: Use only for persistent, session-based background services.

### Internal Persistence (Zero-Copy / Flat-File)
- Write phase checkpoints to `.workdir/tasks/{{task_id}}/state.jsonl`.
- Store large artifacts in flat files under the same task folder.
- Subsequent phases should seek precise keys/offsets instead of loading full artifacts.

### Smart JIT Tool Loading (Mitigated)
- Activation rule: enable JIT only if the skill is `Generalist` or has `>10` tools.
- Planning rule: when JIT is enabled, SKILL.md must include one-sentence capability summaries per tool.
- Implementation rule: call `get_tool_details` and cache schemas in task-local state to avoid repeated latency.

## Workflow

### Phase 1: Ingestion & Checkpointing
1. Retrieve required context variables via [tool_name].
2. Categorize execution profile:
   - `Specialist`: single domain and `<=10` tools.
   - `Generalist`: multi-domain or `>10` tools.
3. If profile is `Generalist`, call `get_tool_details` and cache schemas/indexes in `.workdir/tasks/{{task_id}}/`.
4. Validate data against the **Input Contract**.
5. **CHECKPOINT**: Append phase snapshot to `state.jsonl` with `status: "INITIALIZED"`.

### Phase 2: Logic & Reasoning
6. Execute [core reasoning logic] using external logic in `./advanced/` if complexity is high.
7. **LOGIC GATE**: IF [condition], THEN [path A]; ELSE [path B].
8. For `Specialist` skills, keep embedded schema usage.
9. For `Generalist` skills, use JIT-loaded cached tool schemas.

### Phase 3: Drafting & Asynchronous Gate
10. Call [tool_name] to generate the target artifact/action draft.
11. **HITL GATE**: IF risk level requires approval, append `PENDING_APPROVAL` to `state.jsonl` and **TERMINATE SESSION**.

### Phase 4: Finalization (Resume Point)
12. Upon user approval/resumption, execute the final tool call.
13. Verify output against **Output Contract**.
14. Append completion checkpoint to `state.jsonl`.

### Phase 5: Self-Correction & Auditing
15. **LEDGER**: Append `{ "timestamp", "skill", "task_id", "status", "summary" }` to `execution_ledger.jsonl` (at repository root).
16. **TRACE**: Save raw model output and tool payloads to `.workdir/tasks/{{task_id}}/trace.log`.
17. **LEARN**: IF execution failed or was corrected, update `./references/old-patterns.md` with the new "known-bad" heuristic.

## Tools
| Tool Name | Workflow Scope | Critical Execution Rule |
| :--- | :--- | :--- |
| `<tool_1>` | Phase X | [Execution constraint/required param] |
| `write_file` | All | Exclusively used for checkpointing and logging. |
| `get_tool_details` | Phase 1+ | Mandatory for Generalist/JIT profile; cache results in task-local state. |

## Contracts
| Direction | Artifact Name | Schema Reference | Purpose |
| :--- | :--- | :--- | :--- |
| **Input** | `trigger_context` | `./references/schemas.json#/definitions/input` | Pre-flight validation. |
| **Output** | `final_artifact` | `./references/schemas.json#/definitions/output` | Integrity check. |
| **State** | `execution_state` | `./references/schemas.json#/definitions/state` | Persistent checkpointing. |

## Progressive Disclosure References
- **Examples**: Refer to [`./examples/`](#) for scenario-specific multi-turn traces.
- **Advanced**: Refer to [`./advanced/advanced.md`](#) for complex edge cases.
- **Reference**: Refer to [`./references/api-specs.md`](#) for API/Technical specs.
- **Versioning**: Record functional updates in [`./references/changelog.md`](#).

## Old Patterns
> **IMPORTANT**: The agent MUST consult [`./references/old-patterns.md`](#) during the Decision Tree phase. This file is dynamically updated by the agent in Phase 5 to prevent "Convention Drift" and ensure 100% adherence to evolving project norms.
