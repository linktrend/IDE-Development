# Tool Architect Script Utilities

## Purpose
Scripts in this folder support deterministic creation and validation of tool packages under `/tools`.

## Available Scripts
- `helper_tool.py`: generic helper for structured JSON transforms.
- `create_tool_package.py`: scaffold `/tools/[tool-name]/` with README/interface/bin/test defaults.

## Root Validators
- `python3 ../../validator.py --repo-root . --scan-all`
