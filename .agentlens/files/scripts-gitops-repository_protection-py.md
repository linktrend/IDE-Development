# scripts/gitops/repository_protection.py

[← Back to Module](../modules/root/MODULE.md) | [← Back to INDEX](../INDEX.md)

## Overview

- **Lines:** 1315
- **Language:** Python
- **Symbols:** 60
- **Public symbols:** 43

## Symbol Table

| Line | Kind | Name | Visibility | Signature |
| ---- | ---- | ---- | ---------- | --------- |
| 51 | class | ProtectionError | pub | `class ProtectionError(Exception):` |
| 52 | fn | __init__ | pub | `def __init__(self, message: str, exit_code: int...` |
| 57 | fn | _split_checks | (private) | `def _split_checks(raw: str | None) -> list[str]:` |
| 63 | fn | _unique_ordered | (private) | `def _unique_ordered(items: list[str]) -> list[s...` |
| 73 | fn | managed_baseline | pub | `def managed_baseline(` |
| 92 | fn | union_checks | pub | `def union_checks(managed: list[str], existing: ...` |
| 125 | fn | _status_check_rule | (private) | `def _status_check_rule(checks: list[str]) -> di...` |
| 136 | fn | _writeable_ruleset_rule | (private) | `def _writeable_ruleset_rule(rule: dict[str, Any...` |
| 148 | fn | merge_ruleset_rules | pub | `def merge_ruleset_rules(` |
| 185 | fn | ruleset_body | pub | `def ruleset_body(` |
| 223 | fn | _classic_actor_id | (private) | `def _classic_actor_id(item: Any, *, id_keys: tu...` |
| 250 | fn | _classic_actor_list | (private) | `def _classic_actor_list(items: Any, *, id_keys:...` |
| 262 | fn | _classic_bypass_allowances_for_put | (private) | `def _classic_bypass_allowances_for_put(value: A...` |
| 286 | fn | _classic_field_for_put | (private) | `def _classic_field_for_put(key: str, value: Any...` |
| 358 | fn | _classic_comparable_value | (private) | `def _classic_comparable_value(key: str, value: ...` |
| 382 | fn | classic_bodies_need_write | pub | `def classic_bodies_need_write(` |
| 412 | fn | classic_protection_body | pub | `def classic_protection_body(` |
| 446 | fn | extract_ruleset_checks | pub | `def extract_ruleset_checks(ruleset: dict[str, A...` |
| 461 | fn | extract_classic_checks | pub | `def extract_classic_checks(protection: dict[str...` |
| 475 | class | GitHubClient | pub | `class GitHubClient:` |
| 478 | fn | __init__ | pub | `def __init__(self, repo: str) -> None:` |
| 481 | fn | _api | (private) | `def _api(self, method: str, path: str, input_ob...` |
| 502 | fn | list_rulesets | pub | `def list_rulesets(self) -> tuple[str, list[dict...` |
| 515 | fn | get_ruleset | pub | `def get_ruleset(self, ruleset_id: int) -> dict[...` |
| 521 | fn | create_ruleset | pub | `def create_ruleset(self, body: dict[str, Any]) ...` |
| 527 | fn | update_ruleset | pub | `def update_ruleset(self, ruleset_id: int, body:...` |
| 533 | fn | delete_ruleset | pub | `def delete_ruleset(self, ruleset_id: int) -> None:` |
| 538 | fn | get_branch_protection | pub | `def get_branch_protection(self, branch: str) ->...` |
| 551 | fn | put_branch_protection | pub | `def put_branch_protection(self, branch: str, bo...` |
| 557 | fn | delete_branch_protection | pub | `def delete_branch_protection(self, branch: str)...` |
| 562 | fn | get_repo | pub | `def get_repo(self) -> dict[str, Any]:` |
| 568 | fn | patch_repo | pub | `def patch_repo(self, fields: dict[str, Any]) ->...` |
| 575 | class | FixtureClient | pub | `class FixtureClient(GitHubClient):` |
| 582 | fn | __init__ | pub | `def __init__(self, repo: str, fixture_dir: Path...` |
| 589 | fn | _refuse_mutation | (private) | `def _refuse_mutation(self, op: str) -> None:` |
| 596 | fn | _load | (private) | `def _load(self) -> dict[str, Any]:` |
| 602 | fn | _persist | (private) | `def _persist(self) -> None:` |
| 606 | fn | list_rulesets | pub | `def list_rulesets(self) -> tuple[str, list[dict...` |
| 613 | fn | get_ruleset | pub | `def get_ruleset(self, ruleset_id: int) -> dict[...` |
| 622 | fn | create_ruleset | pub | `def create_ruleset(self, body: dict[str, Any]) ...` |
| 634 | fn | update_ruleset | pub | `def update_ruleset(self, ruleset_id: int, body:...` |
| 647 | fn | delete_ruleset | pub | `def delete_ruleset(self, ruleset_id: int) -> None:` |
| 654 | fn | get_branch_protection | pub | `def get_branch_protection(self, branch: str) ->...` |
| 666 | fn | put_branch_protection | pub | `def put_branch_protection(self, branch: str, bo...` |
| 673 | fn | delete_branch_protection | pub | `def delete_branch_protection(self, branch: str)...` |
| 679 | fn | get_repo | pub | `def get_repo(self) -> dict[str, Any]:` |
| 682 | fn | patch_repo | pub | `def patch_repo(self, fields: dict[str, Any]) ->...` |
| 691 | fn | detect_mechanism | pub | `def detect_mechanism(client: GitHubClient) -> d...` |
| 743 | fn | _find_ruleset | (private) | `def _find_ruleset(` |
| 764 | fn | build_plan | pub | `def build_plan(` |
| 946 | fn | verify_plan | pub | `def verify_plan(plan: dict[str, Any]) -> tuple[...` |
| 974 | fn | _apply_branch_mutation | (private) | `def _apply_branch_mutation(` |
| 1004 | fn | apply_plan | pub | `def apply_plan(client: GitHubClient, plan: dict...` |
| 1057 | fn | rollback_from_snapshot | pub | `def rollback_from_snapshot(client: GitHubClient...` |
| 1110 | fn | resolve_check_overrides | pub | `def resolve_check_overrides(args: argparse.Name...` |
| 1130 | fn | build_client | pub | `def build_client(args: argparse.Namespace) -> G...` |
| 1136 | fn | parse_args | pub | `def parse_args(argv: list[str] | None = None) -...` |
| 1190 | fn | _parse_extra_checks | (private) | `def _parse_extra_checks(items: list[str]) -> di...` |
| 1204 | fn | main | pub | `def main(argv: list[str] | None = None) -> int:` |
| 1307 | fn | _emit | (private) | `def _emit(payload: dict[str, Any], path: str | ...` |

## Public API

### `ProtectionError`

```
class ProtectionError(Exception):
```

**Line:** 51 | **Kind:** class

### `__init__`

```
def __init__(self, message: str, exit_code: int = EXIT_FAILED) -> None:
```

**Line:** 52 | **Kind:** fn

### `managed_baseline`

```
def managed_baseline(
```

**Line:** 73 | **Kind:** fn

### `union_checks`

```
def union_checks(managed: list[str], existing: list[str], extra: list[str] | None = None) -> dict[str, list[str]]:
```

**Line:** 92 | **Kind:** fn

### `merge_ruleset_rules`

```
def merge_ruleset_rules(
```

**Line:** 148 | **Kind:** fn

### `ruleset_body`

```
def ruleset_body(
```

**Line:** 185 | **Kind:** fn

### `classic_bodies_need_write`

```
def classic_bodies_need_write(
```

**Line:** 382 | **Kind:** fn

### `classic_protection_body`

```
def classic_protection_body(
```

**Line:** 412 | **Kind:** fn

### `extract_ruleset_checks`

```
def extract_ruleset_checks(ruleset: dict[str, Any] | None) -> list[str]:
```

**Line:** 446 | **Kind:** fn

### `extract_classic_checks`

```
def extract_classic_checks(protection: dict[str, Any] | None) -> list[str]:
```

**Line:** 461 | **Kind:** fn

### `GitHubClient`

```
class GitHubClient:
```

**Line:** 475 | **Kind:** class

### `__init__`

```
def __init__(self, repo: str) -> None:
```

**Line:** 478 | **Kind:** fn

### `list_rulesets`

```
def list_rulesets(self) -> tuple[str, list[dict[str, Any]] | None, str]:
```

**Line:** 502 | **Kind:** fn

### `get_ruleset`

```
def get_ruleset(self, ruleset_id: int) -> dict[str, Any] | None:
```

**Line:** 515 | **Kind:** fn

### `create_ruleset`

```
def create_ruleset(self, body: dict[str, Any]) -> dict[str, Any]:
```

**Line:** 521 | **Kind:** fn

### `update_ruleset`

```
def update_ruleset(self, ruleset_id: int, body: dict[str, Any]) -> dict[str, Any]:
```

**Line:** 527 | **Kind:** fn

### `delete_ruleset`

```
def delete_ruleset(self, ruleset_id: int) -> None:
```

**Line:** 533 | **Kind:** fn

### `get_branch_protection`

```
def get_branch_protection(self, branch: str) -> tuple[str, dict[str, Any] | None, str]:
```

**Line:** 538 | **Kind:** fn

### `put_branch_protection`

```
def put_branch_protection(self, branch: str, body: dict[str, Any]) -> dict[str, Any]:
```

**Line:** 551 | **Kind:** fn

### `delete_branch_protection`

```
def delete_branch_protection(self, branch: str) -> None:
```

**Line:** 557 | **Kind:** fn

### `get_repo`

```
def get_repo(self) -> dict[str, Any]:
```

**Line:** 562 | **Kind:** fn

### `patch_repo`

```
def patch_repo(self, fields: dict[str, Any]) -> dict[str, Any]:
```

**Line:** 568 | **Kind:** fn

### `FixtureClient`

```
class FixtureClient(GitHubClient):
```

**Line:** 575 | **Kind:** class

### `__init__`

```
def __init__(self, repo: str, fixture_dir: Path, *, read_only: bool = False) -> None:
```

**Line:** 582 | **Kind:** fn

### `list_rulesets`

```
def list_rulesets(self) -> tuple[str, list[dict[str, Any]] | None, str]:
```

**Line:** 606 | **Kind:** fn

### `get_ruleset`

```
def get_ruleset(self, ruleset_id: int) -> dict[str, Any] | None:
```

**Line:** 613 | **Kind:** fn

### `create_ruleset`

```
def create_ruleset(self, body: dict[str, Any]) -> dict[str, Any]:
```

**Line:** 622 | **Kind:** fn

### `update_ruleset`

```
def update_ruleset(self, ruleset_id: int, body: dict[str, Any]) -> dict[str, Any]:
```

**Line:** 634 | **Kind:** fn

### `delete_ruleset`

```
def delete_ruleset(self, ruleset_id: int) -> None:
```

**Line:** 647 | **Kind:** fn

### `get_branch_protection`

```
def get_branch_protection(self, branch: str) -> tuple[str, dict[str, Any] | None, str]:
```

**Line:** 654 | **Kind:** fn

### `put_branch_protection`

```
def put_branch_protection(self, branch: str, body: dict[str, Any]) -> dict[str, Any]:
```

**Line:** 666 | **Kind:** fn

### `delete_branch_protection`

```
def delete_branch_protection(self, branch: str) -> None:
```

**Line:** 673 | **Kind:** fn

### `get_repo`

```
def get_repo(self) -> dict[str, Any]:
```

**Line:** 679 | **Kind:** fn

### `patch_repo`

```
def patch_repo(self, fields: dict[str, Any]) -> dict[str, Any]:
```

**Line:** 682 | **Kind:** fn

### `detect_mechanism`

```
def detect_mechanism(client: GitHubClient) -> dict[str, Any]:
```

**Line:** 691 | **Kind:** fn

### `build_plan`

```
def build_plan(
```

**Line:** 764 | **Kind:** fn

### `verify_plan`

```
def verify_plan(plan: dict[str, Any]) -> tuple[bool, list[str]]:
```

**Line:** 946 | **Kind:** fn

### `apply_plan`

```
def apply_plan(client: GitHubClient, plan: dict[str, Any]) -> list[dict[str, Any]]:
```

**Line:** 1004 | **Kind:** fn

### `rollback_from_snapshot`

```
def rollback_from_snapshot(client: GitHubClient, snapshot: dict[str, Any]) -> list[dict[str, Any]]:
```

**Line:** 1057 | **Kind:** fn

### `resolve_check_overrides`

```
def resolve_check_overrides(args: argparse.Namespace) -> dict[str, Any]:
```

**Line:** 1110 | **Kind:** fn

### `build_client`

```
def build_client(args: argparse.Namespace) -> GitHubClient:
```

**Line:** 1130 | **Kind:** fn

### `parse_args`

```
def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
```

**Line:** 1136 | **Kind:** fn

### `main`

```
def main(argv: list[str] | None = None) -> int:
```

**Line:** 1204 | **Kind:** fn
