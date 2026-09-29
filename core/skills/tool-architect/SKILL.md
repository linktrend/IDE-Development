---
name: tool-architect
description: "Designs, wraps, and validates CLI-first tools for the LiNKskills Global Tools Registry."
usage_trigger: "Use when a required tool is missing in /tools, or when converting APIs/third-party tools into standardized CLI wrappers."
version: 1.0.0
release_tag: v1.0.0
created: 2026-02-22
author: LiNKskills Library
tags: [meta, tooling, registry, cli]
engine:
  min_reasoning_tier: balanced
  preferred_model: gpt-4.1
  context_required: 64000
tooling:
  policy: cli-first
  jit_enabled_if: generalist_or_gt10_tools
  jit_tool_threshold: 10
  require_get_tool_details: true
tools: [read_file, write_file, make_dir, list_dir, shell_exec, get_tool_details]
dependencies: []
permissions: [fs_read, fs_write, shell_exec]
scope_out: ["Do not build hidden proprietary wrappers without interface.json", "Do not bypass /tools registry conventions", "Do not implement governance, entitlements, leases, or permission-to-act"]
format_profile: heavy
persistence:
  required: true
  state_path: ".workdir/tasks/{{task_id}}/state.jsonl"
last_updated: 2026-02-22
---

# Tool Architect

> **Validation:** Tool and skill structure checks use `python3 scripts/validate_skills.py`
> (`validator.py` at repo root). Skill-local helper scripts must not reimplement those rules.

## Mission
Tool Architect is the meta-skill responsible for building and maintaining the **LiNKskills Global Tools Registry** under `/tools`.

## Decision Tree (Fail-Fast & Persistence)
0. **Audit Check**: Is this request a continuation of an existing tool-architect task?
   - YES: seek latest checkpoint in `.workdir/tasks/{{task_id}}/state.jsonl`, then resume.
1. **Registry Check**: Does `/tools` already contain the requested capability?
   - YES: return existing tool path and validate it before creating anything new.
2. **Intelligence Floor Check**: Does runtime satisfy `frontmatter.engine`?
   - NO: fail-fast and request higher-capability runtime.
3. **Tooling Protocol Check**: Is the plan CLI-first with API/MCP only under allowed exceptions?
   - NO: re-plan to comply.
4. **Input Sufficiency Check**: Do we have enough source details (API spec/3rd-party tool behavior) to wrap safely?
   - NO: request missing contract details.
5. **Old Pattern Check**: Consult `./references/old-patterns.md` before execution.

## Rules

### Scope-In
- Create or upgrade tools under `/tools/[tool-name]/`.
- Enforce required tool package layout.
- Ensure wrappers support `--help`, `--version`, and `--json`.
- Ensure outputs are high-signal for agent consumption.

### Scope-Out
- Do not ship wrappers without tests.
- Do not create tools outside `/tools`.
- Do not rely on direct API calls when CLI/script alternatives are viable.

### Tooling Protocol (CLI-First)
1. **Level 1 - Native CLI**: prioritize native cli binaries first.
2. **Level 2 - CLI Wrapper Scripts**: prefer wrapper scripts in `bin/` and skill-local `scripts/`.
3. **Level 3 - Direct API**: direct api usage is exception-only.
4. **Level 4 - MCP**: mcp usage is reserved for persistent background/session services.

### Tool Package Standard
Every tool in `/tools/[tool-name]/` must include:
1. `README.md` with human-readable docs and a **Capability Summary**.
2. `interface.json` with parameters/types/descriptions.
3. `bin/` executable wrapper scripts.
4. `test/` validation scripts.

## Workflow

### Phase 1: Identify
1. Deconstruct source API/third-party tool behavior.
2. Determine required command surface and parameter contract.
3. Categorize complexity profile (`Specialist` vs `Generalist`) for optional JIT metadata planning.
4. **CHECKPOINT**: append analysis record to `state.jsonl`.

### Phase 2: Wrap
5. Create `/tools/[tool-name]/` structure and required files.
6. Implement CLI wrapper in `bin/` with `--help`, `--version`, `--json`.
7. Write `interface.json` for tool-calling.
8. Write `README.md` including Capability Summary and usage examples.
9. **CHECKPOINT**: append wrapper-build record to `state.jsonl`.

### Phase 3: Verify
10. Add tests in `test/` and validate wrapper behavior.
11. Run `python3 scripts/validate_skills.py --scan-all --repo-root .` when tool layout affects registry compliance.
12. Confirm output is high-signal and parseable for agent workflows.
13. If JIT profile applies, ensure `get_tool_details` fetch plan and schema cache notes are included.
14. **CHECKPOINT**: append verification record to `state.jsonl`.

### Phase 4: Finalization
15. Report tool path, interface contract, test status, and known limits.
16. Append completion checkpoint to `state.jsonl`.

### Phase 5: Self-Correction & Auditing
17. Append execution summary to root `execution_ledger.jsonl`.
18. Save trace to `.workdir/tasks/{{task_id}}/trace.log`.
19. Update `./references/old-patterns.md` with new anti-patterns discovered.

## Tools
| Tool Name | Workflow Scope | Critical Execution Rule |
| :--- | :--- | :--- |
| `read_file` | All | Read source specs and existing registry artifacts. |
| `write_file` | All | Write tool interfaces, docs, wrappers, and checkpoints. |
| `make_dir` | Phase 2 | Create canonical tool directory layout. |
| `list_dir` | Phase 1 | Discover existing tools in `/tools`. |
| `shell_exec` | Phase 3 | Run wrapper/test commands for verification. |
| `get_tool_details` | Phase 1+ | Required when JIT metadata for complex tool ecosystems is needed. |

## Contracts
| Direction | Artifact Name | Schema Reference | Purpose |
| :--- | :--- | :--- | :--- |
| **Input** | `tool_request` | `./references/schemas.json#/definitions/input` | Validate requested tool behavior and source context. |
| **Output** | `tool_report` | `./references/schemas.json#/definitions/output` | Validate created/updated tool package report. |
| **State** | `execution_state` | `./references/schemas.json#/definitions/state` | Persistent checkpointing and resumability. |

## Progressive Disclosure References
- **Examples**: `./examples/`
- **Advanced**: `./advanced/advanced.md`
- **Reference**: `./references/api-specs.md`
- **Versioning**: `./references/changelog.md`

## Old Patterns
> Always consult and update `./references/old-patterns.md` to prevent regression.
