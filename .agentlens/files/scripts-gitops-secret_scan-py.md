# scripts/gitops/secret_scan.py

[← Back to Module](../modules/root/MODULE.md) | [← Back to INDEX](../INDEX.md)

## Overview

- **Lines:** 1707
- **Language:** Python
- **Symbols:** 61
- **Public symbols:** 20

## Symbol Table

| Line | Kind | Name | Visibility | Signature |
| ---- | ---- | ---- | ---------- | --------- |
| 161 | fn | managed_scanner_policy_paths | pub | `def managed_scanner_policy_paths(root: Path) ->...` |
| 172 | class | SecretScanError | pub | `class SecretScanError(Exception):` |
| 173 | fn | __init__ | pub | `def __init__(self, code: str, detail: str = "")...` |
| 180 | class | IndexEntry | pub | `class IndexEntry:` |
| 187 | fn | is_regular | pub | `def is_regular(self) -> bool:` |
| 191 | fn | digest_bytes | pub | `def digest_bytes(raw: bytes) -> str:` |
| 195 | fn | _git | (private) | `def _git(root: Path, *args: str, input_text: st...` |
| 209 | fn | _git_bytes | (private) | `def _git_bytes(root: Path, *args: str, input_by...` |
| 223 | fn | _git_identity | (private) | `def _git_identity(root: Path) -> tuple[str, str...` |
| 244 | fn | config_digest | pub | `def config_digest(root: Path, paths: tuple[str,...` |
| 260 | fn | _remote_ref_name | (private) | `def _remote_ref_name(ref: str) -> str:` |
| 268 | fn | changed_paths | pub | `def changed_paths(root: Path, baseline_commit: ...` |
| 326 | fn | _validate_change_scoped_evidence | (private) | `def _validate_change_scoped_evidence(` |
| 424 | fn | tracked_entries | pub | `def tracked_entries(root: Path) -> list[IndexEn...` |
| 451 | fn | tracked_files | pub | `def tracked_files(root: Path) -> list[str]:` |
| 455 | fn | candidate_content_tree | pub | `def candidate_content_tree(root: Path) -> str:` |
| 470 | fn | _shannon | (private) | `def _shannon(value: str) -> float:` |
| 478 | fn | _is_reference_value | (private) | `def _is_reference_value(value: str) -> bool:` |
| 508 | fn | is_realistic_value | pub | `def is_realistic_value(value: str) -> bool:` |
| 521 | fn | is_synthetic_value | pub | `def is_synthetic_value(value: str) -> bool:` |
| 529 | fn | _rule_for_value | (private) | `def _rule_for_value(value: str, *, assigned: bo...` |
| 545 | fn | _add_detection | (private) | `def _add_detection(` |
| 570 | fn | _skip_ws | (private) | `def _skip_ws(text: str, index: int) -> int:` |
| 576 | fn | _read_quoted | (private) | `def _read_quoted(text: str, index: int) -> tupl...` |
| 597 | fn | _read_concat_quoted | (private) | `def _read_concat_quoted(text: str, index: int) ...` |
| 623 | fn | _read_unquoted | (private) | `def _read_unquoted(text: str, index: int) -> tu...` |
| 630 | fn | _is_credential_field | (private) | `def _is_credential_field(name: str) -> bool:` |
| 634 | fn | _is_generic_reference_field | (private) | `def _is_generic_reference_field(name: str) -> b...` |
| 638 | fn | _is_code_expression | (private) | `def _is_code_expression(value: str) -> bool:` |
| 656 | fn | extract_assignments | pub | `def extract_assignments(line: str) -> list[tupl...` |
| 710 | fn | scan_text | pub | `def scan_text(path: str, text: str) -> list[dic...` |
| 772 | fn | _nul_ratio | (private) | `def _nul_ratio(raw: bytes, offset: int) -> float:` |
| 782 | fn | _looks_binary | (private) | `def _looks_binary(raw: bytes) -> bool:` |
| 790 | fn | decode_tracked_text | pub | `def decode_tracked_text(raw: bytes) -> tuple[st...` |
| 834 | fn | _valid_relpath | (private) | `def _valid_relpath(path: str) -> bool:` |
| 841 | fn | _load_json_bytes | (private) | `def _load_json_bytes(raw: bytes) -> Any:` |
| 848 | fn | _validate_declaration | (private) | `def _validate_declaration(payload: Any) -> dict...` |
| 903 | fn | _finding | (private) | `def _finding(` |
| 931 | fn | _error_result | (private) | `def _error_result(exc: SecretScanError, content...` |
| 956 | fn | make_result | pub | `def make_result(` |
| 987 | fn | _evaluate_declarations | (private) | `def _evaluate_declarations(` |
| 1138 | fn | _inherited_fixture_ids | (private) | `def _inherited_fixture_ids(` |
| 1173 | fn | _blob_types_and_sizes | (private) | `def _blob_types_and_sizes(root: Path, oids: lis...` |
| 1192 | fn | _read_blobs | (private) | `def _read_blobs(root: Path, oids: list[str]) ->...` |
| 1221 | fn | _scan_declaration_values | (private) | `def _scan_declaration_values(payload: Any, dete...` |
| 1233 | fn | _run_repository_scanners | (private) | `def _run_repository_scanners(root: Path) -> lis...` |
| 1289 | fn | _scan_regular_blobs | (private) | `def _scan_regular_blobs(` |
| 1352 | fn | _scan_worktree_managed_blobs | (private) | `def _scan_worktree_managed_blobs(` |
| 1389 | fn | _worktree_diff_statuses | (private) | `def _worktree_diff_statuses(root: Path, commit:...` |
| 1415 | fn | _untracked_worktree_paths | (private) | `def _untracked_worktree_paths(root: Path) -> li...` |
| 1420 | fn | _matches_declared_output | (private) | `def _matches_declared_output(path: str, pattern...` |
| 1433 | fn | _package_manifest_entries | (private) | `def _package_manifest_entries(root: Path) -> li...` |
| 1449 | fn | _generated_manifest_contract_declared | (private) | `def _generated_manifest_contract_declared(entri...` |
| 1458 | fn | _generated_transaction_paths | (private) | `def _generated_transaction_paths(root: Path, en...` |
| 1498 | fn | _managed_migration_paths | (private) | `def _managed_migration_paths(root: Path) -> set...` |
| 1522 | fn | _managed_transaction_paths | (private) | `def _managed_transaction_paths(root: Path) -> s...` |
| 1535 | fn | _change_scope_error_result | (private) | `def _change_scope_error_result(exc: SecretScanE...` |
| 1559 | fn | _scan_repository | (private) | `def _scan_repository(root: Path, baseline_evide...` |
| 1638 | fn | scan_repository | pub | `def scan_repository(` |
| 1660 | fn | identify_synthetic_candidates | pub | `def identify_synthetic_candidates(root: Path) -...` |
| 1685 | fn | main | pub | `def main(argv: list[str] | None = None) -> int:` |

## Public API

### `managed_scanner_policy_paths`

```
def managed_scanner_policy_paths(root: Path) -> tuple[str, ...]:
```

**Line:** 161 | **Kind:** fn

### `SecretScanError`

```
class SecretScanError(Exception):
```

**Line:** 172 | **Kind:** class

### `__init__`

```
def __init__(self, code: str, detail: str = "") -> None:
```

**Line:** 173 | **Kind:** fn

### `IndexEntry`

```
class IndexEntry:
```

**Line:** 180 | **Kind:** class

### `is_regular`

```
def is_regular(self) -> bool:
```

**Line:** 187 | **Kind:** fn

### `digest_bytes`

```
def digest_bytes(raw: bytes) -> str:
```

**Line:** 191 | **Kind:** fn

### `config_digest`

```
def config_digest(root: Path, paths: tuple[str, ...] | None = None) -> str:
```

**Line:** 244 | **Kind:** fn

### `changed_paths`

```
def changed_paths(root: Path, baseline_commit: str, candidate_commit: str) -> set[str]:
```

**Line:** 268 | **Kind:** fn

### `tracked_entries`

```
def tracked_entries(root: Path) -> list[IndexEntry]:
```

**Line:** 424 | **Kind:** fn

### `tracked_files`

```
def tracked_files(root: Path) -> list[str]:
```

**Line:** 451 | **Kind:** fn

### `candidate_content_tree`

```
def candidate_content_tree(root: Path) -> str:
```

**Line:** 455 | **Kind:** fn

### `is_realistic_value`

```
def is_realistic_value(value: str) -> bool:
```

**Line:** 508 | **Kind:** fn

### `is_synthetic_value`

```
def is_synthetic_value(value: str) -> bool:
```

**Line:** 521 | **Kind:** fn

### `extract_assignments`

```
def extract_assignments(line: str) -> list[tuple[str, str]]:
```

**Line:** 656 | **Kind:** fn

### `scan_text`

```
def scan_text(path: str, text: str) -> list[dict[str, Any]]:
```

**Line:** 710 | **Kind:** fn

### `decode_tracked_text`

```
def decode_tracked_text(raw: bytes) -> tuple[str | None, str]:
```

**Line:** 790 | **Kind:** fn

### `make_result`

```
def make_result(
```

**Line:** 956 | **Kind:** fn

### `scan_repository`

```
def scan_repository(
```

**Line:** 1638 | **Kind:** fn

### `identify_synthetic_candidates`

```
def identify_synthetic_candidates(root: Path) -> list[dict[str, Any]]:
```

**Line:** 1660 | **Kind:** fn

### `main`

```
def main(argv: list[str] | None = None) -> int:
```

**Line:** 1685 | **Kind:** fn
