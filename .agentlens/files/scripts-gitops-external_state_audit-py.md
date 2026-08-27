# scripts/gitops/external_state_audit.py

[← Back to Module](../modules/root/MODULE.md) | [← Back to INDEX](../INDEX.md)

## Overview

- **Lines:** 1970
- **Language:** Python
- **Symbols:** 67
- **Public symbols:** 55

## Symbol Table

| Line | Kind | Name | Visibility | Signature |
| ---- | ---- | ---- | ---------- | --------- |
| 101 | class | AuditError | pub | `class AuditError(Exception):` |
| 102 | fn | __init__ | pub | `def __init__(self, message: str, exit_code: int...` |
| 107 | fn | _check | (private) | `def _check(` |
| 130 | fn | required_checklist | pub | `def required_checklist() -> list[dict[str, Any]]:` |
| 258 | fn | _secret_env_leak_warnings | (private) | `def _secret_env_leak_warnings() -> list[str]:` |
| 271 | fn | _import_repository_protection | (private) | `def _import_repository_protection() -> Any:` |
| 281 | class | ReadOnlyGitHubClient | pub | `class ReadOnlyGitHubClient:` |
| 284 | fn | __init__ | pub | `def __init__(self, repo: str) -> None:` |
| 290 | fn | _api_get | (private) | `def _api_get(self, path: str) -> tuple[int, Any...` |
| 308 | fn | mutate | pub | `def mutate(self, method: str, *_args: Any, **_k...` |
| 317 | fn | apply | pub | `def apply(self, *_args: Any, **_kwargs: Any) ->...` |
| 323 | fn | list_actions_variables | pub | `def list_actions_variables(self) -> list[dict[s...` |
| 332 | fn | list_actions_secret_names | pub | `def list_actions_secret_names(self) -> list[str]:` |
| 344 | fn | get_installation | pub | `def get_installation(self) -> dict[str, Any] | ...` |
| 366 | fn | list_rulesets | pub | `def list_rulesets(self) -> list[dict[str, Any]]:` |
| 374 | fn | get_ruleset | pub | `def get_ruleset(self, ruleset_id: int) -> dict[...` |
| 383 | fn | get_repo | pub | `def get_repo(self) -> dict[str, Any]:` |
| 389 | fn | get_bugbot_repo_settings | pub | `def get_bugbot_repo_settings(self) -> dict[str,...` |
| 393 | fn | get_app_permissions_observation | pub | `def get_app_permissions_observation(self) -> di...` |
| 397 | fn | get_carlos_boundary_observation | pub | `def get_carlos_boundary_observation(self) -> di...` |
| 401 | fn | list_workflows | pub | `def list_workflows(self) -> list[dict[str, Any]]:` |
| 423 | fn | get_workflow_latest_conclusion | pub | `def get_workflow_latest_conclusion(self, workfl...` |
| 445 | fn | protection_capability | pub | `def protection_capability(self) -> dict[str, Any]:` |
| 449 | class | FixtureClient | pub | `class FixtureClient(ReadOnlyGitHubClient):` |
| 452 | fn | __init__ | pub | `def __init__(self, repo: str, fixture_dir: Path...` |
| 476 | fn | list_actions_variables | pub | `def list_actions_variables(self) -> list[dict[s...` |
| 484 | fn | list_actions_secret_names | pub | `def list_actions_secret_names(self) -> list[str]:` |
| 503 | fn | get_installation | pub | `def get_installation(self) -> dict[str, Any] | ...` |
| 509 | fn | list_rulesets | pub | `def list_rulesets(self) -> list[dict[str, Any]]:` |
| 518 | fn | get_ruleset | pub | `def get_ruleset(self, ruleset_id: int) -> dict[...` |
| 528 | fn | get_repo | pub | `def get_repo(self) -> dict[str, Any]:` |
| 531 | fn | get_bugbot_repo_settings | pub | `def get_bugbot_repo_settings(self) -> dict[str,...` |
| 537 | fn | get_app_permissions_observation | pub | `def get_app_permissions_observation(self) -> di...` |
| 545 | fn | get_carlos_boundary_observation | pub | `def get_carlos_boundary_observation(self) -> di...` |
| 556 | fn | list_workflows | pub | `def list_workflows(self) -> list[dict[str, Any]]:` |
| 564 | fn | get_workflow_latest_conclusion | pub | `def get_workflow_latest_conclusion(self, workfl...` |
| 576 | fn | protection_capability | pub | `def protection_capability(self) -> dict[str, Any]:` |
| 580 | class | UncheckedClient | pub | `class UncheckedClient(ReadOnlyGitHubClient):` |
| 583 | fn | list_actions_variables | pub | `def list_actions_variables(self) -> list[dict[s...` |
| 586 | fn | list_actions_secret_names | pub | `def list_actions_secret_names(self) -> list[str]:` |
| 589 | fn | get_installation | pub | `def get_installation(self) -> dict[str, Any] | ...` |
| 592 | fn | list_rulesets | pub | `def list_rulesets(self) -> list[dict[str, Any]]:` |
| 595 | fn | get_ruleset | pub | `def get_ruleset(self, ruleset_id: int) -> dict[...` |
| 598 | fn | get_repo | pub | `def get_repo(self) -> dict[str, Any]:` |
| 601 | fn | get_bugbot_repo_settings | pub | `def get_bugbot_repo_settings(self) -> dict[str,...` |
| 604 | fn | get_app_permissions_observation | pub | `def get_app_permissions_observation(self) -> di...` |
| 607 | fn | get_carlos_boundary_observation | pub | `def get_carlos_boundary_observation(self) -> di...` |
| 610 | fn | list_workflows | pub | `def list_workflows(self) -> list[dict[str, Any]]:` |
| 613 | fn | get_workflow_latest_conclusion | pub | `def get_workflow_latest_conclusion(self, workfl...` |
| 616 | fn | protection_capability | pub | `def protection_capability(self) -> dict[str, Any]:` |
| 620 | fn | _find_variable | (private) | `def _find_variable(variables: list[dict[str, An...` |
| 627 | fn | _extract_ruleset_checks | (private) | `def _extract_ruleset_checks(ruleset: dict[str, ...` |
| 643 | fn | _extract_non_check_rule_types | (private) | `def _extract_non_check_rule_types(ruleset: dict...` |
| 656 | fn | _is_numeric_app_id | (private) | `def _is_numeric_app_id(value: Any) -> bool:` |
| 663 | fn | _workflow_basename | (private) | `def _workflow_basename(path: str) -> str:` |
| 667 | fn | _unchecked | (private) | `def _unchecked(` |
| 687 | fn | _evaluate_ruleset_branch | (private) | `def _evaluate_ruleset_branch(` |
| 784 | fn | evaluate | pub | `def evaluate(client: ReadOnlyGitHubClient, *, s...` |
| 1682 | fn | summarize | pub | `def summarize(checks: list[dict[str, Any]]) -> ...` |
| 1714 | fn | human_summary | pub | `def human_summary(checks: list[dict[str, Any]],...` |
| 1733 | fn | build_protection_plan_section | pub | `def build_protection_plan_section(` |
| 1784 | fn | build_desired_plan | pub | `def build_desired_plan(checks: list[dict[str, A...` |
| 1814 | fn | build_report | pub | `def build_report(` |
| 1853 | fn | parse_args | pub | `def parse_args(argv: list[str] | None = None) -...` |
| 1895 | fn | build_client | pub | `def build_client(args: argparse.Namespace) -> t...` |
| 1905 | fn | _emit | (private) | `def _emit(payload: dict[str, Any], path: str | ...` |
| 1929 | fn | main | pub | `def main(argv: list[str] | None = None) -> int:` |

## Public API

### `AuditError`

```
class AuditError(Exception):
```

**Line:** 101 | **Kind:** class

### `__init__`

```
def __init__(self, message: str, exit_code: int = EXIT_FAILED) -> None:
```

**Line:** 102 | **Kind:** fn

### `required_checklist`

```
def required_checklist() -> list[dict[str, Any]]:
```

**Line:** 130 | **Kind:** fn

### `ReadOnlyGitHubClient`

```
class ReadOnlyGitHubClient:
```

**Line:** 281 | **Kind:** class

### `__init__`

```
def __init__(self, repo: str) -> None:
```

**Line:** 284 | **Kind:** fn

### `mutate`

```
def mutate(self, method: str, *_args: Any, **_kwargs: Any) -> None:
```

**Line:** 308 | **Kind:** fn

### `apply`

```
def apply(self, *_args: Any, **_kwargs: Any) -> None:
```

**Line:** 317 | **Kind:** fn

### `list_actions_variables`

```
def list_actions_variables(self) -> list[dict[str, Any]]:
```

**Line:** 323 | **Kind:** fn

### `list_actions_secret_names`

```
def list_actions_secret_names(self) -> list[str]:
```

**Line:** 332 | **Kind:** fn

### `get_installation`

```
def get_installation(self) -> dict[str, Any] | None:
```

**Line:** 344 | **Kind:** fn

### `list_rulesets`

```
def list_rulesets(self) -> list[dict[str, Any]]:
```

**Line:** 366 | **Kind:** fn

### `get_ruleset`

```
def get_ruleset(self, ruleset_id: int) -> dict[str, Any] | None:
```

**Line:** 374 | **Kind:** fn

### `get_repo`

```
def get_repo(self) -> dict[str, Any]:
```

**Line:** 383 | **Kind:** fn

### `get_bugbot_repo_settings`

```
def get_bugbot_repo_settings(self) -> dict[str, Any] | None:
```

**Line:** 389 | **Kind:** fn

### `get_app_permissions_observation`

```
def get_app_permissions_observation(self) -> dict[str, Any] | None:
```

**Line:** 393 | **Kind:** fn

### `get_carlos_boundary_observation`

```
def get_carlos_boundary_observation(self) -> dict[str, Any] | None:
```

**Line:** 397 | **Kind:** fn

### `list_workflows`

```
def list_workflows(self) -> list[dict[str, Any]]:
```

**Line:** 401 | **Kind:** fn

### `get_workflow_latest_conclusion`

```
def get_workflow_latest_conclusion(self, workflow_id: Any) -> str | None:
```

**Line:** 423 | **Kind:** fn

### `protection_capability`

```
def protection_capability(self) -> dict[str, Any]:
```

**Line:** 445 | **Kind:** fn

### `FixtureClient`

```
class FixtureClient(ReadOnlyGitHubClient):
```

**Line:** 449 | **Kind:** class

### `__init__`

```
def __init__(self, repo: str, fixture_dir: Path) -> None:
```

**Line:** 452 | **Kind:** fn

### `list_actions_variables`

```
def list_actions_variables(self) -> list[dict[str, Any]]:
```

**Line:** 476 | **Kind:** fn

### `list_actions_secret_names`

```
def list_actions_secret_names(self) -> list[str]:
```

**Line:** 484 | **Kind:** fn

### `get_installation`

```
def get_installation(self) -> dict[str, Any] | None:
```

**Line:** 503 | **Kind:** fn

### `list_rulesets`

```
def list_rulesets(self) -> list[dict[str, Any]]:
```

**Line:** 509 | **Kind:** fn

### `get_ruleset`

```
def get_ruleset(self, ruleset_id: int) -> dict[str, Any] | None:
```

**Line:** 518 | **Kind:** fn

### `get_repo`

```
def get_repo(self) -> dict[str, Any]:
```

**Line:** 528 | **Kind:** fn

### `get_bugbot_repo_settings`

```
def get_bugbot_repo_settings(self) -> dict[str, Any] | None:
```

**Line:** 531 | **Kind:** fn

### `get_app_permissions_observation`

```
def get_app_permissions_observation(self) -> dict[str, Any] | None:
```

**Line:** 537 | **Kind:** fn

### `get_carlos_boundary_observation`

```
def get_carlos_boundary_observation(self) -> dict[str, Any] | None:
```

**Line:** 545 | **Kind:** fn

### `list_workflows`

```
def list_workflows(self) -> list[dict[str, Any]]:
```

**Line:** 556 | **Kind:** fn

### `get_workflow_latest_conclusion`

```
def get_workflow_latest_conclusion(self, workflow_id: Any) -> str | None:
```

**Line:** 564 | **Kind:** fn

### `protection_capability`

```
def protection_capability(self) -> dict[str, Any]:
```

**Line:** 576 | **Kind:** fn

### `UncheckedClient`

```
class UncheckedClient(ReadOnlyGitHubClient):
```

**Line:** 580 | **Kind:** class

### `list_actions_variables`

```
def list_actions_variables(self) -> list[dict[str, Any]]:
```

**Line:** 583 | **Kind:** fn

### `list_actions_secret_names`

```
def list_actions_secret_names(self) -> list[str]:
```

**Line:** 586 | **Kind:** fn

### `get_installation`

```
def get_installation(self) -> dict[str, Any] | None:
```

**Line:** 589 | **Kind:** fn

### `list_rulesets`

```
def list_rulesets(self) -> list[dict[str, Any]]:
```

**Line:** 592 | **Kind:** fn

### `get_ruleset`

```
def get_ruleset(self, ruleset_id: int) -> dict[str, Any] | None:
```

**Line:** 595 | **Kind:** fn

### `get_repo`

```
def get_repo(self) -> dict[str, Any]:
```

**Line:** 598 | **Kind:** fn

### `get_bugbot_repo_settings`

```
def get_bugbot_repo_settings(self) -> dict[str, Any] | None:
```

**Line:** 601 | **Kind:** fn

### `get_app_permissions_observation`

```
def get_app_permissions_observation(self) -> dict[str, Any] | None:
```

**Line:** 604 | **Kind:** fn

### `get_carlos_boundary_observation`

```
def get_carlos_boundary_observation(self) -> dict[str, Any] | None:
```

**Line:** 607 | **Kind:** fn

### `list_workflows`

```
def list_workflows(self) -> list[dict[str, Any]]:
```

**Line:** 610 | **Kind:** fn

### `get_workflow_latest_conclusion`

```
def get_workflow_latest_conclusion(self, workflow_id: Any) -> str | None:
```

**Line:** 613 | **Kind:** fn

### `protection_capability`

```
def protection_capability(self) -> dict[str, Any]:
```

**Line:** 616 | **Kind:** fn

### `evaluate`

```
def evaluate(client: ReadOnlyGitHubClient, *, source: str) -> list[dict[str, Any]]:
```

**Line:** 784 | **Kind:** fn

### `summarize`

```
def summarize(checks: list[dict[str, Any]]) -> dict[str, Any]:
```

**Line:** 1682 | **Kind:** fn

### `human_summary`

```
def human_summary(checks: list[dict[str, Any]], summary: dict[str, Any]) -> str:
```

**Line:** 1714 | **Kind:** fn

### `build_protection_plan_section`

```
def build_protection_plan_section(
```

**Line:** 1733 | **Kind:** fn

### `build_desired_plan`

```
def build_desired_plan(checks: list[dict[str, Any]]) -> list[dict[str, Any]]:
```

**Line:** 1784 | **Kind:** fn

### `build_report`

```
def build_report(
```

**Line:** 1814 | **Kind:** fn

### `parse_args`

```
def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
```

**Line:** 1853 | **Kind:** fn

### `build_client`

```
def build_client(args: argparse.Namespace) -> tuple[ReadOnlyGitHubClient, str]:
```

**Line:** 1895 | **Kind:** fn

### `main`

```
def main(argv: list[str] | None = None) -> int:
```

**Line:** 1929 | **Kind:** fn
