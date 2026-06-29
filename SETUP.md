# Setup Guide

## Purpose

This repository contains the shared AI development core used across Cursor, Codex, and future tools.

The canonical knowledge asset lives in `core/`. The compatibility runtime surface remains in `.cursor/`. GitHub is the source of truth.

The repository also supports:

- session lifecycle for daily resume and close-out behavior
- workspace adoption for one-time installation into an existing `Projects/` workspace

## Clone On Another Machine

Recommended target location:

```bash
mkdir -p ~/Projects
cd ~/Projects
git clone https://github.com/linktrend/IDE-Development.git "IDE Development"
cd "IDE Development"
```

After cloning, use this repository as the primary working copy of the shared development core on that machine.

If the machine already has a `Projects/` workspace containing other repositories, the next step can be workspace adoption so those repositories consume this shared `.cursor` runtime surface.

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

## Workspace Adoption

After cloning `IDE Development` into a `Projects/` folder, an existing workspace can be adopted through the workspace lifecycle capability.

Natural-language triggers include:

- `Install the system into this workspace.`
- `Adopt this workspace.`
- `Wire this workspace.`

Operational result:

- `IDE Development/core` remains canonical knowledge
- `IDE Development/.cursor` remains the shared compatibility runtime surface
- each consumer repository receives a `.cursor` symlink pointing to `../IDE Development/.cursor`

Workspace adoption is one-time.

Session lifecycle remains the daily operational behavior after adoption.

## Installer Position

No separate installer script is required for normal use.

The intended installation model is:

- keep `IDE Development` as a folder in the workspace
- keep `IDE Development/core` as canonical knowledge
- keep `IDE Development/.cursor` as the shared runtime surface
- wire consumer repositories to that runtime surface with `.cursor` symlinks

For Cursor, the practical requirement is that the workspace can see the `IDE Development` folder and the consumer repository `.cursor` symlink resolves correctly.

For Codex, the practical requirement is that agents can discover the repository and follow the `.cursor` compatibility paths into `core`.

An installer or verifier may be added later if manual adoption becomes error-prone across many machines, but it is not part of the required v1 operating model.

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

- Do not copy `core/` or `.cursor/` manually into many repositories.
- Use Git and this repository as the source of truth.
- Make major changes in small commits.
- Run `git status` before letting Codex modify the system.
- Avoid maintaining duplicated compatibility surfaces across multiple repos when they are meant to share the same core.
