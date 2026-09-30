# Example Trace: Error Recovery

## Scenario
Wrapper fails validation because `--json` output is malformed.

## Recovery
- Fix output serializer in `bin/` wrapper.
- Re-run tests in `test/`.
- Append failure/recovery note to old-patterns.
