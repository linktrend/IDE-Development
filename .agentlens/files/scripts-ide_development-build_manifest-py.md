# scripts/ide_development/build_manifest.py

[← Back to Module](../modules/scripts-ide_development/MODULE.md) | [← Back to INDEX](../INDEX.md)

## Overview

- **Lines:** 1360
- **Language:** Python
- **Symbols:** 20
- **Public symbols:** 7

## Symbol Table

| Line | Kind | Name | Visibility | Signature |
| ---- | ---- | ---- | ---------- | --------- |
| 53 | fn | _apply_repo_root | (private) | `def _apply_repo_root(root: Path) -> None:` |
| 63 | fn | repo_root_context | pub | `def repo_root_context(root: Path) -> Iterator[P...` |
| 190 | fn | _slug | (private) | `def _slug(text: str) -> str:` |
| 195 | fn | _entry | (private) | `def _entry(` |
| 233 | fn | _hash_rel | (private) | `def _hash_rel(rel: str) -> str:` |
| 242 | fn | _mode_for | (private) | `def _mode_for(path: Path) -> str:` |
| 252 | fn | _sync_file | (private) | `def _sync_file(src: Path, dest: Path) -> None:` |
| 257 | fn | _library_source_files | (private) | `def _library_source_files() -> list[tuple[str, ...` |
| 272 | fn | _library_platform_rel | (private) | `def _library_platform_rel(library_rel: str) -> ...` |
| 276 | fn | _library_mapping_errors | (private) | `def _library_mapping_errors() -> list[str]:` |
| 301 | fn | _hosted_workflow_files | (private) | `def _hosted_workflow_files() -> list[str]:` |
| 315 | fn | sync_package_payload | pub | `def sync_package_payload() -> None:` |
| 362 | fn | _gitops_script_sources | (private) | `def _gitops_script_sources() -> list[str]:` |
| 396 | fn | build_entries | pub | `def build_entries() -> list[dict[str, Any]]:` |
| 1217 | fn | build_manifest_object | pub | `def build_manifest_object() -> dict[str, Any]:` |
| 1233 | fn | write_manifest | pub | `def write_manifest(path: Path | None = None) ->...` |
| 1244 | fn | _version_alignment_errors | (private) | `def _version_alignment_errors() -> list[str]:` |
| 1266 | fn | _doctrine_sync_errors | (private) | `def _doctrine_sync_errors() -> list[str]:` |
| 1283 | fn | verify_manifest | pub | `def verify_manifest(path: Path | None = None) -...` |
| 1332 | fn | main | pub | `def main(argv: list[str] | None = None) -> int:` |

## Public API

### `repo_root_context`

```
def repo_root_context(root: Path) -> Iterator[Path]:
```

**Line:** 63 | **Kind:** fn

### `sync_package_payload`

```
def sync_package_payload() -> None:
```

**Line:** 315 | **Kind:** fn

### `build_entries`

```
def build_entries() -> list[dict[str, Any]]:
```

**Line:** 396 | **Kind:** fn

### `build_manifest_object`

```
def build_manifest_object() -> dict[str, Any]:
```

**Line:** 1217 | **Kind:** fn

### `write_manifest`

```
def write_manifest(path: Path | None = None) -> dict[str, Any]:
```

**Line:** 1233 | **Kind:** fn

### `verify_manifest`

```
def verify_manifest(path: Path | None = None) -> list[str]:
```

**Line:** 1283 | **Kind:** fn

### `main`

```
def main(argv: list[str] | None = None) -> int:
```

**Line:** 1332 | **Kind:** fn
