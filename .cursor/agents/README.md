# Agents

Local agent definitions live in this directory.

Read `INDEX.yaml` first. It is the progressive-disclosure entrypoint for role selection.

This directory contains:

- delivery roles for program, module, phase, and issue execution
- lightweight control roles for planning, orchestration, review, and integration
- squad compositions that describe how multiple roles cooperate
- legacy or compatibility role documents kept for continuity

Agents should treat `.cursor/` as the source of truth and should not rely on external factory directories.
