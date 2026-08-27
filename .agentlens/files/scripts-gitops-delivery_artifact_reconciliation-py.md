# scripts/gitops/delivery_artifact_reconciliation.py

[← Back to Module](../modules/root/MODULE.md) | [← Back to INDEX](../INDEX.md)

## Overview

- **Lines:** 1104
- **Language:** Python
- **Symbols:** 53
- **Public symbols:** 24

## Symbol Table

| Line | Kind | Name | Visibility | Signature |
| ---- | ---- | ---- | ---------- | --------- |
| 83 | class | ReconciliationError | pub | `class ReconciliationError(Exception):` |
| 86 | fn | __init__ | pub | `def __init__(self, code: str, detail: str) -> N...` |
| 92 | class | IdentityUncertainty | pub | `class IdentityUncertainty(ReconciliationError):` |
| 96 | class | InfrastructureError | pub | `class InfrastructureError(ReconciliationError):` |
| 101 | class | Artifact | pub | `class Artifact:` |
| 125 | fn | __post_init__ | pub | `def __post_init__(self) -> None:` |
| 135 | class | Classification | pub | `class Classification:` |
| 142 | class | Decision | pub | `class Decision:` |
| 151 | fn | _valid_sha | (private) | `def _valid_sha(value: str | None) -> bool:` |
| 155 | fn | _is_protected | (private) | `def _is_protected(name: str) -> bool:` |
| 164 | fn | _git_at | (private) | `def _git_at(path: Path, *args: str) -> subproce...` |
| 173 | fn | _rev_parse | (private) | `def _rev_parse(path: Path, spec: str) -> str | ...` |
| 181 | fn | _git_common_dir | (private) | `def _git_common_dir(path: Path) -> Path | None:` |
| 195 | fn | _safe_branch_name | (private) | `def _safe_branch_name(repo: Path, name: str) ->...` |
| 202 | fn | _load_trusted_owned_refs | (private) | `def _load_trusted_owned_refs(state_dir: Path) -...` |
| 221 | fn | _derive_owner | (private) | `def _derive_owner(name: str, trusted: frozenset...` |
| 231 | fn | _require_live_controller_ref | (private) | `def _require_live_controller_ref(repo: Path, na...` |
| 240 | fn | _same_git_common_dir | (private) | `def _same_git_common_dir(repo: Path, path: Path...` |
| 246 | fn | _lineage_allows_clean | (private) | `def _lineage_allows_clean(repo: Path, head: str...` |
| 264 | fn | _list_worktrees | (private) | `def _list_worktrees(repo: Path) -> list[dict[st...` |
| 272 | fn | flush | pub | `def flush() -> None:` |
| 310 | fn | _worktree_dirty | (private) | `def _worktree_dirty(path: Path) -> bool:` |
| 317 | fn | _integration_ref | (private) | `def _integration_ref(repo: Path) -> str | None:` |
| 324 | fn | _collect_integrated_trees | (private) | `def _collect_integrated_trees(repo: Path, integ...` |
| 338 | fn | _diff_names | (private) | `def _diff_names(repo: Path, base: str, head: st...` |
| 345 | fn | _commits_ahead | (private) | `def _commits_ahead(repo: Path, base: str, head:...` |
| 353 | fn | _local_branch_sha | (private) | `def _local_branch_sha(repo: Path, name: str) ->...` |
| 359 | fn | _is_tag_only | (private) | `def _is_tag_only(repo: Path, name: str) -> bool:` |
| 365 | fn | _unverified | (private) | `def _unverified(artifact: Artifact, **overrides...` |
| 381 | fn | _materialize_ref | (private) | `def _materialize_ref(` |
| 460 | fn | _materialize_worktree | (private) | `def _materialize_worktree(repo: Path, artifact:...` |
| 533 | fn | materialize_artifact | pub | `def materialize_artifact(repo: Path, artifact: ...` |
| 557 | fn | resolve_state_dir | pub | `def resolve_state_dir(repo: Path, override: str...` |
| 567 | fn | ensure_state_dir | pub | `def ensure_state_dir(state_dir: Path) -> Path:` |
| 572 | fn | write_json | pub | `def write_json(path: Path, payload: Mapping[str...` |
| 578 | fn | inventory_root_residue | pub | `def inventory_root_residue(repo: Path) -> list[...` |
| 599 | fn | _move_root_residue_to_state | (private) | `def _move_root_residue_to_state(repo: Path, sta...` |
| 613 | fn | _delete_root_residue | (private) | `def _delete_root_residue(repo: Path) -> list[str]:` |
| 623 | fn | _clear_transients | (private) | `def _clear_transients(state_dir: Path) -> None:` |
| 628 | fn | finish_success | pub | `def finish_success(state_dir: Path, report: Map...` |
| 635 | fn | finish_failure | pub | `def finish_failure(state_dir: Path, report: Map...` |
| 642 | fn | classify_artifact | pub | `def classify_artifact(artifact: Artifact) -> Cl...` |
| 708 | fn | decide_action | pub | `def decide_action(artifact: Artifact, classific...` |
| 732 | fn | classify_inventory | pub | `def classify_inventory(artifacts: Sequence[Arti...` |
| 740 | fn | _try_clean | (private) | `def _try_clean(mutator: CleanFn, artifact: Arti...` |
| 758 | fn | default_mutator | pub | `def default_mutator(repo: Path) -> CleanFn:` |
| 761 | fn | _clean | (private) | `def _clean(artifact: Artifact) -> str:` |
| 850 | fn | _checkout_is_dirty | (private) | `def _checkout_is_dirty(repo: Path) -> list[str]:` |
| 863 | fn | reconcile | pub | `def reconcile(` |
| 1008 | fn | _build_report | (private) | `def _build_report(` |
| 1040 | fn | artifact_from_dict | pub | `def artifact_from_dict(payload: Mapping[str, An...` |
| 1065 | fn | load_inventory | pub | `def load_inventory(path: Path) -> list[Artifact]:` |
| 1076 | fn | main | pub | `def main(argv: Sequence[str] | None = None) -> ...` |

## Public API

### `ReconciliationError`

```
class ReconciliationError(Exception):
```

**Line:** 83 | **Kind:** class

### `__init__`

```
def __init__(self, code: str, detail: str) -> None:
```

**Line:** 86 | **Kind:** fn

### `IdentityUncertainty`

```
class IdentityUncertainty(ReconciliationError):
```

**Line:** 92 | **Kind:** class

### `InfrastructureError`

```
class InfrastructureError(ReconciliationError):
```

**Line:** 96 | **Kind:** class

### `Artifact`

```
class Artifact:
```

**Line:** 101 | **Kind:** class

### `__post_init__`

```
def __post_init__(self) -> None:
```

**Line:** 125 | **Kind:** fn

### `Classification`

```
class Classification:
```

**Line:** 135 | **Kind:** class

### `Decision`

```
class Decision:
```

**Line:** 142 | **Kind:** class

### `flush`

```
def flush() -> None:
```

**Line:** 272 | **Kind:** fn

### `materialize_artifact`

```
def materialize_artifact(repo: Path, artifact: Artifact, *, state_dir: Path) -> Artifact:
```

**Line:** 533 | **Kind:** fn

### `resolve_state_dir`

```
def resolve_state_dir(repo: Path, override: str | os.PathLike[str] | None = None) -> Path:
```

**Line:** 557 | **Kind:** fn

### `ensure_state_dir`

```
def ensure_state_dir(state_dir: Path) -> Path:
```

**Line:** 567 | **Kind:** fn

### `write_json`

```
def write_json(path: Path, payload: Mapping[str, Any]) -> Path:
```

**Line:** 572 | **Kind:** fn

### `inventory_root_residue`

```
def inventory_root_residue(repo: Path) -> list[Artifact]:
```

**Line:** 578 | **Kind:** fn

### `finish_success`

```
def finish_success(state_dir: Path, report: Mapping[str, Any]) -> Path:
```

**Line:** 628 | **Kind:** fn

### `finish_failure`

```
def finish_failure(state_dir: Path, report: Mapping[str, Any], *, diagnostics: Mapping[str, Any]) -> Path:
```

**Line:** 635 | **Kind:** fn

### `classify_artifact`

```
def classify_artifact(artifact: Artifact) -> Classification:
```

**Line:** 642 | **Kind:** fn

### `decide_action`

```
def decide_action(artifact: Artifact, classification: Classification) -> str:
```

**Line:** 708 | **Kind:** fn

### `classify_inventory`

```
def classify_inventory(artifacts: Sequence[Artifact]) -> list[Decision]:
```

**Line:** 732 | **Kind:** fn

### `default_mutator`

```
def default_mutator(repo: Path) -> CleanFn:
```

**Line:** 758 | **Kind:** fn

### `reconcile`

```
def reconcile(
```

**Line:** 863 | **Kind:** fn

### `artifact_from_dict`

```
def artifact_from_dict(payload: Mapping[str, Any]) -> Artifact:
```

**Line:** 1040 | **Kind:** fn

### `load_inventory`

```
def load_inventory(path: Path) -> list[Artifact]:
```

**Line:** 1065 | **Kind:** fn

### `main`

```
def main(argv: Sequence[str] | None = None) -> int:
```

**Line:** 1076 | **Kind:** fn
