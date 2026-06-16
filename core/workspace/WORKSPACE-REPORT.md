# Workspace Report

## Purpose

Define the canonical report produced after a workspace adoption operation.

## Minimum Contents

Every workspace adoption report should include:

- date and time
- workspace root
- system repository path
- repositories discovered
- repositories skipped
- repositories wired
- repositories left untouched due to ambiguity
- backups created
- legacy cleanup actions taken
- verification results
- rollback notes

## Quality Rules

- be explicit about which repositories changed
- preserve ambiguity rather than hiding it
- record backup locations
- record symlink verification results
- make rollback feasible from the report alone

## Relationship To Session Handoff

This report is not the same as a daily handoff report.

- workspace report: one-time workspace installation result
- session handoff: daily continuity artifact
