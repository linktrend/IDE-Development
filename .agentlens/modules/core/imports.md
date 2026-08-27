# Imports

[← Back to MODULE](MODULE.md) | [← Back to INDEX](../../INDEX.md)

## Dependency Graph

```mermaid
graph TD
    core[core] --> link_integrations[link-integrations]
    core[core] --> link_integrations[link-integrations]
    core[core] --> codex[codex]
    core[core] --> dependencies[dependencies]
    core[core] --> __[..]
    core[core] --> dependencies[dependencies]
    core[core] --> node_assert[node:assert]
    core[core] --> node_child_process[node:child_process]
    core[core] --> node_crypto[node:crypto]
    core[core] --> node_fs[node:fs]
    core[core] --> node_os[node:os]
    core[core] --> node_path[node:path]
    core[core] --> node_test[node:test]
    core[core] --> node_url[node:url]
```

## External Dependencies

Dependencies from other modules:

- `../../../link-integrations/errors.mjs`
- `../../../link-integrations/skills-loader.mjs`
- `../codex/adapter.mjs`
- `../dependencies/spdx-expression-validate.mjs`
- `../library-client.mjs`
- `./dependencies/spdx-expression-validate.mjs`
- `node:assert/strict`
- `node:child_process`
- `node:crypto`
- `node:fs`
- `node:os`
- `node:path`
- `node:test`
- `node:url`
