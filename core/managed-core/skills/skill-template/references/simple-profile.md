# Simple Profile — Right-Sized Template Variant

This is the authoring shape for a **`format_profile: simple`** skill, per
[`docs/LINKSKILLS-TECHNICAL-PRD.md`](../../../docs/LINKSKILLS-TECHNICAL-PRD.md) §3.3
(historical design notes: `docs/archive/specs/catalog-eval-telemetry-spec.md` §5). Use it for genuinely stateless,
single-pass skills (a mandatory checklist, a one-shot enforcement pass, a stateless
transform) that finish in one pass with no cross-phase state, no HITL resume, and only a
handful of tools. The heavy profile (`SKILL.md`) forces a task-state machine those skills
never use; the simple profile removes that machinery **only** — never observability or
quality proof.

## What simple keeps vs. drops

| Requirement | Simple | Heavy |
|---|---|---|
| Core frontmatter (`name`, `description`, `usage_trigger`, `version`, `release_tag`, `engine`, `tooling`, `tools`, `permissions`, `scope_out`) | Required | Required |
| `format_profile: simple` in frontmatter | Required (explicit opt-down) | `heavy` / absent |
| `persistence` block (`required: true`, `{{task_id}}` state_path) | **Not required** (omit, or `required: false`) | Required |
| `.workdir/tasks/{{task_id}}/state.jsonl` task ledger | **Not required** | Required |
| `task_id` generation | **Not required** | Required |
| Full multi-phase Decision Tree with checkpoints | **Not required** — a short "Preconditions" list is enough | Required |
| `#/definitions/state` in `references/schemas.json` | **Not required** (keep `input`/`output`) | Required |
| `state.jsonl` / `specialist` / `generalist` body terms | **Not required** | Required |
| CLI-first tooling protocol terms (`native cli`, `cli wrapper`, `direct api`, `mcp`, `get_tool_details`) | Required | Required |
| Progressive-disclosure folder shape (`SKILL.md` + `examples/` + `advanced/` + `references/{schemas.json,api-specs.md,old-patterns.md,changelog.md}` + `scripts/`) | Required | Required |
| **Phase 5 ledger append to `execution_ledger.jsonl`** | **Required** (telemetry is universal) | Required |
| Baseline eval suite (`references/eval-suite.yaml`) | Required (all skills) | Required (all skills) |
| SKILL.md body ≤ 500 lines | Required | Required |

## Minimal simple `SKILL.md` skeleton

```markdown
---
name: <skill-id>
description: "<what it does, third person, >=10 chars>"
usage_trigger: "Use when <single-pass trigger>."
version: 1.0.0
release_tag: v1.0.0
created: YYYY-MM-DD
author: LiNKskills Library
tags: [<tags>]
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
scope_out: ["<forbidden action>"]
format_profile: simple
last_updated: YYYY-MM-DD
---

# <skill-id>

## Preconditions (Fail-Fast)
1. Intelligence floor check against `frontmatter.engine`.
2. Tooling policy check.
3. Confirm required inputs are present; otherwise stop and request them.

## <Core single-pass logic>
- The one deterministic pass this skill performs (checklist, enforcement, transform).

## Tooling Protocol (CLI-First)
1. **Level 1 - Native CLI**: prefer system binaries.
2. **Level 2 - CLI Wrapper Scripts**: `scripts/` logic layer.
3. **Level 3 - Direct API**: exception-only.
4. **Level 4 - MCP**: persistent session services only.
Call `get_tool_details` when the skill is Generalist or has >10 tools.

## Ledger (Telemetry — mandatory)
On completion, append `{ "timestamp", "skill", "task_id", "status", "summary" }` to the
root `execution_ledger.jsonl`. Telemetry is required for **every** skill regardless of
profile. A simple skill may use a lightweight `task_id` purely as a ledger correlation id
(it does not imply a resumable state machine).

## Contracts
| Direction | Schema Reference | Purpose |
| :--- | :--- | :--- |
| **Input** | `./references/schemas.json#/definitions/input` | Pre-flight validation. |
| **Output** | `./references/schemas.json#/definitions/output` | Integrity check. |
```

## Choosing a profile
- Cross-phase state, resume-after-HITL, or a task ledger → **heavy**.
- One deterministic pass, no resume, few tools → **simple**.
- Unsure → default to **heavy** (safe default; opting down to simple is a reviewable change).
