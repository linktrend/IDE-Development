# PKT-08 phase/release integration evidence

## Exact source identity

- Requested Phase head: `28e81c28181445e092969ce91b09fe7fa7710f38`
- Requested Phase tree: `3ebe4ac27843077ebe96d8899f185d7de4ff0c67`
- Reconciled package source checkpoint: `a650ce1bcb194eff94790bc7f0480453f1bfd416`
- Reconciled package source tree: `a456ad1263680ab293697cdf84a74cd95e259633`
- Artifact source checkpoint: `a650ce1bcb194eff94790bc7f0480453f1bfd416`
- Managed package: `2.4.0`
- Manifest SHA-256: `sha256:4bdf6ffcf4a34c37b7fe9ee11732cb1c23140b39bdb2542b4961097fdcc09f7c`

The branch contains the exact Phase head as the first parent of the deliberate
reconciliation commit `9017683`. PKT-08 bounded repairs were retained; stale
pre-PKT-01 release evidence was replaced. The package source checkpoint
precedes this evidence-only commit.

## Tree-bound verification

Executed from `/workspace`:

```text
python3 -m unittest \
  tests.execution_protocol.test_canonical_manifest \
  tests.execution_protocol.test_continuous_utilization \
  tests.execution_protocol.test_lifecycle \
  tests.execution_protocol.test_protocol
```

Result: **83 tests passed**. The cleanroom test imported the scheduler from an
extracted package tree, not from the IDE checkout.

Additional checks:

- `python3 -m scripts.ide_development.build_manifest --verify`: passed;
- fixture-aware secret scan: passed, 42 approved synthetic findings, 0 blocking;
- `git diff --check`: passed;
- no Fast, paid, legacy publisher, protected-branch merge, staging promotion, or
  main promotion was run.

## Extracted package proof

Built from clean cwd `/tmp/pkt08-phase-release` at the artifact source
checkpoint. The release-candidate command completed with reproducibility and
disposable install verification:

```text
python3 scripts/ide-development.py release-candidate create --json --skip-evidence
```

The tar archive was extracted into a fresh temporary directory with no IDE
checkout on `PYTHONPATH`. It contained the scheduler runtime and its lifecycle
and protocol dependencies, continuous-utilization config, schema, example, and
hosted-capacity doctrine. JSON Schema validation passed, the extracted runtime
admitted a hosted work item, and no source file contained the release checkout
path.

Archive receipts:

| Format | Bytes | SHA-256 |
|---|---:|---|
| tar.gz | 549699 | `sha256:8e2a71fc7d4d6819c222ed67234c1e05ba284482fd690882cc8e382b696e77e4` |
| zip | 670618 | `sha256:039bd7e28823fd97d7a129c5fa977546598c22a6b9e870f103525c5474206c08` |

Machine-readable metadata:

- `release-candidate-2.4.0.json`;
- `managed-core-release-2.4.0.json`;
- ignored `build/release-candidate/release-candidate.json`;
- ignored `build/release-candidate/SHA256SUMS.json`.

## Governance boundary

Draft Phase PR [#343](https://github.com/linktrend/IDE-Development/pull/343) was
not merged or modified. No tag, GitHub Release, protected-branch merge,
staging promotion, or main promotion was performed. `v2.4.0` remains a pending
governed publication, not a live release claim.
