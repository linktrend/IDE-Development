#!/usr/bin/env python3
"""One-shot proof and bounded payload of the official v2.5.2 Content repair path.

This file is intended to run only in the reviewed hosted workflow. It rebuilds
a disposable Git worktree from an exact Content Development snapshot and runs
the official installer against that disposable target. It never opens a live
Content checkout and emits only hashes/identities/path names.
"""

from __future__ import annotations

import argparse
import base64
import gzip
import hashlib
import datetime as dt
import json
import os
import pathlib
import stat
import subprocess
import sys
import time
import zipfile


CANDIDATE_SHA = "6f61bce1ba4ee1d690dc063605387c8842077644"
CANDIDATE_TREE = "7f56c2f7ca893848c66c1e61fac43d1f7155a816"
CONTENT_DEV_SHA = "1de0143e11583b57017071970ae77aea55fed515"
CONTENT_DEV_TREE = "8ad902f75cdf1ea00ab1d5fc1a44228e6f44e808"
SOURCE_MANIFEST_SHA256 = "815a6c5de11a8ad7dda27e9f7eaad57dd3f2e37487e68c9492b05a7872aee07f"
SNAPSHOT_GZIP_SHA256 = "d1a7da625934b56a11f5a54957e2f18d912527bac9f162f300b68461c9b879bb"
RECEIPT_SHA256 = "05fd0cb8e79b789c74e9bad812a8e5f62a882356197e7e82b8f49aa7c4eef86f"
BASELINE_MANIFEST_SHA256 = "249bc5f183623a7f03000e52ad01d113d5abf0d4d5db23343defeaaacb1e973f"
TARGET_REL = pathlib.Path("content-proof/targets/development")
REPORT_REL = pathlib.Path("content-policy-proof-evidence/report.json")


class ProofFailure(Exception):
    def __init__(self, code: str) -> None:
        super().__init__(code)
        self.code = code


def require(ok: bool, code: str) -> None:
    if not ok:
        raise ProofFailure(code)


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def run(argv: list[str], *, cwd: pathlib.Path | None = None, timeout: int = 60) -> subprocess.CompletedProcess[bytes]:
    try:
        return subprocess.run(
            argv,
            cwd=cwd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout,
            check=False,
        )
    except subprocess.TimeoutExpired as exc:
        raise ProofFailure("proof_command_timeout") from exc


def git(root: pathlib.Path, *args: str) -> str:
    result = run(["git", *args], cwd=root)
    require(result.returncode == 0, "proof_git_identity_failed")
    try:
        return result.stdout.decode("utf-8").strip()
    except UnicodeDecodeError as exc:
        raise ProofFailure("proof_git_output_invalid") from exc


def validate_run_binding(expected_control_sha: str, deadline_utc: str) -> None:
    require(len(expected_control_sha) == 40 and all(c in "0123456789abcdef" for c in expected_control_sha), "proof_control_sha_invalid")
    require(os.environ.get("GITHUB_SHA") == expected_control_sha, "proof_expected_control_sha_mismatch")
    require(os.environ.get("GITHUB_WORKFLOW_SHA") == expected_control_sha, "proof_workflow_control_sha_mismatch")
    try:
        deadline = dt.datetime.fromisoformat(deadline_utc.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ProofFailure("proof_deadline_invalid") from exc
    require(deadline.tzinfo is not None and deadline.utcoffset() == dt.timedelta(0), "proof_deadline_not_utc")
    require(deadline >= dt.datetime.now(dt.timezone.utc) + dt.timedelta(minutes=15), "proof_deadline_margin_rejected")


def emit_report(report: dict[str, object], output: pathlib.Path) -> None:
    """Persist only the closed metadata contract, including blocked outcomes."""
    contract = json.loads(pathlib.Path(__file__).with_name("REPORT-CONTRACT.json").read_text())
    require(set(report) <= set(contract["allowedReportKeys"]), "proof_report_shape_rejected")
    require(report.get("status") in contract["statuses"], "proof_report_shape_rejected")
    require(report.get("stage") in contract["stages"], "proof_report_shape_rejected")
    if "failureCode" in report:
        require(report["failureCode"] in contract["failureCodes"], "proof_report_shape_rejected")
    encoded = (json.dumps(report, sort_keys=True, indent=2) + "\n").encode()
    require(len(encoded) <= 32 * 1024, "proof_report_size_limit")
    require(not output.is_symlink(), "proof_report_path_rejected")
    output.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    output.write_bytes(encoded)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--control-root", type=pathlib.Path, required=True)
    parser.add_argument("--candidate-root", type=pathlib.Path, required=True)
    parser.add_argument("--target-root", type=pathlib.Path, required=True)
    parser.add_argument("--candidate-sha", required=True)
    parser.add_argument("--candidate-tree", required=True)
    parser.add_argument("--content-development-sha", required=True)
    parser.add_argument("--content-development-tree", required=True)
    parser.add_argument("--expected-control-sha", required=True)
    parser.add_argument("--deadline-utc", required=True)
    parser.add_argument("--artifact", type=pathlib.Path, required=True)
    parser.add_argument("--report", type=pathlib.Path, required=True)
    args = parser.parse_args()
    report_path = pathlib.Path(os.environ["RUNNER_TEMP"]) / REPORT_REL

    report: dict[str, object] = {
        "schemaVersion": 1,
        "kind": "content-disposable-same-version-repair-proof",
        "status": "blocked",
        "sourceRepository": "linktrend/IDE-Development",
        "sourceCommit": CANDIDATE_SHA,
        "sourceTree": CANDIDATE_TREE,
        "targetRepository": "linktrend/LiNKcontent",
        "targetBranch": "development",
        "targetCommit": CONTENT_DEV_SHA,
        "targetTree": CONTENT_DEV_TREE,
        "proofScope": "disposable installer proof only; no live consumer write or promotion",
        "stage": "run_binding",
        "controlCommit": os.environ.get("GITHUB_SHA", "")[:40],
        "workflowCommit": os.environ.get("GITHUB_WORKFLOW_SHA", "")[:40],
        "snapshotSha256Expected": SNAPSHOT_GZIP_SHA256,
        "repairManifestSha256Expected": RECEIPT_SHA256,
        "sourceManifestSha256Expected": SOURCE_MANIFEST_SHA256,
        "rawStdoutRetained": False,
        "rawStderrRetained": False,
        "liveConsumerChanged": False,
    }
    try:
        require(args.report.resolve(strict=False) == report_path, "proof_report_path_rejected")
        emit_report(report, report_path)
        validate_run_binding(args.expected_control_sha, args.deadline_utc)
        require(args.candidate_sha == CANDIDATE_SHA, "proof_candidate_sha_rejected")
        require(args.candidate_tree == CANDIDATE_TREE, "proof_candidate_tree_rejected")
        require(args.content_development_sha == CONTENT_DEV_SHA, "proof_content_dev_sha_rejected")
        require(args.content_development_tree == CONTENT_DEV_TREE, "proof_content_dev_tree_rejected")

        report["stage"] = "input_identity"
        candidate = args.candidate_root.resolve(strict=True)
        control = args.control_root.resolve(strict=True)
        snapshot_path = control / "CONTENT-DEVELOPMENT-SNAPSHOT.json.gz"
        receipt_path = control / "REPAIR-development.json"
        snapshot_bytes = snapshot_path.read_bytes()
        receipt_bytes = receipt_path.read_bytes()
        require(sha256(snapshot_bytes) == SNAPSHOT_GZIP_SHA256, "proof_snapshot_blob_rejected")
        require(sha256(receipt_bytes) == RECEIPT_SHA256, "proof_receipt_blob_rejected")

        require(git(candidate, "rev-parse", "HEAD") == CANDIDATE_SHA, "proof_source_head_rejected")
        require(git(candidate, "rev-parse", "HEAD^{tree}") == CANDIDATE_TREE, "proof_source_tree_rejected")
        source_manifest = candidate / "core/managed-core/MANIFEST.json"
        require(sha256(source_manifest.read_bytes()) == SOURCE_MANIFEST_SHA256, "proof_source_manifest_rejected")
        require(git(candidate, "status", "--porcelain=v1", "-uall") == "", "proof_source_checkout_dirty")

        report["stage"] = "snapshot_identity"
        snapshot = json.loads(gzip.decompress(snapshot_bytes))
        receipt = json.loads(receipt_bytes)
        require(snapshot["kind"] == "content-dev-exact-managed-preimage", "proof_snapshot_kind_rejected")
        require(snapshot["repository"] == "linktrend/LiNKcontent", "proof_target_repository_rejected")
        require(snapshot["commit"] == CONTENT_DEV_SHA and snapshot["gitTree"] == CONTENT_DEV_TREE, "proof_snapshot_target_identity_rejected")
        require(snapshot["manifestDigest"] == "sha256:" + BASELINE_MANIFEST_SHA256, "proof_installed_manifest_pin_rejected")
        require(sha256(base64.b64decode(snapshot["manifest"]["base64"])) == BASELINE_MANIFEST_SHA256, "proof_installed_manifest_bytes_rejected")
        require(sha256(base64.b64decode(snapshot["installedState"]["base64"])) == snapshot["installedStateDigest"].removeprefix("sha256:"), "proof_installed_state_bytes_rejected")

        package_manifest = json.loads(source_manifest.read_text())
        package_entries = {entry["destination"]: entry for entry in package_manifest["files"]}
        prior_state = json.loads(base64.b64decode(snapshot["installedState"]["base64"]))
        expected_paths = sorted(snapshot["changedManagedPaths"])
        receipt_paths = sorted(row["path"] for row in receipt["paths"])
        require(expected_paths == receipt_paths and len(expected_paths) == 20, "proof_repair_path_set_rejected")
        require(receipt["source"]["commit"] == CANDIDATE_SHA and receipt["source"]["tree"] == CANDIDATE_TREE, "proof_receipt_source_identity_rejected")
        require(receipt["source"]["manifestDigest"] == "sha256:" + SOURCE_MANIFEST_SHA256, "proof_receipt_source_manifest_rejected")
        require(receipt["installed"]["manifestDigest"] == snapshot["manifestDigest"], "proof_receipt_installed_manifest_rejected")
        target = args.target_root
        expected_target = pathlib.Path("/home/runner/work/IDE-Development/IDE-Development") / TARGET_REL
        require(target.resolve(strict=False) == expected_target, "proof_target_path_rejected")
        require(receipt["targetWorktree"] == str(expected_target), "proof_receipt_target_path_rejected")

        # Validate every exact installed preimage and source entry before making
        # the synthetic target repository. No source file contents are emitted.
        snapshot_files = snapshot["files"]
        require(set(snapshot_files) == set(expected_paths), "proof_snapshot_path_set_rejected")
        receipt_by_path = {row["path"]: row for row in receipt["paths"]}
        report["stage"] = "preimage_and_source_binding"
        for rel in expected_paths:
            entry = package_entries.get(rel)
            prior = prior_state["files"].get(rel)
            saved = snapshot_files[rel]
            row = receipt_by_path[rel]
            require(entry is not None and prior is not None, "proof_managed_entry_missing")
            data = base64.b64decode(saved["base64"], validate=True)
            source_data = candidate / entry["source"]
            require(sha256(data) == prior["contentHash"].removeprefix("sha256:"), "proof_target_preimage_digest_rejected")
            require(row["installedDigest"] == prior["contentHash"] and row["installedSourceDigest"] == prior["sourceHash"], "proof_receipt_preimage_rejected")
            require(row["source"] == entry["source"] and row["sourceDigest"] == entry["sourceHash"], "proof_receipt_manifest_binding_rejected")
            require(row["sourceBytes"] == source_data.stat().st_size and sha256(source_data.read_bytes()) == entry["sourceHash"].removeprefix("sha256:"), "proof_source_file_binding_rejected")
            actual_mode = stat.S_IMODE(source_data.stat().st_mode)
            expected_mode = int(entry["mode"], 8)
            require(actual_mode == expected_mode, "proof_source_mode_rejected")

        # Seed a disposable repository with the exact managed preimage subset.
        # Its Git commit is intentionally synthetic; target anchor SHA/tree in
        # the report remain the independently captured live Content identity.
        report["stage"] = "disposable_seed"
        require(not target.exists(), "proof_target_already_exists")
        target.mkdir(parents=True)
        def materialize(rel: str, packed: dict[str, object]) -> None:
            path = target / rel
            path.parent.mkdir(parents=True, exist_ok=True)
            data = base64.b64decode(packed["base64"], validate=True)
            require(sha256(data) == str(packed["sha256"]).removeprefix("sha256:"), "proof_snapshot_file_digest_rejected")
            path.write_bytes(data)
            path.chmod(0o755 if packed.get("gitMode") == "100755" else 0o644)

        materialize(".ide-development/MANIFEST.json", snapshot["manifest"])
        materialize(".ide-development/installed-state.json", snapshot["installedState"])
        for rel in expected_paths:
            materialize(rel, snapshot_files[rel])
        run(["git", "init", "--quiet"], cwd=target)
        run(["git", "config", "user.name", "Content snapshot proof"], cwd=target)
        run(["git", "config", "user.email", "content-proof@example.invalid"], cwd=target)
        run(["git", "add", "-f", "--", ".ide-development/MANIFEST.json", ".ide-development/installed-state.json", *expected_paths], cwd=target)
        seed = run(["git", "commit", "--quiet", "-m", "synthetic Content installed-state preimage"], cwd=target)
        require(seed.returncode == 0, "proof_disposable_target_seed_failed")
        report["syntheticTargetBaseCommit"] = git(target, "rev-parse", "HEAD")

        report["stage"] = "official_installer"
        emit_report(report, report_path)
        started = time.monotonic()
        cli = candidate / "scripts/ide-development.py"
        result = run([
            sys.executable, str(cli), "repair", "--package", str(candidate),
            "--target", str(target), "--repair-manifest", str(receipt_path), "--json",
        ], cwd=candidate, timeout=180)
        report["installerExitCode"] = result.returncode
        report["installerStdoutSha256"] = sha256(result.stdout)
        report["installerStderrSha256"] = sha256(result.stderr)
        report["installerElapsedSeconds"] = round(time.monotonic() - started, 3)
        require(result.returncode == 0, "proof_official_repair_failed")
        try:
            installer = json.loads(result.stdout)
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise ProofFailure("proof_installer_json_invalid") from exc
        require(installer.get("command") == "repair" and installer.get("applied") is True, "proof_installer_result_rejected")

        report["stage"] = "post_install_binding"
        installed_manifest = target / ".ide-development/MANIFEST.json"
        installed_state_path = target / ".ide-development/installed-state.json"
        require(sha256(installed_manifest.read_bytes()) == SOURCE_MANIFEST_SHA256, "proof_post_manifest_rejected")
        next_state = json.loads(installed_state_path.read_text())
        require(next_state.get("manifestHash") == "sha256:" + SOURCE_MANIFEST_SHA256, "proof_post_state_manifest_binding_rejected")
        for rel in expected_paths:
            entry = package_entries[rel]
            actual = (target / rel).read_bytes()
            # Official transaction.apply_action uses read_only_mode(entry.mode).
            # This checks the actual managed physical mode without rewriting it.
            require(stat.S_IMODE((target / rel).stat().st_mode) == (int(entry["mode"], 8) & ~0o222), "proof_post_file_mode_rejected")
            row = next_state["files"].get(rel)
            require(sha256(actual) == entry["sourceHash"].removeprefix("sha256:"), "proof_post_file_digest_rejected")
            require(row is not None and row.get("sourceHash") == entry["sourceHash"] and row.get("contentHash") == entry["sourceHash"], "proof_post_state_path_binding_rejected")
        protected_rows = set(expected_paths) | {".ide-development/MANIFEST.json"}
        for rel, before in prior_state["files"].items():
            if rel not in protected_rows:
                require(next_state["files"].get(rel) == before, "proof_non_target_state_row_changed")

        report["stage"] = "exact_output_scope"
        changed_git = set(filter(None, git(target, "diff", "--name-only", "-z", "HEAD", "--").split("\0")))
        expected_git = set(expected_paths) | {".ide-development/MANIFEST.json", ".ide-development/installed-state.json"}
        require(changed_git == expected_git, "proof_disposable_diff_scope_rejected")
        require(git(target, "ls-files", "--others", "--exclude-standard", "-z") == "", "proof_disposable_untracked_output")
        require(set(filter(None, git(target, "ls-files", "-z").split("\0"))) == expected_git, "proof_disposable_index_path_set_rejected")
        add_result = run(["git", "add", "-f", "--", *sorted(expected_git)], cwd=target)
        require(add_result.returncode == 0, "proof_exact_stage_failed")
        staged = set(filter(None, git(target, "diff", "--cached", "--name-only", "-z", "HEAD", "--").split("\0")))
        require(staged == expected_git, "proof_staged_path_set_rejected")
        require(git(target, "diff", "--name-only", "-z", "--").strip() == "", "proof_unstaged_path_remains")
        require(git(target, "ls-files", "--others", "--exclude-standard", "-z") == "", "proof_untracked_path_remains")
        post_tree = git(target, "write-tree")

        # Package only the exact twenty managed replacements plus the package
        # manifest and installed-state file. The sidecar manifest inventories
        # every payload byte; no snapshot or unrelated target file is included.
        report["stage"] = "payload_assembly"
        artifact_entries = []
        for rel in sorted(expected_git):
            path = target / rel
            require(path.is_file() and not path.is_symlink(), "proof_artifact_nonregular_file")
            data = path.read_bytes()
            mode = stat.S_IMODE(path.stat().st_mode)
            expected_mode = (int(package_entries[rel]["mode"], 8) & ~0o222) if rel in package_entries else 0o444
            require(mode == expected_mode, "proof_artifact_mode_binding_rejected")
            artifact_entries.append({
                "path": rel,
                "sha256": "sha256:" + sha256(data),
                "bytes": len(data),
                "mode": "100755" if mode == 0o555 else "100644",
                "physicalMode": f"{mode:04o}",
            })
            require(mode in (0o444, 0o555), "proof_artifact_mode_rejected")
        require(len(artifact_entries) == 22, "proof_artifact_file_count_rejected")
        report.update({
            "status": "PASS_DISPOSABLE_ONLY",
            "sourceManifestDigest": "sha256:" + SOURCE_MANIFEST_SHA256,
            "targetInstalledManifestDigestBefore": snapshot["manifestDigest"],
            "targetInstalledStateDigestBefore": snapshot["installedStateDigest"],
            "repairManifestSha256": RECEIPT_SHA256,
            "replacedManagedPathCount": len(expected_paths),
            "changedGitPathCount": len(changed_git),
            "postRepairTargetTree": post_tree,
            "liveConsumerChanged": False,
            "mainAction": "no separate installer receipt; carry Development tree through the ordinary protected direct-main promotion",
        })
        manifest = {
            "schemaVersion": 1,
            "kind": "content-disposable-repair-payload",
            "sourceRepository": "linktrend/IDE-Development",
            "sourceCommit": CANDIDATE_SHA,
            "sourceTree": CANDIDATE_TREE,
            "controlCommit": args.expected_control_sha,
            "deadlineUtc": args.deadline_utc,
            "targetRepository": "linktrend/LiNKcontent",
            "targetBranch": "development",
            "targetCommit": CONTENT_DEV_SHA,
            "targetTree": CONTENT_DEV_TREE,
            "postRepairDisposableTree": post_tree,
            "repairReceiptSha256": "sha256:" + RECEIPT_SHA256,
            "proofStatus": "PASS_DISPOSABLE_ONLY",
            "payloadFiles": artifact_entries,
            "payloadFileCount": len(artifact_entries),
            "scope": "exactly 20 repaired managed destinations, .ide-development/MANIFEST.json, and .ide-development/installed-state.json",
            "liveConsumerChanged": False,
        }
        manifest_bytes = (json.dumps(manifest, sort_keys=True, indent=2) + "\n").encode()
        require(len(manifest_bytes) <= 32 * 1024, "proof_artifact_manifest_size_limit")
        args.artifact.parent.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(args.artifact, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
            for entry in artifact_entries:
                rel = entry["path"]
                archive.write(target / rel, arcname=rel)
            archive.writestr("content-repair-artifact-manifest.json", manifest_bytes)
        require(args.artifact.stat().st_size <= 4 * 1024 * 1024, "proof_artifact_size_limit")
        report["stage"] = "complete"
    except ProofFailure as exc:
        report["status"] = "BLOCKED"
        report["failureCode"] = exc.code
    except Exception:
        report["status"] = "BLOCKED"
        report["failureCode"] = "proof_unexpected_error"
    try:
        emit_report(report, report_path)
    except Exception:
        print("content_disposable_repair_proof=BLOCKED failureCode=proof_report_write_failed")
        return 1
    if report["status"] != "PASS_DISPOSABLE_ONLY":
        print("content_disposable_repair_proof=BLOCKED failureCode=" + str(report["failureCode"]))
        return 1
    print("content_disposable_repair_proof=" + str(report["status"]))
    return 0 if report["status"] == "PASS_DISPOSABLE_ONLY" else 1


if __name__ == "__main__":
    raise SystemExit(main())
