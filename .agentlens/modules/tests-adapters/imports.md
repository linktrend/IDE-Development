# Imports

[← Back to MODULE](MODULE.md) | [← Back to INDEX](../../INDEX.md)

## Dependency Graph

```mermaid
graph TD
    tests_adapters[tests-adapters] --> link_integrations[link-integrations]
    tests_adapters[tests-adapters] --> codex[codex]
    tests_adapters[tests-adapters] --> cursor[cursor]
    tests_adapters[tests-adapters] --> __future__[__future__]
    tests_adapters[tests-adapters] --> json[json]
    tests_adapters[tests-adapters] --> node_assert[node:assert]
    tests_adapters[tests-adapters] --> node_test[node:test]
    tests_adapters[tests-adapters] --> pathlib[pathlib]
    tests_adapters[tests-adapters] --> shutil[shutil]
    tests_adapters[tests-adapters] --> tempfile[tempfile]
    tests_adapters[tests-adapters] --> unittest[unittest]
```

## Internal Dependencies

Dependencies within this module:

- `re`

## External Dependencies

Dependencies from other modules:

- `../../core/link-integrations/errors.mjs`
- `../../core/managed-core/platforms/codex/adapter.mjs`
- `../../core/managed-core/platforms/cursor/adapter.mjs`
- `__future__`
- `json`
- `node:assert/strict`
- `node:test`
- `pathlib`
- `shutil`
- `tempfile`
- `unittest`
