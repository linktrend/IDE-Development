# Lane B Result — Clean-room install / upgrade / drift / rollback

**Work packet:** Issue #67 Work Packet 1
**Lane:** B (clean-room acceptance)
**Date (UTC):** 2026-08-02T02:01:31Z
**Host:** Darwin / Python 3.9.6
**Production installer edits:** none
**Commit/push/PR:** not performed (subagent constraint)

## Commands and exit codes

```bash
python3 tests/cleanroom_acceptance/run_tests.py
# exit 0
# Summary: passed=16 failed=0 skipped=0

python3 tests/managed-core-migration-bb/run_tests.py --with-installer
# exit 0
# Summary: passed=40 failed=0 skipped=0
```

Package source used by clean-room runner:

```text
fixture:tests/cleanroom_acceptance/fixtures/extracted-rc-package
```

Lane D extracted RC paths were probed and **not present**:

- `artifacts/release-candidate/extracted`
- `dist/release-candidate/extracted`
- `build/release-candidate/extracted`

## Coverage map (required scenarios)

| # | Scenario | Result | Notes |
|---|---|---|---|
| 1 | Brand-new repository installation | PASS (`01-brand-new-install`) | Physical managed core + Cursor/Codex entrypoints; nested discovery; verify ok |
| 2 | Repeat install/update idempotence | PASS (`02-idempotent-repeat`) | Byte+mode fingerprint unchanged across install×2 + noop update |
| 3 | Upgrade from sparse GitOps layout | PASS (`03-sparse-gitops-upgrade`) | Exact obsolete sparse note removed; consumer gitops/tech files preserved |
| 4 | External `.cursor` symlink migration | PASS (`04-external-cursor-symlink`) | Physical migrate; outside byte-identical; rollback restores symlink |
| 5 | Physical `.cursor` consumer-owned content | PASS (`05-physical-cursor-consumer-owned`) | Rules/commands/skills preserved; managed entrypoints added |
| 6 | Root `AGENTS.md` consumer text | PASS (`06-agents-md-consumer-text`) | Outside-marker text preserved through install+update |
| 7 | Repo-specific `.agents/skills` + tech docs | PASS (`07-repo-specific-agents-skills`) | Consumer skill/docs preserved; managed Codex skill installed; nested discovery |
| 8 | Exact obsolete removal + conflict refusal | PASS (`08-obsolete-exact-removal`, `08-obsolete-conflict-refuse`) | Exact hash remove; modified bytes → exit 11, file kept |
| 9 | Drift detection + deterministic repair | PASS (`09-drift-and-deterministic-repair`, `09-drift-mode-repair`) | Drift exit 10; blind overwrite refused; package-byte restore + update; mode repair; marker repair |
| 10 | Interrupted recovery + byte/mode rollback | PASS (`10-interrupted-recovery`, `10-byte-mode-rollback`) | Next `update` recovers; `rollback` restores exact bytes/modes |
| 11 | Extracted RC install without checkout | PASS (`11-extracted-rc-no-checkout-access`) | Temp extract bundles package + installer scripts; install/version from extract cwd |

Additional checks:

| Check | Result |
|---|---|
| Installer entrypoint present | PASS |
| Package fixture has no absolute checkout paths | PASS |
| No installed path escapes disposable consumer | PASS (post-install) |
| No absolute source-checkout path in installed files/state | PASS |
| Cursor + native Codex discovery from nested directories | PASS (scenarios 01, 07, 11) |

## Counts

| Suite | Passed | Failed | Skipped | Exit |
|---|---:|---:|---:|---:|
| `tests/cleanroom_acceptance/run_tests.py` | 16 | 0 | 0 | 0 |
| `tests/managed-core-migration-bb/run_tests.py --with-installer` | 40 | 0 | 0 | 0 |

## Owned paths touched

- `tests/cleanroom_acceptance/**` (new primary harness + extracted package fixture + this result)
- `tests/managed-core-migration-bb/**` — **not modified** (BB remained green without fixture changes)

## Gaps / dependencies

1. **Lane D RC archive not present yet.** Scenario 11 simulates an extracted release-candidate by copying the self-contained fixture and bundling `scripts/ide-development.py` + `scripts/ide_development/` into a disposable extract at runtime. When Lane D publishes an extract under one of the probed paths, the runner will prefer it automatically (`resolve_package_source`).
2. **Content-drift “repair” is operator-restore then update.** The installer correctly fail-closes (`exit 11`) on owned content drift away from both installed-state and package; deterministic repair proven by restoring package bytes then `update`/`verify`, plus automatic mode and marker repairs.
3. **Isolation is logical, not chroot.** Scenario 11 does not unmount the IDE Development checkout (impossible in this harness); it proves install uses only the extract entrypoint/package/cwd and that installed artifacts contain no absolute checkout paths.
4. **Fixture package is intentionally minimal** relative to full production managed-core payload (sample rule/skills + core files). It is sufficient for contract acceptance; full production manifest breadth belongs to packaging/unit suites and future Lane D RC contents.
5. **No production installer defects reproduced.** No stop-for-lead defect report required.

## Blockers

None for Lane B acceptance on this host. Remaining packet-level dependency: Lane D real RC extract for stronger “no checkout access” proof in CI/artifact form.
