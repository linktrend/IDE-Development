# PKT-08 phase/release integration evidence

## Candidate identity

- Requested phase head: `f7fae3b09ce4d3196a6967b60f8422779ff82a13`
- Requested phase tree: `5d8016dfee4c27d6b63aa601d4ca4748a29fdb47`
- Governed repair checkpoint: `b5cf7d08fb17e4deceec235cf99aa56350ab5196`
- Artifact source checkpoint: `5d3adc78e12bf62d1c48052d90b8c46a56a27895`
- Managed package: `2.4.0`
- Manifest SHA-256: `sha256:dcac9d44a1867a8627501e8385a4c385db8c6d29d4ad213d315d421a6785c3c4`

The requested phase checkout was kept isolated. Its proof checkout carried only
the bounded PKT-08 repairs needed to make the phase checks executable and
reproducible: CI `jsonschema` installation, synthetic secret-fixture
declarations, V25 completion/waiver behavior, portable-version assertions, and
the manifest refresh.

## Exact phase verification

Run from the isolated proof checkout at
`/tmp/ide-development-pkt08-f7fae3b`, whose base is the requested phase
commit and whose index contains only the bounded PKT-08 proof repairs:

```text
cd /tmp/ide-development-pkt08-f7fae3b
GIT_CONFIG_COUNT=2 \
GIT_CONFIG_KEY_0=core.hooksPath \
GIT_CONFIG_VALUE_0=/dev/null \
GIT_CONFIG_KEY_1=commit.gpgsign \
GIT_CONFIG_VALUE_1=false \
bash scripts/verify-ide-development.sh
cd /tmp/ide-development-pkt08-f7fae3b
GIT_CONFIG_COUNT=2 \
GIT_CONFIG_KEY_0=core.hooksPath \
GIT_CONFIG_VALUE_0=/dev/null \
GIT_CONFIG_KEY_1=commit.gpgsign \
GIT_CONFIG_VALUE_1=false \
bash tests/test-portable-v2-integration.sh --full
```

Both commands exited `0`.

The two Git config overrides disabled only the machine-inherited Cursor hook and
SSH commit signing for synthetic temporary repositories. They were restored
after verification. The required checks included:

- Stage 1 verification: all checks passed;
- fast profile and full profile inventory: passed;
- secret scan: passed with no unapproved findings;
- GitOps behavioral suite: 22 groups passed;
- lifecycle suite: passed;
- portable v2 full harness: all checks passed;
- `git diff --check`: passed.

These are local exact-checkout results, not hosted CI, protected-branch, or
production proof.

## Phase and review boundary

Draft Phase PR [#343](https://github.com/linktrend/IDE-Development/pull/343)
remains open, draft, based on `development`, with head
`phase/v2.5@f7fae3b09ce4d3196a6967b60f8422779ff82a13`.

V25 `V25_BOOTSTRAP_LEAN` is preserved. Review Ready is a waived legacy gate,
not a success status and not a merge trigger. The independent exact-head review
receipt must be attached by the Phase Integrator; no implementer self-review is
claimed here. Conditional Full remains governed by the exact final Phase head.

## Release artifact boundary

The official release-candidate CLI was run from a clean alternate checkout of
`5d3adc78e12bf62d1c48052d90b8c46a56a27895`. It produced reproducible tar.gz
and zip archives, passed disposable install verification, and wrote the
machine-readable metadata in:

- `release-candidate-2.4.0.json`;
- `managed-core-release-2.4.0.json`;
- ignored `build/release-candidate/release-candidate.json`;
- ignored `build/release-candidate/SHA256SUMS.json`.

Archive receipts:

| Format | Bytes | SHA-256 |
|---|---:|---|
| tar.gz | 533734 | `sha256:e133bdb396c73edfd0efe67b42a621f978ea90fe1594b52f3eb7fc1e812ce19e` |
| zip | 649919 | `sha256:b47f6f0885b30c35df7a3239a2658a1ee3087c4d1f9fe9a0227398c09ffed4f2` |

No tag, GitHub Release, protected-branch merge, staging promotion, or main
promotion was performed. `v2.4.0` is therefore a pending governed publication,
not a claim that a live release exists.
