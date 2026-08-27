# scripts/tests/test_linktrend_review_gate.py

[← Back to Module](../modules/scripts-tests/MODULE.md) | [← Back to INDEX](../INDEX.md)

## Overview

- **Lines:** 2336
- **Language:** Python
- **Symbols:** 43
- **Public symbols:** 34

## Symbol Table

| Line | Kind | Name | Visibility | Signature |
| ---- | ---- | ---- | ---------- | --------- |
| 88 | fn | _actions_check | (private) | `def _actions_check(` |
| 115 | fn | _workflow_run | (private) | `def _workflow_run(` |
| 136 | fn | _jobs_for | (private) | `def _jobs_for(` |
| 157 | fn | _wf_shas | (private) | `def _wf_shas(` |
| 172 | fn | _trusted_extract_kwargs | (private) | `def _trusted_extract_kwargs(` |
| 203 | fn | _trusted_provenance | (private) | `def _trusted_provenance(kind: str = "github.rep...` |
| 211 | fn | _verified_quota | (private) | `def _verified_quota(*, source: str = "repair_ob...` |
| 228 | fn | _trusted_full_receipt | (private) | `def _trusted_full_receipt(**overrides) -> dict:` |
| 254 | class | LinktrendReviewGateTests | pub | `class LinktrendReviewGateTests(unittest.TestCase):` |
| 255 | fn | test_packaged_surfaces_exist | pub | `def test_packaged_surfaces_exist(self) -> None:` |
| 294 | fn | _classify | (private) | `def _classify(self, **kwargs):` |
| 308 | fn | test_all_classified_outcomes | pub | `def test_all_classified_outcomes(self) -> None:` |
| 357 | fn | test_failure_never_becomes_advisory_via_heuristic | pub | `def test_failure_never_becomes_advisory_via_heu...` |
| 388 | fn | test_fail_closed_missing_malformed_forged_wrong_head | pub | `def test_fail_closed_missing_malformed_forged_w...` |
| 399 | fn | test_full_failure_blocks_bugbot_request | pub | `def test_full_failure_blocks_bugbot_request(sel...` |
| 405 | fn | test_full_receipt_required_before_successful_gate_publish | pub | `def test_full_receipt_required_before_successfu...` |
| 517 | fn | test_normalize_full_receipt_never_injects_live_tree | pub | `def test_normalize_full_receipt_never_injects_l...` |
| 549 | fn | test_overlay_retained_full_suite_receipt_fills_git_tree | pub | `def test_overlay_retained_full_suite_receipt_fi...` |
| 594 | fn | test_infrastructure_attempts_count_only_infra_markers | pub | `def test_infrastructure_attempts_count_only_inf...` |
| 617 | fn | test_new_commit_invalidates_prior_outcome | pub | `def test_new_commit_invalidates_prior_outcome(s...` |
| 622 | fn | test_raw_bugbot_required_contexts_rejected | pub | `def test_raw_bugbot_required_contexts_rejected(...` |
| 632 | fn | test_protection_and_consumer_defaults_migrated | pub | `def test_protection_and_consumer_defaults_migra...` |
| 646 | fn | test_managed_surfaces_reject_raw_bugbot_required_defaults | pub | `def test_managed_surfaces_reject_raw_bugbot_req...` |
| 692 | fn | test_workflow_forbids_heuristic_and_wires_alert_fallback_full | pub | `def test_workflow_forbids_heuristic_and_wires_a...` |
| 793 | fn | test_pr_cannot_rewrite_classifier_or_self_approve | pub | `def test_pr_cannot_rewrite_classifier_or_self_a...` |
| 849 | fn | test_durable_founder_alert_dedupe_and_fail_closed | pub | `def test_durable_founder_alert_dedupe_and_fail_...` |
| 894 | fn | test_workflow_path_wrong_tree_receipt_negative | pub | `def test_workflow_path_wrong_tree_receipt_negat...` |
| 918 | fn | test_candidate_planted_allowlisted_provider_evidence_never_authorizes_success | pub | `def test_candidate_planted_allowlisted_provider...` |
| 986 | fn | test_forged_full_receipt_authorship_and_candidate_file_provenance | pub | `def test_forged_full_receipt_authorship_and_can...` |
| 1117 | fn | test_details_url_hijack_and_producer_membership_binding | pub | `def test_details_url_hijack_and_producer_member...` |
| 1317 | fn | test_same_app_check_name_collision_requires_default_branch_workflow_identity | pub | `def test_same_app_check_name_collision_requires...` |
| 1577 | fn | fake_lookup | pub | `def fake_lookup(path: str, ref: str) -> str:` |
| 1601 | fn | test_provider_extractor_requires_exact_item_and_run_head | pub | `def test_provider_extractor_requires_exact_item...` |
| 1677 | fn | test_paginated_slurp_flatten_multi_page_bodies_and_dedupe | pub | `def test_paginated_slurp_flatten_multi_page_bod...` |
| 1727 | fn | test_slurp_json_stdin_handles_arg_max_and_pipefail_hold | pub | `def test_slurp_json_stdin_handles_arg_max_and_p...` |
| 1822 | fn | test_undocumented_task_hold_rejected | pub | `def test_undocumented_task_hold_rejected(self) ...` |
| 1828 | fn | test_fallback_reviewer_rules_and_comment | pub | `def test_fallback_reviewer_rules_and_comment(se...` |
| 1861 | fn | test_same_account_comment_not_github_approval | pub | `def test_same_account_comment_not_github_approv...` |
| 1884 | fn | test_observer_rejects_raw_bugbot_as_managed_gate | pub | `def test_observer_rejects_raw_bugbot_as_managed...` |
| 1914 | fn | test_workflow_static_no_trailing_whitespace | pub | `def test_workflow_static_no_trailing_whitespace...` |
| 1924 | fn | test_detect_findings_from_trustworthy_event_evidence | pub | `def test_detect_findings_from_trustworthy_event...` |
| 2003 | fn | test_candidate_cannot_replace_classifier_or_self_approve | pub | `def test_candidate_cannot_replace_classifier_or...` |
| 2138 | fn | test_planted_allowlisted_provider_error_and_forged_receipt_rejected | pub | `def test_planted_allowlisted_provider_error_and...` |

## Public API

### `LinktrendReviewGateTests`

```
class LinktrendReviewGateTests(unittest.TestCase):
```

**Line:** 254 | **Kind:** class

### `test_packaged_surfaces_exist`

```
def test_packaged_surfaces_exist(self) -> None:
```

**Line:** 255 | **Kind:** fn

### `test_all_classified_outcomes`

```
def test_all_classified_outcomes(self) -> None:
```

**Line:** 308 | **Kind:** fn

### `test_failure_never_becomes_advisory_via_heuristic`

```
def test_failure_never_becomes_advisory_via_heuristic(self) -> None:
```

**Line:** 357 | **Kind:** fn

### `test_fail_closed_missing_malformed_forged_wrong_head`

```
def test_fail_closed_missing_malformed_forged_wrong_head(self) -> None:
```

**Line:** 388 | **Kind:** fn

### `test_full_failure_blocks_bugbot_request`

```
def test_full_failure_blocks_bugbot_request(self) -> None:
```

**Line:** 399 | **Kind:** fn

### `test_full_receipt_required_before_successful_gate_publish`

```
def test_full_receipt_required_before_successful_gate_publish(self) -> None:
```

**Line:** 405 | **Kind:** fn

### `test_normalize_full_receipt_never_injects_live_tree`

```
def test_normalize_full_receipt_never_injects_live_tree(self) -> None:
```

**Line:** 517 | **Kind:** fn

### `test_overlay_retained_full_suite_receipt_fills_git_tree`

```
def test_overlay_retained_full_suite_receipt_fills_git_tree(self) -> None:
```

**Line:** 549 | **Kind:** fn

### `test_infrastructure_attempts_count_only_infra_markers`

```
def test_infrastructure_attempts_count_only_infra_markers(self) -> None:
```

**Line:** 594 | **Kind:** fn

### `test_new_commit_invalidates_prior_outcome`

```
def test_new_commit_invalidates_prior_outcome(self) -> None:
```

**Line:** 617 | **Kind:** fn

### `test_raw_bugbot_required_contexts_rejected`

```
def test_raw_bugbot_required_contexts_rejected(self) -> None:
```

**Line:** 622 | **Kind:** fn

### `test_protection_and_consumer_defaults_migrated`

```
def test_protection_and_consumer_defaults_migrated(self) -> None:
```

**Line:** 632 | **Kind:** fn

### `test_managed_surfaces_reject_raw_bugbot_required_defaults`

```
def test_managed_surfaces_reject_raw_bugbot_required_defaults(self) -> None:
```

**Line:** 646 | **Kind:** fn

### `test_workflow_forbids_heuristic_and_wires_alert_fallback_full`

```
def test_workflow_forbids_heuristic_and_wires_alert_fallback_full(self) -> None:
```

**Line:** 692 | **Kind:** fn

### `test_pr_cannot_rewrite_classifier_or_self_approve`

```
def test_pr_cannot_rewrite_classifier_or_self_approve(self) -> None:
```

**Line:** 793 | **Kind:** fn

### `test_durable_founder_alert_dedupe_and_fail_closed`

```
def test_durable_founder_alert_dedupe_and_fail_closed(self) -> None:
```

**Line:** 849 | **Kind:** fn

### `test_workflow_path_wrong_tree_receipt_negative`

```
def test_workflow_path_wrong_tree_receipt_negative(self) -> None:
```

**Line:** 894 | **Kind:** fn

### `test_candidate_planted_allowlisted_provider_evidence_never_authorizes_success`

```
def test_candidate_planted_allowlisted_provider_evidence_never_authorizes_success(self) -> None:
```

**Line:** 918 | **Kind:** fn

### `test_forged_full_receipt_authorship_and_candidate_file_provenance`

```
def test_forged_full_receipt_authorship_and_candidate_file_provenance(self) -> None:
```

**Line:** 986 | **Kind:** fn

### `test_details_url_hijack_and_producer_membership_binding`

```
def test_details_url_hijack_and_producer_membership_binding(self) -> None:
```

**Line:** 1117 | **Kind:** fn

### `test_same_app_check_name_collision_requires_default_branch_workflow_identity`

```
def test_same_app_check_name_collision_requires_default_branch_workflow_identity(
```

**Line:** 1317 | **Kind:** fn

### `fake_lookup`

```
def fake_lookup(path: str, ref: str) -> str:
```

**Line:** 1577 | **Kind:** fn

### `test_provider_extractor_requires_exact_item_and_run_head`

```
def test_provider_extractor_requires_exact_item_and_run_head(self) -> None:
```

**Line:** 1601 | **Kind:** fn

### `test_paginated_slurp_flatten_multi_page_bodies_and_dedupe`

```
def test_paginated_slurp_flatten_multi_page_bodies_and_dedupe(self) -> None:
```

**Line:** 1677 | **Kind:** fn

### `test_slurp_json_stdin_handles_arg_max_and_pipefail_hold`

```
def test_slurp_json_stdin_handles_arg_max_and_pipefail_hold(self) -> None:
```

**Line:** 1727 | **Kind:** fn

### `test_undocumented_task_hold_rejected`

```
def test_undocumented_task_hold_rejected(self) -> None:
```

**Line:** 1822 | **Kind:** fn

### `test_fallback_reviewer_rules_and_comment`

```
def test_fallback_reviewer_rules_and_comment(self) -> None:
```

**Line:** 1828 | **Kind:** fn

### `test_same_account_comment_not_github_approval`

```
def test_same_account_comment_not_github_approval(self) -> None:
```

**Line:** 1861 | **Kind:** fn

### `test_observer_rejects_raw_bugbot_as_managed_gate`

```
def test_observer_rejects_raw_bugbot_as_managed_gate(self) -> None:
```

**Line:** 1884 | **Kind:** fn

### `test_workflow_static_no_trailing_whitespace`

```
def test_workflow_static_no_trailing_whitespace(self) -> None:
```

**Line:** 1914 | **Kind:** fn

### `test_detect_findings_from_trustworthy_event_evidence`

```
def test_detect_findings_from_trustworthy_event_evidence(self) -> None:
```

**Line:** 1924 | **Kind:** fn

### `test_candidate_cannot_replace_classifier_or_self_approve`

```
def test_candidate_cannot_replace_classifier_or_self_approve(self) -> None:
```

**Line:** 2003 | **Kind:** fn

### `test_planted_allowlisted_provider_error_and_forged_receipt_rejected`

```
def test_planted_allowlisted_provider_error_and_forged_receipt_rejected(self) -> None:
```

**Line:** 2138 | **Kind:** fn
