# Old Patterns & Blacklist

## Deprecated Heuristics
- **Direct API by Default**: [Date Added]
  - **Reason**: Increases complexity and reduces portability.
  - **New Protocol**: Use CLI-first ordering and reserve APIs for explicit exceptions.

- **No Interface Contract**: [Date Added]
  - **Reason**: Breaks tool-calling reliability.
  - **New Protocol**: Require `interface.json` for every tool package.

- **No Capability Summary**: [Date Added]
  - **Reason**: JIT planning blind spots.
  - **New Protocol**: README must include a Capability Summary section.
