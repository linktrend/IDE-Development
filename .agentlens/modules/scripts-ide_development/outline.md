# Outline

[← Back to MODULE](MODULE.md) | [← Back to INDEX](../../INDEX.md)

Symbol maps for 5 large files in this module.

## scripts/ide_development/build_manifest.py (1360 lines)

| Line | Kind | Name | Visibility |
| ---- | ---- | ---- | ---------- |
| 53 | fn | _apply_repo_root | (private) |
| 63 | fn | repo_root_context | pub |
| 190 | fn | _slug | (private) |
| 195 | fn | _entry | (private) |
| 233 | fn | _hash_rel | (private) |
| 242 | fn | _mode_for | (private) |
| 252 | fn | _sync_file | (private) |
| 257 | fn | _library_source_files | (private) |
| 272 | fn | _library_platform_rel | (private) |
| 276 | fn | _library_mapping_errors | (private) |
| 301 | fn | _hosted_workflow_files | (private) |
| 315 | fn | sync_package_payload | pub |
| 362 | fn | _gitops_script_sources | (private) |
| 396 | fn | build_entries | pub |
| 1217 | fn | build_manifest_object | pub |
| 1233 | fn | write_manifest | pub |
| 1244 | fn | _version_alignment_errors | (private) |
| 1266 | fn | _doctrine_sync_errors | (private) |
| 1283 | fn | verify_manifest | pub |
| 1332 | fn | main | pub |

## scripts/ide_development/engine.py (586 lines)

| Line | Kind | Name | Visibility |
| ---- | ---- | ---- | ---------- |
| 34 | fn | _load_repository_ci_contract_module | (private) |
| 73 | fn | _normalize_consumer_workflow_contract | (private) |
| 115 | class | EngineResult | pub |
| 116 | fn | __init__ | pub |
| 121 | fn | _detect_package_root | (private) |
| 128 | fn | _prepare | (private) |
| 143 | fn | _pending_recovery | (private) |
| 154 | fn | _maybe_recover | (private) |
| 163 | fn | _plan_payload | (private) |
| 169 | fn | _repository_ci_trigger_audit | (private) |
| 174 | fn | _resolve_authorized_upgrade | (private) |
| 218 | fn | _post_install_verification | (private) |
| 252 | fn | _run_post_install_secret_scan | (private) |
| 294 | fn | run_plan | pub |
| 352 | fn | run_install_or_update | pub |
| 450 | fn | run_drift | pub |
| 483 | fn | run_verify | pub |
| 532 | fn | run_version | pub |
| 562 | fn | run_rollback | pub |

## scripts/ide_development/plan.py (857 lines)

| Line | Kind | Name | Visibility |
| ---- | ---- | ---- | ---------- |
| 19 | class | OpKind | pub |
| 29 | class | DriftKind | pub |
| 40 | class | ConflictKind | pub |
| 51 | class | PlanAction | pub |
| 62 | fn | to_dict | pub |
| 81 | class | DriftItem | pub |
| 88 | fn | to_dict | pub |
| 102 | class | ConflictItem | pub |
| 107 | fn | to_dict | pub |
| 112 | class | Plan | pub |
| 121 | fn | to_dict | pub |
| 142 | fn | has_conflicts | pub |
| 146 | fn | has_drift | pub |
| 150 | fn | mutating_actions | pub |
| 158 | fn | _file_mode | (private) |
| 162 | fn | _classify_marker | (private) |
| 244 | fn | _classify_existing | (private) |
| 382 | fn | _plan_as_missing_under_migrate | (private) |
| 398 | fn | build_plan | pub |
| 435 | fn | dest_for | pub |
| 712 | fn | build_drift_report | pub |
| 856 | fn | meaningful_drift | pub |

## scripts/ide_development/release_candidate.py (1025 lines)

| Line | Kind | Name | Visibility |
| ---- | ---- | ---- | ---------- |
| 79 | fn | _is_code_call_assignment | (private) |
| 175 | class | ReleaseCandidateError | pub |
| 181 | fn | _repo_rel | (private) |
| 189 | fn | _read_text | (private) |
| 193 | fn | _git_output | (private) |
| 209 | fn | worktree_is_dirty | pub |
| 214 | fn | source_commit_sha | pub |
| 221 | fn | _normalize_version | (private) |
| 225 | fn | validate_versions | pub |
| 247 | fn | validate_schemas | pub |
| 271 | fn | validate_tests_and_evidence | pub |
| 295 | fn | regenerate_manifest_deterministically | pub |
| 320 | fn | _is_excluded_rel | (private) |
| 341 | fn | collect_package_paths | pub |
| 372 | fn | _refuse_symlink | (private) |
| 380 | fn | _scan_bytes_for_secrets | (private) |
| 399 | fn | _scan_bytes_for_host_paths | (private) |
| 424 | fn | stage_package_tree | pub |
| 465 | fn | _fixed_tarinfo | (private) |
| 478 | fn | build_tar_gz | pub |
| 502 | fn | build_zip | pub |
| 518 | fn | _archive_basename | (private) |
| 522 | fn | write_checksums | pub |
| 544 | fn | write_metadata | pub |
| 548 | fn | verify_archive_install | pub |
| 689 | fn | _safe_name | (private) |
| 694 | fn | create_release_candidate | pub |
| 874 | fn | verify_release_candidate_archive | pub |
| 908 | fn | build_parser | pub |
| 956 | fn | main | pub |

## scripts/ide_development/transaction.py (680 lines)

| Line | Kind | Name | Visibility |
| ---- | ---- | ---- | ---------- |
| 40 | class | BackupRecord | pub |
| 49 | fn | to_dict | pub |
| 63 | fn | from_dict | pub |
| 75 | fn | current_tx_dir | pub |
| 79 | fn | last_tx_dir | pub |
| 83 | fn | journal_path | pub |
| 87 | fn | backups_dir | pub |
| 91 | fn | read_journal | pub |
| 98 | fn | write_journal | pub |
| 104 | fn | _entry_map | (private) |
| 108 | fn | backup_migrate_symlink | pub |
| 138 | fn | backup_path | pub |
| 168 | fn | write_backup_file | pub |
| 178 | fn | apply_action | pub |
| 218 | fn | restore_backup | pub |
| 246 | fn | build_next_state | pub |
| 315 | fn | _promote_current_to_last | (private) |
| 325 | fn | _recover_interrupted_unlocked | (private) |
| 349 | fn | recover_interrupted | pub |
| 359 | fn | apply_plan | pub |
| 387 | fn | _apply_plan_unlocked | (private) |
| 627 | fn | rollback_last | pub |
| 633 | fn | _rollback_last_unlocked | (private) |
