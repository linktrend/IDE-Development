# scripts/gitops/coordinator/state.py

[← Back to Module](../modules/scripts-gitops-coordinator/MODULE.md) | [← Back to INDEX](../INDEX.md)

## Overview

- **Lines:** 1078
- **Language:** Python
- **Symbols:** 71
- **Public symbols:** 54

## Symbol Table

| Line | Kind | Name | Visibility | Signature |
| ---- | ---- | ---- | ---------- | --------- |
| 46 | class | StateError | pub | `class StateError(ValueError):` |
| 49 | fn | __init__ | pub | `def __init__(self, code: str, detail: str) -> N...` |
| 54 | fn | to_dict | pub | `def to_dict(self) -> dict[str, str]:` |
| 58 | fn | _sha | (private) | `def _sha(value: Any, *, field_name: str) -> str:` |
| 65 | class | CandidateIdentity | pub | `class CandidateIdentity:` |
| 72 | fn | __post_init__ | pub | `def __post_init__(self) -> None:` |
| 87 | fn | to_dict | pub | `def to_dict(self) -> dict[str, Any]:` |
| 97 | fn | from_dict | pub | `def from_dict(cls, payload: Mapping[str, Any]) ...` |
| 106 | fn | canonical | pub | `def canonical(self) -> str:` |
| 110 | fn | _git | (private) | `def _git(repo: Path, *args: str) -> str:` |
| 117 | fn | _repository_name | (private) | `def _repository_name(repo: Path) -> str:` |
| 130 | fn | _safe_dependency | (private) | `def _safe_dependency(repo: Path, raw: str) -> t...` |
| 143 | fn | compute_candidate_identity | pub | `def compute_candidate_identity(repo_path: str |...` |
| 158 | class | DeliveryState | pub | `class DeliveryState:` |
| 174 | fn | __post_init__ | pub | `def __post_init__(self) -> None:` |
| 184 | fn | state_id | pub | `def state_id(self) -> str:` |
| 188 | fn | new | pub | `def new(cls, repository: str, phase_branch: str...` |
| 191 | fn | to_dict | pub | `def to_dict(self) -> dict[str, Any]:` |
| 212 | fn | from_dict | pub | `def from_dict(cls, payload: Mapping[str, Any]) ...` |
| 229 | fn | _event_parts | (private) | `def _event_parts(event: str | Mapping[str, Any]...` |
| 240 | fn | _assert_event_identity | (private) | `def _assert_event_identity(state: DeliveryState...` |
| 256 | fn | _record_gate | (private) | `def _record_gate(state: DeliveryState, gate: st...` |
| 266 | fn | transition | pub | `def transition(state: DeliveryState, event: str...` |
| 385 | fn | _state_path | (private) | `def _state_path(state_id: str | os.PathLike[str...` |
| 389 | fn | save_state | pub | `def save_state(state: DeliveryState, state_id: ...` |
| 411 | fn | load_state | pub | `def load_state(state_id: str | os.PathLike[str]...` |
| 458 | fn | _p2_text | (private) | `def _p2_text(value: Any, field_name: str) -> str:` |
| 465 | class | PhaseCandidateIdentity | pub | `class PhaseCandidateIdentity:` |
| 476 | fn | __post_init__ | pub | `def __post_init__(self) -> None:` |
| 489 | fn | to_dict | pub | `def to_dict(self) -> dict[str, str]:` |
| 501 | fn | from_dict | pub | `def from_dict(cls, payload: Mapping[str, Any]) ...` |
| 515 | fn | canonical | pub | `def canonical(self) -> str:` |
| 520 | class | CandidateSeal | pub | `class CandidateSeal:` |
| 529 | fn | __post_init__ | pub | `def __post_init__(self) -> None:` |
| 540 | fn | candidate_id | pub | `def candidate_id(self) -> str:` |
| 550 | fn | concurrency_key | pub | `def concurrency_key(self, workflow: str) -> str:` |
| 553 | fn | to_dict | pub | `def to_dict(self) -> dict[str, Any]:` |
| 564 | fn | from_dict | pub | `def from_dict(cls, payload: Mapping[str, Any]) ...` |
| 582 | class | CandidateRecord | pub | `class CandidateRecord:` |
| 590 | fn | __post_init__ | pub | `def __post_init__(self) -> None:` |
| 601 | fn | candidate_id | pub | `def candidate_id(self) -> str:` |
| 604 | fn | to_dict | pub | `def to_dict(self) -> dict[str, Any]:` |
| 615 | fn | from_dict | pub | `def from_dict(cls, payload: Mapping[str, Any]) ...` |
| 630 | class | CandidateLifecycleState | pub | `class CandidateLifecycleState:` |
| 642 | fn | __post_init__ | pub | `def __post_init__(self) -> None:` |
| 660 | fn | new | pub | `def new(cls, repository: str, phase_id: str, ph...` |
| 663 | fn | to_dict | pub | `def to_dict(self) -> dict[str, Any]:` |
| 679 | fn | from_dict | pub | `def from_dict(cls, payload: Mapping[str, Any]) ...` |
| 693 | class | LifecycleOutcome | pub | `class LifecycleOutcome:` |
| 702 | fn | outcome_code | pub | `def outcome_code(self) -> str:` |
| 705 | fn | to_dict | pub | `def to_dict(self) -> dict[str, Any]:` |
| 713 | fn | concurrency_key | pub | `def concurrency_key(repository: str, workflow: ...` |
| 724 | fn | _p2_event_name | (private) | `def _p2_event_name(event: Mapping[str, Any]) ->...` |
| 731 | fn | _p2_event_id | (private) | `def _p2_event_id(event: Mapping[str, Any]) -> str:` |
| 739 | fn | _p2_candidate | (private) | `def _p2_candidate(state: CandidateLifecycleStat...` |
| 746 | fn | _p2_replace_candidate | (private) | `def _p2_replace_candidate(state: CandidateLifec...` |
| 752 | fn | _p2_supersede_for_pr | (private) | `def _p2_supersede_for_pr(state: CandidateLifecy...` |
| 765 | fn | _p2_invalidate_older_candidates | (private) | `def _p2_invalidate_older_candidates(state: Cand...` |
| 788 | fn | _p2_assert_event_identity | (private) | `def _p2_assert_event_identity(state: CandidateL...` |
| 803 | class | CandidateLifecycle | pub | `class CandidateLifecycle:` |
| 806 | fn | __init__ | pub | `def __init__(self, state: CandidateLifecycleSta...` |
| 810 | fn | new | pub | `def new(cls, repository: str, phase_id: str, ph...` |
| 814 | fn | from_dict | pub | `def from_dict(cls, payload: Mapping[str, Any]) ...` |
| 817 | fn | to_dict | pub | `def to_dict(self) -> dict[str, Any]:` |
| 820 | fn | _outcome | (private) | `def _outcome(self, code: str, *, candidate_id: ...` |
| 823 | fn | apply | pub | `def apply(self, event: Mapping[str, Any]) -> Li...` |
| 1016 | class | CandidateLifecycleStore | pub | `class CandidateLifecycleStore:` |
| 1019 | fn | __init__ | pub | `def __init__(self, path: str | os.PathLike[str]):` |
| 1023 | fn | load | pub | `def load(self) -> CandidateLifecycle:` |
| 1034 | fn | save | pub | `def save(self, lifecycle: CandidateLifecycle) -...` |
| 1062 | fn | apply | pub | `def apply(self, event: Mapping[str, Any]) -> Li...` |

## Public API

### `StateError`

```
class StateError(ValueError):
```

**Line:** 46 | **Kind:** class

### `__init__`

```
def __init__(self, code: str, detail: str) -> None:
```

**Line:** 49 | **Kind:** fn

### `to_dict`

```
def to_dict(self) -> dict[str, str]:
```

**Line:** 54 | **Kind:** fn

### `CandidateIdentity`

```
class CandidateIdentity:
```

**Line:** 65 | **Kind:** class

### `__post_init__`

```
def __post_init__(self) -> None:
```

**Line:** 72 | **Kind:** fn

### `to_dict`

```
def to_dict(self) -> dict[str, Any]:
```

**Line:** 87 | **Kind:** fn

### `from_dict`

```
def from_dict(cls, payload: Mapping[str, Any]) -> "CandidateIdentity":
```

**Line:** 97 | **Kind:** fn

### `canonical`

```
def canonical(self) -> str:
```

**Line:** 106 | **Kind:** fn

### `compute_candidate_identity`

```
def compute_candidate_identity(repo_path: str | os.PathLike[str], dependency_files: list[str] | tuple[str, ...]) -> CandidateIdentity:
```

**Line:** 143 | **Kind:** fn

### `DeliveryState`

```
class DeliveryState:
```

**Line:** 158 | **Kind:** class

### `__post_init__`

```
def __post_init__(self) -> None:
```

**Line:** 174 | **Kind:** fn

### `state_id`

```
def state_id(self) -> str:
```

**Line:** 184 | **Kind:** fn

### `new`

```
def new(cls, repository: str, phase_branch: str, phase_id: str, immutable_base_sha: str) -> "DeliveryState":
```

**Line:** 188 | **Kind:** fn

### `to_dict`

```
def to_dict(self) -> dict[str, Any]:
```

**Line:** 191 | **Kind:** fn

### `from_dict`

```
def from_dict(cls, payload: Mapping[str, Any]) -> "DeliveryState":
```

**Line:** 212 | **Kind:** fn

### `transition`

```
def transition(state: DeliveryState, event: str | Mapping[str, Any]) -> DeliveryState:
```

**Line:** 266 | **Kind:** fn

### `save_state`

```
def save_state(state: DeliveryState, state_id: str | os.PathLike[str]) -> Path:
```

**Line:** 389 | **Kind:** fn

### `load_state`

```
def load_state(state_id: str | os.PathLike[str]) -> DeliveryState | None:
```

**Line:** 411 | **Kind:** fn

### `PhaseCandidateIdentity`

```
class PhaseCandidateIdentity:
```

**Line:** 465 | **Kind:** class

### `__post_init__`

```
def __post_init__(self) -> None:
```

**Line:** 476 | **Kind:** fn

### `to_dict`

```
def to_dict(self) -> dict[str, str]:
```

**Line:** 489 | **Kind:** fn

### `from_dict`

```
def from_dict(cls, payload: Mapping[str, Any]) -> "PhaseCandidateIdentity":
```

**Line:** 501 | **Kind:** fn

### `canonical`

```
def canonical(self) -> str:
```

**Line:** 515 | **Kind:** fn

### `CandidateSeal`

```
class CandidateSeal:
```

**Line:** 520 | **Kind:** class

### `__post_init__`

```
def __post_init__(self) -> None:
```

**Line:** 529 | **Kind:** fn

### `candidate_id`

```
def candidate_id(self) -> str:
```

**Line:** 540 | **Kind:** fn

### `concurrency_key`

```
def concurrency_key(self, workflow: str) -> str:
```

**Line:** 550 | **Kind:** fn

### `to_dict`

```
def to_dict(self) -> dict[str, Any]:
```

**Line:** 553 | **Kind:** fn

### `from_dict`

```
def from_dict(cls, payload: Mapping[str, Any]) -> "CandidateSeal":
```

**Line:** 564 | **Kind:** fn

### `CandidateRecord`

```
class CandidateRecord:
```

**Line:** 582 | **Kind:** class

### `__post_init__`

```
def __post_init__(self) -> None:
```

**Line:** 590 | **Kind:** fn

### `candidate_id`

```
def candidate_id(self) -> str:
```

**Line:** 601 | **Kind:** fn

### `to_dict`

```
def to_dict(self) -> dict[str, Any]:
```

**Line:** 604 | **Kind:** fn

### `from_dict`

```
def from_dict(cls, payload: Mapping[str, Any]) -> "CandidateRecord":
```

**Line:** 615 | **Kind:** fn

### `CandidateLifecycleState`

```
class CandidateLifecycleState:
```

**Line:** 630 | **Kind:** class

### `__post_init__`

```
def __post_init__(self) -> None:
```

**Line:** 642 | **Kind:** fn

### `new`

```
def new(cls, repository: str, phase_id: str, phase_branch: str, immutable_base_sha: str) -> "CandidateLifecycleState":
```

**Line:** 660 | **Kind:** fn

### `to_dict`

```
def to_dict(self) -> dict[str, Any]:
```

**Line:** 663 | **Kind:** fn

### `from_dict`

```
def from_dict(cls, payload: Mapping[str, Any]) -> "CandidateLifecycleState":
```

**Line:** 679 | **Kind:** fn

### `LifecycleOutcome`

```
class LifecycleOutcome:
```

**Line:** 693 | **Kind:** class

### `outcome_code`

```
def outcome_code(self) -> str:
```

**Line:** 702 | **Kind:** fn

### `to_dict`

```
def to_dict(self) -> dict[str, Any]:
```

**Line:** 705 | **Kind:** fn

### `concurrency_key`

```
def concurrency_key(repository: str, workflow: str, pr_number: int) -> str:
```

**Line:** 713 | **Kind:** fn

### `CandidateLifecycle`

```
class CandidateLifecycle:
```

**Line:** 803 | **Kind:** class

### `__init__`

```
def __init__(self, state: CandidateLifecycleState):
```

**Line:** 806 | **Kind:** fn

### `new`

```
def new(cls, repository: str, phase_id: str, phase_branch: str, immutable_base_sha: str) -> "CandidateLifecycle":
```

**Line:** 810 | **Kind:** fn

### `from_dict`

```
def from_dict(cls, payload: Mapping[str, Any]) -> "CandidateLifecycle":
```

**Line:** 814 | **Kind:** fn

### `to_dict`

```
def to_dict(self) -> dict[str, Any]:
```

**Line:** 817 | **Kind:** fn

### `apply`

```
def apply(self, event: Mapping[str, Any]) -> LifecycleOutcome:
```

**Line:** 823 | **Kind:** fn

### `CandidateLifecycleStore`

```
class CandidateLifecycleStore:
```

**Line:** 1016 | **Kind:** class

### `__init__`

```
def __init__(self, path: str | os.PathLike[str]):
```

**Line:** 1019 | **Kind:** fn

### `load`

```
def load(self) -> CandidateLifecycle:
```

**Line:** 1023 | **Kind:** fn

### `save`

```
def save(self, lifecycle: CandidateLifecycle) -> Path:
```

**Line:** 1034 | **Kind:** fn

### `apply`

```
def apply(self, event: Mapping[str, Any]) -> LifecycleOutcome:
```

**Line:** 1062 | **Kind:** fn
