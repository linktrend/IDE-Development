# scripts/gitops/packager_coordinator.py

[← Back to Module](../modules/root/MODULE.md) | [← Back to INDEX](../INDEX.md)

## Overview

- **Lines:** 1231
- **Language:** Python
- **Symbols:** 61
- **Public symbols:** 36

## Symbol Table

| Line | Kind | Name | Visibility | Signature |
| ---- | ---- | ---- | ---------- | --------- |
| 98 | class | CoordinatorError | pub | `class CoordinatorError(ValueError):` |
| 101 | fn | __init__ | pub | `def __init__(self, code: str, detail: str) -> N...` |
| 106 | fn | to_dict | pub | `def to_dict(self) -> dict[str, str]:` |
| 110 | class | GitHubPort | pub | `class GitHubPort(Protocol):` |
| 113 | fn | ensure_draft_phase_pr | pub | `def ensure_draft_phase_pr(` |
| 126 | fn | list_open_phase_prs | pub | `def list_open_phase_prs(self, *, repository: st...` |
| 129 | fn | completion_bound | pub | `def completion_bound(` |
| 136 | fn | add_label | pub | `def add_label(self, pr_number: int, label: str)...` |
| 139 | fn | dispatch_workflow | pub | `def dispatch_workflow(self, name: str, inputs: ...` |
| 143 | class | PushPort | pub | `class PushPort(Protocol):` |
| 146 | fn | push_phase_ref | pub | `def push_phase_ref(self, repo: Path, remote: st...` |
| 151 | class | MemoryGitHub | pub | `class MemoryGitHub:` |
| 163 | fn | _key | (private) | `def _key(self, repository: str, head: str, base...` |
| 166 | fn | ensure_draft_phase_pr | pub | `def ensure_draft_phase_pr(` |
| 204 | fn | list_open_phase_prs | pub | `def list_open_phase_prs(self, *, repository: st...` |
| 209 | fn | completion_bound | pub | `def completion_bound(` |
| 228 | fn | add_label | pub | `def add_label(self, pr_number: int, label: str)...` |
| 231 | fn | dispatch_workflow | pub | `def dispatch_workflow(self, name: str, inputs: ...` |
| 235 | class | GitPushAdapter | pub | `class GitPushAdapter:` |
| 238 | fn | push_phase_ref | pub | `def push_phase_ref(self, repo: Path, remote: st...` |
| 252 | fn | _github_api | (private) | `def _github_api(` |
| 281 | class | LiveGitHub | pub | `class LiveGitHub:` |
| 292 | fn | _request | (private) | `def _request(self, method: str, url: str, token...` |
| 297 | fn | _pr_identity | (private) | `def _pr_identity(self, payload: Mapping[str, An...` |
| 313 | fn | ensure_draft_phase_pr | pub | `def ensure_draft_phase_pr(` |
| 376 | fn | _bound_live_pr | (private) | `def _bound_live_pr(self, identity: dict[str, An...` |
| 389 | fn | list_open_phase_prs | pub | `def list_open_phase_prs(self, *, repository: st...` |
| 405 | fn | completion_bound | pub | `def completion_bound(` |
| 418 | fn | add_label | pub | `def add_label(self, pr_number: int, label: str)...` |
| 421 | fn | dispatch_workflow | pub | `def dispatch_workflow(self, name: str, inputs: ...` |
| 425 | fn | resolve_production_adapters | pub | `def resolve_production_adapters(repository: str...` |
| 444 | fn | assert_live_phase_pr | pub | `def assert_live_phase_pr(pr: Mapping[str, Any])...` |
| 456 | class | AcceptedSource | pub | `class AcceptedSource:` |
| 461 | fn | to_dict | pub | `def to_dict(self) -> dict[str, Any]:` |
| 465 | fn | _git | (private) | `def _git(repo: Path, *args: str, check: bool = ...` |
| 479 | fn | parse_accept | pub | `def parse_accept(raw: str, order: int) -> Accep...` |
| 493 | fn | parse_fast_trigger_contract | pub | `def parse_fast_trigger_contract(text: str) -> d...` |
| 513 | fn | full_may_start | pub | `def full_may_start(` |
| 542 | fn | consume_handoff | pub | `def consume_handoff(` |
| 568 | fn | _remote_sha | (private) | `def _remote_sha(repo: Path, remote: str, branch...` |
| 575 | fn | _object_exists | (private) | `def _object_exists(repo: Path, sha: str) -> bool:` |
| 580 | fn | _changed_paths | (private) | `def _changed_paths(repo: Path, base: str, sha: ...` |
| 585 | fn | _is_ancestor | (private) | `def _is_ancestor(repo: Path, ancestor: str, des...` |
| 596 | fn | _probe_conflicts | (private) | `def _probe_conflicts(repo: Path, development: s...` |
| 651 | fn | _validate_source | (private) | `def _validate_source(` |
| 691 | fn | _git_common_dir | (private) | `def _git_common_dir(repo: Path) -> Path:` |
| 699 | fn | _coordinator_state_dir | (private) | `def _coordinator_state_dir(repo: Path, phase_br...` |
| 704 | fn | _local_sha | (private) | `def _local_sha(repo: Path, branch: str) -> str:` |
| 709 | fn | _assert_live_phase_pr_optional | (private) | `def _assert_live_phase_pr_optional(pr: Mapping[...` |
| 714 | fn | _unique_phase_commits | (private) | `def _unique_phase_commits(` |
| 737 | fn | _existing_phase_shas | (private) | `def _existing_phase_shas(repo: Path, remote: st...` |
| 745 | fn | _remaining_sources | (private) | `def _remaining_sources(repo: Path, start_sha: s...` |
| 754 | fn | _assemble_in_worktree | (private) | `def _assemble_in_worktree(` |
| 805 | fn | _write_isolated_state | (private) | `def _write_isolated_state(repo: Path, phase_bra...` |
| 819 | fn | _stable_title | (private) | `def _stable_title(phase_branch: str) -> str:` |
| 823 | fn | _candidate_revision | (private) | `def _candidate_revision(repository: str, phase_...` |
| 837 | fn | _phase_record | (private) | `def _phase_record(` |
| 899 | fn | _handoff_from | (private) | `def _handoff_from(record: Mapping[str, Any], *,...` |
| 925 | fn | assemble_phase | pub | `def assemble_phase(` |
| 1124 | fn | invalidate_handoff_if_head_changed | pub | `def invalidate_handoff_if_head_changed(handoff:...` |
| 1133 | fn | main | pub | `def main(argv: list[str] | None = None) -> int:` |

## Public API

### `CoordinatorError`

```
class CoordinatorError(ValueError):
```

**Line:** 98 | **Kind:** class

### `__init__`

```
def __init__(self, code: str, detail: str) -> None:
```

**Line:** 101 | **Kind:** fn

### `to_dict`

```
def to_dict(self) -> dict[str, str]:
```

**Line:** 106 | **Kind:** fn

### `GitHubPort`

```
class GitHubPort(Protocol):
```

**Line:** 110 | **Kind:** class

### `ensure_draft_phase_pr`

```
def ensure_draft_phase_pr(
```

**Line:** 113 | **Kind:** fn

### `list_open_phase_prs`

```
def list_open_phase_prs(self, *, repository: str, head: str, base: str) -> list[dict[str, Any]]:
```

**Line:** 126 | **Kind:** fn

### `completion_bound`

```
def completion_bound(
```

**Line:** 129 | **Kind:** fn

### `add_label`

```
def add_label(self, pr_number: int, label: str) -> None:
```

**Line:** 136 | **Kind:** fn

### `dispatch_workflow`

```
def dispatch_workflow(self, name: str, inputs: Mapping[str, Any]) -> None:
```

**Line:** 139 | **Kind:** fn

### `PushPort`

```
class PushPort(Protocol):
```

**Line:** 143 | **Kind:** class

### `push_phase_ref`

```
def push_phase_ref(self, repo: Path, remote: str, branch: str, sha: str) -> str:
```

**Line:** 146 | **Kind:** fn

### `MemoryGitHub`

```
class MemoryGitHub:
```

**Line:** 151 | **Kind:** class

### `ensure_draft_phase_pr`

```
def ensure_draft_phase_pr(
```

**Line:** 166 | **Kind:** fn

### `list_open_phase_prs`

```
def list_open_phase_prs(self, *, repository: str, head: str, base: str) -> list[dict[str, Any]]:
```

**Line:** 204 | **Kind:** fn

### `completion_bound`

```
def completion_bound(
```

**Line:** 209 | **Kind:** fn

### `add_label`

```
def add_label(self, pr_number: int, label: str) -> None:
```

**Line:** 228 | **Kind:** fn

### `dispatch_workflow`

```
def dispatch_workflow(self, name: str, inputs: Mapping[str, Any]) -> None:
```

**Line:** 231 | **Kind:** fn

### `GitPushAdapter`

```
class GitPushAdapter:
```

**Line:** 235 | **Kind:** class

### `push_phase_ref`

```
def push_phase_ref(self, repo: Path, remote: str, branch: str, sha: str) -> str:
```

**Line:** 238 | **Kind:** fn

### `LiveGitHub`

```
class LiveGitHub:
```

**Line:** 281 | **Kind:** class

### `ensure_draft_phase_pr`

```
def ensure_draft_phase_pr(
```

**Line:** 313 | **Kind:** fn

### `list_open_phase_prs`

```
def list_open_phase_prs(self, *, repository: str, head: str, base: str) -> list[dict[str, Any]]:
```

**Line:** 389 | **Kind:** fn

### `completion_bound`

```
def completion_bound(
```

**Line:** 405 | **Kind:** fn

### `add_label`

```
def add_label(self, pr_number: int, label: str) -> None:
```

**Line:** 418 | **Kind:** fn

### `dispatch_workflow`

```
def dispatch_workflow(self, name: str, inputs: Mapping[str, Any]) -> None:
```

**Line:** 421 | **Kind:** fn

### `resolve_production_adapters`

```
def resolve_production_adapters(repository: str) -> tuple[LiveGitHub, GitPushAdapter]:
```

**Line:** 425 | **Kind:** fn

### `assert_live_phase_pr`

```
def assert_live_phase_pr(pr: Mapping[str, Any]) -> None:
```

**Line:** 444 | **Kind:** fn

### `AcceptedSource`

```
class AcceptedSource:
```

**Line:** 456 | **Kind:** class

### `to_dict`

```
def to_dict(self) -> dict[str, Any]:
```

**Line:** 461 | **Kind:** fn

### `parse_accept`

```
def parse_accept(raw: str, order: int) -> AcceptedSource:
```

**Line:** 479 | **Kind:** fn

### `parse_fast_trigger_contract`

```
def parse_fast_trigger_contract(text: str) -> dict[str, Any]:
```

**Line:** 493 | **Kind:** fn

### `full_may_start`

```
def full_may_start(
```

**Line:** 513 | **Kind:** fn

### `consume_handoff`

```
def consume_handoff(
```

**Line:** 542 | **Kind:** fn

### `assemble_phase`

```
def assemble_phase(
```

**Line:** 925 | **Kind:** fn

### `invalidate_handoff_if_head_changed`

```
def invalidate_handoff_if_head_changed(handoff: Mapping[str, Any], *, live_head: str) -> dict[str, Any]:
```

**Line:** 1124 | **Kind:** fn

### `main`

```
def main(argv: list[str] | None = None) -> int:
```

**Line:** 1133 | **Kind:** fn
