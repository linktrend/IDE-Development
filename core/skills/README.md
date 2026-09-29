# Skills

Skills are local, focused instructions for recurring work patterns.

## LiNKskills pin

These five skills are owned by LiNKskills and synced byte-for-byte:
`git-safeguard`, `persistent-qa`, `repository-manager`, `skill-template`, `tool-architect`.

Pin: `linktrend/LiNKskills` commit `28334c4d409dc74a680bf4e09fa2dab22726e229`
(tree `3038dfc1f24c256f9c7547f906a988ce222e2044`, LiNKskills `VERSION` 1.0.0).

Re-sync with `python3 scripts/sync-linkskills.py --write --commit <sha>`.
`python3 scripts/sync-linkskills.py --check` verifies the lock hashes offline.
Do not edit synced skill files locally; change them upstream and re-pin.
The other skills in this tree are IDE Development-local until a decision on moving them to LiNKskills.

Start with `SKILLS_CATALOG.md`, then open only the skill needed for the current task.

## Current Scope

The current catalog contains skills that were already stabilized or normalized into the shared core.

It is not intended to be the final inventory of all development skills used across existing repositories.

Imported, refactored, or repurposed repository-specific skills should be evaluated before they are added here so the shared core does not accumulate duplicate, stale, or overly narrow instructions.

If older repositories contain skills informally known as `g skills` or `gstack`, evaluate them through the migration process:

1. inventory the source skills
2. identify duplicates and overlaps
3. decide whether each skill should be imported, merged into an existing skill, rewritten, or left repository-local
4. update `SKILLS_CATALOG.md` only after the shared version is ready

## Skill Template

Use `skills/skill-template/SKILL.md` as the normalization target for new shared skills.

The IDE Development skill template is adapted from the LiNKskills golden template, but it aligns to this system's artifacts, gates, and progressive-disclosure model.
