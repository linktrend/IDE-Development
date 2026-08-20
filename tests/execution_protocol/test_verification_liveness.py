"""PKT-08 durable verification-liveness contract tests."""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from jsonschema import Draft202012Validator  # noqa: E402

from core.execution.protocol import discover_runtime  # noqa: E402
from core.execution.verification_liveness import (  # noqa: E402
    VERIFICATION_STATES,
    deterministic_artifact_paths,
    ensure_no_duplicate_full_execution,
    heartbeat_verification_run,
    load_verification_liveness_config,
    reconcile_verification_run,
    restart_orphaned_verification,
    start_verification_run,
    validate_verification_run,
)

COMMIT = "004bd5faa1e14ee100a018e16dcb049f0fb2d8eb"
TREE = "6c55220132cc7e9a1baef06f8c147ee9ac9431e7"
NOW = datetime(2026, 8, 20, 12, 0, tzinfo=timezone.utc)


def _run(root: Path, *, started_at: datetime = NOW, handle_id: str = "pid-01") -> dict:
    return start_verification_run(
        run_id="PKT-08-FULL-01",
        packet_id="PKT-08",
        repository="linktrend/IDE-Development",
        canonical_checkout=root,
        cwd=root,
        commit=COMMIT,
        tree=TREE,
        command=("python3", "-m", "unittest", "discover", "-s", "tests"),
        started_at=started_at,
        timeout_seconds=3600,
        durable_handle={"kind": "local_pid", "id": handle_id},
    )


def _running_observation(run: dict, **overrides: object) -> dict:
    observation = {
        "handle": {
            "kind": run["durableHandle"]["kind"],
            "id": run["durableHandle"]["id"],
            "status": "RUNNING",
            "alive": True,
        },
        "commandDigest": run["commandDigest"],
        "logPath": run["logPath"],
        "receiptPath": run["receiptPath"],
        "commit": run["commit"],
        "tree": run["tree"],
    }
    observation.update(overrides)
    return observation


class VerificationLivenessContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory(prefix="pkt08-liveness-")
        self.checkout = Path(self.tmp.name) / "checkout"
        self.checkout.mkdir()

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def test_source_contract_markdown_has_no_trailing_hard_break_spaces(self) -> None:
        for rel in (
            "core/contracts/VERIFICATION-LIVENESS-CONTRACT.md",
            "core/managed-core/content/doctrine/VERIFICATION-LIVENESS.md",
        ):
            lines = (ROOT / rel).read_text(encoding="utf-8").splitlines()
            violations = [
                f"{rel}:{line_number}"
                for line_number, line in enumerate(lines, 1)
                if line.endswith((" ", "\t"))
            ]
            self.assertEqual(violations, [], violations)

    def test_protocol_discovery_requires_and_exposes_liveness_surfaces(self) -> None:
        discovered = discover_runtime(ROOT)
        for path in (
            discovered.verification_liveness_contract,
            discovered.verification_run_schema,
            discovered.verification_liveness_doctrine,
            discovered.verification_liveness_config,
            discovered.verification_liveness_schema,
            discovered.verification_run_managed_schema,
            discovered.verification_run_example,
            discovered.verification_run_managed_example,
        ):
            self.assertTrue(path.is_file(), path)

    def test_start_binds_all_durable_identity_and_artifact_fields(self) -> None:
        run = _run(self.checkout)
        self.assertEqual(set(VERIFICATION_STATES), {
            "STARTED",
            "LIVE",
            "TERMINAL",
            "ORPHANED",
            "TIMED_OUT",
            "RESTARTED",
        })
        self.assertEqual(run["canonicalCheckout"], str(self.checkout.resolve()))
        self.assertEqual(run["cwd"], str(self.checkout.resolve()))
        self.assertEqual(run["repository"], "linktrend/IDE-Development")
        self.assertEqual(run["commit"], COMMIT)
        self.assertEqual(run["tree"], TREE)
        self.assertEqual(
            run["commandDigest"],
            "sha256:" + hashlib.sha256(
                json.dumps(
                    ["python3", "-m", "unittest", "discover", "-s", "tests"],
                    separators=(",", ":"),
                ).encode()
            ).hexdigest(),
        )
        expected_log, expected_receipt = deterministic_artifact_paths(
            self.checkout, "PKT-08-FULL-01"
        )
        self.assertEqual(run["logPath"], expected_log)
        self.assertEqual(run["receiptPath"], expected_receipt)
        self.assertEqual(run["startedAt"], "2026-08-20T12:00:00Z")
        self.assertEqual(run["timeoutSeconds"], 3600)
        self.assertEqual(run["durableHandle"]["id"], "pid-01")
        self.assertEqual(run["state"], "STARTED")
        self.assertTrue(validate_verification_run(run, repo_root=ROOT).ok)

    def test_schema_and_managed_example_are_valid(self) -> None:
        self.assertEqual(
            (ROOT / "core/contracts/VERIFICATION-RUN.schema.json").read_bytes(),
            (ROOT / "core/managed-core/schemas/verification-run.schema.json").read_bytes(),
        )
        schema = json.loads(
            (ROOT / "core/managed-core/schemas/verification-run.schema.json").read_text(
                encoding="utf-8"
            )
        )
        example = json.loads(
            (ROOT / "core/managed-core/examples/verification-run.example.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertFalse(list(Draft202012Validator(schema).iter_errors(example)))
        self.assertTrue(validate_verification_run(example, repo_root=ROOT).ok)
        config_schema = json.loads(
            (ROOT / "core/managed-core/schemas/verification-liveness.schema.json").read_text(
                encoding="utf-8"
            )
        )
        config = load_verification_liveness_config(ROOT)
        self.assertFalse(list(Draft202012Validator(config_schema).iter_errors(config)))
        self.assertFalse(config["paidFallback"])
        self.assertFalse(config["fastFallback"])

    def test_live_heartbeat_reconciles(self) -> None:
        run = _run(self.checkout)
        result = reconcile_verification_run(
            run,
            now=NOW + timedelta(seconds=30),
            observation=_running_observation(run),
        )
        self.assertTrue(result.ok)
        self.assertEqual(result.state, "LIVE")

    def test_heartbeat_updates_durable_live_record(self) -> None:
        run = _run(self.checkout)
        updated = heartbeat_verification_run(
            run,
            now=NOW + timedelta(seconds=30),
            durable_handle=run["durableHandle"],
        )
        self.assertEqual(updated["state"], "LIVE")
        self.assertEqual(updated["lastHeartbeatAt"], "2026-08-20T12:00:30Z")

    def test_terminal_hosted_receipt_reconciles(self) -> None:
        run = _run(self.checkout)
        run["durableHandle"] = {"kind": "hosted_check", "id": "check-01"}
        run["state"] = "TERMINAL"
        result = reconcile_verification_run(
            run,
            now=NOW + timedelta(seconds=30),
            observation={
                **_running_observation(run),
                "handle": {
                    "kind": "hosted_check",
                    "id": "check-01",
                    "status": "COMPLETED",
                    "alive": False,
                },
                "receiptPresent": True,
            },
        )
        self.assertTrue(result.ok)
        self.assertEqual(result.state, "TERMINAL")

    def test_stale_running_state_is_rejected(self) -> None:
        run = _run(self.checkout, started_at=NOW - timedelta(seconds=300))
        result = reconcile_verification_run(
            run,
            now=NOW,
            observation=_running_observation(run),
        )
        self.assertFalse(result.ok)
        self.assertEqual(result.state, "ORPHANED")
        self.assertEqual(result.reason, "stale_running_state")

    def test_missing_handle_is_rejected_and_orphaned(self) -> None:
        run = _run(self.checkout)
        result = reconcile_verification_run(run, now=NOW, observation={})
        self.assertFalse(result.ok)
        self.assertEqual(result.state, "ORPHANED")
        self.assertEqual(result.reason, "missing_durable_handle")

    def test_dead_handle_is_rejected_and_orphaned(self) -> None:
        run = _run(self.checkout)
        result = reconcile_verification_run(
            run,
            now=NOW,
            observation=_running_observation(
                run,
                handle={
                    "kind": "local_pid",
                    "id": "pid-01",
                    "status": "RUNNING",
                    "alive": False,
                },
            ),
        )
        self.assertFalse(result.ok)
        self.assertEqual(result.state, "ORPHANED")
        self.assertEqual(result.reason, "dead_durable_handle")

    def test_completed_hosted_check_marked_running_is_rejected(self) -> None:
        run = _run(self.checkout)
        run["durableHandle"] = {"kind": "hosted_check", "id": "check-01"}
        result = reconcile_verification_run(
            run,
            now=NOW,
            observation={
                **_running_observation(run),
                "handle": {
                    "kind": "hosted_check",
                    "id": "check-01",
                    "status": "COMPLETED",
                    "alive": False,
                },
            },
        )
        self.assertFalse(result.ok)
        self.assertEqual(result.reason, "completed_hosted_check_marked_running")

    def test_command_log_and_tree_mismatches_are_rejected(self) -> None:
        for field, replacement, reason in (
            ("commandDigest", "sha256:" + "a" * 64, "command_digest_mismatch"),
            ("logPath", "/other/run.log", "log_path_mismatch"),
            ("tree", "b" * 40, "tree_mismatch"),
        ):
            with self.subTest(field=field):
                run = _run(self.checkout)
                result = reconcile_verification_run(
                    run,
                    now=NOW,
                    observation=_running_observation(run, **{field: replacement}),
                )
                self.assertFalse(result.ok)
                self.assertEqual(result.reason, reason)

    def test_canonical_checkout_and_cwd_mismatch_is_rejected(self) -> None:
        run = _run(self.checkout)
        result = reconcile_verification_run(
            run,
            now=NOW,
            observation=_running_observation(
                run,
                canonicalCheckout="/other/checkout",
            ),
        )
        self.assertFalse(result.ok)
        self.assertEqual(result.reason, "canonical_checkout_mismatch")

    def test_equivalent_physical_paths_pass_and_different_paths_fail(self) -> None:
        alias = Path(self.tmp.name) / "checkout-alias"
        alias.symlink_to(self.checkout, target_is_directory=True)
        run = start_verification_run(
            run_id="PKT-08-FULL-ALIAS",
            packet_id="PKT-08",
            repository="linktrend/IDE-Development",
            canonical_checkout=alias,
            cwd=self.checkout,
            commit=COMMIT,
            tree=TREE,
            command=("python3", "-m", "unittest"),
            started_at=NOW,
            timeout_seconds=3600,
            durable_handle={"kind": "local_pid", "id": "pid-alias"},
        )
        self.assertEqual(run["canonicalCheckout"], str(self.checkout.resolve()))
        self.assertEqual(
            deterministic_artifact_paths(alias, "PKT-08-FULL-ALIAS"),
            (run["logPath"], run["receiptPath"]),
        )
        alias_document = dict(run)
        alias_document["canonicalCheckout"] = str(alias)
        alias_document["cwd"] = str(alias)
        alias_document["logPath"] = str(
            alias / ".linktrend/verification/PKT-08-FULL-ALIAS.log"
        )
        alias_document["receiptPath"] = str(
            alias / ".linktrend/verification/PKT-08-FULL-ALIAS.receipt.json"
        )
        self.assertTrue(validate_verification_run(alias_document, repo_root=ROOT).ok)
        equivalent = reconcile_verification_run(
            run,
            now=NOW,
            observation=_running_observation(
                run,
                canonicalCheckout=str(alias),
                cwd=str(alias),
                logPath=str(alias / ".linktrend/verification/PKT-08-FULL-ALIAS.log"),
                receiptPath=str(
                    alias / ".linktrend/verification/PKT-08-FULL-ALIAS.receipt.json"
                ),
            ),
        )
        self.assertTrue(equivalent.ok)
        self.assertEqual(equivalent.state, "LIVE")

        other = Path(self.tmp.name) / "other-checkout"
        other.mkdir()
        different = reconcile_verification_run(
            run,
            now=NOW,
            observation=_running_observation(
                run,
                canonicalCheckout=str(other),
            ),
        )
        self.assertFalse(different.ok)
        self.assertEqual(different.reason, "canonical_checkout_mismatch")

    def test_repository_mismatch_and_timeout_are_rejected(self) -> None:
        run = _run(self.checkout)
        mismatch = reconcile_verification_run(
            run,
            now=NOW,
            observation=_running_observation(run, repository="other/repository"),
        )
        self.assertFalse(mismatch.ok)
        self.assertEqual(mismatch.reason, "repository_mismatch")

        timed = _run(self.checkout, started_at=NOW - timedelta(seconds=3601))
        timeout = reconcile_verification_run(
            timed,
            now=NOW,
            observation=_running_observation(timed),
        )
        self.assertFalse(timeout.ok)
        self.assertEqual(timeout.state, "TIMED_OUT")
        self.assertEqual(timeout.reason, "verification_timeout")

    def test_duplicate_same_tree_full_execution_is_rejected(self) -> None:
        first = _run(self.checkout)
        candidate = dict(first)
        candidate["runId"] = "PKT-08-FULL-02"
        with self.assertRaisesRegex(ValueError, "duplicate_same_tree_full_execution"):
            ensure_no_duplicate_full_execution(candidate, (first,))

    def test_only_incomplete_orphaned_runs_can_restart(self) -> None:
        orphaned = _run(self.checkout)
        orphaned["state"] = "ORPHANED"
        restarted = restart_orphaned_verification(
            orphaned,
            now=NOW + timedelta(seconds=60),
            durable_handle={"kind": "local_pid", "id": "pid-02"},
        )
        self.assertEqual(restarted["state"], "RESTARTED")
        self.assertEqual(restarted["restartCount"], 1)
        self.assertEqual(restarted["durableHandle"]["id"], "pid-02")

        terminal = _run(self.checkout)
        terminal["state"] = "TERMINAL"
        with self.assertRaisesRegex(ValueError, "restart_requires_incomplete_orphan"):
            restart_orphaned_verification(
                terminal,
                now=NOW,
                durable_handle={"kind": "local_pid", "id": "pid-03"},
            )

        timed_out = _run(self.checkout)
        timed_out["state"] = "TIMED_OUT"
        with self.assertRaisesRegex(ValueError, "restart_requires_incomplete_orphan"):
            restart_orphaned_verification(
                timed_out,
                now=NOW,
                durable_handle={"kind": "local_pid", "id": "pid-04"},
            )

    def test_restart_policy_is_bounded(self) -> None:
        orphaned = _run(self.checkout)
        orphaned["state"] = "ORPHANED"
        orphaned["restartCount"] = 1
        with self.assertRaisesRegex(ValueError, "automatic_restart_limit_reached"):
            restart_orphaned_verification(
                orphaned,
                now=NOW,
                durable_handle={"kind": "local_pid", "id": "pid-02"},
            )

    def test_extracted_managed_runtime_validates_without_checkout(self) -> None:
        manifest = json.loads(
            (ROOT / "core/managed-core/MANIFEST.json").read_text(encoding="utf-8")
        )
        wanted = {
            "core/execution/__init__.py",
            "core/execution/lifecycle.py",
            "core/execution/manifest_persistence.py",
            "core/execution/protocol.py",
            "core/execution/scheduler.py",
            "core/execution/transactional_dispatch.py",
            "core/execution/verification_liveness.py",
            "core/managed-core/schemas/verification-run.schema.json",
            "core/managed-core/schemas/verification-liveness.schema.json",
            "core/managed-core/schemas/manifest-persistence.schema.json",
            "core/managed-core/examples/verification-run.example.json",
            "core/managed-core/content/config/verification-liveness.json",
            "core/managed-core/content/config/manifest-persistence.json",
            "core/managed-core/content/doctrine/VERIFICATION-LIVENESS.md",
            "core/contracts/VERIFICATION-LIVENESS-CONTRACT.md",
            "core/contracts/VERIFICATION-RUN.schema.json",
        }
        by_source = {entry["source"]: entry for entry in manifest["files"]}
        tmp = Path(tempfile.mkdtemp(prefix="pkt08-extract-"))
        try:
            for rel in wanted:
                self.assertIn(rel, by_source, rel)
                source = ROOT / rel
                entry = by_source[rel]
                digest = "sha256:" + hashlib.sha256(source.read_bytes()).hexdigest()
                self.assertEqual(entry["sourceHash"], digest, rel)
                for destination in (rel, entry["destination"]):
                    target = tmp / destination
                    target.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(source, target)
            self.assertNotIn(str(ROOT.resolve()), "\n".join(
                p.read_text(encoding="utf-8")
                for p in tmp.rglob("*")
                if p.is_file()
            ))
            probe = subprocess.run(
                [
                    sys.executable,
                    "-c",
                    (
                        "from pathlib import Path\n"
                        "from core.execution.verification_liveness import "
                        "load_verification_schema, validate_verification_run\n"
                        "import json\n"
                "from jsonschema import Draft202012Validator\n"
                        "root = Path.cwd()\n"
                        "schema = load_verification_schema(root)\n"
                        "example = json.loads((root / "
                        "'core/managed-core/examples/verification-run.example.json').read_text())\n"
                        "assert validate_verification_run(example, schema=schema, repo_root=root).ok\n"
                "config_schema = json.loads((root / "
                "'core/managed-core/schemas/verification-liveness.schema.json').read_text())\n"
                "config = json.loads((root / "
                "'core/managed-core/content/config/verification-liveness.json').read_text())\n"
                "assert not list(Draft202012Validator(config_schema).iter_errors(config))\n"
                    ),
                ],
                cwd=tmp,
                env={**os.environ, "PYTHONPATH": str(tmp)},
                text=True,
                capture_output=True,
            )
            self.assertEqual(probe.returncode, 0, probe.stderr)
        finally:
            shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
