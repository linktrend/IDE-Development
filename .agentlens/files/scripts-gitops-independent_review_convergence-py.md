# scripts/gitops/independent_review_convergence.py

[← Back to Module](../modules/root/MODULE.md) | [← Back to INDEX](../INDEX.md)

## Overview

- **Lines:** 1212
- **Language:** Python
- **Symbols:** 70
- **Public symbols:** 60

## Symbol Table

| Line | Kind | Name | Visibility | Signature |
| ---- | ---- | ---- | ---------- | --------- |
| 75 | class | ConvergenceError | pub | `class ConvergenceError(ValueError):` |
| 78 | fn | __init__ | pub | `def __init__(self, code: str, detail: str) -> N...` |
| 83 | fn | to_dict | pub | `def to_dict(self) -> dict[str, str]:` |
| 87 | class | Clock | pub | `class Clock(Protocol):` |
| 88 | fn | now | pub | `def now(self) -> float: ...` |
| 91 | class | SystemClock | pub | `class SystemClock:` |
| 92 | fn | now | pub | `def now(self) -> float:` |
| 96 | class | ReviewerAdapter | pub | `class ReviewerAdapter(Protocol):` |
| 97 | fn | start | pub | `def start(self, session: "ReviewSession") -> "R...` |
| 99 | fn | cancel | pub | `def cancel(self, lease: "ReviewerLease") -> Non...` |
| 101 | fn | result | pub | `def result(self, lease: "ReviewerLease") -> Map...` |
| 105 | class | Finding | pub | `class Finding:` |
| 115 | fn | to_dict | pub | `def to_dict(self) -> dict[str, Any]:` |
| 129 | class | LedgerEntry | pub | `class LedgerEntry:` |
| 138 | fn | to_dict | pub | `def to_dict(self) -> dict[str, Any]:` |
| 153 | class | ReviewerLease | pub | `class ReviewerLease:` |
| 163 | class | RepairBatch | pub | `class RepairBatch:` |
| 171 | fn | to_dict | pub | `def to_dict(self) -> dict[str, Any]:` |
| 183 | class | ProgressDecision | pub | `class ProgressDecision:` |
| 190 | fn | to_dict | pub | `def to_dict(self) -> dict[str, Any]:` |
| 201 | class | ReviewSession | pub | `class ReviewSession:` |
| 243 | fn | to_dict | pub | `def to_dict(self) -> dict[str, Any]:` |
| 282 | fn | require_sha | pub | `def require_sha(value: str, label: str) -> str:` |
| 289 | fn | normalize_words | pub | `def normalize_words(text: str) -> list[str]:` |
| 293 | fn | token_jaccard | pub | `def token_jaccard(left: str, right: str) -> float:` |
| 301 | fn | normalize_paths | pub | `def normalize_paths(paths: Sequence[str]) -> li...` |
| 312 | fn | require_finding_paths | pub | `def require_finding_paths(paths: Any) -> list[s...` |
| 329 | fn | require_touched_paths | pub | `def require_touched_paths(paths: Any) -> list[s...` |
| 346 | fn | same_finding | pub | `def same_finding(left: Finding, right: Finding)...` |
| 368 | fn | severity_is_reduced | pub | `def severity_is_reduced(previous: str, current:...` |
| 372 | fn | parse_finding | pub | `def parse_finding(raw: Mapping[str, Any]) -> Fi...` |
| 397 | fn | ledger_to_dict | pub | `def ledger_to_dict(session: ReviewSession, entr...` |
| 408 | fn | find_entry | pub | `def find_entry(entries: Sequence[LedgerEntry], ...` |
| 415 | fn | blocking_unresolved | pub | `def blocking_unresolved(entries: Sequence[Ledge...` |
| 424 | fn | open_session | pub | `def open_session(` |
| 474 | fn | apply_repository_policy | pub | `def apply_repository_policy(session: ReviewSess...` |
| 486 | fn | record_founder_authority | pub | `def record_founder_authority(` |
| 513 | fn | _reset_infra_if_head_changed | (private) | `def _reset_infra_if_head_changed(session: Revie...` |
| 519 | fn | record_preflight | pub | `def record_preflight(` |
| 553 | fn | record_infrastructure_failure | pub | `def record_infrastructure_failure(` |
| 574 | fn | start_reviewer | pub | `def start_reviewer(` |
| 597 | fn | timeout_reviewer | pub | `def timeout_reviewer(` |
| 631 | fn | _require_reviewer_actor | (private) | `def _require_reviewer_actor(session: ReviewSess...` |
| 640 | fn | _hold_malformed | (private) | `def _hold_malformed(session: ReviewSession, det...` |
| 646 | fn | _require_bound_identity | (private) | `def _require_bound_identity(session: ReviewSess...` |
| 657 | fn | ingest_review | pub | `def ingest_review(` |
| 714 | fn | _classify_into_ledger | (private) | `def _classify_into_ledger(` |
| 777 | fn | consolidate_repair_batch | pub | `def consolidate_repair_batch(session: ReviewSes...` |
| 795 | fn | cancel_live_reviewer | pub | `def cancel_live_reviewer(` |
| 814 | fn | apply_repair | pub | `def apply_repair(` |
| 858 | fn | invalidate_evidence | pub | `def invalidate_evidence(session: ReviewSession)...` |
| 863 | fn | record_full_evidence | pub | `def record_full_evidence(session: ReviewSession...` |
| 880 | fn | _has_continue_until_clean | (private) | `def _has_continue_until_clean(session: ReviewSe...` |
| 885 | fn | _resource_exhausted | (private) | `def _resource_exhausted(session: ReviewSession,...` |
| 897 | fn | record_compute_units | pub | `def record_compute_units(` |
| 921 | fn | _stall | (private) | `def _stall(session: ReviewSession, reason: str)...` |
| 927 | fn | evaluate_progress | pub | `def evaluate_progress(` |
| 1007 | fn | authorize_split | pub | `def authorize_split(` |
| 1040 | fn | ingest_integration_review | pub | `def ingest_integration_review(` |
| 1061 | fn | founder_decision_packet | pub | `def founder_decision_packet(` |
| 1101 | fn | _proposed_decisions | (private) | `def _proposed_decisions(session: ReviewSession)...` |
| 1113 | fn | write_state | pub | `def write_state(state_dir: Path, session: Revie...` |
| 1130 | class | MemoryReviewer | pub | `class MemoryReviewer:` |
| 1133 | fn | __init__ | pub | `def __init__(self) -> None:` |
| 1139 | fn | queue | pub | `def queue(self, session_id: str, payload: Mappi...` |
| 1142 | fn | start | pub | `def start(self, session: ReviewSession) -> Revi...` |
| 1155 | fn | cancel | pub | `def cancel(self, lease: ReviewerLease) -> None:` |
| 1161 | fn | result | pub | `def result(self, lease: ReviewerLease) -> Mappi...` |
| 1165 | fn | _print_json | (private) | `def _print_json(payload: Mapping[str, Any]) -> ...` |
| 1170 | fn | main | pub | `def main(argv: list[str] | None = None) -> int:` |

## Public API

### `ConvergenceError`

```
class ConvergenceError(ValueError):
```

**Line:** 75 | **Kind:** class

### `__init__`

```
def __init__(self, code: str, detail: str) -> None:
```

**Line:** 78 | **Kind:** fn

### `to_dict`

```
def to_dict(self) -> dict[str, str]:
```

**Line:** 83 | **Kind:** fn

### `Clock`

```
class Clock(Protocol):
```

**Line:** 87 | **Kind:** class

### `now`

```
def now(self) -> float: ...
```

**Line:** 88 | **Kind:** fn

### `SystemClock`

```
class SystemClock:
```

**Line:** 91 | **Kind:** class

### `now`

```
def now(self) -> float:
```

**Line:** 92 | **Kind:** fn

### `ReviewerAdapter`

```
class ReviewerAdapter(Protocol):
```

**Line:** 96 | **Kind:** class

### `start`

```
def start(self, session: "ReviewSession") -> "ReviewerLease": ...
```

**Line:** 97 | **Kind:** fn

### `cancel`

```
def cancel(self, lease: "ReviewerLease") -> None: ...
```

**Line:** 99 | **Kind:** fn

### `result`

```
def result(self, lease: "ReviewerLease") -> Mapping[str, Any] | None: ...
```

**Line:** 101 | **Kind:** fn

### `Finding`

```
class Finding:
```

**Line:** 105 | **Kind:** class

### `to_dict`

```
def to_dict(self) -> dict[str, Any]:
```

**Line:** 115 | **Kind:** fn

### `LedgerEntry`

```
class LedgerEntry:
```

**Line:** 129 | **Kind:** class

### `to_dict`

```
def to_dict(self) -> dict[str, Any]:
```

**Line:** 138 | **Kind:** fn

### `ReviewerLease`

```
class ReviewerLease:
```

**Line:** 153 | **Kind:** class

### `RepairBatch`

```
class RepairBatch:
```

**Line:** 163 | **Kind:** class

### `to_dict`

```
def to_dict(self) -> dict[str, Any]:
```

**Line:** 171 | **Kind:** fn

### `ProgressDecision`

```
class ProgressDecision:
```

**Line:** 183 | **Kind:** class

### `to_dict`

```
def to_dict(self) -> dict[str, Any]:
```

**Line:** 190 | **Kind:** fn

### `ReviewSession`

```
class ReviewSession:
```

**Line:** 201 | **Kind:** class

### `to_dict`

```
def to_dict(self) -> dict[str, Any]:
```

**Line:** 243 | **Kind:** fn

### `require_sha`

```
def require_sha(value: str, label: str) -> str:
```

**Line:** 282 | **Kind:** fn

### `normalize_words`

```
def normalize_words(text: str) -> list[str]:
```

**Line:** 289 | **Kind:** fn

### `token_jaccard`

```
def token_jaccard(left: str, right: str) -> float:
```

**Line:** 293 | **Kind:** fn

### `normalize_paths`

```
def normalize_paths(paths: Sequence[str]) -> list[str]:
```

**Line:** 301 | **Kind:** fn

### `require_finding_paths`

```
def require_finding_paths(paths: Any) -> list[str]:
```

**Line:** 312 | **Kind:** fn

### `require_touched_paths`

```
def require_touched_paths(paths: Any) -> list[str]:
```

**Line:** 329 | **Kind:** fn

### `same_finding`

```
def same_finding(left: Finding, right: Finding) -> bool:
```

**Line:** 346 | **Kind:** fn

### `severity_is_reduced`

```
def severity_is_reduced(previous: str, current: str) -> bool:
```

**Line:** 368 | **Kind:** fn

### `parse_finding`

```
def parse_finding(raw: Mapping[str, Any]) -> Finding:
```

**Line:** 372 | **Kind:** fn

### `ledger_to_dict`

```
def ledger_to_dict(session: ReviewSession, entries: Sequence[LedgerEntry]) -> dict[str, Any]:
```

**Line:** 397 | **Kind:** fn

### `find_entry`

```
def find_entry(entries: Sequence[LedgerEntry], finding: Finding) -> LedgerEntry | None:
```

**Line:** 408 | **Kind:** fn

### `blocking_unresolved`

```
def blocking_unresolved(entries: Sequence[LedgerEntry]) -> list[LedgerEntry]:
```

**Line:** 415 | **Kind:** fn

### `open_session`

```
def open_session(
```

**Line:** 424 | **Kind:** fn

### `apply_repository_policy`

```
def apply_repository_policy(session: ReviewSession, policy: Mapping[str, Any]) -> None:
```

**Line:** 474 | **Kind:** fn

### `record_founder_authority`

```
def record_founder_authority(
```

**Line:** 486 | **Kind:** fn

### `record_preflight`

```
def record_preflight(
```

**Line:** 519 | **Kind:** fn

### `record_infrastructure_failure`

```
def record_infrastructure_failure(
```

**Line:** 553 | **Kind:** fn

### `start_reviewer`

```
def start_reviewer(
```

**Line:** 574 | **Kind:** fn

### `timeout_reviewer`

```
def timeout_reviewer(
```

**Line:** 597 | **Kind:** fn

### `ingest_review`

```
def ingest_review(
```

**Line:** 657 | **Kind:** fn

### `consolidate_repair_batch`

```
def consolidate_repair_batch(session: ReviewSession, entries: Sequence[LedgerEntry]) -> RepairBatch:
```

**Line:** 777 | **Kind:** fn

### `cancel_live_reviewer`

```
def cancel_live_reviewer(
```

**Line:** 795 | **Kind:** fn

### `apply_repair`

```
def apply_repair(
```

**Line:** 814 | **Kind:** fn

### `invalidate_evidence`

```
def invalidate_evidence(session: ReviewSession) -> None:
```

**Line:** 858 | **Kind:** fn

### `record_full_evidence`

```
def record_full_evidence(session: ReviewSession, *, head_sha: str) -> None:
```

**Line:** 863 | **Kind:** fn

### `record_compute_units`

```
def record_compute_units(
```

**Line:** 897 | **Kind:** fn

### `evaluate_progress`

```
def evaluate_progress(
```

**Line:** 927 | **Kind:** fn

### `authorize_split`

```
def authorize_split(
```

**Line:** 1007 | **Kind:** fn

### `ingest_integration_review`

```
def ingest_integration_review(
```

**Line:** 1040 | **Kind:** fn

### `founder_decision_packet`

```
def founder_decision_packet(
```

**Line:** 1061 | **Kind:** fn

### `write_state`

```
def write_state(state_dir: Path, session: ReviewSession, entries: Sequence[LedgerEntry], clock: Clock | None = None) -> None:
```

**Line:** 1113 | **Kind:** fn

### `MemoryReviewer`

```
class MemoryReviewer:
```

**Line:** 1130 | **Kind:** class

### `__init__`

```
def __init__(self) -> None:
```

**Line:** 1133 | **Kind:** fn

### `queue`

```
def queue(self, session_id: str, payload: Mapping[str, Any]) -> None:
```

**Line:** 1139 | **Kind:** fn

### `start`

```
def start(self, session: ReviewSession) -> ReviewerLease:
```

**Line:** 1142 | **Kind:** fn

### `cancel`

```
def cancel(self, lease: ReviewerLease) -> None:
```

**Line:** 1155 | **Kind:** fn

### `result`

```
def result(self, lease: ReviewerLease) -> Mapping[str, Any] | None:
```

**Line:** 1161 | **Kind:** fn

### `main`

```
def main(argv: list[str] | None = None) -> int:
```

**Line:** 1170 | **Kind:** fn
