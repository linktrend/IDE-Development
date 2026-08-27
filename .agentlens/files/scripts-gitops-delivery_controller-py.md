# scripts/gitops/delivery_controller.py

[← Back to Module](../modules/root/MODULE.md) | [← Back to INDEX](../INDEX.md)

## Overview

- **Lines:** 1511
- **Language:** Python
- **Symbols:** 53
- **Public symbols:** 45

## Symbol Table

| Line | Kind | Name | Visibility | Signature |
| ---- | ---- | ---- | ---------- | --------- |
| 92 | class | StagedRolloutConfig | pub | `class StagedRolloutConfig:` |
| 101 | fn | __post_init__ | pub | `def __post_init__(self) -> None:` |
| 121 | fn | from_mapping | pub | `def from_mapping(cls, payload: Mapping[str, Any...` |
| 151 | class | ControllerError | pub | `class ControllerError(ValueError):` |
| 154 | fn | __init__ | pub | `def __init__(self, code: str, detail: str = "")...` |
| 159 | fn | to_dict | pub | `def to_dict(self) -> dict[str, str]:` |
| 163 | fn | _receipt_workflow_run_id | (private) | `def _receipt_workflow_run_id(receipt: Mapping[s...` |
| 178 | class | GitHubPort | pub | `class GitHubPort(Protocol):` |
| 181 | fn | get_pull_request | pub | `def get_pull_request(self, *, repository: str, ...` |
| 184 | fn | merge_pull_request | pub | `def merge_pull_request(` |
| 196 | fn | create_pull_request | pub | `def create_pull_request(` |
| 208 | fn | delete_ref | pub | `def delete_ref(self, *, repository: str, ref: s...` |
| 211 | fn | push_protected | pub | `def push_protected(self, *, repository: str, br...` |
| 216 | class | MemoryGitHub | pub | `class MemoryGitHub:` |
| 229 | fn | get_pull_request | pub | `def get_pull_request(self, *, repository: str, ...` |
| 237 | fn | merge_pull_request | pub | `def merge_pull_request(` |
| 282 | fn | create_pull_request | pub | `def create_pull_request(` |
| 314 | fn | delete_ref | pub | `def delete_ref(self, *, repository: str, ref: s...` |
| 325 | fn | push_protected | pub | `def push_protected(self, *, repository: str, br...` |
| 332 | fn | _github_api | (private) | `def _github_api(` |
| 369 | class | LiveGitHub | pub | `class LiveGitHub:` |
| 376 | fn | _request | (private) | `def _request(self, method: str, url: str, body:...` |
| 381 | fn | get_pull_request | pub | `def get_pull_request(self, *, repository: str, ...` |
| 406 | fn | merge_pull_request | pub | `def merge_pull_request(` |
| 453 | fn | _merge_with_gh_admin | (private) | `def _merge_with_gh_admin(` |
| 501 | fn | create_pull_request | pub | `def create_pull_request(` |
| 542 | fn | ensure_promote_ref | pub | `def ensure_promote_ref(self, *, repository: str...` |
| 578 | fn | delete_ref | pub | `def delete_ref(self, *, repository: str, ref: s...` |
| 587 | fn | push_protected | pub | `def push_protected(self, *, repository: str, br...` |
| 591 | fn | resolve_production_github | pub | `def resolve_production_github(repository: str) ...` |
| 607 | fn | call_with_infrastructure_retry | pub | `def call_with_infrastructure_retry(operation: C...` |
| 630 | fn | require_promotion_source_equality | pub | `def require_promotion_source_equality(` |
| 647 | fn | _rollout_config | (private) | `def _rollout_config(rollout: StagedRolloutConfi...` |
| 651 | fn | _promotion_branch | (private) | `def _promotion_branch(config: StagedRolloutConf...` |
| 658 | fn | agent_env_fingerprint | pub | `def agent_env_fingerprint(environ: Mapping[str,...` |
| 666 | fn | require_controller_role | pub | `def require_controller_role(role: str) -> str:` |
| 677 | fn | accept_phase_pr | pub | `def accept_phase_pr(` |
| 726 | fn | _check_named_gates | (private) | `def _check_named_gates(` |
| 747 | fn | _check_repository_owned_ci | (private) | `def _check_repository_owned_ci(` |
| 777 | fn | verify_development_eligibility | pub | `def verify_development_eligibility(` |
| 831 | fn | merge_to_development | pub | `def merge_to_development(` |
| 873 | fn | promote_to_staging | pub | `def promote_to_staging(` |
| 959 | fn | prepare_main_promotion | pub | `def prepare_main_promotion(` |
| 1030 | fn | complete_main_promotion | pub | `def complete_main_promotion(` |
| 1091 | fn | authorize_cleanup_from_evidence | pub | `def authorize_cleanup_from_evidence(` |
| 1120 | fn | cleanup_temporary_branches | pub | `def cleanup_temporary_branches(` |
| 1161 | fn | stop_on_protected_merge_rejection | pub | `def stop_on_protected_merge_rejection(exc: Base...` |
| 1176 | fn | run_identical_under_agents | pub | `def run_identical_under_agents(` |
| 1209 | fn | write_operation_record | pub | `def write_operation_record(path: Path, record: ...` |
| 1221 | fn | deliver_phase_to_development | pub | `def deliver_phase_to_development(` |
| 1280 | fn | recover_phase_to_development | pub | `def recover_phase_to_development(` |
| 1327 | fn | main | pub | `def main(argv: list[str] | None = None) -> int:` |
| 1375 | fn | load | pub | `def load(path: str) -> Any:` |

## Public API

### `StagedRolloutConfig`

```
class StagedRolloutConfig:
```

**Line:** 92 | **Kind:** class

### `__post_init__`

```
def __post_init__(self) -> None:
```

**Line:** 101 | **Kind:** fn

### `from_mapping`

```
def from_mapping(cls, payload: Mapping[str, Any] | None) -> "StagedRolloutConfig":
```

**Line:** 121 | **Kind:** fn

### `ControllerError`

```
class ControllerError(ValueError):
```

**Line:** 151 | **Kind:** class

### `__init__`

```
def __init__(self, code: str, detail: str = "") -> None:
```

**Line:** 154 | **Kind:** fn

### `to_dict`

```
def to_dict(self) -> dict[str, str]:
```

**Line:** 159 | **Kind:** fn

### `GitHubPort`

```
class GitHubPort(Protocol):
```

**Line:** 178 | **Kind:** class

### `get_pull_request`

```
def get_pull_request(self, *, repository: str, number: int) -> dict[str, Any]:
```

**Line:** 181 | **Kind:** fn

### `merge_pull_request`

```
def merge_pull_request(
```

**Line:** 184 | **Kind:** fn

### `create_pull_request`

```
def create_pull_request(
```

**Line:** 196 | **Kind:** fn

### `delete_ref`

```
def delete_ref(self, *, repository: str, ref: str) -> bool:
```

**Line:** 208 | **Kind:** fn

### `push_protected`

```
def push_protected(self, *, repository: str, branch: str, sha: str) -> None:
```

**Line:** 211 | **Kind:** fn

### `MemoryGitHub`

```
class MemoryGitHub:
```

**Line:** 216 | **Kind:** class

### `get_pull_request`

```
def get_pull_request(self, *, repository: str, number: int) -> dict[str, Any]:
```

**Line:** 229 | **Kind:** fn

### `merge_pull_request`

```
def merge_pull_request(
```

**Line:** 237 | **Kind:** fn

### `create_pull_request`

```
def create_pull_request(
```

**Line:** 282 | **Kind:** fn

### `delete_ref`

```
def delete_ref(self, *, repository: str, ref: str) -> bool:
```

**Line:** 314 | **Kind:** fn

### `push_protected`

```
def push_protected(self, *, repository: str, branch: str, sha: str) -> None:
```

**Line:** 325 | **Kind:** fn

### `LiveGitHub`

```
class LiveGitHub:
```

**Line:** 369 | **Kind:** class

### `get_pull_request`

```
def get_pull_request(self, *, repository: str, number: int) -> dict[str, Any]:
```

**Line:** 381 | **Kind:** fn

### `merge_pull_request`

```
def merge_pull_request(
```

**Line:** 406 | **Kind:** fn

### `create_pull_request`

```
def create_pull_request(
```

**Line:** 501 | **Kind:** fn

### `ensure_promote_ref`

```
def ensure_promote_ref(self, *, repository: str, branch: str, head_sha: str) -> str:
```

**Line:** 542 | **Kind:** fn

### `delete_ref`

```
def delete_ref(self, *, repository: str, ref: str) -> bool:
```

**Line:** 578 | **Kind:** fn

### `push_protected`

```
def push_protected(self, *, repository: str, branch: str, sha: str) -> None:
```

**Line:** 587 | **Kind:** fn

### `resolve_production_github`

```
def resolve_production_github(repository: str) -> LiveGitHub:
```

**Line:** 591 | **Kind:** fn

### `call_with_infrastructure_retry`

```
def call_with_infrastructure_retry(operation: Callable[[], Any], *, attempts: int | None = None) -> Any:
```

**Line:** 607 | **Kind:** fn

### `require_promotion_source_equality`

```
def require_promotion_source_equality(
```

**Line:** 630 | **Kind:** fn

### `agent_env_fingerprint`

```
def agent_env_fingerprint(environ: Mapping[str, str] | None = None) -> str:
```

**Line:** 658 | **Kind:** fn

### `require_controller_role`

```
def require_controller_role(role: str) -> str:
```

**Line:** 666 | **Kind:** fn

### `accept_phase_pr`

```
def accept_phase_pr(
```

**Line:** 677 | **Kind:** fn

### `verify_development_eligibility`

```
def verify_development_eligibility(
```

**Line:** 777 | **Kind:** fn

### `merge_to_development`

```
def merge_to_development(
```

**Line:** 831 | **Kind:** fn

### `promote_to_staging`

```
def promote_to_staging(
```

**Line:** 873 | **Kind:** fn

### `prepare_main_promotion`

```
def prepare_main_promotion(
```

**Line:** 959 | **Kind:** fn

### `complete_main_promotion`

```
def complete_main_promotion(
```

**Line:** 1030 | **Kind:** fn

### `authorize_cleanup_from_evidence`

```
def authorize_cleanup_from_evidence(
```

**Line:** 1091 | **Kind:** fn

### `cleanup_temporary_branches`

```
def cleanup_temporary_branches(
```

**Line:** 1120 | **Kind:** fn

### `stop_on_protected_merge_rejection`

```
def stop_on_protected_merge_rejection(exc: BaseException) -> dict[str, Any]:
```

**Line:** 1161 | **Kind:** fn

### `run_identical_under_agents`

```
def run_identical_under_agents(
```

**Line:** 1176 | **Kind:** fn

### `write_operation_record`

```
def write_operation_record(path: Path, record: Mapping[str, Any]) -> dict[str, Any]:
```

**Line:** 1209 | **Kind:** fn

### `deliver_phase_to_development`

```
def deliver_phase_to_development(
```

**Line:** 1221 | **Kind:** fn

### `recover_phase_to_development`

```
def recover_phase_to_development(
```

**Line:** 1280 | **Kind:** fn

### `main`

```
def main(argv: list[str] | None = None) -> int:
```

**Line:** 1327 | **Kind:** fn

### `load`

```
def load(path: str) -> Any:
```

**Line:** 1375 | **Kind:** fn
