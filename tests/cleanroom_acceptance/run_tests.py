#!/usr/bin/env python3
"""Clean-room acceptance suite for managed-core install/upgrade/drift/rollback.

Lane B (Issue #67 Work Packet 1). Uses fresh temporary Git repositories and a
self-contained extracted package fixture (or Lane D RC extract when present).

Run:
  python3 tests/cleanroom_acceptance/run_tests.py
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
import tempfile
from pathlib import Path

# Allow `python3 tests/cleanroom_acceptance/run_tests.py` without PYTHONPATH.
sys.path.insert(0, str(Path(__file__).resolve().parent))

from harness.assertions import (  # noqa: E402
    assert_cursor_codex_discovery,
    assert_no_checkout_paths_in_tree,
    assert_no_escape_symlinks,
)
from harness.installer import (  # noqa: E402
    EXIT_CONFLICT,
    EXIT_DRIFT,
    EXIT_OK,
    managed_identity_map,
    materialize_isolated_rc_extract,
    materialize_package_copy,
    mode_octal,
    plant_interrupted_current_transaction,
    resolve_package_source,
    rewrite_manifest_source_hash,
    run_installer,
)
from harness.paths import PACKAGE_FIXTURE, REPO_ROOT  # noqa: E402
from harness.reporter import Reporter  # noqa: E402
from harness.repo import cleanup_repo, make_consumer_repo  # noqa: E402


def _pkg_bytes(package: Path, *parts: str) -> bytes:
    return (package.joinpath(*parts)).read_bytes()


def _manifest(package: Path) -> dict:
    return json.loads(
        (package / "core" / "managed-core" / "MANIFEST.json").read_text(
            encoding="utf-8"
        )
    )


def _legacy_fixture(package: Path) -> bool:
    """The checked-in Lane B fixture has deliberately synthetic sample files."""
    return (package / "core" / "managed-core" / "files" / "CORE.txt").is_file()


def _managed_entry(package: Path, destination: str) -> dict:
    for entry in _manifest(package).get("files") or []:
        if entry.get("destination") == destination:
            return entry
    raise AssertionError(f"package manifest has no destination: {destination}")


def _contract_paths(package: Path) -> dict[str, str]:
    """Return package-specific probes without weakening either package lane."""
    if _legacy_fixture(package):
        return {
            "core": ".ide-development/CORE.txt",
            "cursor_rule": ".cursor/rules/sample-rule.mdc",
            "cursor_skill": ".cursor/skills/sample-skill/SKILL.md",
            "codex_skill": ".agents/skills/sample-skill/SKILL.md",
        }
    return {
        "core": ".ide-development/VERSION",
        "cursor_rule": ".cursor/rules/00-bootstrap.mdc",
        "cursor_skill": ".cursor/skills/action-queue/SKILL.md",
        "codex_skill": ".agents/skills/action-queue/SKILL.md",
    }


def _probe_entry(package: Path) -> tuple[dict, Path, str]:
    """Choose a stable managed file for drift/transaction tests."""
    paths = _contract_paths(package)
    destination = paths["core"]
    entry = _managed_entry(package, destination)
    return entry, package / entry["source"], destination


def _fail_cli(rep: Reporter, name: str, result, *, expect: int | None = None) -> None:
    detail = (
        f"exit={result.returncode} expected={expect} "
        f"stdout={result.stdout[:500]!r} stderr={result.stderr[:300]!r}"
    )
    rep.fail(name, detail)


def test_01_brand_new_install(rep: Reporter, package: Path) -> Path | None:
    """1. Brand-new repository installation."""
    repo = make_consumer_repo(prefix="cr-01-")
    try:
        result = run_installer("install", package=package, target=repo)
        if result.returncode != EXIT_OK:
            _fail_cli(rep, "01-brand-new-install", result, expect=EXIT_OK)
            return None
        paths = _contract_paths(package)
        for rel in (
            paths["core"],
            ".ide-development/installed-state.json",
            paths["cursor_rule"],
            paths["cursor_skill"],
            paths["codex_skill"],
            "AGENTS.md",
        ):
            path = repo / rel
            if not path.is_file() or path.is_symlink():
                rep.fail("01-brand-new-install", f"missing physical {rel}")
                return None
        nested = repo / "apps" / "nested" / "deep"
        nested.mkdir(parents=True)
        disc_errs = assert_cursor_codex_discovery(
            repo,
            from_nested=nested,
            cursor_rule_rel=paths["cursor_rule"],
            cursor_skill_rel=paths["cursor_skill"],
            codex_skill_rel=paths["codex_skill"],
        )
        escape_errs = assert_no_escape_symlinks(repo)
        leak_errs = assert_no_checkout_paths_in_tree(repo)
        errors = disc_errs + escape_errs + leak_errs
        if errors:
            rep.fail("01-brand-new-install", "; ".join(errors[:6]))
            return None
        verify = run_installer("verify", package=package, target=repo)
        if verify.returncode != EXIT_OK:
            _fail_cli(rep, "01-brand-new-verify", verify, expect=EXIT_OK)
            return None
        rep.ok("01-brand-new-install")
        return repo
    except Exception as exc:  # noqa: BLE001
        cleanup_repo(repo)
        rep.fail("01-brand-new-install", str(exc))
        return None


def test_02_idempotent_repeat(rep: Reporter, package: Path) -> None:
    """2. Repeat install/update idempotence."""
    repo = make_consumer_repo(prefix="cr-02-")
    try:
        first = run_installer("install", package=package, target=repo)
        if first.returncode != EXIT_OK:
            _fail_cli(rep, "02-idempotent-first-install", first, expect=EXIT_OK)
            return
        snap1 = managed_identity_map(repo)
        second = run_installer("install", package=package, target=repo)
        if second.returncode != EXIT_OK:
            _fail_cli(rep, "02-idempotent-second-install", second, expect=EXIT_OK)
            return
        snap2 = managed_identity_map(repo)
        if snap1 != snap2:
            rep.fail("02-idempotent-second-install", "managed bytes/modes changed")
            return
        updated = run_installer("update", package=package, target=repo)
        if updated.returncode != EXIT_OK:
            _fail_cli(rep, "02-idempotent-noop-update", updated, expect=EXIT_OK)
            return
        snap3 = managed_identity_map(repo)
        if snap1 != snap3:
            rep.fail("02-idempotent-noop-update", "managed bytes/modes changed")
            return
        rep.ok("02-idempotent-repeat")
    finally:
        cleanup_repo(repo)


def test_03_sparse_gitops_upgrade(rep: Reporter, package: Path) -> None:
    """3. Upgrade from sparse GitOps layout."""
    bootstrap_rel = (
        ".cursor/rules/cursor-gitops-bootstrap.mdc"
        if _legacy_fixture(package)
        else ".cursor/rules/consumer-sparse-bootstrap.mdc"
    )
    consumer_gate_rel = (
        "scripts/gitops/completion_gate.py"
        if _legacy_fixture(package)
        else "scripts/local/completion_gate.py"
    )
    sparse_note = _pkg_bytes(
        package,
        "core",
        "managed-core",
        "migrations",
        "known-bytes",
        "obsolete-sparse-gitops-note-v1.md",
    )
    repo = make_consumer_repo(
        prefix="cr-03-",
        files={
            ".github/linktrend-gitops-consumer.json": (
                '{\n  "schemaVersion": 1,\n  "ciWorkflowName": "CI"\n}\n'
            ),
            bootstrap_rel: "# sparse gitops bootstrap\n",
            ".ide-development-upgrade-notes/obsolete-sparse-gitops-note-v1.md": sparse_note,
            consumer_gate_rel: "# consumer sparse runtime\nprint('sparse')\n",
            "docs/TECHNICAL.md": "# repository-specific technical instructions\nKeep.\n",
        },
    )
    try:
        consumer_gate = (repo / consumer_gate_rel).read_bytes()
        tech = (repo / "docs/TECHNICAL.md").read_bytes()
        bootstrap = (repo / bootstrap_rel).read_bytes()

        result = run_installer("install", package=package, target=repo)
        if result.returncode != EXIT_OK:
            _fail_cli(rep, "03-sparse-gitops-upgrade", result, expect=EXIT_OK)
            return
        note = repo / ".ide-development-upgrade-notes/obsolete-sparse-gitops-note-v1.md"
        if note.exists():
            rep.fail("03-sparse-gitops-upgrade", "obsolete sparse note was not removed")
            return
        if (repo / consumer_gate_rel).read_bytes() != consumer_gate:
            rep.fail("03-sparse-gitops-upgrade", "consumer gitops script mutated")
            return
        consumer_config = json.loads(
            (repo / ".github/linktrend-gitops-consumer.json").read_text(encoding="utf-8")
        )
        if (
            consumer_config.get("fastWorkflowName") != "Linktrend Fast Checks"
            or consumer_config.get("ciWorkflowName") != "CI"
        ):
            rep.fail("03-sparse-gitops-upgrade", "consumer workflow declarations changed")
            return
        if (repo / "docs/TECHNICAL.md").read_bytes() != tech:
            rep.fail("03-sparse-gitops-upgrade", "technical instructions mutated")
            return
        # Sparse bootstrap is consumer-owned (not in catalog as exact match remove
        # and not a managed destination) — must remain.
        if (repo / bootstrap_rel).read_bytes() != bootstrap:
            rep.fail("03-sparse-gitops-upgrade", "sparse bootstrap rule mutated")
            return
        if not (repo / _contract_paths(package)["core"]).is_file():
            rep.fail("03-sparse-gitops-upgrade", "managed core missing after upgrade")
            return
        rep.ok("03-sparse-gitops-upgrade")
    finally:
        cleanup_repo(repo)


def test_04_external_cursor_symlink(rep: Reporter, package_src: Path) -> None:
    """4. External .cursor symlink → physical migrate; outside untouched."""
    tmp = Path(tempfile.mkdtemp(prefix="cr-04-"))
    repo: Path | None = None
    try:
        package = materialize_package_copy(tmp / "package", source=package_src)
        outside = tmp / "outside-cursor"
        outside.mkdir()
        secret = outside / "secret.txt"
        secret.write_text("OUTSIDE_MUST_STAY\n", encoding="utf-8")
        before = secret.read_bytes()
        listing = {p.name for p in outside.iterdir()}

        repo = make_consumer_repo(
            prefix="cr-04-repo-",
            files={"CONSUMER.md": "consumer owned docs\n"},
            symlinks={".cursor": str(outside)},
        )
        consumer_before = (repo / "CONSUMER.md").read_bytes()
        original_target = os.readlink(repo / ".cursor")

        result = run_installer("install", package=package, target=repo)
        if result.returncode != EXIT_OK:
            _fail_cli(rep, "04-external-cursor-migrate", result, expect=EXIT_OK)
            return
        cursor = repo / ".cursor"
        if cursor.is_symlink() or not cursor.is_dir():
            rep.fail("04-external-cursor-migrate", ".cursor not physical directory")
            return
        sample = repo / _contract_paths(package)["cursor_rule"]
        if not sample.is_file() or sample.is_symlink():
            rep.fail("04-external-cursor-migrate", "managed cursor rule missing")
            return
        if secret.read_bytes() != before or {p.name for p in outside.iterdir()} != listing:
            rep.fail("04-external-cursor-migrate", "outside target mutated during install")
            return
        if (outside / "rules").exists():
            rep.fail("04-external-cursor-migrate", "installer wrote through symlink")
            return
        if (repo / "CONSUMER.md").read_bytes() != consumer_before:
            rep.fail("04-external-cursor-migrate", "CONSUMER.md mutated")
            return

        rolled = run_installer("rollback", package=package, target=repo)
        if rolled.returncode != EXIT_OK:
            _fail_cli(rep, "04-external-cursor-rollback", rolled, expect=EXIT_OK)
            return
        if not (repo / ".cursor").is_symlink():
            rep.fail("04-external-cursor-rollback", "did not restore symlink")
            return
        if os.readlink(repo / ".cursor") != original_target:
            rep.fail("04-external-cursor-rollback", "symlink target mismatch")
            return
        if secret.read_bytes() != before or {p.name for p in outside.iterdir()} != listing:
            rep.fail("04-external-cursor-rollback", "outside mutated during rollback")
            return
        rep.ok("04-external-cursor-symlink")
    finally:
        if repo is not None:
            cleanup_repo(repo)
        shutil.rmtree(tmp, ignore_errors=True)


def test_05_physical_cursor_consumer_owned(rep: Reporter, package: Path) -> None:
    """5. Existing physical .cursor with consumer-owned rules/commands/skills."""
    repo = make_consumer_repo(
        prefix="cr-05-",
        files={
            ".cursor/rules/consumer-local.mdc": (
                "---\ndescription: Consumer owned rule\nalwaysApply: true\n---\n\n# Keep\n"
            ),
            ".cursor/commands/consumer-cmd.md": "# consumer command\nDo not overwrite.\n",
            ".cursor/skills/consumer-skill/SKILL.md": "# Consumer skill\nPreserve.\n",
        },
    )
    try:
        before = {
            rel: (repo / rel).read_bytes()
            for rel in (
                ".cursor/rules/consumer-local.mdc",
                ".cursor/commands/consumer-cmd.md",
                ".cursor/skills/consumer-skill/SKILL.md",
            )
        }
        result = run_installer("install", package=package, target=repo)
        if result.returncode != EXIT_OK:
            _fail_cli(rep, "05-physical-cursor-consumer-owned", result, expect=EXIT_OK)
            return
        for rel, content in before.items():
            if (repo / rel).read_bytes() != content:
                rep.fail("05-physical-cursor-consumer-owned", f"mutated {rel}")
                return
        if not (repo / _contract_paths(package)["cursor_rule"]).is_file():
            rep.fail("05-physical-cursor-consumer-owned", "managed rule missing")
            return
        if not (repo / _contract_paths(package)["cursor_skill"]).is_file():
            rep.fail("05-physical-cursor-consumer-owned", "managed cursor skill missing")
            return
        rep.ok("05-physical-cursor-consumer-owned")
    finally:
        cleanup_repo(repo)


def test_06_agents_md_consumer_text(rep: Reporter, package: Path) -> None:
    """6. Root AGENTS.md with consumer text outside managed markers."""
    managed_block = _pkg_bytes(
        package, "core", "managed-core", "platforms", "codex", "AGENTS.managed-section.md"
    ).decode("utf-8")
    repo = make_consumer_repo(
        prefix="cr-06-",
        files={
            "AGENTS.md": (
                "# Consumer AGENTS\n\nRepository-specific guidance OUTSIDE markers.\n"
            ),
        },
    )
    try:
        result = run_installer("install", package=package, target=repo)
        if result.returncode != EXIT_OK:
            _fail_cli(rep, "06-agents-md-consumer-text", result, expect=EXIT_OK)
            return
        text = (repo / "AGENTS.md").read_text(encoding="utf-8")
        if "Repository-specific guidance OUTSIDE markers." not in text:
            rep.fail("06-agents-md-consumer-text", "consumer text lost")
            return
        if "BEGIN LINKTREND-IDE-MANAGED" not in text or "END LINKTREND-IDE-MANAGED" not in text:
            rep.fail("06-agents-md-consumer-text", "managed markers missing")
            return
        if managed_block.strip() not in text:
            rep.fail("06-agents-md-consumer-text", "managed block missing")
            return
        # Second update must preserve consumer text byte-identical outside markers.
        outside_before = text.split("<!-- BEGIN LINKTREND-IDE-MANAGED -->")[0]
        updated = run_installer("update", package=package, target=repo)
        if updated.returncode != EXIT_OK:
            _fail_cli(rep, "06-agents-md-idempotent", updated, expect=EXIT_OK)
            return
        text2 = (repo / "AGENTS.md").read_text(encoding="utf-8")
        outside_after = text2.split("<!-- BEGIN LINKTREND-IDE-MANAGED -->")[0]
        if outside_before != outside_after:
            rep.fail("06-agents-md-consumer-text", "consumer region changed on update")
            return
        rep.ok("06-agents-md-consumer-text")
    finally:
        cleanup_repo(repo)


def test_07_repo_specific_agents_skills(rep: Reporter, package: Path) -> None:
    """7. Repository-specific .agents/skills and technical instructions."""
    repo = make_consumer_repo(
        prefix="cr-07-",
        files={
            ".agents/skills/consumer-domain/SKILL.md": (
                "# Consumer domain skill\nProduct-specific instructions.\n"
            ),
            "docs/architecture.md": "# Architecture\nDo not overwrite.\n",
        },
    )
    try:
        skill_before = (repo / ".agents/skills/consumer-domain/SKILL.md").read_bytes()
        arch_before = (repo / "docs/architecture.md").read_bytes()
        result = run_installer("install", package=package, target=repo)
        if result.returncode != EXIT_OK:
            _fail_cli(rep, "07-repo-specific-agents-skills", result, expect=EXIT_OK)
            return
        if (repo / ".agents/skills/consumer-domain/SKILL.md").read_bytes() != skill_before:
            rep.fail("07-repo-specific-agents-skills", "consumer skill mutated")
            return
        if (repo / "docs/architecture.md").read_bytes() != arch_before:
            rep.fail("07-repo-specific-agents-skills", "technical docs mutated")
            return
        managed = repo / _contract_paths(package)["codex_skill"]
        if not managed.is_file() or managed.is_symlink():
            rep.fail("07-repo-specific-agents-skills", "managed Codex skill missing")
            return
        nested = repo / "packages" / "svc" / "nested"
        nested.mkdir(parents=True)
        paths = _contract_paths(package)
        errs = assert_cursor_codex_discovery(
            repo,
            from_nested=nested,
            cursor_rule_rel=paths["cursor_rule"],
            cursor_skill_rel=paths["cursor_skill"],
            codex_skill_rel=paths["codex_skill"],
        )
        if errs:
            rep.fail("07-repo-specific-agents-skills", "; ".join(errs))
            return
        rep.ok("07-repo-specific-agents-skills")
    finally:
        cleanup_repo(repo)


def test_08_obsolete_removal_and_conflict(rep: Reporter, package: Path) -> None:
    """8. Exact-known obsolete removal AND modified/unknown conflict refusal."""
    if _legacy_fixture(package):
        obsolete_path = ".cursor/rules/obsolete-generic.mdc"
        obsolete_exact = _pkg_bytes(
            package, "core", "managed-core", "files", "obsolete-generic.txt"
        )
        obsolete_v1_path = ".cursor/rules/obsolete-generic-v1.mdc"
        obsolete_v1 = _pkg_bytes(
            package,
            "core",
            "managed-core",
            "migrations",
            "known-bytes",
            "obsolete-generic-v1.mdc",
        )
    else:
        catalog = json.loads(
            (package / "core" / "managed-core" / "migrations" / "catalog.json").read_text(
                encoding="utf-8"
            )
        )
        entry = next(
            item
            for item in catalog["entries"]
            if item.get("action") == "remove"
            and item.get("knownBytes")
            and item.get("path") == ".cursor/rules/obsolete-generic-v1.mdc"
        )
        obsolete_path = entry["path"]
        obsolete_exact = _pkg_bytes(package, *entry["knownBytes"].split("/"))
        obsolete_v1_path = obsolete_path
        obsolete_v1 = obsolete_exact

    # Exact removal
    repo_ok = make_consumer_repo(
        prefix="cr-08a-",
        files={
            obsolete_path: obsolete_exact,
            obsolete_v1_path: obsolete_v1,
        },
    )
    try:
        result = run_installer("install", package=package, target=repo_ok)
        if result.returncode != EXIT_OK:
            _fail_cli(rep, "08-obsolete-exact-removal", result, expect=EXIT_OK)
            return
        if (repo_ok / obsolete_path).exists() or (repo_ok / obsolete_v1_path).exists():
            rep.fail("08-obsolete-exact-removal", "known obsolete file was not removed")
            return
        rep.ok("08-obsolete-exact-removal")
    finally:
        cleanup_repo(repo_ok)

    # Modified conflict refusal
    repo_bad = make_consumer_repo(
        prefix="cr-08b-",
        files={
            obsolete_path: "MODIFIED — not reviewed obsolete bytes\n",
        },
    )
    try:
        before = (repo_bad / obsolete_path).read_bytes()
        result = run_installer("install", package=package, target=repo_bad)
        if result.returncode != EXIT_CONFLICT:
            _fail_cli(rep, "08-obsolete-conflict-refuse", result, expect=EXIT_CONFLICT)
            return
        if not (repo_bad / obsolete_path).exists():
            rep.fail("08-obsolete-conflict-refuse", "modified obsolete file was deleted")
            return
        if (repo_bad / obsolete_path).read_bytes() != before:
            rep.fail("08-obsolete-conflict-refuse", "modified obsolete file bytes changed")
            return
        rep.ok("08-obsolete-conflict-refuse")
    finally:
        cleanup_repo(repo_bad)


def test_09_drift_and_deterministic_repair(rep: Reporter, package_src: Path) -> None:
    """9. Drift detection + deterministic repair."""
    tmp = Path(tempfile.mkdtemp(prefix="cr-09-"))
    repo: Path | None = None
    try:
        package = materialize_package_copy(tmp / "package", source=package_src)
        repo = make_consumer_repo(prefix="cr-09-repo-")
        installed = run_installer("install", package=package, target=repo)
        if installed.returncode != EXIT_OK:
            _fail_cli(rep, "09-drift-preinstall", installed, expect=EXIT_OK)
            return

        entry, source, destination = _probe_entry(package)
        core = repo / destination
        original = core.read_bytes()
        original_mode = mode_octal(core)

        # Content drift → detect, refuse blind overwrite, then repair by restoring
        # package bytes and updating (state repair when actual == package hash).
        core.write_text("drifted-content\n", encoding="utf-8")
        drift = run_installer("drift", package=package, target=repo)
        if drift.returncode != EXIT_DRIFT:
            _fail_cli(rep, "09-drift-detect", drift, expect=EXIT_DRIFT)
            return
        kinds = {item.get("kind") for item in (drift.payload or {}).get("drift") or []}
        if "modified" not in kinds:
            rep.fail("09-drift-detect", f"expected modified drift, got {kinds}")
            return
        refused = run_installer("update", package=package, target=repo)
        if refused.returncode != EXIT_CONFLICT:
            _fail_cli(rep, "09-drift-refuse-blind-overwrite", refused, expect=EXIT_CONFLICT)
            return

        # Deterministic repair: restore package bytes, then update repairs state.
        core.write_bytes(original)
        core.chmod(int(original_mode, 8))
        repaired = run_installer("update", package=package, target=repo)
        if repaired.returncode != EXIT_OK:
            _fail_cli(rep, "09-drift-content-repair", repaired, expect=EXIT_OK)
            return
        verify = run_installer("verify", package=package, target=repo)
        if verify.returncode != EXIT_OK:
            _fail_cli(rep, "09-drift-content-repair-verify", verify, expect=EXIT_OK)
            return

        # Mode drift: update should deterministically restore expected mode.
        core.chmod(0o0600)
        if mode_octal(core) == original_mode:
            rep.skip("09-drift-mode-repair", "filesystem ignored chmod (unexpected)")
        else:
            mode_fix = run_installer("update", package=package, target=repo)
            if mode_fix.returncode != EXIT_OK:
                _fail_cli(rep, "09-drift-mode-repair", mode_fix, expect=EXIT_OK)
                return
            if mode_octal(core) != original_mode:
                rep.fail(
                    "09-drift-mode-repair",
                    f"mode not restored got={mode_octal(core)} want={original_mode}",
                )
                return
            rep.ok("09-drift-mode-repair")

        # Marker drift repair (managed region)
        agents = repo / "AGENTS.md"
        agents.write_text(
            "# Consumer AGENTS\n\nKeep me.\n\n"
            "<!-- BEGIN LINKTREND-IDE-MANAGED -->\nDRIFTED BLOCK\n"
            "<!-- END LINKTREND-IDE-MANAGED -->\n",
            encoding="utf-8",
        )
        marker_repair = run_installer("update", package=package, target=repo)
        if marker_repair.returncode != EXIT_OK:
            _fail_cli(rep, "09-drift-marker-repair", marker_repair, expect=EXIT_OK)
            return
        text = agents.read_text(encoding="utf-8")
        managed_block = _pkg_bytes(
            package,
            "core",
            "managed-core",
            "platforms",
            "codex",
            "AGENTS.managed-section.md",
        ).decode("utf-8")
        if "Keep me." not in text or managed_block.strip() not in text:
            rep.fail("09-drift-marker-repair", "marker upsert did not repair correctly")
            return
        if "DRIFTED BLOCK" in text:
            rep.fail("09-drift-marker-repair", "drifted managed block remained")
            return
        rep.ok("09-drift-and-deterministic-repair")
    finally:
        if repo is not None:
            cleanup_repo(repo)
        shutil.rmtree(tmp, ignore_errors=True)


def test_10_interrupted_recovery_and_rollback(rep: Reporter, package_src: Path) -> None:
    """10. Interrupted transaction recovery + byte/mode-exact rollback."""
    tmp = Path(tempfile.mkdtemp(prefix="cr-10-"))
    repo: Path | None = None
    try:
        package = materialize_package_copy(tmp / "package", source=package_src)
        repo = make_consumer_repo(prefix="cr-10-repo-")
        installed = run_installer("install", package=package, target=repo)
        if installed.returncode != EXIT_OK:
            _fail_cli(rep, "10-preinstall", installed, expect=EXIT_OK)
            return

        entry, source, destination = _probe_entry(package)
        core = repo / destination
        original = core.read_bytes()
        original_mode = mode_octal(core)
        plant_interrupted_current_transaction(
            repo, rel_path=destination, original=original, mode=original_mode
        )
        if core.read_bytes() == original:
            rep.fail("10-interrupt-plant", "interrupt plant did not change destination")
            return

        recovered = run_installer("update", package=package, target=repo)
        if recovered.returncode != EXIT_OK:
            _fail_cli(rep, "10-interrupted-recovery", recovered, expect=EXIT_OK)
            return
        if core.read_bytes() != original or mode_octal(core) != original_mode:
            rep.fail("10-interrupted-recovery", "bytes/mode not restored after recovery")
            return
        # current-transaction must be cleared
        if (repo / ".git" / "ide-development" / "current-transaction").exists():
            rep.fail("10-interrupted-recovery", "current-transaction still present")
            return
        rep.ok("10-interrupted-recovery")

        # Byte/mode-exact rollback after a real mutating update
        mutated = tmp / "mutated-package"
        shutil.copytree(package, mutated)
        mutated_core = mutated / entry["source"]
        mutated_core.write_text("CORE_MUTATED_FOR_ROLLBACK\n", encoding="utf-8")
        rewrite_manifest_source_hash(mutated, entry["id"], mutated_core)
        pre_update = core.read_bytes()
        pre_mode = mode_octal(core)
        updated = run_installer("update", package=mutated, target=repo)
        if updated.returncode != EXIT_OK:
            _fail_cli(rep, "10-rollback-setup-update", updated, expect=EXIT_OK)
            return
        if core.read_bytes() == pre_update:
            rep.fail("10-rollback-setup-update", "update did not change CORE.txt")
            return
        rolled = run_installer("rollback", package=package, target=repo)
        if rolled.returncode != EXIT_OK:
            _fail_cli(rep, "10-byte-mode-rollback", rolled, expect=EXIT_OK)
            return
        if core.read_bytes() != pre_update or mode_octal(core) != pre_mode:
            rep.fail("10-byte-mode-rollback", "rollback not byte/mode exact")
            return
        rep.ok("10-byte-mode-rollback")
    finally:
        if repo is not None:
            cleanup_repo(repo)
        shutil.rmtree(tmp, ignore_errors=True)


def test_11_extracted_rc_no_checkout_access(rep: Reporter, package_src: Path) -> None:
    """11. Extracted RC install with no access to IDE Development checkout."""
    tmp = Path(tempfile.mkdtemp(prefix="cr-11-"))
    repo: Path | None = None
    try:
        extract = materialize_isolated_rc_extract(tmp / "rc-extract", source=package_src)
        entry = extract / "scripts" / "ide-development.py"
        if not entry.is_file():
            rep.fail("11-extracted-rc", "installer not bundled into extract")
            return

        # Shadow REPO_ROOT by ensuring cwd/package/entrypoint are all under tmp,
        # and by clearing env markers. We cannot unmount the checkout, but we
        # never pass REPO_ROOT as package/target/entrypoint.
        repo = make_consumer_repo(prefix="cr-11-repo-")
        result = run_installer(
            "install",
            package=extract,
            target=repo,
            entrypoint=entry,
            cwd=extract,
            env={
                "LINKTREND_CLEANROOM_ISOLATED": "1",
                "PWD": str(extract),
            },
        )
        if result.returncode != EXIT_OK:
            _fail_cli(rep, "11-extracted-rc-install", result, expect=EXIT_OK)
            return
        if not (repo / _contract_paths(package_src)["core"]).is_file():
            rep.fail("11-extracted-rc-install", "managed core missing")
            return
        nested = repo / "src" / "nested"
        nested.mkdir(parents=True)
        paths = _contract_paths(package_src)
        errors = (
            assert_cursor_codex_discovery(
                repo,
                from_nested=nested,
                cursor_rule_rel=paths["cursor_rule"],
                cursor_skill_rel=paths["cursor_skill"],
                codex_skill_rel=paths["codex_skill"],
            )
            + assert_no_escape_symlinks(repo)
            + assert_no_checkout_paths_in_tree(repo)
        )
        # Also ensure installed-state has no absolute checkout path.
        state = (repo / ".ide-development" / "installed-state.json").read_text(encoding="utf-8")
        if str(REPO_ROOT.resolve()) in state or str(REPO_ROOT) in state:
            errors.append("installed-state embeds checkout path")
        # version command from extract without checkout package path
        version = run_installer(
            "version",
            package=extract,
            target=repo,
            entrypoint=entry,
            cwd=extract,
        )
        if version.returncode != EXIT_OK:
            _fail_cli(rep, "11-extracted-rc-version", version, expect=EXIT_OK)
            return
        expected_version = _manifest(package_src).get("packageVersion")
        if (version.payload or {}).get("packageVersion") != expected_version:
            rep.fail(
                "11-extracted-rc-version",
                f"unexpected version payload: {version.payload}",
            )
            return
        if errors:
            rep.fail("11-extracted-rc", "; ".join(errors[:8]))
            return
        # The checked-in fixture has an explicit Lane B provenance note; a real
        # release archive proves its provenance through the archive manifest.
        if _legacy_fixture(package_src):
            note = PACKAGE_FIXTURE / "PACKAGE_NOTE.txt"
            if not note.is_file():
                rep.fail("11-extracted-rc-dependency-note", "missing PACKAGE_NOTE.txt")
                return
        rep.ok("11-extracted-rc-no-checkout-access")
    finally:
        if repo is not None:
            cleanup_repo(repo)
        shutil.rmtree(tmp, ignore_errors=True)


def test_portability_package_fixture(rep: Reporter) -> None:
    """Fixture package itself must not embed absolute checkout paths."""
    errors: list[str] = []
    for path in sorted(PACKAGE_FIXTURE.rglob("*")):
        if not path.is_file() or path.name == "PACKAGE_NOTE.txt":
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        if str(REPO_ROOT.resolve()) in text or str(REPO_ROOT) in text:
            errors.append(path.relative_to(PACKAGE_FIXTURE).as_posix())
    if errors:
        rep.fail("portability-package-fixture", f"checkout paths in {errors[:5]}")
    else:
        rep.ok("portability-package-fixture")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--list",
        action="store_true",
        help="List scenario ids and exit",
    )
    args = parser.parse_args(argv)
    scenarios = [
        "01-brand-new-install",
        "02-idempotent-repeat",
        "03-sparse-gitops-upgrade",
        "04-external-cursor-symlink",
        "05-physical-cursor-consumer-owned",
        "06-agents-md-consumer-text",
        "07-repo-specific-agents-skills",
        "08-obsolete-removal-and-conflict",
        "09-drift-and-deterministic-repair",
        "10-interrupted-recovery-and-rollback",
        "11-extracted-rc-no-checkout-access",
    ]
    if args.list:
        for sid in scenarios:
            print(sid)
        return 0

    rep = Reporter()
    try:
        package_src, provenance = resolve_package_source()
    except FileNotFoundError as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1
    print(f"package_source={provenance}")
    print(f"package_path={package_src}")

    if not (REPO_ROOT / "scripts" / "ide-development.py").is_file():
        rep.fail("installer-entrypoint", "scripts/ide-development.py missing")
        print(f"\nSummary: {rep.summary_line()}")
        return 1
    rep.ok("installer-entrypoint")

    test_portability_package_fixture(rep)

    # Shared mutable-safe package copy for read-mostly tests
    work = Path(tempfile.mkdtemp(prefix="cr-shared-pkg-"))
    try:
        package = materialize_package_copy(work / "package", source=package_src)

        leftover = test_01_brand_new_install(rep, package)
        if leftover is not None:
            cleanup_repo(leftover)

        test_02_idempotent_repeat(rep, package)
        test_03_sparse_gitops_upgrade(rep, package)
        test_04_external_cursor_symlink(rep, package_src)
        test_05_physical_cursor_consumer_owned(rep, package)
        test_06_agents_md_consumer_text(rep, package)
        test_07_repo_specific_agents_skills(rep, package)
        test_08_obsolete_removal_and_conflict(rep, package)
        test_09_drift_and_deterministic_repair(rep, package_src)
        test_10_interrupted_recovery_and_rollback(rep, package_src)
        test_11_extracted_rc_no_checkout_access(rep, package_src)
    finally:
        shutil.rmtree(work, ignore_errors=True)

    print(f"\nSummary: {rep.summary_line()}")
    return 1 if rep.failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
