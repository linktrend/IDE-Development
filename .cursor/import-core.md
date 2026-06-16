# Import Core

The canonical knowledge asset now lives under `core/`.

The `.cursor/` directory remains as a compatibility runtime surface for existing consumers, bootstrap rules, path-based references, and tool integrations that expect `.cursor/...`.

Packaging model:

- `core/` contains the portable knowledge asset
- `.cursor/` retains Cursor-specific files such as `rules/` and `mcp.json`
- the remaining `.cursor/...` paths resolve into `core/` through adapter links

Operational rule:

- preserve `.cursor/...` compatibility
- preserve existing command surfaces
- preserve existing doctrine and path semantics
- use `core/` as the canonical storage location for portable knowledge going forward

Do not treat this file as new doctrine. It is packaging guidance only.
