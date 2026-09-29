# Old Patterns & Blacklist

## Deprecated Heuristics
- Approving releases without independent QA evidence.
  - Reason: high false-positive quality signal.
  - Replacement: evidence-backed verdict protocol.

## Known Failure Modes
- Failing to persist recurring bugs across sessions.
  - Resolution: mandatory BUG_HISTORY append in Phase 4.
