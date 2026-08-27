# scripts/gitops/generated_output_closure.py

[← Back to Module](../modules/root/MODULE.md) | [← Back to INDEX](../INDEX.md)

## Overview

- **Lines:** 1151
- **Language:** Python
- **Symbols:** 38
- **Public symbols:** 17

## Symbol Table

| Line | Kind | Name | Visibility | Signature |
| ---- | ---- | ---- | ---------- | --------- |
| 30 | class | ClosureError | pub | `class ClosureError(ValueError):` |
| 33 | fn | __init__ | pub | `def __init__(self, code: str, detail: str, **di...` |
| 42 | class | OutputSpec | pub | `class OutputSpec:` |
| 52 | class | GeneratedOutputGraph | pub | `class GeneratedOutputGraph:` |
| 59 | fn | output_paths | pub | `def output_paths(self) -> frozenset[str]:` |
| 62 | fn | ordered_outputs | pub | `def ordered_outputs(self) -> tuple[OutputSpec, ...` |
| 82 | fn | _relative | (private) | `def _relative(root: Path, path: Path) -> str:` |
| 86 | fn | _safe_relative | (private) | `def _safe_relative(value: object, label: str) -...` |
| 95 | fn | _resolve_graph_path | (private) | `def _resolve_graph_path(root: Path, graph_path:...` |
| 103 | fn | load_graph | pub | `def load_graph(repo_root: Path | str, graph_pat...` |
| 166 | fn | _audit_command | (private) | `def _audit_command(root: Path, command: Iterabl...` |
| 237 | fn | audit_dogfood_improvement_closure | pub | `def audit_dogfood_improvement_closure(` |
| 395 | fn | _git_index_entries | (private) | `def _git_index_entries(root: Path) -> list[tupl...` |
| 417 | fn | _expanded_exclusions | (private) | `def _expanded_exclusions(root: Path, graph: Gen...` |
| 425 | fn | _graph_exclusions | (private) | `def _graph_exclusions(root: Path, graph_path: s...` |
| 434 | fn | candidate_source_tree | pub | `def candidate_source_tree(root: Path | str, gra...` |
| 452 | fn | _walk_files | (private) | `def _walk_files(root: Path, exclusions: Iterabl...` |
| 465 | fn | _glob_matches | (private) | `def _glob_matches(rel: str, pattern: str) -> bool:` |
| 478 | fn | _source_paths | (private) | `def _source_paths(root: Path, spec: OutputSpec,...` |
| 491 | fn | _digest_file | (private) | `def _digest_file(path: Path) -> str:` |
| 495 | fn | _source_digest | (private) | `def _source_digest(root: Path, paths: Iterable[...` |
| 501 | fn | _output_digests | (private) | `def _output_digests(root: Path, graph: Generate...` |
| 512 | fn | _declared_output_paths | (private) | `def _declared_output_paths(root: Path, graph: G...` |
| 516 | fn | _git_dirty | (private) | `def _git_dirty(root: Path, rel: str) -> bool:` |
| 527 | fn | _diagnostic | (private) | `def _diagnostic(` |
| 550 | fn | close_generated_outputs | pub | `def close_generated_outputs(` |
| 679 | fn | _resolve_commit | (private) | `def _resolve_commit(root: Path, value: str) -> ...` |
| 692 | fn | _remote_target_ref | (private) | `def _remote_target_ref(root: Path, ref: str) ->...` |
| 713 | fn | _ensure_remote_target_ref | (private) | `def _ensure_remote_target_ref(root: Path, remot...` |
| 741 | fn | bind_push_event_baseline | pub | `def bind_push_event_baseline(` |
| 822 | fn | resolve_candidate_baseline | pub | `def resolve_candidate_baseline(` |
| 942 | fn | candidate_diff_check | pub | `def candidate_diff_check(` |
| 975 | fn | finalize_candidate | pub | `def finalize_candidate(` |
| 1008 | fn | _copy_for_verify | (private) | `def _copy_for_verify(source: Path, destination:...` |
| 1009 | fn | ignore | pub | `def ignore(_directory: str, names: list[str]) -...` |
| 1015 | fn | verify_generated_outputs | pub | `def verify_generated_outputs(` |
| 1061 | fn | _generate_secret_scan_fixtures | (private) | `def _generate_secret_scan_fixtures(repo_root: P...` |
| 1101 | fn | main | pub | `def main(argv: list[str] | None = None) -> int:` |

## Public API

### `ClosureError`

```
class ClosureError(ValueError):
```

**Line:** 30 | **Kind:** class

### `__init__`

```
def __init__(self, code: str, detail: str, **diagnostics: Any) -> None:
```

**Line:** 33 | **Kind:** fn

### `OutputSpec`

```
class OutputSpec:
```

**Line:** 42 | **Kind:** class

### `GeneratedOutputGraph`

```
class GeneratedOutputGraph:
```

**Line:** 52 | **Kind:** class

### `output_paths`

```
def output_paths(self) -> frozenset[str]:
```

**Line:** 59 | **Kind:** fn

### `ordered_outputs`

```
def ordered_outputs(self) -> tuple[OutputSpec, ...]:
```

**Line:** 62 | **Kind:** fn

### `load_graph`

```
def load_graph(repo_root: Path | str, graph_path: str = GRAPH_RELATIVE_PATH) -> GeneratedOutputGraph:
```

**Line:** 103 | **Kind:** fn

### `audit_dogfood_improvement_closure`

```
def audit_dogfood_improvement_closure(
```

**Line:** 237 | **Kind:** fn

### `candidate_source_tree`

```
def candidate_source_tree(root: Path | str, graph_path: str | None = GRAPH_RELATIVE_PATH) -> str:
```

**Line:** 434 | **Kind:** fn

### `close_generated_outputs`

```
def close_generated_outputs(
```

**Line:** 550 | **Kind:** fn

### `bind_push_event_baseline`

```
def bind_push_event_baseline(
```

**Line:** 741 | **Kind:** fn

### `resolve_candidate_baseline`

```
def resolve_candidate_baseline(
```

**Line:** 822 | **Kind:** fn

### `candidate_diff_check`

```
def candidate_diff_check(
```

**Line:** 942 | **Kind:** fn

### `finalize_candidate`

```
def finalize_candidate(
```

**Line:** 975 | **Kind:** fn

### `ignore`

```
def ignore(_directory: str, names: list[str]) -> set[str]:
```

**Line:** 1009 | **Kind:** fn

### `verify_generated_outputs`

```
def verify_generated_outputs(
```

**Line:** 1015 | **Kind:** fn

### `main`

```
def main(argv: list[str] | None = None) -> int:
```

**Line:** 1101 | **Kind:** fn
