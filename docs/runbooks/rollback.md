# Runbook — rollback (managed-core installer)

**Audience:** Operators recovering from a failed or unwanted `install` / `update` transaction.
**Scope:** Consumer (or disposable) repositories that used `scripts/ide-development.py`.
**Related:** [`release-candidate.md`](./release-candidate.md) · [`../contracts/MANAGED-CORE-V2.md`](../contracts/MANAGED-CORE-V2.md) · [`../CURRENT-STATUS.md`](../CURRENT-STATUS.md)
**Status boundary (2026-08-02):** Rollback remains the recovery path for disposable or **approved** consumer installs. WP04 consumer rollout is prepared / not executed — this runbook does not authorize real consumer mutation.

---

## Plain English

Every mutating installer operation (`install`, `update`) is supposed to:

1. build a deterministic plan first,
2. write a transaction record with **exact pre-change backups**,
3. apply file changes atomically,
4. update committed installed-state only after success.

If something goes wrong — or you need to undo the last successful mutation — **`rollback` restores the exact pre-change bytes and modes** recorded for that last transaction. It does not invent a new “best guess” layout.

---

## Command

```bash
# From system source (or extracted RC entrypoint), targeting the consumer:
python3 scripts/ide-development.py rollback --repo /path/to/consumer

# Machine-readable:
python3 scripts/ide-development.py rollback --repo /path/to/consumer --json

# Dry-run / plan-only (no writes):
python3 scripts/ide-development.py rollback --repo /path/to/consumer --dry-run
```

`--package` may be supplied when operating from an extracted release candidate rather than the live system checkout.

---

## What rollback restores

| Item | Behavior |
|---|---|
| Managed files touched by the last transaction | Restored to exact pre-change bytes + modes from `.git/ide-development/` backups |
| Consumer-owned paths never in the plan | Left untouched |
| External symlink migration | If the transaction unlinked an external `.cursor` symlink and created a physical tree, rollback restores that symlink byte-for-byte and removes only the in-repo physical tree the installer created — **outside target must remain byte-identical** |
| Marker-managed `AGENTS.md` | Restored per transaction backup (consumer text outside markers was preserved on install) |

Transaction metadata lives under **Git-local** `.git/ide-development/` (`last-transaction/`, lock, backups) — not as packaged secrets.

---

## When to use rollback

1. Install/update partially failed and left a recoverable transaction.
2. Verification after install/update fails and you need the previous byte state.
3. Acceptance tests deliberately mutate then prove exact restore.
4. An approved consumer change must be undone **before** further commits complicate recovery (prefer rollback of the installer transaction; do not hand-edit managed hashes).

---

## Fail-closed expectations

| Situation | Expected behavior |
|---|---|
| No last transaction / missing backups | Non-zero exit; do not fabricate restores |
| Corrupt journal or backup map | Fail closed (`rollback_failure` class — see contract exit codes) |
| Concurrent lock held | Fail closed; do not force through |
| Paths outside the recorded transaction | Not reverted |

Installer exit-code classes (contract): `0` clean · `10` drift · `11` conflict · `12` invalid_package · `13` rollback_failure · `1` unexpected.

---

## Operator checklist

1. `python3 scripts/ide-development.py version --repo <target>` — record package identity.
2. `python3 scripts/ide-development.py verify --repo <target>` — capture failure output if any.
3. `python3 scripts/ide-development.py rollback --repo <target> --dry-run` — confirm planned restores.
4. `python3 scripts/ide-development.py rollback --repo <target>` — apply.
5. Re-run `verify` / `drift` and confirm consumer-owned files outside managed ownership are unchanged.
6. For symlink migration cases, confirm the external symlink target directory was never written.

---

## What rollback is not

- Not a substitute for `git checkout` of unrelated dirty consumer work.
- Not live GitHub settings rollback (external state is separate).
- Not permission to roll forward on real consumers before WP04 Principal approval (consumer rollout remains prepared / not executed).
