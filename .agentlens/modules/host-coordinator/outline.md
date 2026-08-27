# Outline

[← Back to MODULE](MODULE.md) | [← Back to INDEX](../../INDEX.md)

Symbol maps for 1 large files in this module.

## host/coordinator/queue.py (659 lines)

| Line | Kind | Name | Visibility |
| ---- | ---- | ---- | ---------- |
| 28 | fn | _now | (private) |
| 32 | fn | _json | (private) |
| 36 | fn | _candidate | (private) |
| 58 | fn | candidate_key | pub |
| 62 | fn | priority_for | pub |
| 77 | class | QueueRequest | pub |
| 87 | fn | normalized | pub |
| 108 | class | QueueResult | pub |
| 115 | fn | ok | pub |
| 119 | class | QueueStore | pub |
| 122 | fn | __init__ | pub |
| 133 | fn | close | pub |
| 137 | fn | _migrate | (private) |
| 256 | fn | register_repository | pub |
| 269 | fn | repository | pub |
| 273 | fn | enqueue | pub |
| 309 | fn | get | pub |
| 315 | fn | _row | (private) |
| 325 | fn | list_jobs | pub |
| 330 | fn | next_job | pub |
| 337 | fn | score | pub |
| 345 | fn | mark_started | pub |
| 372 | fn | record_result | pub |
| 405 | fn | _upsert_alert | (private) |
| 414 | fn | alerts | pub |
| 417 | fn | cancel_obsolete | pub |
| 434 | fn | recover | pub |
| 443 | fn | recover_expired_leases | pub |
| 472 | fn | renew_lease | pub |
| 483 | fn | claim_next | pub |
| 589 | fn | record_lease_result | pub |
| 601 | fn | poll_state | pub |
| 609 | fn | update_poll | pub |
| 614 | fn | approve | pub |
| 618 | fn | approval | pub |
| 626 | fn | set_runtime | pub |
| 632 | fn | runtime | pub |
| 640 | fn | configure_default_store | pub |
| 645 | fn | _store | (private) |
| 651 | fn | enqueue | pub |
| 655 | fn | cancel_obsolete | pub |
