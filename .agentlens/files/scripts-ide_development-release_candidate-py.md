# scripts/ide_development/release_candidate.py

[← Back to Module](../modules/scripts-ide_development/MODULE.md) | [← Back to INDEX](../INDEX.md)

## Overview

- **Lines:** 1025
- **Language:** Python
- **Symbols:** 30
- **Public symbols:** 18

## Symbol Table

| Line | Kind | Name | Visibility | Signature |
| ---- | ---- | ---- | ---------- | --------- |
| 79 | fn | _is_code_call_assignment | (private) | `def _is_code_call_assignment(text: str, match: ...` |
| 175 | class | ReleaseCandidateError | pub | `class ReleaseCandidateError(InstallerError):` |
| 181 | fn | _repo_rel | (private) | `def _repo_rel(path: Path, *, root: Path = REPO_...` |
| 189 | fn | _read_text | (private) | `def _read_text(path: Path) -> str:` |
| 193 | fn | _git_output | (private) | `def _git_output(args: Sequence[str], *, cwd: Pa...` |
| 209 | fn | worktree_is_dirty | pub | `def worktree_is_dirty(repo_root: Path = REPO_RO...` |
| 214 | fn | source_commit_sha | pub | `def source_commit_sha(repo_root: Path = REPO_RO...` |
| 221 | fn | _normalize_version | (private) | `def _normalize_version(text: str) -> str:` |
| 225 | fn | validate_versions | pub | `def validate_versions(repo_root: Path = REPO_RO...` |
| 247 | fn | validate_schemas | pub | `def validate_schemas(repo_root: Path = REPO_ROO...` |
| 271 | fn | validate_tests_and_evidence | pub | `def validate_tests_and_evidence(repo_root: Path...` |
| 295 | fn | regenerate_manifest_deterministically | pub | `def regenerate_manifest_deterministically(repo_...` |
| 320 | fn | _is_excluded_rel | (private) | `def _is_excluded_rel(rel: str) -> bool:` |
| 341 | fn | collect_package_paths | pub | `def collect_package_paths(repo_root: Path = REP...` |
| 372 | fn | _refuse_symlink | (private) | `def _refuse_symlink(path: Path, rel: str) -> None:` |
| 380 | fn | _scan_bytes_for_secrets | (private) | `def _scan_bytes_for_secrets(rel: str, data: byt...` |
| 399 | fn | _scan_bytes_for_host_paths | (private) | `def _scan_bytes_for_host_paths(rel: str, data: ...` |
| 424 | fn | stage_package_tree | pub | `def stage_package_tree(` |
| 465 | fn | _fixed_tarinfo | (private) | `def _fixed_tarinfo(name: str, size: int, mode: ...` |
| 478 | fn | build_tar_gz | pub | `def build_tar_gz(staging_root: Path, archive_pa...` |
| 502 | fn | build_zip | pub | `def build_zip(staging_root: Path, archive_path:...` |
| 518 | fn | _archive_basename | (private) | `def _archive_basename(version: str) -> str:` |
| 522 | fn | write_checksums | pub | `def write_checksums(*, output_dir: Path, versio...` |
| 544 | fn | write_metadata | pub | `def write_metadata(path: Path, payload: dict[st...` |
| 548 | fn | verify_archive_install | pub | `def verify_archive_install(` |
| 689 | fn | _safe_name | (private) | `def _safe_name(name: str) -> str:` |
| 694 | fn | create_release_candidate | pub | `def create_release_candidate(` |
| 874 | fn | verify_release_candidate_archive | pub | `def verify_release_candidate_archive(` |
| 908 | fn | build_parser | pub | `def build_parser() -> argparse.ArgumentParser:` |
| 956 | fn | main | pub | `def main(argv: Sequence[str] | None = None) -> ...` |

## Public API

### `ReleaseCandidateError`

```
class ReleaseCandidateError(InstallerError):
```

**Line:** 175 | **Kind:** class

### `worktree_is_dirty`

```
def worktree_is_dirty(repo_root: Path = REPO_ROOT) -> bool:
```

**Line:** 209 | **Kind:** fn

### `source_commit_sha`

```
def source_commit_sha(repo_root: Path = REPO_ROOT) -> str:
```

**Line:** 214 | **Kind:** fn

### `validate_versions`

```
def validate_versions(repo_root: Path = REPO_ROOT) -> str:
```

**Line:** 225 | **Kind:** fn

### `validate_schemas`

```
def validate_schemas(repo_root: Path = REPO_ROOT) -> list[str]:
```

**Line:** 247 | **Kind:** fn

### `validate_tests_and_evidence`

```
def validate_tests_and_evidence(repo_root: Path = REPO_ROOT) -> list[str]:
```

**Line:** 271 | **Kind:** fn

### `regenerate_manifest_deterministically`

```
def regenerate_manifest_deterministically(repo_root: Path = REPO_ROOT) -> tuple[bytes, str]:
```

**Line:** 295 | **Kind:** fn

### `collect_package_paths`

```
def collect_package_paths(repo_root: Path = REPO_ROOT) -> list[str]:
```

**Line:** 341 | **Kind:** fn

### `stage_package_tree`

```
def stage_package_tree(
```

**Line:** 424 | **Kind:** fn

### `build_tar_gz`

```
def build_tar_gz(staging_root: Path, archive_path: Path, identities: Sequence[str]) -> int:
```

**Line:** 478 | **Kind:** fn

### `build_zip`

```
def build_zip(staging_root: Path, archive_path: Path, identities: Sequence[str]) -> int:
```

**Line:** 502 | **Kind:** fn

### `write_checksums`

```
def write_checksums(*, output_dir: Path, version: str, archives: list[dict[str, Any]]) -> Path:
```

**Line:** 522 | **Kind:** fn

### `write_metadata`

```
def write_metadata(path: Path, payload: dict[str, Any]) -> None:
```

**Line:** 544 | **Kind:** fn

### `verify_archive_install`

```
def verify_archive_install(
```

**Line:** 548 | **Kind:** fn

### `create_release_candidate`

```
def create_release_candidate(
```

**Line:** 694 | **Kind:** fn

### `verify_release_candidate_archive`

```
def verify_release_candidate_archive(
```

**Line:** 874 | **Kind:** fn

### `build_parser`

```
def build_parser() -> argparse.ArgumentParser:
```

**Line:** 908 | **Kind:** fn

### `main`

```
def main(argv: Sequence[str] | None = None) -> int:
```

**Line:** 956 | **Kind:** fn
