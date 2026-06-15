# Wire Checklist

Use this checklist when installing or validating the shared `.cursor` system.

## Structure

- [ ] `.cursor/README.md` exists
- [ ] `rules/`, `skills/`, `prompts/`, `agents/`, `templates/`, `commands/` exist
- [ ] `workflows/` and `checklists/` exist
- [ ] command files point to local prompts

## Guidance

- [ ] `skills/SKILLS_CATALOG.md` exists
- [ ] bootstrap rule points to local files
- [ ] required templates exist
- [ ] required prompts exist

## Verification

- [ ] no required runtime dependency on `LiNKdev`
- [ ] unresolved automation or infrastructure assumptions are documented
- [ ] setup gaps are explicit, not implied
