# scripts/gitops/repository_ci_contract.py

[← Back to Module](../modules/root/MODULE.md) | [← Back to INDEX](../INDEX.md)

## Overview

- **Lines:** 1337
- **Language:** Python
- **Symbols:** 37
- **Public symbols:** 32

## Symbol Table

| Line | Kind | Name | Visibility | Signature |
| ---- | ---- | ---- | ---------- | --------- |
| 65 | class | ContractError | pub | `class ContractError(Exception):` |
| 68 | fn | __init__ | pub | `def __init__(self, code: str, detail: str = "")...` |
| 74 | fn | digest_bytes | pub | `def digest_bytes(raw: bytes) -> str:` |
| 78 | fn | digest_text | pub | `def digest_text(text: str) -> str:` |
| 82 | fn | digest_json | pub | `def digest_json(value: Any) -> str:` |
| 86 | fn | _is_sha40 | (private) | `def _is_sha40(value: str) -> bool:` |
| 90 | fn | load_json | pub | `def load_json(path: Path) -> Any:` |
| 97 | fn | default_contract | pub | `def default_contract() -> dict[str, Any]:` |
| 162 | fn | validate_contract | pub | `def validate_contract(contract: Mapping[str, An...` |
| 205 | fn | load_contract | pub | `def load_contract(root: Path, *, path: Path | N...` |
| 212 | fn | normalize_repo_path | pub | `def normalize_repo_path(path: str) -> str:` |
| 219 | fn | path_is_trusted | pub | `def path_is_trusted(path: str, prefixes: Sequen...` |
| 224 | fn | classify_changed_paths | pub | `def classify_changed_paths(` |
| 267 | class | ProfileDecision | pub | `class ProfileDecision:` |
| 274 | fn | to_dict | pub | `def to_dict(self) -> dict[str, Any]:` |
| 278 | fn | select_profile | pub | `def select_profile(` |
| 363 | class | AggregateGateResult | pub | `class AggregateGateResult:` |
| 370 | fn | to_dict | pub | `def to_dict(self) -> dict[str, Any]:` |
| 374 | fn | evaluate_aggregate_gate | pub | `def evaluate_aggregate_gate(` |
| 475 | fn | validate_coverage_manifest | pub | `def validate_coverage_manifest(` |
| 536 | fn | validate_artifact_file | pub | `def validate_artifact_file(` |
| 582 | fn | run_component_preflight | pub | `def run_component_preflight(` |
| 751 | fn | _default_bootstrap_runner | (private) | `def _default_bootstrap_runner(command: list[str...` |
| 760 | fn | compute_cache_key | pub | `def compute_cache_key(` |
| 789 | fn | evaluate_cache_advisory | pub | `def evaluate_cache_advisory(` |
| 826 | fn | expand_reverse_dependencies | pub | `def expand_reverse_dependencies(` |
| 892 | fn | validate_affected_surface_evidence | pub | `def validate_affected_surface_evidence(evidence...` |
| 928 | fn | verify_promotion_exact_receipt | pub | `def verify_promotion_exact_receipt(` |
| 1037 | fn | evaluate_promotion_with_receipt | pub | `def evaluate_promotion_with_receipt(` |
| 1073 | fn | authorize_omission | pub | `def authorize_omission(` |
| 1103 | fn | innermost_diagnostic | pub | `def innermost_diagnostic(failures: Sequence[Map...` |
| 1127 | fn | _workflow_looks_expensive | (private) | `def _workflow_looks_expensive(text: str, marker...` |
| 1132 | fn | _has_broad_promotion_trigger | (private) | `def _has_broad_promotion_trigger(text: str) -> ...` |
| 1169 | fn | audit_workflow_triggers | pub | `def audit_workflow_triggers(` |
| 1208 | fn | installer_audit_repository_ci_triggers | pub | `def installer_audit_repository_ci_triggers(` |
| 1231 | fn | _parser | (private) | `def _parser() -> argparse.ArgumentParser:` |
| 1271 | fn | main | pub | `def main(argv: Sequence[str] | None = None) -> ...` |

## Public API

### `ContractError`

```
class ContractError(Exception):
```

**Line:** 65 | **Kind:** class

### `__init__`

```
def __init__(self, code: str, detail: str = "") -> None:
```

**Line:** 68 | **Kind:** fn

### `digest_bytes`

```
def digest_bytes(raw: bytes) -> str:
```

**Line:** 74 | **Kind:** fn

### `digest_text`

```
def digest_text(text: str) -> str:
```

**Line:** 78 | **Kind:** fn

### `digest_json`

```
def digest_json(value: Any) -> str:
```

**Line:** 82 | **Kind:** fn

### `load_json`

```
def load_json(path: Path) -> Any:
```

**Line:** 90 | **Kind:** fn

### `default_contract`

```
def default_contract() -> dict[str, Any]:
```

**Line:** 97 | **Kind:** fn

### `validate_contract`

```
def validate_contract(contract: Mapping[str, Any]) -> dict[str, Any]:
```

**Line:** 162 | **Kind:** fn

### `load_contract`

```
def load_contract(root: Path, *, path: Path | None = None) -> dict[str, Any]:
```

**Line:** 205 | **Kind:** fn

### `normalize_repo_path`

```
def normalize_repo_path(path: str) -> str:
```

**Line:** 212 | **Kind:** fn

### `path_is_trusted`

```
def path_is_trusted(path: str, prefixes: Sequence[str]) -> bool:
```

**Line:** 219 | **Kind:** fn

### `classify_changed_paths`

```
def classify_changed_paths(
```

**Line:** 224 | **Kind:** fn

### `ProfileDecision`

```
class ProfileDecision:
```

**Line:** 267 | **Kind:** class

### `to_dict`

```
def to_dict(self) -> dict[str, Any]:
```

**Line:** 274 | **Kind:** fn

### `select_profile`

```
def select_profile(
```

**Line:** 278 | **Kind:** fn

### `AggregateGateResult`

```
class AggregateGateResult:
```

**Line:** 363 | **Kind:** class

### `to_dict`

```
def to_dict(self) -> dict[str, Any]:
```

**Line:** 370 | **Kind:** fn

### `evaluate_aggregate_gate`

```
def evaluate_aggregate_gate(
```

**Line:** 374 | **Kind:** fn

### `validate_coverage_manifest`

```
def validate_coverage_manifest(
```

**Line:** 475 | **Kind:** fn

### `validate_artifact_file`

```
def validate_artifact_file(
```

**Line:** 536 | **Kind:** fn

### `run_component_preflight`

```
def run_component_preflight(
```

**Line:** 582 | **Kind:** fn

### `compute_cache_key`

```
def compute_cache_key(
```

**Line:** 760 | **Kind:** fn

### `evaluate_cache_advisory`

```
def evaluate_cache_advisory(
```

**Line:** 789 | **Kind:** fn

### `expand_reverse_dependencies`

```
def expand_reverse_dependencies(
```

**Line:** 826 | **Kind:** fn

### `validate_affected_surface_evidence`

```
def validate_affected_surface_evidence(evidence: Mapping[str, Any]) -> dict[str, Any]:
```

**Line:** 892 | **Kind:** fn

### `verify_promotion_exact_receipt`

```
def verify_promotion_exact_receipt(
```

**Line:** 928 | **Kind:** fn

### `evaluate_promotion_with_receipt`

```
def evaluate_promotion_with_receipt(
```

**Line:** 1037 | **Kind:** fn

### `authorize_omission`

```
def authorize_omission(
```

**Line:** 1073 | **Kind:** fn

### `innermost_diagnostic`

```
def innermost_diagnostic(failures: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
```

**Line:** 1103 | **Kind:** fn

### `audit_workflow_triggers`

```
def audit_workflow_triggers(
```

**Line:** 1169 | **Kind:** fn

### `installer_audit_repository_ci_triggers`

```
def installer_audit_repository_ci_triggers(
```

**Line:** 1208 | **Kind:** fn

### `main`

```
def main(argv: Sequence[str] | None = None) -> int:
```

**Line:** 1271 | **Kind:** fn
