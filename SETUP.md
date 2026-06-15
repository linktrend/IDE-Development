# Setup Guide

## Purpose

This repository contains the shared AI development core used across Cursor, Codex, and future tools.

The active system lives in `.cursor/`. GitHub is the source of truth.

## Clone On Another Machine

Recommended target location:

```bash
mkdir -p ~/Projects
cd ~/Projects
git clone https://github.com/linktrend/IDE-Development.git "IDE Development"
cd "IDE Development"
```

After cloning, use this repository as the primary working copy of the shared `.cursor` system on that machine.

## Mac Mini Setup

On the Mac Mini, clone into:

```bash
~/Projects/IDE Development
```

Commands:

```bash
mkdir -p ~/Projects
cd ~/Projects
git clone https://github.com/linktrend/IDE-Development.git "IDE Development"
cd "IDE Development"
git status
```

## Pull Updates

Before using or editing the system on any machine:

```bash
git pull
git status
```

## Make Changes Safely

Use one working copy at a time for active edits. Do not make overlapping manual changes on both the MacBook and Mac Mini and then try to reconcile them later.

Before letting Cursor, Codex, or another agent modify the system:

```bash
git status
```

If the working tree is clean, make the smallest useful change, then review the result before committing.

## MacBook Update Flow

Typical update flow:

```bash
git pull
git status
git add .cursor README.md SETUP.md .gitignore
git commit -m "..."
git push
```

If other root files are intentionally changed, stage them explicitly rather than using broad adds by habit.

## Warning

- Do not copy `.cursor` manually into many repositories.
- Use Git and this repository as the source of truth.
- Make major changes in small commits.
- Run `git status` before letting Codex modify the system.
- Avoid maintaining duplicated `.cursor` systems across multiple repos when they are meant to share the same core.
