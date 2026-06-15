# Dispatch Workflow

Dispatch is the coordination layer between planning, review, integration, and execution.

## Purpose

Define how work becomes ready, how roles are triggered, and what evidence must exist before the next stage begins.

## Core Roles

- planner
- executor
- reviewer
- integrator
- operator or principal

## Principles

1. Labels and state should be explicit.
2. Automation may assist, but local files remain authoritative.
3. No role should assume readiness without documented proof.
4. Review and integration must be separate concerns.

## Minimal Trigger Model

| Role | Typical Trigger | Expected Output |
|------|------------------|-----------------|
| Planner | `Go` or new initiative | plan artifacts |
| Executor | ready issue | implementation and proof |
| Reviewer | review-ready work | findings or approval |
| Integrator | merge-ready work | coherent integrated state |

## Required Evidence

- objective is documented
- acceptance criteria exist
- proof expectations exist
- blockers are explicit
