---
issue_id: "HYBRID-SMOKE-001"
title: "Add hybrid registry to operator guide Key docs"
status: "done"
parent_program: "hybrid-smoke"
parent_module: "hybrid-smoke"
parent_phase: "trigger-2-verification"
depends_on: []
objective: "Add docs/HYBRID-SKILLS-REGISTRY.md to the operator guide Key docs section."
scope:
  - "docs/LINKDEVELOPER-WORKSPACE-OPERATOR-GUIDE.md"
out_of_scope:
  - "Other docs beyond Key docs list"
inputs:
  - "core/pilots/hybrid-smoke/PRD.md"
  - "docs/HYBRID-SKILLS-REGISTRY.md"
expected_outputs:
  - "Operator guide Key docs includes hybrid registry path"
acceptance_criteria:
  - "Key docs section lists docs/HYBRID-SKILLS-REGISTRY.md"
  - "Section 7 describes hybrid as installed/wired, not reference-only"
proof_requirements:
  - "Before/after summary of operator guide change"
review_requirements:
  - "Independent reviewer confirms criteria from proof"
integration_requirements:
  - "Integration recorded; issue done only after passing review"
suggested_role_types:
  - "orchestrator"
  - "reviewer"
  - "integrator"
read_first:
  - "core/pilots/hybrid-smoke/PRD.md"
  - "docs/HYBRID-SKILLS-REGISTRY.md"
  - "docs/LINKDEVELOPER-WORKSPACE-OPERATOR-GUIDE.md"
read_forbidden:
  - "LiNKdev/"
blocking_questions: []
optional_fields:
  priority: "low"
  risk_level: "low"
  estimated_effort: "5 minutes"
  notes:
    - "Trigger 2 hybrid smoke — mattpocock path simulated"
---

# Issue

## Objective

Wire hybrid skills discoverability into the Carlos-facing operator guide Key docs list.

## Hybrid path taken

Trigger 2 simulation: PRD in hand → `hybrid-grill` (no gaps) → approve → `hybrid-to-issues` → `small-change` execution.

## State history

| State | When | Notes |
|-------|------|-------|
| ready | 2026-07-10 | Sliced from PRD via mattpocock path |
| in_progress | 2026-07-10 | Doc edit started |
| review_ready | 2026-07-10 | Proof complete |
| done | 2026-07-10 | Review pass + integration |
