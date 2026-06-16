# Baseline

## Purpose

This repository contains the current stable baseline of the global AI development core.

## Current Layers

- Doctrine: execution laws, runtime model, and autonomous module execution under `execution/`
- Artifacts: canonical templates for intent, program, module, phase, issue, proof, review, and integration under `templates/`
- Agents: delivery roles, control roles, and the autonomous development squad under `agents/`
- Commands: preferred execution command wrappers plus retained legacy compatibility commands under `commands/`

## Compatibility

- legacy `linkdev-*` commands remain for continuity
- compatibility templates remain where older repositories may still expect them

## Ready

- progressive-disclosure indexes for execution, templates, agents, and commands
- doctrine-driven planning and execution entrypoints
- artifact model for supervised real module use

## Not Ready

- unsupervised production rollout across live repositories
- automation software such as validators, schedulers, or orchestration scripts

## Recommended Next Use

Use this baseline to run a supervised low-risk real module test, then refine operational gaps without changing the core doctrine unnecessarily.
