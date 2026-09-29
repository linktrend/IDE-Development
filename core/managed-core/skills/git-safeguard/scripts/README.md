# Internal Script Utilities

## Guidelines
- **Black Box Principle**: The agent should run these scripts with `--help` to understand parameters rather than reading the source code.
- **Pathing**: Always use relative paths from the skill root.

## Available Scripts
- `helper_tool.py`: [High-level purpose]
- Root-level validator: run `python3 ../../validator.py --path skills/<skill-name> --repo-root .` from repository root.
