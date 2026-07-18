# Application pipeline — release-ready checklist

Use before setting terminal state `release_ready`. This checklist does **not** authorize deploy.

## Required

- [ ] Exactly six fixed Modules present in order under `docs/development/<program-id>/modules/`
- [ ] Module 1 Principal approval recorded for Intent + Technical PRD
- [ ] Technical PRD acceptance criteria all mapped (Module 2) and verified (Module 4)
- [ ] Technical Design independent review approved (Module 2)
- [ ] Every required Issue `done` with proof, independent review, integration (PR/CI where applicable)
- [ ] Module 5 publication state is `merged`, `publication_pending`, or `not_applicable`
- [ ] Critical full-repo verification result recorded
- [ ] SHA256 proof manifest present (`proof-manifest.sha256`)
- [ ] Ship-criteria checklist complete
- [ ] Independent program-release report present
- [ ] Principal pre-deploy decision explicitly recorded
- [ ] Validator accepts terminal `release_ready`
- [ ] No deploy command was run
- [ ] No automatic promotion to staging/main was performed
