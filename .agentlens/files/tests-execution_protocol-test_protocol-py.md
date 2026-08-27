# tests/execution_protocol/test_protocol.py

[← Back to Module](../modules/tests-execution_protocol/MODULE.md) | [← Back to INDEX](../INDEX.md)

## Overview

- **Lines:** 679
- **Language:** Python
- **Symbols:** 63
- **Public symbols:** 62

## Symbol Table

| Line | Kind | Name | Visibility | Signature |
| ---- | ---- | ---- | ---------- | --------- |
| 59 | fn | example_manifest | pub | `def example_manifest() -> dict:` |
| 64 | class | DiscoveryTests | pub | `class DiscoveryTests(unittest.TestCase):` |
| 65 | fn | test_runtime_discovers_protocol_1_0_1_surfaces | pub | `def test_runtime_discovers_protocol_1_0_1_surfa...` |
| 79 | fn | test_protocol_and_doctrine_share_version_1_0_1 | pub | `def test_protocol_and_doctrine_share_version_1_...` |
| 88 | fn | test_missing_surface_fails_closed | pub | `def test_missing_surface_fails_closed(self) -> ...` |
| 92 | fn | test_runtime_discovers_installed_consumer_layout | pub | `def test_runtime_discovers_installed_consumer_l...` |
| 121 | class | ManifestSchemaTests | pub | `class ManifestSchemaTests(unittest.TestCase):` |
| 122 | fn | test_example_manifest_is_schema_valid | pub | `def test_example_manifest_is_schema_valid(self)...` |
| 128 | fn | test_unknown_top_level_field_is_rejected | pub | `def test_unknown_top_level_field_is_rejected(se...` |
| 135 | fn | test_wrong_protocol_version_is_rejected | pub | `def test_wrong_protocol_version_is_rejected(sel...` |
| 141 | fn | test_short_commit_is_rejected | pub | `def test_short_commit_is_rejected(self) -> None:` |
| 147 | fn | test_schema_loader_matches_discovery | pub | `def test_schema_loader_matches_discovery(self) ...` |
| 155 | fn | test_missing_amendment_is_rejected | pub | `def test_missing_amendment_is_rejected(self) ->...` |
| 162 | class | ExactCandidateTests | pub | `class ExactCandidateTests(unittest.TestCase):` |
| 163 | fn | test_identical_identity_is_not_invalidated | pub | `def test_identical_identity_is_not_invalidated(...` |
| 173 | fn | test_new_commit_or_tree_invalidates | pub | `def test_new_commit_or_tree_invalidates(self) -...` |
| 196 | fn | test_digest_change_invalidates_when_bound | pub | `def test_digest_change_invalidates_when_bound(s...` |
| 216 | class | BoundedRetryTests | pub | `class BoundedRetryTests(unittest.TestCase):` |
| 217 | fn | test_ordinary_source_allows_three_then_stops | pub | `def test_ordinary_source_allows_three_then_stop...` |
| 224 | fn | test_infrastructure_retries_once_then_stops | pub | `def test_infrastructure_retries_once_then_stops...` |
| 232 | fn | test_code_failure_never_retries | pub | `def test_code_failure_never_retries(self) -> None:` |
| 239 | class | OrchestrationLeaseTests | pub | `class OrchestrationLeaseTests(unittest.TestCase):` |
| 240 | fn | test_exclusive_live_lease_blocks_other_holder | pub | `def test_exclusive_live_lease_blocks_other_hold...` |
| 261 | fn | test_expired_lease_cannot_mutate | pub | `def test_expired_lease_cannot_mutate(self) -> N...` |
| 281 | fn | test_matching_live_lease_authorizes_holder | pub | `def test_matching_live_lease_authorizes_holder(...` |
| 302 | class | ResourceUncertaintyTests | pub | `class ResourceUncertaintyTests(unittest.TestCase):` |
| 303 | fn | test_missing_snapshot_is_uncertain_and_not_admitted | pub | `def test_missing_snapshot_is_uncertain_and_not_...` |
| 309 | fn | test_unknown_field_is_blocking | pub | `def test_unknown_field_is_blocking(self) -> None:` |
| 321 | fn | test_complete_snapshot_admits | pub | `def test_complete_snapshot_admits(self) -> None:` |
| 334 | class | AutomaticApprovalTests | pub | `class AutomaticApprovalTests(unittest.TestCase):` |
| 335 | fn | test_checkpoint_is_automatic | pub | `def test_checkpoint_is_automatic(self) -> None:` |
| 341 | fn | test_main_promote_requires_recorded_founder | pub | `def test_main_promote_requires_recorded_founder...` |
| 351 | fn | test_self_review_and_self_merge_are_forbidden | pub | `def test_self_review_and_self_merge_are_forbidd...` |
| 357 | class | GitAuthorityTests | pub | `class GitAuthorityTests(unittest.TestCase):` |
| 358 | fn | test_implementer_may_push_issue_branch_only | pub | `def test_implementer_may_push_issue_branch_only...` |
| 374 | fn | test_implementer_cannot_open_or_merge | pub | `def test_implementer_cannot_open_or_merge(self)...` |
| 389 | class | PublisherAuthorityTests | pub | `class PublisherAuthorityTests(unittest.TestCase):` |
| 390 | fn | test_no_singular_legacy_publisher_is_canonical_for_v25 | pub | `def test_no_singular_legacy_publisher_is_canoni...` |
| 402 | fn | test_failed_or_missing_legacy_publisher_is_waived_not_pass | pub | `def test_failed_or_missing_legacy_publisher_is_...` |
| 419 | class | IssueCheckpointTests | pub | `class IssueCheckpointTests(unittest.TestCase):` |
| 420 | fn | test_complete_evidence_accepts_without_review_ready_or_token | pub | `def test_complete_evidence_accepts_without_revi...` |
| 437 | fn | test_missing_terra_verification_is_not_accepted | pub | `def test_missing_terra_verification_is_not_acce...` |
| 451 | class | AdministratorRecoveryTests | pub | `class AdministratorRecoveryTests(unittest.TestC...` |
| 452 | fn | test_named_exact_head_recovery_after_replacement_proof | pub | `def test_named_exact_head_recovery_after_replac...` |
| 461 | fn | test_unnamed_or_extra_operations_are_denied | pub | `def test_unnamed_or_extra_operations_are_denied...` |
| 485 | class | AutoworkDiscoveryTests | pub | `class AutoworkDiscoveryTests(unittest.TestCase):` |
| 486 | fn | test_callable_discovery_is_required | pub | `def test_callable_discovery_is_required(self) -...` |
| 494 | fn | test_uncallable_cannot_claim_live_pass | pub | `def test_uncallable_cannot_claim_live_pass(self...` |
| 507 | class | DurableHeartbeatGateTests | pub | `class DurableHeartbeatGateTests(unittest.TestCa...` |
| 508 | fn | _record | (private) | `def _record(self) -> dict:` |
| 519 | fn | test_write_and_readback_admits | pub | `def test_write_and_readback_admits(self) -> None:` |
| 524 | fn | test_missing_readback_is_rejected | pub | `def test_missing_readback_is_rejected(self) -> ...` |
| 538 | fn | test_mutated_readback_is_rejected | pub | `def test_mutated_readback_is_rejected(self) -> ...` |
| 555 | class | CheckoutBoundReceiptTests | pub | `class CheckoutBoundReceiptTests(unittest.TestCa...` |
| 556 | fn | test_exact_checkout_receipt_is_promotable | pub | `def test_exact_checkout_receipt_is_promotable(s...` |
| 573 | fn | test_merge_ref_identity_is_forbidden | pub | `def test_merge_ref_identity_is_forbidden(self) ...` |
| 591 | class | RetryExhaustionRecoveryTests | pub | `class RetryExhaustionRecoveryTests(unittest.Tes...` |
| 592 | fn | test_ordinary_exhaustion_requires_new_identity | pub | `def test_ordinary_exhaustion_requires_new_ident...` |
| 617 | fn | test_infrastructure_hold_allows_named_exception | pub | `def test_infrastructure_hold_allows_named_excep...` |
| 640 | class | HostedCapacitySchedulerTests | pub | `class HostedCapacitySchedulerTests(unittest.Tes...` |
| 641 | fn | test_busy_allocator_without_snapshot_is_uncertain | pub | `def test_busy_allocator_without_snapshot_is_unc...` |
| 650 | fn | test_complete_snapshot_with_no_slots_is_exhausted | pub | `def test_complete_snapshot_with_no_slots_is_exh...` |
| 664 | fn | test_complete_snapshot_with_slots_schedules | pub | `def test_complete_snapshot_with_slots_schedules...` |

## Public API

### `example_manifest`

```
def example_manifest() -> dict:
```

**Line:** 59 | **Kind:** fn

### `DiscoveryTests`

```
class DiscoveryTests(unittest.TestCase):
```

**Line:** 64 | **Kind:** class

### `test_runtime_discovers_protocol_1_0_1_surfaces`

```
def test_runtime_discovers_protocol_1_0_1_surfaces(self) -> None:
```

**Line:** 65 | **Kind:** fn

### `test_protocol_and_doctrine_share_version_1_0_1`

```
def test_protocol_and_doctrine_share_version_1_0_1(self) -> None:
```

**Line:** 79 | **Kind:** fn

### `test_missing_surface_fails_closed`

```
def test_missing_surface_fails_closed(self) -> None:
```

**Line:** 88 | **Kind:** fn

### `test_runtime_discovers_installed_consumer_layout`

```
def test_runtime_discovers_installed_consumer_layout(self) -> None:
```

**Line:** 92 | **Kind:** fn

### `ManifestSchemaTests`

```
class ManifestSchemaTests(unittest.TestCase):
```

**Line:** 121 | **Kind:** class

### `test_example_manifest_is_schema_valid`

```
def test_example_manifest_is_schema_valid(self) -> None:
```

**Line:** 122 | **Kind:** fn

### `test_unknown_top_level_field_is_rejected`

```
def test_unknown_top_level_field_is_rejected(self) -> None:
```

**Line:** 128 | **Kind:** fn

### `test_wrong_protocol_version_is_rejected`

```
def test_wrong_protocol_version_is_rejected(self) -> None:
```

**Line:** 135 | **Kind:** fn

### `test_short_commit_is_rejected`

```
def test_short_commit_is_rejected(self) -> None:
```

**Line:** 141 | **Kind:** fn

### `test_schema_loader_matches_discovery`

```
def test_schema_loader_matches_discovery(self) -> None:
```

**Line:** 147 | **Kind:** fn

### `test_missing_amendment_is_rejected`

```
def test_missing_amendment_is_rejected(self) -> None:
```

**Line:** 155 | **Kind:** fn

### `ExactCandidateTests`

```
class ExactCandidateTests(unittest.TestCase):
```

**Line:** 162 | **Kind:** class

### `test_identical_identity_is_not_invalidated`

```
def test_identical_identity_is_not_invalidated(self) -> None:
```

**Line:** 163 | **Kind:** fn

### `test_new_commit_or_tree_invalidates`

```
def test_new_commit_or_tree_invalidates(self) -> None:
```

**Line:** 173 | **Kind:** fn

### `test_digest_change_invalidates_when_bound`

```
def test_digest_change_invalidates_when_bound(self) -> None:
```

**Line:** 196 | **Kind:** fn

### `BoundedRetryTests`

```
class BoundedRetryTests(unittest.TestCase):
```

**Line:** 216 | **Kind:** class

### `test_ordinary_source_allows_three_then_stops`

```
def test_ordinary_source_allows_three_then_stops(self) -> None:
```

**Line:** 217 | **Kind:** fn

### `test_infrastructure_retries_once_then_stops`

```
def test_infrastructure_retries_once_then_stops(self) -> None:
```

**Line:** 224 | **Kind:** fn

### `test_code_failure_never_retries`

```
def test_code_failure_never_retries(self) -> None:
```

**Line:** 232 | **Kind:** fn

### `OrchestrationLeaseTests`

```
class OrchestrationLeaseTests(unittest.TestCase):
```

**Line:** 239 | **Kind:** class

### `test_exclusive_live_lease_blocks_other_holder`

```
def test_exclusive_live_lease_blocks_other_holder(self) -> None:
```

**Line:** 240 | **Kind:** fn

### `test_expired_lease_cannot_mutate`

```
def test_expired_lease_cannot_mutate(self) -> None:
```

**Line:** 261 | **Kind:** fn

### `test_matching_live_lease_authorizes_holder`

```
def test_matching_live_lease_authorizes_holder(self) -> None:
```

**Line:** 281 | **Kind:** fn

### `ResourceUncertaintyTests`

```
class ResourceUncertaintyTests(unittest.TestCase):
```

**Line:** 302 | **Kind:** class

### `test_missing_snapshot_is_uncertain_and_not_admitted`

```
def test_missing_snapshot_is_uncertain_and_not_admitted(self) -> None:
```

**Line:** 303 | **Kind:** fn

### `test_unknown_field_is_blocking`

```
def test_unknown_field_is_blocking(self) -> None:
```

**Line:** 309 | **Kind:** fn

### `test_complete_snapshot_admits`

```
def test_complete_snapshot_admits(self) -> None:
```

**Line:** 321 | **Kind:** fn

### `AutomaticApprovalTests`

```
class AutomaticApprovalTests(unittest.TestCase):
```

**Line:** 334 | **Kind:** class

### `test_checkpoint_is_automatic`

```
def test_checkpoint_is_automatic(self) -> None:
```

**Line:** 335 | **Kind:** fn

### `test_main_promote_requires_recorded_founder`

```
def test_main_promote_requires_recorded_founder(self) -> None:
```

**Line:** 341 | **Kind:** fn

### `test_self_review_and_self_merge_are_forbidden`

```
def test_self_review_and_self_merge_are_forbidden(self) -> None:
```

**Line:** 351 | **Kind:** fn

### `GitAuthorityTests`

```
class GitAuthorityTests(unittest.TestCase):
```

**Line:** 357 | **Kind:** class

### `test_implementer_may_push_issue_branch_only`

```
def test_implementer_may_push_issue_branch_only(self) -> None:
```

**Line:** 358 | **Kind:** fn

### `test_implementer_cannot_open_or_merge`

```
def test_implementer_cannot_open_or_merge(self) -> None:
```

**Line:** 374 | **Kind:** fn

### `PublisherAuthorityTests`

```
class PublisherAuthorityTests(unittest.TestCase):
```

**Line:** 389 | **Kind:** class

### `test_no_singular_legacy_publisher_is_canonical_for_v25`

```
def test_no_singular_legacy_publisher_is_canonical_for_v25(self) -> None:
```

**Line:** 390 | **Kind:** fn

### `test_failed_or_missing_legacy_publisher_is_waived_not_pass`

```
def test_failed_or_missing_legacy_publisher_is_waived_not_pass(self) -> None:
```

**Line:** 402 | **Kind:** fn

### `IssueCheckpointTests`

```
class IssueCheckpointTests(unittest.TestCase):
```

**Line:** 419 | **Kind:** class

### `test_complete_evidence_accepts_without_review_ready_or_token`

```
def test_complete_evidence_accepts_without_review_ready_or_token(self) -> None:
```

**Line:** 420 | **Kind:** fn

### `test_missing_terra_verification_is_not_accepted`

```
def test_missing_terra_verification_is_not_accepted(self) -> None:
```

**Line:** 437 | **Kind:** fn

### `AdministratorRecoveryTests`

```
class AdministratorRecoveryTests(unittest.TestCase):
```

**Line:** 451 | **Kind:** class

### `test_named_exact_head_recovery_after_replacement_proof`

```
def test_named_exact_head_recovery_after_replacement_proof(self) -> None:
```

**Line:** 452 | **Kind:** fn

### `test_unnamed_or_extra_operations_are_denied`

```
def test_unnamed_or_extra_operations_are_denied(self) -> None:
```

**Line:** 461 | **Kind:** fn

### `AutoworkDiscoveryTests`

```
class AutoworkDiscoveryTests(unittest.TestCase):
```

**Line:** 485 | **Kind:** class

### `test_callable_discovery_is_required`

```
def test_callable_discovery_is_required(self) -> None:
```

**Line:** 486 | **Kind:** fn

### `test_uncallable_cannot_claim_live_pass`

```
def test_uncallable_cannot_claim_live_pass(self) -> None:
```

**Line:** 494 | **Kind:** fn

### `DurableHeartbeatGateTests`

```
class DurableHeartbeatGateTests(unittest.TestCase):
```

**Line:** 507 | **Kind:** class

### `test_write_and_readback_admits`

```
def test_write_and_readback_admits(self) -> None:
```

**Line:** 519 | **Kind:** fn

### `test_missing_readback_is_rejected`

```
def test_missing_readback_is_rejected(self) -> None:
```

**Line:** 524 | **Kind:** fn

### `test_mutated_readback_is_rejected`

```
def test_mutated_readback_is_rejected(self) -> None:
```

**Line:** 538 | **Kind:** fn

### `CheckoutBoundReceiptTests`

```
class CheckoutBoundReceiptTests(unittest.TestCase):
```

**Line:** 555 | **Kind:** class

### `test_exact_checkout_receipt_is_promotable`

```
def test_exact_checkout_receipt_is_promotable(self) -> None:
```

**Line:** 556 | **Kind:** fn

### `test_merge_ref_identity_is_forbidden`

```
def test_merge_ref_identity_is_forbidden(self) -> None:
```

**Line:** 573 | **Kind:** fn

### `RetryExhaustionRecoveryTests`

```
class RetryExhaustionRecoveryTests(unittest.TestCase):
```

**Line:** 591 | **Kind:** class

### `test_ordinary_exhaustion_requires_new_identity`

```
def test_ordinary_exhaustion_requires_new_identity(self) -> None:
```

**Line:** 592 | **Kind:** fn

### `test_infrastructure_hold_allows_named_exception`

```
def test_infrastructure_hold_allows_named_exception(self) -> None:
```

**Line:** 617 | **Kind:** fn

### `HostedCapacitySchedulerTests`

```
class HostedCapacitySchedulerTests(unittest.TestCase):
```

**Line:** 640 | **Kind:** class

### `test_busy_allocator_without_snapshot_is_uncertain`

```
def test_busy_allocator_without_snapshot_is_uncertain(self) -> None:
```

**Line:** 641 | **Kind:** fn

### `test_complete_snapshot_with_no_slots_is_exhausted`

```
def test_complete_snapshot_with_no_slots_is_exhausted(self) -> None:
```

**Line:** 650 | **Kind:** fn

### `test_complete_snapshot_with_slots_schedules`

```
def test_complete_snapshot_with_slots_schedules(self) -> None:
```

**Line:** 664 | **Kind:** fn
