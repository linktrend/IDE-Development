# scripts/gitops/linktrend_review_gate.py

[← Back to Module](../modules/root/MODULE.md) | [← Back to INDEX](../INDEX.md)

## Overview

- **Lines:** 2270
- **Language:** Python
- **Symbols:** 69
- **Public symbols:** 57

## Symbol Table

| Line | Kind | Name | Visibility | Signature |
| ---- | ---- | ---- | ---------- | --------- |
| 147 | class | ReviewGateError | pub | `class ReviewGateError(Exception):` |
| 150 | fn | __init__ | pub | `def __init__(self, code: str, detail: str = "")...` |
| 156 | fn | require_sha40 | pub | `def require_sha40(value: str, label: str = "sha...` |
| 163 | fn | _norm | (private) | `def _norm(value: Any) -> str:` |
| 167 | fn | _lower | (private) | `def _lower(value: Any) -> str:` |
| 171 | fn | structured_bugbot_findings_present | pub | `def structured_bugbot_findings_present(` |
| 204 | class | Classification | pub | `class Classification:` |
| 220 | fn | to_dict | pub | `def to_dict(self) -> dict[str, Any]:` |
| 228 | fn | assert_full_suite_allows_bugbot | pub | `def assert_full_suite_allows_bugbot(full_suite_...` |
| 237 | fn | reject_third_infrastructure_attempt | pub | `def reject_third_infrastructure_attempt(attempt...` |
| 247 | fn | invalidate_if_head_changed | pub | `def invalidate_if_head_changed(*, bound_head: s...` |
| 254 | fn | require_no_raw_bugbot_required | pub | `def require_no_raw_bugbot_required(contexts: Se...` |
| 268 | fn | require_review_gate_on_development | pub | `def require_review_gate_on_development(contexts...` |
| 278 | fn | reject_undocumented_task_hold | pub | `def reject_undocumented_task_hold(` |
| 290 | fn | evaluate_fallback_review | pub | `def evaluate_fallback_review(` |
| 325 | fn | evaluate_github_approval | pub | `def evaluate_github_approval(` |
| 363 | fn | _provider_class | (private) | `def _provider_class(raw: Mapping[str, Any] | No...` |
| 372 | fn | evidence_channel_is_trusted | pub | `def evidence_channel_is_trusted(channel: str) -...` |
| 376 | fn | _provenance_mapping | (private) | `def _provenance_mapping(raw: Mapping[str, Any] ...` |
| 382 | fn | verified_provider_unavailability | pub | `def verified_provider_unavailability(` |
| 435 | fn | authenticate_provider_unavailability_evidence | pub | `def authenticate_provider_unavailability_evidence(` |
| 493 | fn | provider_error_from_usage_limit_repair_issues | pub | `def provider_error_from_usage_limit_repair_issues(` |
| 543 | fn | stamp_full_receipt_provenance | pub | `def stamp_full_receipt_provenance(` |
| 574 | fn | _positive_int | (private) | `def _positive_int(value: Any) -> int | None:` |
| 582 | fn | findings_present_from_event_evidence | pub | `def findings_present_from_event_evidence(` |
| 632 | fn | _as_check_run_list | (private) | `def _as_check_run_list(check_runs: Any) -> list...` |
| 647 | fn | _as_workflow_run_list | (private) | `def _as_workflow_run_list(workflow_runs: Any) -...` |
| 662 | fn | _as_int | (private) | `def _as_int(value: Any) -> int | None:` |
| 671 | fn | check_suite_id_from_check_run | pub | `def check_suite_id_from_check_run(check_run: Ma...` |
| 680 | fn | check_run_numeric_id | pub | `def check_run_numeric_id(check_run: Mapping[str...` |
| 684 | fn | workflow_run_id_from_check_run | pub | `def workflow_run_id_from_check_run(check_run: M...` |
| 697 | fn | index_workflow_runs_by_id | pub | `def index_workflow_runs_by_id(workflow_runs: An...` |
| 709 | fn | index_workflow_runs_by_check_suite_id | pub | `def index_workflow_runs_by_check_suite_id(` |
| 723 | fn | _as_workflow_job_list | (private) | `def _as_workflow_job_list(workflow_jobs: Any) -...` |
| 738 | fn | check_run_id_from_job | pub | `def check_run_id_from_job(job: Mapping[str, Any...` |
| 750 | fn | index_successful_jobs_by_check_run_id | pub | `def index_successful_jobs_by_check_run_id(` |
| 770 | fn | producer_run_is_successful | pub | `def producer_run_is_successful(workflow_run: Ma...` |
| 778 | fn | check_output_is_successful | pub | `def check_output_is_successful(check_run: Mappi...` |
| 782 | fn | workflow_file_shas_for_path | pub | `def workflow_file_shas_for_path(` |
| 813 | fn | trusted_default_branch_workflow_binding | pub | `def trusted_default_branch_workflow_binding(` |
| 843 | fn | resolve_authenticated_workflow_run_for_check | pub | `def resolve_authenticated_workflow_run_for_check(` |
| 907 | fn | build_workflow_file_shas_payload | pub | `def build_workflow_file_shas_payload(` |
| 930 | fn | lookup | pub | `def lookup(path: str, ref: str) -> str: # type:...` |
| 951 | fn | _gh_contents_blob_sha | (private) | `def _gh_contents_blob_sha(repository: str, path...` |
| 973 | fn | build_workflow_jobs_payload | pub | `def build_workflow_jobs_payload(` |
| 988 | fn | lookup | pub | `def lookup(run_id: int) -> list[Any]: # type: i...` |
| 1007 | fn | _gh_workflow_jobs | (private) | `def _gh_workflow_jobs(repository: str, run_id: ...` |
| 1031 | fn | extract_trusted_provider_evidence_from_check_runs | pub | `def extract_trusted_provider_evidence_from_chec...` |
| 1103 | fn | extract_trusted_full_receipt_from_check_runs | pub | `def extract_trusted_full_receipt_from_check_runs(` |
| 1183 | fn | count_infrastructure_attempts | pub | `def count_infrastructure_attempts(markers: Sequ...` |
| 1195 | fn | founder_alert_marker | pub | `def founder_alert_marker(head_sha: str) -> str:` |
| 1199 | fn | infrastructure_attempt_marker | pub | `def infrastructure_attempt_marker(head_sha: str...` |
| 1203 | fn | fallback_request_marker | pub | `def fallback_request_marker(head_sha: str) -> str:` |
| 1207 | fn | build_durable_founder_alert | pub | `def build_durable_founder_alert(classification:...` |
| 1235 | fn | flatten_gh_slurp_pages | pub | `def flatten_gh_slurp_pages(pages: Any) -> list[...` |
| 1264 | fn | comment_bodies_from_slurp | pub | `def comment_bodies_from_slurp(pages: Any) -> li...` |
| 1274 | fn | issue_bodies_from_slurp | pub | `def issue_bodies_from_slurp(pages: Any) -> list...` |
| 1286 | fn | founder_alert_already_recorded | pub | `def founder_alert_already_recorded(existing_bod...` |
| 1292 | fn | decide_founder_alert_publish | pub | `def decide_founder_alert_publish(` |
| 1317 | fn | simulate_repeated_founder_alert_events | pub | `def simulate_repeated_founder_alert_events(` |
| 1339 | fn | normalize_full_receipt_payload | pub | `def normalize_full_receipt_payload(raw: Any) ->...` |
| 1398 | fn | overlay_retained_full_suite_receipt | pub | `def overlay_retained_full_suite_receipt(` |
| 1454 | fn | require_full_receipt_for_gate_success | pub | `def require_full_receipt_for_gate_success(` |
| 1526 | fn | build_fallback_request_comment | pub | `def build_fallback_request_comment(` |
| 1544 | fn | classify_bugbot_result | pub | `def classify_bugbot_result(` |
| 1748 | fn | gate_commit_status | pub | `def gate_commit_status(classification: Classifi...` |
| 1763 | fn | migrated_required_contexts | pub | `def migrated_required_contexts(contexts: Sequen...` |
| 1776 | fn | _load_json_arg | (private) | `def _load_json_arg(raw: str) -> Any:` |
| 1786 | fn | main | pub | `def main(argv: list[str] | None = None) -> int:` |

## Public API

### `ReviewGateError`

```
class ReviewGateError(Exception):
```

**Line:** 147 | **Kind:** class

### `__init__`

```
def __init__(self, code: str, detail: str = "") -> None:
```

**Line:** 150 | **Kind:** fn

### `require_sha40`

```
def require_sha40(value: str, label: str = "sha") -> str:
```

**Line:** 156 | **Kind:** fn

### `structured_bugbot_findings_present`

```
def structured_bugbot_findings_present(
```

**Line:** 171 | **Kind:** fn

### `Classification`

```
class Classification:
```

**Line:** 204 | **Kind:** class

### `to_dict`

```
def to_dict(self) -> dict[str, Any]:
```

**Line:** 220 | **Kind:** fn

### `assert_full_suite_allows_bugbot`

```
def assert_full_suite_allows_bugbot(full_suite_status: str) -> None:
```

**Line:** 228 | **Kind:** fn

### `reject_third_infrastructure_attempt`

```
def reject_third_infrastructure_attempt(attempts: int) -> None:
```

**Line:** 237 | **Kind:** fn

### `invalidate_if_head_changed`

```
def invalidate_if_head_changed(*, bound_head: str, live_head: str) -> None:
```

**Line:** 247 | **Kind:** fn

### `require_no_raw_bugbot_required`

```
def require_no_raw_bugbot_required(contexts: Sequence[str]) -> None:
```

**Line:** 254 | **Kind:** fn

### `require_review_gate_on_development`

```
def require_review_gate_on_development(contexts: Sequence[str]) -> None:
```

**Line:** 268 | **Kind:** fn

### `reject_undocumented_task_hold`

```
def reject_undocumented_task_hold(
```

**Line:** 278 | **Kind:** fn

### `evaluate_fallback_review`

```
def evaluate_fallback_review(
```

**Line:** 290 | **Kind:** fn

### `evaluate_github_approval`

```
def evaluate_github_approval(
```

**Line:** 325 | **Kind:** fn

### `evidence_channel_is_trusted`

```
def evidence_channel_is_trusted(channel: str) -> bool:
```

**Line:** 372 | **Kind:** fn

### `verified_provider_unavailability`

```
def verified_provider_unavailability(
```

**Line:** 382 | **Kind:** fn

### `authenticate_provider_unavailability_evidence`

```
def authenticate_provider_unavailability_evidence(
```

**Line:** 435 | **Kind:** fn

### `provider_error_from_usage_limit_repair_issues`

```
def provider_error_from_usage_limit_repair_issues(
```

**Line:** 493 | **Kind:** fn

### `stamp_full_receipt_provenance`

```
def stamp_full_receipt_provenance(
```

**Line:** 543 | **Kind:** fn

### `findings_present_from_event_evidence`

```
def findings_present_from_event_evidence(
```

**Line:** 582 | **Kind:** fn

### `check_suite_id_from_check_run`

```
def check_suite_id_from_check_run(check_run: Mapping[str, Any]) -> int | None:
```

**Line:** 671 | **Kind:** fn

### `check_run_numeric_id`

```
def check_run_numeric_id(check_run: Mapping[str, Any]) -> int | None:
```

**Line:** 680 | **Kind:** fn

### `workflow_run_id_from_check_run`

```
def workflow_run_id_from_check_run(check_run: Mapping[str, Any]) -> int | None:
```

**Line:** 684 | **Kind:** fn

### `index_workflow_runs_by_id`

```
def index_workflow_runs_by_id(workflow_runs: Any) -> dict[int, Mapping[str, Any]]:
```

**Line:** 697 | **Kind:** fn

### `index_workflow_runs_by_check_suite_id`

```
def index_workflow_runs_by_check_suite_id(
```

**Line:** 709 | **Kind:** fn

### `check_run_id_from_job`

```
def check_run_id_from_job(job: Mapping[str, Any]) -> int | None:
```

**Line:** 738 | **Kind:** fn

### `index_successful_jobs_by_check_run_id`

```
def index_successful_jobs_by_check_run_id(
```

**Line:** 750 | **Kind:** fn

### `producer_run_is_successful`

```
def producer_run_is_successful(workflow_run: Mapping[str, Any]) -> bool:
```

**Line:** 770 | **Kind:** fn

### `check_output_is_successful`

```
def check_output_is_successful(check_run: Mapping[str, Any]) -> bool:
```

**Line:** 778 | **Kind:** fn

### `workflow_file_shas_for_path`

```
def workflow_file_shas_for_path(
```

**Line:** 782 | **Kind:** fn

### `trusted_default_branch_workflow_binding`

```
def trusted_default_branch_workflow_binding(
```

**Line:** 813 | **Kind:** fn

### `resolve_authenticated_workflow_run_for_check`

```
def resolve_authenticated_workflow_run_for_check(
```

**Line:** 843 | **Kind:** fn

### `build_workflow_file_shas_payload`

```
def build_workflow_file_shas_payload(
```

**Line:** 907 | **Kind:** fn

### `lookup`

```
def lookup(path: str, ref: str) -> str:  # type: ignore[misc]
```

**Line:** 930 | **Kind:** fn

### `build_workflow_jobs_payload`

```
def build_workflow_jobs_payload(
```

**Line:** 973 | **Kind:** fn

### `lookup`

```
def lookup(run_id: int) -> list[Any]:  # type: ignore[misc]
```

**Line:** 988 | **Kind:** fn

### `extract_trusted_provider_evidence_from_check_runs`

```
def extract_trusted_provider_evidence_from_check_runs(
```

**Line:** 1031 | **Kind:** fn

### `extract_trusted_full_receipt_from_check_runs`

```
def extract_trusted_full_receipt_from_check_runs(
```

**Line:** 1103 | **Kind:** fn

### `count_infrastructure_attempts`

```
def count_infrastructure_attempts(markers: Sequence[str] | None, *, head_sha: str) -> int:
```

**Line:** 1183 | **Kind:** fn

### `founder_alert_marker`

```
def founder_alert_marker(head_sha: str) -> str:
```

**Line:** 1195 | **Kind:** fn

### `infrastructure_attempt_marker`

```
def infrastructure_attempt_marker(head_sha: str, attempt: int) -> str:
```

**Line:** 1199 | **Kind:** fn

### `fallback_request_marker`

```
def fallback_request_marker(head_sha: str) -> str:
```

**Line:** 1203 | **Kind:** fn

### `build_durable_founder_alert`

```
def build_durable_founder_alert(classification: Classification) -> dict[str, Any]:
```

**Line:** 1207 | **Kind:** fn

### `flatten_gh_slurp_pages`

```
def flatten_gh_slurp_pages(pages: Any) -> list[Any]:
```

**Line:** 1235 | **Kind:** fn

### `comment_bodies_from_slurp`

```
def comment_bodies_from_slurp(pages: Any) -> list[str]:
```

**Line:** 1264 | **Kind:** fn

### `issue_bodies_from_slurp`

```
def issue_bodies_from_slurp(pages: Any) -> list[str]:
```

**Line:** 1274 | **Kind:** fn

### `founder_alert_already_recorded`

```
def founder_alert_already_recorded(existing_bodies: Sequence[str], *, head_sha: str) -> bool:
```

**Line:** 1286 | **Kind:** fn

### `decide_founder_alert_publish`

```
def decide_founder_alert_publish(
```

**Line:** 1292 | **Kind:** fn

### `simulate_repeated_founder_alert_events`

```
def simulate_repeated_founder_alert_events(
```

**Line:** 1317 | **Kind:** fn

### `normalize_full_receipt_payload`

```
def normalize_full_receipt_payload(raw: Any) -> dict[str, Any] | None:
```

**Line:** 1339 | **Kind:** fn

### `overlay_retained_full_suite_receipt`

```
def overlay_retained_full_suite_receipt(
```

**Line:** 1398 | **Kind:** fn

### `require_full_receipt_for_gate_success`

```
def require_full_receipt_for_gate_success(
```

**Line:** 1454 | **Kind:** fn

### `build_fallback_request_comment`

```
def build_fallback_request_comment(
```

**Line:** 1526 | **Kind:** fn

### `classify_bugbot_result`

```
def classify_bugbot_result(
```

**Line:** 1544 | **Kind:** fn

### `gate_commit_status`

```
def gate_commit_status(classification: Classification) -> dict[str, str]:
```

**Line:** 1748 | **Kind:** fn

### `migrated_required_contexts`

```
def migrated_required_contexts(contexts: Sequence[str]) -> list[str]:
```

**Line:** 1763 | **Kind:** fn

### `main`

```
def main(argv: list[str] | None = None) -> int:
```

**Line:** 1786 | **Kind:** fn
