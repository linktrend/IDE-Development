# Handoff Report

## Purpose

Define the canonical structure for repository-level handoff reports stored under:

`docs/handoff/YYYY-MM-DD.md`

The handoff report is a continuity artifact for the next session.

It does not replace:

- `PROGRAM.md`
- `MODULE.md`
- `PHASE.md`
- `ISSUE.md`
- `PROOF.md`
- `REVIEW.md`
- `INTEGRATION.md`

## Required Fields

Every handoff report should include:

- date
- time
- repository
- active branch
- summary of completed work
- remaining work
- blockers
- recommended next action

## Recommended Supporting Fields

When relevant, also include:

- active module
- ready issues
- pending review or integration gates
- key files changed
- commands or workflows most likely to be used next

## Quality Rules

- be concise
- prefer references over duplication
- do not claim completion without evidence
- do not hide blockers
- make the next session start without guessing

## Storage Rule

Store the artifact at:

`docs/handoff/YYYY-MM-DD.md`

Use one file per date unless repository practice explicitly requires a finer-grained split.

## Read Next

1. `SESSION-START.md`
2. `SESSION-END.md`
