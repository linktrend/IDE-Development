# Advanced Execution Logic

## Complex Cases
- Multi-step APIs with pagination: wrap pagination flags in CLI and provide deterministic JSON output.
- Streaming APIs: allowed as direct API exception when low-latency streaming is required.
- High-serialization DB queries: allowed as direct API exception when wrapper overhead is prohibitive.

## JIT Notes
- Activate JIT planning only for Generalist or >10-tool ecosystems.
- Cache `get_tool_details` responses in task-local state for reuse.
