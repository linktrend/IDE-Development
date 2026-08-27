# scripts/tests/test_fixture_aware_secret_scan.py

[← Back to Module](../modules/scripts-tests/MODULE.md) | [← Back to INDEX](../INDEX.md)

## Overview

- **Lines:** 1538
- **Language:** Python
- **Symbols:** 86
- **Public symbols:** 84

## Symbol Table

| Line | Kind | Name | Visibility | Signature |
| ---- | ---- | ---- | ---------- | --------- |
| 51 | fn | git | pub | `def git(root: Path, *args: str) -> str:` |
| 58 | fn | sha | pub | `def sha(root: Path, spec: str = "HEAD") -> str:` |
| 62 | fn | tree | pub | `def tree(root: Path, spec: str = "HEAD^{tree}")...` |
| 66 | fn | init_repo | pub | `def init_repo() -> tuple[tempfile.TemporaryDire...` |
| 80 | fn | write_tracked | pub | `def write_tracked(root: Path, rel: str, text: s...` |
| 87 | fn | write_tracked_bytes | pub | `def write_tracked_bytes(root: Path, rel: str, r...` |
| 94 | fn | commit | pub | `def commit(root: Path, message: str) -> tuple[s...` |
| 100 | fn | synthetic_value | pub | `def synthetic_value(name: str = "integrity-secr...` |
| 104 | fn | value_digest | pub | `def value_digest(value: str) -> str:` |
| 108 | class | CodeExpressionTests | pub | `class CodeExpressionTests(unittest.TestCase):` |
| 109 | fn | test_callable_keyword_arguments_are_not_credentials | pub | `def test_callable_keyword_arguments_are_not_cre...` |
| 115 | fn | test_bash_parameter_defaults_exclude_operator_from_secret_value | pub | `def test_bash_parameter_defaults_exclude_operat...` |
| 126 | fn | test_non_parameter_value_keeps_leading_dash | pub | `def test_non_parameter_value_keeps_leading_dash...` |
| 134 | class | ChangedPathStatusTests | pub | `class ChangedPathStatusTests(unittest.TestCase):` |
| 135 | fn | test_copy_status_includes_source_and_destination | pub | `def test_copy_status_includes_source_and_destin...` |
| 143 | fn | test_rename_status_includes_source_and_destination | pub | `def test_rename_status_includes_source_and_dest...` |
| 151 | fn | test_malformed_copy_status_fails_closed | pub | `def test_malformed_copy_status_fails_closed(sel...` |
| 157 | fn | test_delete_and_invalid_copy_paths_remain_fail_closed | pub | `def test_delete_and_invalid_copy_paths_remain_f...` |
| 169 | fn | test_declared_migration_deletion_is_included | pub | `def test_declared_migration_deletion_is_include...` |
| 184 | fn | test_undeclared_migration_deletion_fails_closed | pub | `def test_undeclared_migration_deletion_fails_cl...` |
| 194 | fn | declaration | pub | `def declaration(` |
| 209 | fn | fixture | pub | `def fixture(` |
| 231 | fn | write_declaration | pub | `def write_declaration(root: Path, payload: dict...` |
| 239 | fn | kinds | pub | `def kinds(result: dict) -> list[str]:` |
| 243 | fn | by_kind | pub | `def by_kind(result: dict, kind: str) -> list[di...` |
| 247 | class | PackagingContractTests | pub | `class PackagingContractTests(unittest.TestCase):` |
| 248 | fn | test_schemas_index_manifest_and_fast_cover_scanner | pub | `def test_schemas_index_manifest_and_fast_cover_...` |
| 305 | fn | test_checked_in_fixture_declaration_binds_current_candidate_tree | pub | `def test_checked_in_fixture_declaration_binds_c...` |
| 311 | fn | test_doctrine_and_installer_docs_name_fixture_contract | pub | `def test_doctrine_and_installer_docs_name_fixtu...` |
| 322 | class | AcU1001SyntheticLiteralTests | pub | `class AcU1001SyntheticLiteralTests(unittest.Tes...` |
| 323 | fn | test_declared_synthetic_assignment_passes_without_syntax_evasion | pub | `def test_declared_synthetic_assignment_passes_w...` |
| 361 | class | AcU1004ExactScopeTests | pub | `class AcU1004ExactScopeTests(unittest.TestCase):` |
| 362 | fn | test_same_bytes_in_other_file_line_field_or_production_path_fail | pub | `def test_same_bytes_in_other_file_line_field_or...` |
| 408 | class | AcU1005FailClosedTests | pub | `class AcU1005FailClosedTests(unittest.TestCase):` |
| 409 | fn | _declared_repo | (private) | `def _declared_repo(self, value: str | None = No...` |
| 433 | fn | test_one_byte_change_fails_closed | pub | `def test_one_byte_change_fails_closed(self) -> ...` |
| 443 | fn | test_stale_digest_fails_closed | pub | `def test_stale_digest_fails_closed(self) -> None:` |
| 454 | fn | test_renamed_file_fails_closed | pub | `def test_renamed_file_fails_closed(self) -> None:` |
| 469 | fn | test_duplicated_value_fails_closed | pub | `def test_duplicated_value_fails_closed(self) ->...` |
| 478 | fn | test_duplicate_fixture_ids_cannot_hide_stale_declaration | pub | `def test_duplicate_fixture_ids_cannot_hide_stal...` |
| 521 | fn | test_unknown_rule_fails_closed | pub | `def test_unknown_rule_fails_closed(self) -> None:` |
| 532 | fn | test_undeclared_fixture_fails_closed | pub | `def test_undeclared_fixture_fails_closed(self) ...` |
| 542 | class | AcU1006RealisticFormatsTests | pub | `class AcU1006RealisticFormatsTests(unittest.Tes...` |
| 543 | fn | test_realistic_formats_cannot_be_approved | pub | `def test_realistic_formats_cannot_be_approved(s...` |
| 592 | class | AcU1007AggregationTests | pub | `class AcU1007AggregationTests(unittest.TestCase):` |
| 593 | fn | test_one_run_reports_all_findings_and_fixture_errors | pub | `def test_one_run_reports_all_findings_and_fixtu...` |
| 635 | class | AcU1008BindingTests | pub | `class AcU1008BindingTests(unittest.TestCase):` |
| 636 | fn | test_tree_or_policy_change_invalidates_until_refresh | pub | `def test_tree_or_policy_change_invalidates_unti...` |
| 679 | fn | test_changed_package_source_refreshes_binding_without_oscillation | pub | `def test_changed_package_source_refreshes_bindi...` |
| 723 | class | AcU1002NoBlindSpotTests | pub | `class AcU1002NoBlindSpotTests(unittest.TestCase):` |
| 724 | fn | test_production_path_and_test_directory_are_both_scanned | pub | `def test_production_path_and_test_directory_are...` |
| 736 | fn | test_missing_or_malformed_declaration_fails_closed | pub | `def test_missing_or_malformed_declaration_fails...` |
| 751 | class | AcU1009RepositoryScannersTests | pub | `class AcU1009RepositoryScannersTests(unittest.T...` |
| 752 | fn | test_repository_owned_scanner_failure_remains_blocking | pub | `def test_repository_owned_scanner_failure_remai...` |
| 797 | fn | test_fixture_declaration_cannot_suppress_repository_scanner | pub | `def test_fixture_declaration_cannot_suppress_re...` |
| 823 | class | AcU1003MigrationHelperTests | pub | `class AcU1003MigrationHelperTests(unittest.Test...` |
| 824 | fn | test_migration_identifies_candidates_and_never_writes_approval | pub | `def test_migration_identifies_candidates_and_ne...` |
| 850 | class | CliAggregationTests | pub | `class CliAggregationTests(unittest.TestCase):` |
| 851 | fn | test_cli_writes_aggregate_result_and_nonzero_on_findings | pub | `def test_cli_writes_aggregate_result_and_nonzer...` |
| 870 | class | AdversarialRepairTests | pub | `class AdversarialRepairTests(unittest.TestCase):` |
| 871 | fn | test_directory_symlink_and_option_like_path_use_index_identities | pub | `def test_directory_symlink_and_option_like_path...` |
| 891 | fn | test_suffix_named_text_and_utf16_are_scanned | pub | `def test_suffix_named_text_and_utf16_are_scanne...` |
| 911 | fn | test_declaration_bytes_and_notes_cannot_hide_credentials | pub | `def test_declaration_bytes_and_notes_cannot_hid...` |
| 946 | fn | test_unquoted_env_yaml_short_and_escaped_secrets | pub | `def test_unquoted_env_yaml_short_and_escaped_se...` |
| 972 | fn | test_quoted_member_and_call_references_are_not_assignment_findings | pub | `def test_quoted_member_and_call_references_are_...` |
| 981 | fn | test_six_credential_formats_remain_blocking | pub | `def test_six_credential_formats_remain_blocking...` |
| 1002 | fn | test_huge_input_and_scanner_timeout_are_typed_results | pub | `def test_huge_input_and_scanner_timeout_are_typ...` |
| 1025 | fn | test_schema_extras_and_typed_failures_match_result_schema | pub | `def test_schema_extras_and_typed_failures_match...` |
| 1059 | fn | test_undecodable_nul_content_fails_closed | pub | `def test_undecodable_nul_content_fails_closed(s...` |
| 1068 | fn | test_binary_and_high_control_content_is_typed_nonblocking_skip | pub | `def test_binary_and_high_control_content_is_typ...` |
| 1077 | fn | test_bound_bytes_must_match_detected_value | pub | `def test_bound_bytes_must_match_detected_value(...` |
| 1103 | fn | test_matching_bytes_still_approve_synthetic_only | pub | `def test_matching_bytes_still_approve_synthetic...` |
| 1130 | class | ChangeScopedEvidenceTests | pub | `class ChangeScopedEvidenceTests(unittest.TestCa...` |
| 1131 | fn | _candidate_with_baseline | (private) | `def _candidate_with_baseline(self) -> tuple[tem...` |
| 1160 | fn | test_changed_credential_blocks_and_unchanged_finding_is_inherited | pub | `def test_changed_credential_blocks_and_unchange...` |
| 1181 | fn | test_unchanged_baseline_fixture_declaration_is_inherited | pub | `def test_unchanged_baseline_fixture_declaration...` |
| 1235 | fn | test_changed_source_cannot_use_inherited_fixture_row | pub | `def test_changed_source_cannot_use_inherited_fi...` |
| 1249 | fn | test_ten_thousand_approved_inherited_findings_do_not_force_full_rescan | pub | `def test_ten_thousand_approved_inherited_findin...` |
| 1282 | fn | test_identity_config_and_managed_path_drift_fail_closed | pub | `def test_identity_config_and_managed_path_drift...` |
| 1296 | fn | test_expected_managed_edit_is_scanned_but_unrelated_dirty_state_blocks | pub | `def test_expected_managed_edit_is_scanned_but_u...` |
| 1329 | fn | test_installer_manifest_destinations_are_allowed_but_unrelated_dirty_is_not | pub | `def test_installer_manifest_destinations_are_al...` |
| 1347 | fn | test_untracked_installer_manifest_destination_is_allowed_but_unrelated_is_not | pub | `def test_untracked_installer_manifest_destinati...` |
| 1364 | fn | test_generated_manifest_and_declared_migration_cleanup_are_allowed_but_unrelated_paths_block | pub | `def test_generated_manifest_and_declared_migrat...` |
| 1466 | fn | test_absent_declared_migration_path_is_allowed_but_absent_unrelated_path_blocks | pub | `def test_absent_declared_migration_path_is_allo...` |
| 1516 | fn | test_rename_is_scope_ambiguity_not_an_ignore | pub | `def test_rename_is_scope_ambiguity_not_an_ignor...` |
| 1527 | fn | test_extracted_managed_root_uses_packaged_policy_paths | pub | `def test_extracted_managed_root_uses_packaged_p...` |

## Public API

### `git`

```
def git(root: Path, *args: str) -> str:
```

**Line:** 51 | **Kind:** fn

### `sha`

```
def sha(root: Path, spec: str = "HEAD") -> str:
```

**Line:** 58 | **Kind:** fn

### `tree`

```
def tree(root: Path, spec: str = "HEAD^{tree}") -> str:
```

**Line:** 62 | **Kind:** fn

### `init_repo`

```
def init_repo() -> tuple[tempfile.TemporaryDirectory[str], Path]:
```

**Line:** 66 | **Kind:** fn

### `write_tracked`

```
def write_tracked(root: Path, rel: str, text: str) -> None:
```

**Line:** 80 | **Kind:** fn

### `write_tracked_bytes`

```
def write_tracked_bytes(root: Path, rel: str, raw: bytes) -> None:
```

**Line:** 87 | **Kind:** fn

### `commit`

```
def commit(root: Path, message: str) -> tuple[str, str]:
```

**Line:** 94 | **Kind:** fn

### `synthetic_value`

```
def synthetic_value(name: str = "integrity-secret-property") -> str:
```

**Line:** 100 | **Kind:** fn

### `value_digest`

```
def value_digest(value: str) -> str:
```

**Line:** 104 | **Kind:** fn

### `CodeExpressionTests`

```
class CodeExpressionTests(unittest.TestCase):
```

**Line:** 108 | **Kind:** class

### `test_callable_keyword_arguments_are_not_credentials`

```
def test_callable_keyword_arguments_are_not_credentials(self) -> None:
```

**Line:** 109 | **Kind:** fn

### `test_bash_parameter_defaults_exclude_operator_from_secret_value`

```
def test_bash_parameter_defaults_exclude_operator_from_secret_value(self) -> None:
```

**Line:** 115 | **Kind:** fn

### `test_non_parameter_value_keeps_leading_dash`

```
def test_non_parameter_value_keeps_leading_dash(self) -> None:
```

**Line:** 126 | **Kind:** fn

### `ChangedPathStatusTests`

```
class ChangedPathStatusTests(unittest.TestCase):
```

**Line:** 134 | **Kind:** class

### `test_copy_status_includes_source_and_destination`

```
def test_copy_status_includes_source_and_destination(self) -> None:
```

**Line:** 135 | **Kind:** fn

### `test_rename_status_includes_source_and_destination`

```
def test_rename_status_includes_source_and_destination(self) -> None:
```

**Line:** 143 | **Kind:** fn

### `test_malformed_copy_status_fails_closed`

```
def test_malformed_copy_status_fails_closed(self) -> None:
```

**Line:** 151 | **Kind:** fn

### `test_delete_and_invalid_copy_paths_remain_fail_closed`

```
def test_delete_and_invalid_copy_paths_remain_fail_closed(self) -> None:
```

**Line:** 157 | **Kind:** fn

### `test_declared_migration_deletion_is_included`

```
def test_declared_migration_deletion_is_included(self) -> None:
```

**Line:** 169 | **Kind:** fn

### `test_undeclared_migration_deletion_fails_closed`

```
def test_undeclared_migration_deletion_fails_closed(self) -> None:
```

**Line:** 184 | **Kind:** fn

### `declaration`

```
def declaration(
```

**Line:** 194 | **Kind:** fn

### `fixture`

```
def fixture(
```

**Line:** 209 | **Kind:** fn

### `write_declaration`

```
def write_declaration(root: Path, payload: dict, rel: str = ".github/linktrend-secret-scan-fixtures.json") -> Path:
```

**Line:** 231 | **Kind:** fn

### `kinds`

```
def kinds(result: dict) -> list[str]:
```

**Line:** 239 | **Kind:** fn

### `by_kind`

```
def by_kind(result: dict, kind: str) -> list[dict]:
```

**Line:** 243 | **Kind:** fn

### `PackagingContractTests`

```
class PackagingContractTests(unittest.TestCase):
```

**Line:** 247 | **Kind:** class

### `test_schemas_index_manifest_and_fast_cover_scanner`

```
def test_schemas_index_manifest_and_fast_cover_scanner(self) -> None:
```

**Line:** 248 | **Kind:** fn

### `test_checked_in_fixture_declaration_binds_current_candidate_tree`

```
def test_checked_in_fixture_declaration_binds_current_candidate_tree(self) -> None:
```

**Line:** 305 | **Kind:** fn

### `test_doctrine_and_installer_docs_name_fixture_contract`

```
def test_doctrine_and_installer_docs_name_fixture_contract(self) -> None:
```

**Line:** 311 | **Kind:** fn

### `AcU1001SyntheticLiteralTests`

```
class AcU1001SyntheticLiteralTests(unittest.TestCase):
```

**Line:** 322 | **Kind:** class

### `test_declared_synthetic_assignment_passes_without_syntax_evasion`

```
def test_declared_synthetic_assignment_passes_without_syntax_evasion(self) -> None:
```

**Line:** 323 | **Kind:** fn

### `AcU1004ExactScopeTests`

```
class AcU1004ExactScopeTests(unittest.TestCase):
```

**Line:** 361 | **Kind:** class

### `test_same_bytes_in_other_file_line_field_or_production_path_fail`

```
def test_same_bytes_in_other_file_line_field_or_production_path_fail(self) -> None:
```

**Line:** 362 | **Kind:** fn

### `AcU1005FailClosedTests`

```
class AcU1005FailClosedTests(unittest.TestCase):
```

**Line:** 408 | **Kind:** class

### `test_one_byte_change_fails_closed`

```
def test_one_byte_change_fails_closed(self) -> None:
```

**Line:** 433 | **Kind:** fn

### `test_stale_digest_fails_closed`

```
def test_stale_digest_fails_closed(self) -> None:
```

**Line:** 443 | **Kind:** fn

### `test_renamed_file_fails_closed`

```
def test_renamed_file_fails_closed(self) -> None:
```

**Line:** 454 | **Kind:** fn

### `test_duplicated_value_fails_closed`

```
def test_duplicated_value_fails_closed(self) -> None:
```

**Line:** 469 | **Kind:** fn

### `test_duplicate_fixture_ids_cannot_hide_stale_declaration`

```
def test_duplicate_fixture_ids_cannot_hide_stale_declaration(self) -> None:
```

**Line:** 478 | **Kind:** fn

### `test_unknown_rule_fails_closed`

```
def test_unknown_rule_fails_closed(self) -> None:
```

**Line:** 521 | **Kind:** fn

### `test_undeclared_fixture_fails_closed`

```
def test_undeclared_fixture_fails_closed(self) -> None:
```

**Line:** 532 | **Kind:** fn

### `AcU1006RealisticFormatsTests`

```
class AcU1006RealisticFormatsTests(unittest.TestCase):
```

**Line:** 542 | **Kind:** class

### `test_realistic_formats_cannot_be_approved`

```
def test_realistic_formats_cannot_be_approved(self) -> None:
```

**Line:** 543 | **Kind:** fn

### `AcU1007AggregationTests`

```
class AcU1007AggregationTests(unittest.TestCase):
```

**Line:** 592 | **Kind:** class

### `test_one_run_reports_all_findings_and_fixture_errors`

```
def test_one_run_reports_all_findings_and_fixture_errors(self) -> None:
```

**Line:** 593 | **Kind:** fn

### `AcU1008BindingTests`

```
class AcU1008BindingTests(unittest.TestCase):
```

**Line:** 635 | **Kind:** class

### `test_tree_or_policy_change_invalidates_until_refresh`

```
def test_tree_or_policy_change_invalidates_until_refresh(self) -> None:
```

**Line:** 636 | **Kind:** fn

### `test_changed_package_source_refreshes_binding_without_oscillation`

```
def test_changed_package_source_refreshes_binding_without_oscillation(self) -> None:
```

**Line:** 679 | **Kind:** fn

### `AcU1002NoBlindSpotTests`

```
class AcU1002NoBlindSpotTests(unittest.TestCase):
```

**Line:** 723 | **Kind:** class

### `test_production_path_and_test_directory_are_both_scanned`

```
def test_production_path_and_test_directory_are_both_scanned(self) -> None:
```

**Line:** 724 | **Kind:** fn

### `test_missing_or_malformed_declaration_fails_closed`

```
def test_missing_or_malformed_declaration_fails_closed(self) -> None:
```

**Line:** 736 | **Kind:** fn

### `AcU1009RepositoryScannersTests`

```
class AcU1009RepositoryScannersTests(unittest.TestCase):
```

**Line:** 751 | **Kind:** class

### `test_repository_owned_scanner_failure_remains_blocking`

```
def test_repository_owned_scanner_failure_remains_blocking(self) -> None:
```

**Line:** 752 | **Kind:** fn

### `test_fixture_declaration_cannot_suppress_repository_scanner`

```
def test_fixture_declaration_cannot_suppress_repository_scanner(self) -> None:
```

**Line:** 797 | **Kind:** fn

### `AcU1003MigrationHelperTests`

```
class AcU1003MigrationHelperTests(unittest.TestCase):
```

**Line:** 823 | **Kind:** class

### `test_migration_identifies_candidates_and_never_writes_approval`

```
def test_migration_identifies_candidates_and_never_writes_approval(self) -> None:
```

**Line:** 824 | **Kind:** fn

### `CliAggregationTests`

```
class CliAggregationTests(unittest.TestCase):
```

**Line:** 850 | **Kind:** class

### `test_cli_writes_aggregate_result_and_nonzero_on_findings`

```
def test_cli_writes_aggregate_result_and_nonzero_on_findings(self) -> None:
```

**Line:** 851 | **Kind:** fn

### `AdversarialRepairTests`

```
class AdversarialRepairTests(unittest.TestCase):
```

**Line:** 870 | **Kind:** class

### `test_directory_symlink_and_option_like_path_use_index_identities`

```
def test_directory_symlink_and_option_like_path_use_index_identities(self) -> None:
```

**Line:** 871 | **Kind:** fn

### `test_suffix_named_text_and_utf16_are_scanned`

```
def test_suffix_named_text_and_utf16_are_scanned(self) -> None:
```

**Line:** 891 | **Kind:** fn

### `test_declaration_bytes_and_notes_cannot_hide_credentials`

```
def test_declaration_bytes_and_notes_cannot_hide_credentials(self) -> None:
```

**Line:** 911 | **Kind:** fn

### `test_unquoted_env_yaml_short_and_escaped_secrets`

```
def test_unquoted_env_yaml_short_and_escaped_secrets(self) -> None:
```

**Line:** 946 | **Kind:** fn

### `test_quoted_member_and_call_references_are_not_assignment_findings`

```
def test_quoted_member_and_call_references_are_not_assignment_findings(self) -> None:
```

**Line:** 972 | **Kind:** fn

### `test_six_credential_formats_remain_blocking`

```
def test_six_credential_formats_remain_blocking(self) -> None:
```

**Line:** 981 | **Kind:** fn

### `test_huge_input_and_scanner_timeout_are_typed_results`

```
def test_huge_input_and_scanner_timeout_are_typed_results(self) -> None:
```

**Line:** 1002 | **Kind:** fn

### `test_schema_extras_and_typed_failures_match_result_schema`

```
def test_schema_extras_and_typed_failures_match_result_schema(self) -> None:
```

**Line:** 1025 | **Kind:** fn

### `test_undecodable_nul_content_fails_closed`

```
def test_undecodable_nul_content_fails_closed(self) -> None:
```

**Line:** 1059 | **Kind:** fn

### `test_binary_and_high_control_content_is_typed_nonblocking_skip`

```
def test_binary_and_high_control_content_is_typed_nonblocking_skip(self) -> None:
```

**Line:** 1068 | **Kind:** fn

### `test_bound_bytes_must_match_detected_value`

```
def test_bound_bytes_must_match_detected_value(self) -> None:
```

**Line:** 1077 | **Kind:** fn

### `test_matching_bytes_still_approve_synthetic_only`

```
def test_matching_bytes_still_approve_synthetic_only(self) -> None:
```

**Line:** 1103 | **Kind:** fn

### `ChangeScopedEvidenceTests`

```
class ChangeScopedEvidenceTests(unittest.TestCase):
```

**Line:** 1130 | **Kind:** class

### `test_changed_credential_blocks_and_unchanged_finding_is_inherited`

```
def test_changed_credential_blocks_and_unchanged_finding_is_inherited(self) -> None:
```

**Line:** 1160 | **Kind:** fn

### `test_unchanged_baseline_fixture_declaration_is_inherited`

```
def test_unchanged_baseline_fixture_declaration_is_inherited(self) -> None:
```

**Line:** 1181 | **Kind:** fn

### `test_changed_source_cannot_use_inherited_fixture_row`

```
def test_changed_source_cannot_use_inherited_fixture_row(self) -> None:
```

**Line:** 1235 | **Kind:** fn

### `test_ten_thousand_approved_inherited_findings_do_not_force_full_rescan`

```
def test_ten_thousand_approved_inherited_findings_do_not_force_full_rescan(self) -> None:
```

**Line:** 1249 | **Kind:** fn

### `test_identity_config_and_managed_path_drift_fail_closed`

```
def test_identity_config_and_managed_path_drift_fail_closed(self) -> None:
```

**Line:** 1282 | **Kind:** fn

### `test_expected_managed_edit_is_scanned_but_unrelated_dirty_state_blocks`

```
def test_expected_managed_edit_is_scanned_but_unrelated_dirty_state_blocks(self) -> None:
```

**Line:** 1296 | **Kind:** fn

### `test_installer_manifest_destinations_are_allowed_but_unrelated_dirty_is_not`

```
def test_installer_manifest_destinations_are_allowed_but_unrelated_dirty_is_not(self) -> None:
```

**Line:** 1329 | **Kind:** fn

### `test_untracked_installer_manifest_destination_is_allowed_but_unrelated_is_not`

```
def test_untracked_installer_manifest_destination_is_allowed_but_unrelated_is_not(self) -> None:
```

**Line:** 1347 | **Kind:** fn

### `test_generated_manifest_and_declared_migration_cleanup_are_allowed_but_unrelated_paths_block`

```
def test_generated_manifest_and_declared_migration_cleanup_are_allowed_but_unrelated_paths_block(self) -> None:
```

**Line:** 1364 | **Kind:** fn

### `test_absent_declared_migration_path_is_allowed_but_absent_unrelated_path_blocks`

```
def test_absent_declared_migration_path_is_allowed_but_absent_unrelated_path_blocks(self) -> None:
```

**Line:** 1466 | **Kind:** fn

### `test_rename_is_scope_ambiguity_not_an_ignore`

```
def test_rename_is_scope_ambiguity_not_an_ignore(self) -> None:
```

**Line:** 1516 | **Kind:** fn

### `test_extracted_managed_root_uses_packaged_policy_paths`

```
def test_extracted_managed_root_uses_packaged_policy_paths(self) -> None:
```

**Line:** 1527 | **Kind:** fn
