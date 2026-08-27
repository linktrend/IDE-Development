# scripts/tests/test_independent_review_convergence.py

[← Back to Module](../modules/scripts-tests/MODULE.md) | [← Back to INDEX](../INDEX.md)

## Overview

- **Lines:** 1038
- **Language:** Python
- **Symbols:** 54
- **Public symbols:** 54

## Symbol Table

| Line | Kind | Name | Visibility | Signature |
| ---- | ---- | ---- | ---------- | --------- |
| 71 | class | FakeClock | pub | `class FakeClock:` |
| 72 | fn | __init__ | pub | `def __init__(self, start: float = 1_000.0) -> N...` |
| 75 | fn | now | pub | `def now(self) -> float:` |
| 78 | fn | advance | pub | `def advance(self, seconds: float) -> None:` |
| 82 | fn | finding | pub | `def finding(` |
| 103 | fn | open_default | pub | `def open_default(**kwargs):` |
| 121 | fn | review | pub | `def review(session, entries, findings, *, head=...` |
| 135 | fn | cycle | pub | `def cycle(session, entries, *, new_head: str, n...` |
| 149 | class | SchemaAndIdentityTests | pub | `class SchemaAndIdentityTests(unittest.TestCase):` |
| 150 | fn | test_schemas_and_indexes_are_packaged | pub | `def test_schemas_and_indexes_are_packaged(self)...` |
| 164 | fn | test_exact_identity_and_role_separation | pub | `def test_exact_identity_and_role_separation(sel...` |
| 189 | class | AcU0901ObservableLoopTests | pub | `class AcU0901ObservableLoopTests(unittest.TestC...` |
| 190 | fn | test_session_always_has_status_and_no_terminal_cycle_cap | pub | `def test_session_always_has_status_and_no_termi...` |
| 201 | class | AcU0905ConsolidatedBatchTests | pub | `class AcU0905ConsolidatedBatchTests(unittest.Te...` |
| 202 | fn | test_many_findings_one_batch_one_cycle | pub | `def test_many_findings_one_batch_one_cycle(self...` |
| 221 | class | AcU0906StableFingerprintTests | pub | `class AcU0906StableFingerprintTests(unittest.Te...` |
| 222 | fn | test_wording_and_new_commit_cannot_hide_finding | pub | `def test_wording_and_new_commit_cannot_hide_fin...` |
| 245 | class | AcU0907InfrastructureBoundTests | pub | `class AcU0907InfrastructureBoundTests(unittest....` |
| 246 | fn | test_two_preflight_failures_do_not_consume_cycles_third_rejected | pub | `def test_two_preflight_failures_do_not_consume_...` |
| 261 | class | AcU0908UnattendedAndFounderContinueTests | pub | `class AcU0908UnattendedAndFounderContinueTests(...` |
| 262 | fn | test_unattended_pauses_after_three_then_continue_until_clean_has_no_cap | pub | `def test_unattended_pauses_after_three_then_con...` |
| 290 | fn | test_continue_until_clean_keeps_progressing_past_three_without_new_approval | pub | `def test_continue_until_clean_keeps_progressing...` |
| 315 | class | AcU0909StallConditionsTests | pub | `class AcU0909StallConditionsTests(unittest.Test...` |
| 316 | fn | test_repeated_unresolved_after_two_repairs_stalls | pub | `def test_repeated_unresolved_after_two_repairs_...` |
| 325 | fn | test_two_no_progress_cycles_stall | pub | `def test_two_no_progress_cycles_stall(self) -> ...` |
| 346 | fn | test_repair_reintroduction_stalls | pub | `def test_repair_reintroduction_stalls(self) -> ...` |
| 361 | fn | test_redesign_and_resource_limit_stall | pub | `def test_redesign_and_resource_limit_stall(self...` |
| 375 | class | AcU0904And10SplitHistoryTests | pub | `class AcU0904And10SplitHistoryTests(unittest.Te...` |
| 376 | fn | test_split_retains_root_ledger_and_cannot_fabricate_progress | pub | `def test_split_retains_root_ledger_and_cannot_f...` |
| 411 | class | AcU0911SingleReviewerHoldTests | pub | `class AcU0911SingleReviewerHoldTests(unittest.T...` |
| 412 | fn | test_slow_reviewer_is_single_live_process_and_timeout_is_not_clean | pub | `def test_slow_reviewer_is_single_live_process_a...` |
| 433 | class | AcU0912ExactHeadInvalidationTests | pub | `class AcU0912ExactHeadInvalidationTests(unittes...` |
| 434 | fn | test_full_and_prior_review_become_stale_after_repair | pub | `def test_full_and_prior_review_become_stale_aft...` |
| 458 | class | AcU0913StopCannotBypassFindingsTests | pub | `class AcU0913StopCannotBypassFindingsTests(unit...` |
| 459 | fn | test_stalled_packet_preserves_findings_and_cannot_be_clean | pub | `def test_stalled_packet_preserves_findings_and_...` |
| 480 | class | AcU0902And03PreservationTests | pub | `class AcU0902And03PreservationTests(unittest.Te...` |
| 481 | fn | test_completed_work_and_findings_are_preserved_in_packet | pub | `def test_completed_work_and_findings_are_preser...` |
| 493 | class | IndependentReviewRepairProbeTests | pub | `class IndependentReviewRepairProbeTests(unittes...` |
| 496 | fn | test_p1_01_distinct_fingerprints_never_fuzzy_merge | pub | `def test_p1_01_distinct_fingerprints_never_fuzz...` |
| 513 | fn | test_p1_02_ingest_requires_exact_head_tree_and_path_list | pub | `def test_p1_02_ingest_requires_exact_head_tree_...` |
| 552 | fn | test_p1_02_repair_cancels_live_reviewer_and_rejects_omitted_head | pub | `def test_p1_02_repair_cancels_live_reviewer_and...` |
| 582 | fn | test_p1_03_apply_repair_fails_closed_after_unattended_and_stop_states | pub | `def test_p1_03_apply_repair_fails_closed_after_...` |
| 648 | fn | test_p2_01_same_identity_severity_reduction_is_progress | pub | `def test_p2_01_same_identity_severity_reduction...` |
| 675 | fn | test_p2_02_first_seen_on_touched_paths_is_introduced_by_repair | pub | `def test_p2_02_first_seen_on_touched_paths_is_i...` |
| 694 | fn | test_p2_03_compute_units_accounting_can_stall | pub | `def test_p2_03_compute_units_accounting_can_sta...` |
| 708 | fn | test_p2_04_non_object_finding_is_hold_without_cycle | pub | `def test_p2_04_non_object_finding_is_hold_witho...` |
| 725 | fn | test_p1_04_empty_ledger_hold_stays_hold_and_blocks_evaluate_full_repair | pub | `def test_p1_04_empty_ledger_hold_stays_hold_and...` |
| 807 | fn | test_p1_04_hold_with_findings_stays_hold_and_cannot_repair | pub | `def test_p1_04_hold_with_findings_stays_hold_an...` |
| 838 | fn | test_p1_05_stalled_empty_ingest_preserves_repeated_and_infra_stops | pub | `def test_p1_05_stalled_empty_ingest_preserves_r...` |
| 878 | fn | test_p2_05_touched_paths_reject_string_empty_malformed_before_state_change | pub | `def test_p2_05_touched_paths_reject_string_empt...` |
| 934 | fn | test_p1_06_empty_ingest_after_consolidate_only_cannot_use_stale_pending_batch | pub | `def test_p1_06_empty_ingest_after_consolidate_o...` |
| 960 | fn | test_p1_06_repair_review_empty_ingest_still_marks_consumed_batch_corrected | pub | `def test_p1_06_repair_review_empty_ingest_still...` |
| 982 | fn | test_p1_06_in_progress_empty_ingest_preserves_repeated_pending_batch | pub | `def test_p1_06_in_progress_empty_ingest_preserv...` |
| 1004 | fn | test_p1_06_integration_empty_ingest_cannot_fabricate_clean_via_stale_batch | pub | `def test_p1_06_integration_empty_ingest_cannot_...` |

## Public API

### `FakeClock`

```
class FakeClock:
```

**Line:** 71 | **Kind:** class

### `__init__`

```
def __init__(self, start: float = 1_000.0) -> None:
```

**Line:** 72 | **Kind:** fn

### `now`

```
def now(self) -> float:
```

**Line:** 75 | **Kind:** fn

### `advance`

```
def advance(self, seconds: float) -> None:
```

**Line:** 78 | **Kind:** fn

### `finding`

```
def finding(
```

**Line:** 82 | **Kind:** fn

### `open_default`

```
def open_default(**kwargs):
```

**Line:** 103 | **Kind:** fn

### `review`

```
def review(session, entries, findings, *, head=None, tree=None):
```

**Line:** 121 | **Kind:** fn

### `cycle`

```
def cycle(session, entries, *, new_head: str, new_tree: str, remaining: list[dict[str, object]], touched=None):
```

**Line:** 135 | **Kind:** fn

### `SchemaAndIdentityTests`

```
class SchemaAndIdentityTests(unittest.TestCase):
```

**Line:** 149 | **Kind:** class

### `test_schemas_and_indexes_are_packaged`

```
def test_schemas_and_indexes_are_packaged(self) -> None:
```

**Line:** 150 | **Kind:** fn

### `test_exact_identity_and_role_separation`

```
def test_exact_identity_and_role_separation(self) -> None:
```

**Line:** 164 | **Kind:** fn

### `AcU0901ObservableLoopTests`

```
class AcU0901ObservableLoopTests(unittest.TestCase):
```

**Line:** 189 | **Kind:** class

### `test_session_always_has_status_and_no_terminal_cycle_cap`

```
def test_session_always_has_status_and_no_terminal_cycle_cap(self) -> None:
```

**Line:** 190 | **Kind:** fn

### `AcU0905ConsolidatedBatchTests`

```
class AcU0905ConsolidatedBatchTests(unittest.TestCase):
```

**Line:** 201 | **Kind:** class

### `test_many_findings_one_batch_one_cycle`

```
def test_many_findings_one_batch_one_cycle(self) -> None:
```

**Line:** 202 | **Kind:** fn

### `AcU0906StableFingerprintTests`

```
class AcU0906StableFingerprintTests(unittest.TestCase):
```

**Line:** 221 | **Kind:** class

### `test_wording_and_new_commit_cannot_hide_finding`

```
def test_wording_and_new_commit_cannot_hide_finding(self) -> None:
```

**Line:** 222 | **Kind:** fn

### `AcU0907InfrastructureBoundTests`

```
class AcU0907InfrastructureBoundTests(unittest.TestCase):
```

**Line:** 245 | **Kind:** class

### `test_two_preflight_failures_do_not_consume_cycles_third_rejected`

```
def test_two_preflight_failures_do_not_consume_cycles_third_rejected(self) -> None:
```

**Line:** 246 | **Kind:** fn

### `AcU0908UnattendedAndFounderContinueTests`

```
class AcU0908UnattendedAndFounderContinueTests(unittest.TestCase):
```

**Line:** 261 | **Kind:** class

### `test_unattended_pauses_after_three_then_continue_until_clean_has_no_cap`

```
def test_unattended_pauses_after_three_then_continue_until_clean_has_no_cap(self) -> None:
```

**Line:** 262 | **Kind:** fn

### `test_continue_until_clean_keeps_progressing_past_three_without_new_approval`

```
def test_continue_until_clean_keeps_progressing_past_three_without_new_approval(self) -> None:
```

**Line:** 290 | **Kind:** fn

### `AcU0909StallConditionsTests`

```
class AcU0909StallConditionsTests(unittest.TestCase):
```

**Line:** 315 | **Kind:** class

### `test_repeated_unresolved_after_two_repairs_stalls`

```
def test_repeated_unresolved_after_two_repairs_stalls(self) -> None:
```

**Line:** 316 | **Kind:** fn

### `test_two_no_progress_cycles_stall`

```
def test_two_no_progress_cycles_stall(self) -> None:
```

**Line:** 325 | **Kind:** fn

### `test_repair_reintroduction_stalls`

```
def test_repair_reintroduction_stalls(self) -> None:
```

**Line:** 346 | **Kind:** fn

### `test_redesign_and_resource_limit_stall`

```
def test_redesign_and_resource_limit_stall(self) -> None:
```

**Line:** 361 | **Kind:** fn

### `AcU0904And10SplitHistoryTests`

```
class AcU0904And10SplitHistoryTests(unittest.TestCase):
```

**Line:** 375 | **Kind:** class

### `test_split_retains_root_ledger_and_cannot_fabricate_progress`

```
def test_split_retains_root_ledger_and_cannot_fabricate_progress(self) -> None:
```

**Line:** 376 | **Kind:** fn

### `AcU0911SingleReviewerHoldTests`

```
class AcU0911SingleReviewerHoldTests(unittest.TestCase):
```

**Line:** 411 | **Kind:** class

### `test_slow_reviewer_is_single_live_process_and_timeout_is_not_clean`

```
def test_slow_reviewer_is_single_live_process_and_timeout_is_not_clean(self) -> None:
```

**Line:** 412 | **Kind:** fn

### `AcU0912ExactHeadInvalidationTests`

```
class AcU0912ExactHeadInvalidationTests(unittest.TestCase):
```

**Line:** 433 | **Kind:** class

### `test_full_and_prior_review_become_stale_after_repair`

```
def test_full_and_prior_review_become_stale_after_repair(self) -> None:
```

**Line:** 434 | **Kind:** fn

### `AcU0913StopCannotBypassFindingsTests`

```
class AcU0913StopCannotBypassFindingsTests(unittest.TestCase):
```

**Line:** 458 | **Kind:** class

### `test_stalled_packet_preserves_findings_and_cannot_be_clean`

```
def test_stalled_packet_preserves_findings_and_cannot_be_clean(self) -> None:
```

**Line:** 459 | **Kind:** fn

### `AcU0902And03PreservationTests`

```
class AcU0902And03PreservationTests(unittest.TestCase):
```

**Line:** 480 | **Kind:** class

### `test_completed_work_and_findings_are_preserved_in_packet`

```
def test_completed_work_and_findings_are_preserved_in_packet(self) -> None:
```

**Line:** 481 | **Kind:** fn

### `IndependentReviewRepairProbeTests`

```
class IndependentReviewRepairProbeTests(unittest.TestCase):
```

**Line:** 493 | **Kind:** class

### `test_p1_01_distinct_fingerprints_never_fuzzy_merge`

```
def test_p1_01_distinct_fingerprints_never_fuzzy_merge(self) -> None:
```

**Line:** 496 | **Kind:** fn

### `test_p1_02_ingest_requires_exact_head_tree_and_path_list`

```
def test_p1_02_ingest_requires_exact_head_tree_and_path_list(self) -> None:
```

**Line:** 513 | **Kind:** fn

### `test_p1_02_repair_cancels_live_reviewer_and_rejects_omitted_head`

```
def test_p1_02_repair_cancels_live_reviewer_and_rejects_omitted_head(self) -> None:
```

**Line:** 552 | **Kind:** fn

### `test_p1_03_apply_repair_fails_closed_after_unattended_and_stop_states`

```
def test_p1_03_apply_repair_fails_closed_after_unattended_and_stop_states(self) -> None:
```

**Line:** 582 | **Kind:** fn

### `test_p2_01_same_identity_severity_reduction_is_progress`

```
def test_p2_01_same_identity_severity_reduction_is_progress(self) -> None:
```

**Line:** 648 | **Kind:** fn

### `test_p2_02_first_seen_on_touched_paths_is_introduced_by_repair`

```
def test_p2_02_first_seen_on_touched_paths_is_introduced_by_repair(self) -> None:
```

**Line:** 675 | **Kind:** fn

### `test_p2_03_compute_units_accounting_can_stall`

```
def test_p2_03_compute_units_accounting_can_stall(self) -> None:
```

**Line:** 694 | **Kind:** fn

### `test_p2_04_non_object_finding_is_hold_without_cycle`

```
def test_p2_04_non_object_finding_is_hold_without_cycle(self) -> None:
```

**Line:** 708 | **Kind:** fn

### `test_p1_04_empty_ledger_hold_stays_hold_and_blocks_evaluate_full_repair`

```
def test_p1_04_empty_ledger_hold_stays_hold_and_blocks_evaluate_full_repair(self) -> None:
```

**Line:** 725 | **Kind:** fn

### `test_p1_04_hold_with_findings_stays_hold_and_cannot_repair`

```
def test_p1_04_hold_with_findings_stays_hold_and_cannot_repair(self) -> None:
```

**Line:** 807 | **Kind:** fn

### `test_p1_05_stalled_empty_ingest_preserves_repeated_and_infra_stops`

```
def test_p1_05_stalled_empty_ingest_preserves_repeated_and_infra_stops(self) -> None:
```

**Line:** 838 | **Kind:** fn

### `test_p2_05_touched_paths_reject_string_empty_malformed_before_state_change`

```
def test_p2_05_touched_paths_reject_string_empty_malformed_before_state_change(self) -> None:
```

**Line:** 878 | **Kind:** fn

### `test_p1_06_empty_ingest_after_consolidate_only_cannot_use_stale_pending_batch`

```
def test_p1_06_empty_ingest_after_consolidate_only_cannot_use_stale_pending_batch(self) -> None:
```

**Line:** 934 | **Kind:** fn

### `test_p1_06_repair_review_empty_ingest_still_marks_consumed_batch_corrected`

```
def test_p1_06_repair_review_empty_ingest_still_marks_consumed_batch_corrected(self) -> None:
```

**Line:** 960 | **Kind:** fn

### `test_p1_06_in_progress_empty_ingest_preserves_repeated_pending_batch`

```
def test_p1_06_in_progress_empty_ingest_preserves_repeated_pending_batch(self) -> None:
```

**Line:** 982 | **Kind:** fn

### `test_p1_06_integration_empty_ingest_cannot_fabricate_clean_via_stale_batch`

```
def test_p1_06_integration_empty_ingest_cannot_fabricate_clean_via_stale_batch(self) -> None:
```

**Line:** 1004 | **Kind:** fn
