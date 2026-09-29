# Example Trace: Error Recovery

## Scenario
Memory retrieval fails during BUG_HISTORY lookup.

## Recovery
- Skill records transient retrieval error and retries once.
- If still unavailable, proceeds with local audit and flags history sync as pending.
- Writes checkpoint for later recovery and prevents silent data loss.
