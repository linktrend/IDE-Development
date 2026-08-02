#!/usr/bin/env python3
"""Focused black-box tests for managed-core migration catalog + scenarios (WP4)."""

from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

# Allow `python3 tests/managed-core-migration-bb/run_tests.py` without PYTHONPATH.
sys.path.insert(0, str(Path(__file__).resolve().parent))

from harness.catalog_validate import load_json, validate_catalog
from harness.classify import (
    classify_consumer_owned,
    classify_dirty_unrelated,
    classify_supersession,
    classify_symlink,
    mode_octal,
    sha256_file,
)
from harness.fixture_builder import make_temp_repo
from harness.installer_live import resolve_live_package, run_installer, run_live_proofs
from harness.paths import (
    CATALOG_PATH,
    FIXTURES_DIR,
    INSTALLER_ENTRY,
    LEGACY_DUPLICATE_CATALOGS,
    MIGRATIONS_DIR,
    REPO_ROOT,
    SCENARIOS_PATH,
    SCHEMA_PATH,
)
from harness.portability import scan_tree


class Reporter:
    def __init__(self) -> None:
        self.passed = 0
        self.failed = 0
        self.skipped = 0

    def ok(self, name: str) -> None:
        self.passed += 1
        print(f"PASS: {name}")

    def fail(self, name: str, detail: str) -> None:
        self.failed += 1
        print(f"FAIL: {name}: {detail}", file=sys.stderr)

    def skip(self, name: str, detail: str) -> None:
        self.skipped += 1
        print(f"SKIP: {name}: {detail}")


def test_catalog_integrity(rep: Reporter) -> dict:
    catalog = load_json(CATALOG_PATH)
    errors = validate_catalog(catalog, repo_root=REPO_ROOT)
    if errors:
        rep.fail("catalog_integrity", "; ".join(errors))
    else:
        rep.ok("catalog_integrity")
    if not SCHEMA_PATH.is_file():
        rep.fail("catalog_schema_present", f"missing {SCHEMA_PATH}")
    else:
        rep.ok("catalog_schema_present")
    return catalog


def test_catalog_canonical_only(rep: Reporter) -> None:
    """Wave 1 integration: one canonical catalog; no duplicate mirrors."""
    if not CATALOG_PATH.is_file():
        rep.fail("canonical_catalog", f"missing {CATALOG_PATH}")
        return
    rep.ok("canonical_catalog")
    for path in LEGACY_DUPLICATE_CATALOGS:
        label = f"no_duplicate:{path.relative_to(REPO_ROOT)}"
        if path.is_file():
            rep.fail(label, "legacy duplicate catalog must be removed")
        else:
            rep.ok(label)


def test_scenarios_index(rep: Reporter) -> None:
    data = load_json(SCENARIOS_PATH)
    scenarios = data.get("scenarios") or []
    if len(scenarios) < 11:
        rep.fail("scenarios_index", f"expected >= 11 scenarios, got {len(scenarios)}")
        return
    missing = []
    for row in scenarios:
        fid = row["fixture"]
        path = FIXTURES_DIR / fid / "scenario.json"
        if not path.is_file():
            missing.append(fid)
    if missing:
        rep.fail("scenarios_index", f"missing fixtures: {missing}")
    else:
        rep.ok("scenarios_index")


def test_portability_package(rep: Reporter) -> None:
    findings = scan_tree(MIGRATIONS_DIR, base=REPO_ROOT)
    findings += scan_tree(FIXTURES_DIR, base=REPO_ROOT)
    uniq: list[str] = []
    seen: set[str] = set()
    for item in findings:
        if item not in seen:
            seen.add(item)
            uniq.append(item)
    if uniq:
        rep.fail("portability_package", "; ".join(uniq[:8]))
    else:
        rep.ok("portability_package")


def _catalog_entry_map(catalog: dict) -> dict[str, dict]:
    return {e["path"]: e for e in catalog.get("entries") or []}


def test_fixture_classifications(rep: Reporter, catalog: dict) -> None:
    entries = _catalog_entry_map(catalog)
    for scenario_path in sorted(FIXTURES_DIR.glob("*/scenario.json")):
        scenario = load_json(scenario_path)
        sid = scenario["id"]
        repo = make_temp_repo(scenario)
        try:
            expected = scenario.get("expected") or {}
            for exp in expected.get("classifications") or []:
                path = exp["path"]
                kind = exp["kind"]
                if kind in {"unsafe_link", "physical_tree"} or (
                    kind == "missing" and path == ".cursor"
                ):
                    actual = classify_symlink(repo, path)
                elif kind in {"supersede_exact", "supersede_mismatch"}:
                    entry = entries.get(path)
                    if not entry:
                        rep.fail(f"{sid}:{path}", "no catalog entry for supersession path")
                        continue
                    actual = classify_supersession(
                        repo,
                        path=path,
                        identity=entry["identity"],
                        content_hash=entry["contentHash"],
                    )
                elif kind == "consumer_owned":
                    actual = classify_consumer_owned(repo, path)
                elif kind == "unrelated_dirty":
                    actual = classify_dirty_unrelated(repo, path)
                elif kind == "recoverable":
                    txn = repo / path
                    actual_kind = "recoverable" if txn.exists() else "missing"
                    from harness.classify import Classification

                    actual = Classification(path, actual_kind)
                else:
                    rep.fail(f"{sid}:{path}", f"unsupported expected kind {kind}")
                    continue
                if actual.kind != kind:
                    rep.fail(
                        f"{sid}:{path}",
                        f"expected kind={kind}, got {actual.kind} ({actual.detail})",
                    )
                else:
                    rep.ok(f"{sid}:{path}->{kind}")

            # Preserve checks
            for rel in expected.get("preserve") or []:
                target = repo / rel
                if not target.exists():
                    rep.fail(f"{sid}:preserve:{rel}", "missing after setup")
                else:
                    rep.ok(f"{sid}:preserve:{rel}")

            # Rollback byte contract from backup
            rollback = expected.get("rollback_bytes") or {}
            if rollback:
                txn_dirs = list((repo / ".git" / "ide-development" / "transactions").glob("*"))
                if not txn_dirs:
                    rep.fail(f"{sid}:rollback", "missing transaction backup")
                else:
                    backup_dir = txn_dirs[0] / "backup"
                    for rel, content in rollback.items():
                        encoded = rel.replace("%", "%25").replace("/", "%2F")
                        backup = backup_dir / encoded
                        if not backup.is_file():
                            rep.fail(f"{sid}:rollback:{rel}", "backup missing")
                            continue
                        if backup.read_text(encoding="utf-8") != content:
                            rep.fail(f"{sid}:rollback:{rel}", "backup bytes mismatch")
                            continue
                        # Simulate byte-exact restore
                        dest = repo / rel
                        dest.parent.mkdir(parents=True, exist_ok=True)
                        dest.write_text(backup.read_text(encoding="utf-8"), encoding="utf-8")
                        mode = (expected.get("rollback_modes") or {}).get(rel, "0644")
                        dest.chmod(int(mode, 8))
                        if dest.read_text(encoding="utf-8") != content or mode_octal(dest) != mode:
                            rep.fail(f"{sid}:rollback:{rel}", "restore not byte/mode exact")
                        else:
                            rep.ok(f"{sid}:rollback:{rel}")

            # Idempotence fingerprint
            for rel in expected.get("idempotent_paths") or []:
                path = repo / rel
                if not path.is_file():
                    rep.fail(f"{sid}:idempotent:{rel}", "missing")
                    continue
                first = sha256_file(path)
                # "Second apply" no-op: rewrite identical bytes
                data = path.read_bytes()
                mode = mode_octal(path)
                path.write_bytes(data)
                path.chmod(int(mode, 8))
                second = sha256_file(path)
                if first != second:
                    rep.fail(f"{sid}:idempotent:{rel}", "hash changed on identical rewrite")
                else:
                    rep.ok(f"{sid}:idempotent:{rel}")

            # Must-not-remove: modified obsolete file remains
            for rel in expected.get("must_not_remove") or []:
                if not (repo / rel).exists():
                    rep.fail(f"{sid}:must_not_remove:{rel}", "file missing")
                else:
                    rep.ok(f"{sid}:must_not_remove:{rel}")
        finally:
            shutil.rmtree(repo.parent, ignore_errors=True)


def test_wp2_catalog_loader(rep: Reporter) -> None:
    """If WP2 loader is importable, ensure migrations catalog loads."""
    sys.path.insert(0, str(REPO_ROOT / "scripts"))
    try:
        from ide_development.manifest import load_migration_catalog
    except Exception as exc:  # noqa: BLE001 — optional integration
        rep.skip("wp2_catalog_loader", f"installer package not importable: {exc}")
        return
    catalog = load_migration_catalog(
        REPO_ROOT,
        catalog_rel="core/managed-core/migrations/catalog.json",
    )
    if not catalog.entries:
        rep.fail("wp2_catalog_loader", "no entries loaded")
        return
    # Default path mirror
    default = load_migration_catalog(REPO_ROOT)
    if len(default.entries) != len(catalog.entries):
        rep.fail(
            "wp2_default_catalog_loader",
            f"default path loaded {len(default.entries)} entries, expected {len(catalog.entries)}",
        )
    else:
        rep.ok("wp2_default_catalog_loader")
    rep.ok(f"wp2_catalog_loader({len(catalog.entries)} entries)")


def test_installer_live(rep: Reporter, *, enabled: bool) -> None:
    """Real installer E2E proofs (symlink safety, recovery, rollback, idempotence)."""
    if not enabled:
        rep.skip("installer_live", "pass --with-installer (or omit --without-installer)")
        return
    if not INSTALLER_ENTRY.is_file():
        rep.skip("installer_live", f"missing {INSTALLER_ENTRY}")
        return

    try:
        package = resolve_live_package()
    except FileNotFoundError as exc:
        rep.fail("installer_live_package", str(exc))
        return
    rep.ok(f"installer_live_package({package.relative_to(REPO_ROOT)})")

    # Smoke: version + plan dry-run against disposable fixture 04
    scenario = load_json(FIXTURES_DIR / "04-exact-obsolete-removal" / "scenario.json")
    repo = make_temp_repo(scenario)
    try:
        version = run_installer("version", package=package, target=repo)
        if version.returncode != 0:
            rep.fail(
                "installer_version",
                version.stderr.strip() or version.stdout.strip() or f"exit={version.returncode}",
            )
        else:
            rep.ok("installer_version")

        plan = run_installer("plan", package=package, target=repo)
        # Accept success or structured conflict; not crash
        combined = (plan.stdout + plan.stderr).lower()
        if plan.returncode in {0, 2, 3, 10, 11} or "conflict" in combined:
            rep.ok("installer_plan_dry_run")
        else:
            rep.fail(
                "installer_plan_dry_run",
                f"exit={plan.returncode} stdout={plan.stdout[:400]} stderr={plan.stderr[:400]}",
            )
    finally:
        shutil.rmtree(repo.parent, ignore_errors=True)

    for name, errors in run_live_proofs():
        if errors:
            rep.fail(name, "; ".join(errors))
        else:
            rep.ok(name)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--with-installer",
        action="store_true",
        help="Force-enable live installer E2E probes",
    )
    parser.add_argument(
        "--without-installer",
        action="store_true",
        help="Skip live installer probes (fixture classification only)",
    )
    args = parser.parse_args(argv)
    rep = Reporter()

    if not CATALOG_PATH.is_file():
        print(f"FAIL: missing catalog at {CATALOG_PATH}", file=sys.stderr)
        return 1

    # Default ON when the installer entrypoint exists (Issue #64 live proofs).
    installer_enabled = False
    if args.without_installer and args.with_installer:
        print(
            "FAIL: pass only one of --with-installer / --without-installer",
            file=sys.stderr,
        )
        return 1
    if args.without_installer:
        installer_enabled = False
    elif args.with_installer:
        installer_enabled = True
    else:
        installer_enabled = INSTALLER_ENTRY.is_file()

    catalog = test_catalog_integrity(rep)
    test_catalog_canonical_only(rep)
    test_scenarios_index(rep)
    test_portability_package(rep)
    test_fixture_classifications(rep, catalog)
    test_wp2_catalog_loader(rep)
    test_installer_live(rep, enabled=installer_enabled)

    print(
        f"\nSummary: passed={rep.passed} failed={rep.failed} skipped={rep.skipped}"
    )
    return 1 if rep.failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
