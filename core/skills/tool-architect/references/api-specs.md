# Tool Architect Technical Reference

## Wrapper Requirements
- Every wrapper must expose: `--help`, `--version`, and `--json`.
- Output should be high-signal plain text or JSON suitable for agent parsing.

## Tool Registry Paths
- Skills: `/skills/[skill-name]`
- Tools: `/tools/[tool-name]`

## interface.json Contract
Top-level keys required:
- `name`
- `description`
- `capability_summary`
- `parameters` (array of `{name,type,description}`)
