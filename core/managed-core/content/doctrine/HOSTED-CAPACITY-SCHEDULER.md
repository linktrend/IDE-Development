# Hosted-capacity scheduler (Coding Execution Protocol)

**Status:** Canonical for Coding Execution Protocol 1.0.1 amendment `V25_BOOTSTRAP_LEAN`  
**Authority:** PKT-01 follow-on hosted-capacity scheduler doctrine  
**Does not:** dispatch GitHub Actions, paid models, Fast gates, Full Suite, or provider-live jobs

This doctrine governs **whether** hosted work may be scheduled. It does not implement a worker runtime, queue, or CI workflow.

## Snapshot first

A hosted slot is diagnosed only from a **complete** resource snapshot:

- `cpu_percent`
- `memory_percent`
- `free_disk_gib`
- `docker_available`

Missing snapshot fields remain `resource_uncertain`. Uncertainty is blocking. Interactive-use pressure refuses admission.

## Busy is not a diagnosis

An allocator or worker registry reporting `busy` or `exhausted` is **not** a final capacity diagnosis while the snapshot is incomplete. That combination stays `resource_uncertain`.

`capacity_exhausted` is allowed only after the snapshot is complete and available slots are known and non-positive.

## Schedule rule

| Snapshot | Slots | Allocator hint | Decision |
|---|---|---|---|
| incomplete / unknown | any | any, including busy/exhausted | `resource_uncertain`, not scheduled |
| complete | unknown | busy/exhausted | `allocator_busy_not_diagnosis`, not scheduled |
| complete | `<= 0` | any | `capacity_exhausted`, not scheduled |
| complete | `> 0` | eligible | `scheduled` |

## Proof limits

A `scheduled` verdict is not hosted CI proof, not Fast/Full success, and not authorization to publish Review Ready or mutate providers. Implementers on PKT-01 must not start paid or Fast runs from this doctrine.
