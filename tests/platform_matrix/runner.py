"""Unittest discovery + filtering for the cross-platform matrix."""

from __future__ import annotations

import sys
import time
import traceback
import unittest
from pathlib import Path
from typing import List, Optional, Sequence, Tuple

from . import REPO_ROOT, SCRIPTS_DIR
from .exclusions import Exclusion, active_exclusions, exclusion_summary, should_exclude
from .summary import (
    MatrixSummary,
    TestCaseRecord,
    default_coverage_areas,
    host_platform_info,
    write_summary,
)


def _ensure_import_paths() -> None:
    for path in (str(SCRIPTS_DIR), str(REPO_ROOT / "tests")):
        if path not in sys.path:
            sys.path.insert(0, path)


def discover_suites(
    *,
    include_existing: bool = True,
    include_matrix: bool = True,
) -> Tuple[unittest.TestSuite, List[str]]:
    """Discover installer unit tests + matrix supplements."""
    _ensure_import_paths()
    loader = unittest.defaultTestLoader
    suite = unittest.TestSuite()
    labels: List[str] = []

    if include_existing:
        start = str(SCRIPTS_DIR / "ide_development_tests")
        discovered = loader.discover(
            start_dir=start,
            pattern="test_*.py",
            top_level_dir=str(SCRIPTS_DIR),
        )
        suite.addTests(discovered)
        labels.append("scripts/ide_development_tests")

    if include_matrix:
        matrix_dir = str(REPO_ROOT / "tests" / "platform_matrix")
        discovered = loader.discover(
            start_dir=matrix_dir,
            pattern="test_*.py",
            top_level_dir=str(REPO_ROOT / "tests"),
        )
        suite.addTests(discovered)
        labels.append("tests/platform_matrix")

    return suite, labels


def _iter_tests(suite: unittest.TestSuite):
    for test in suite:
        if isinstance(test, unittest.TestSuite):
            yield from _iter_tests(test)
        else:
            yield test


def apply_exclusions(
    suite: unittest.TestSuite,
    exclusions: Optional[Sequence[Exclusion]] = None,
) -> unittest.TestSuite:
    """Rebuild suite, skipping excluded tests via unittest.skip."""
    rules = list(exclusions) if exclusions is not None else active_exclusions()
    out = unittest.TestSuite()
    for test in _iter_tests(suite):
        test_id = test.id()
        rule = should_exclude(test_id, rules)
        if rule is None:
            out.addTest(test)
            continue

        reason = (
            f"platform exclusion ({sys.platform}): {rule.reason}; "
            f"equivalent={rule.equivalent_coverage}"
        )

        class _Excluded(unittest.TestCase):
            def runTest(self):
                self.skipTest(reason)

        excluded = _Excluded()
        # Preserve original identity in JSON / TextTest reports.
        excluded.id = lambda _id=test_id: _id  # type: ignore[method-assign]
        out.addTest(excluded)
    return out


class _RecordingResult(unittest.TextTestResult):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.records: List[TestCaseRecord] = []
        self._started: dict = {}

    def startTest(self, test):
        self._started[id(test)] = time.perf_counter()
        super().startTest(test)

    def addSuccess(self, test):
        self._record(test, "pass")
        super().addSuccess(test)

    def addFailure(self, test, err):
        self._record(test, "fail", err=err)
        super().addFailure(test, err)

    def addError(self, test, err):
        self._record(test, "error", err=err)
        super().addError(test, err)

    def addSkip(self, test, reason):
        exclusion_reason = ""
        equivalent = ""
        text = reason or ""
        if "equivalent=" in text:
            exclusion_reason = text
            equivalent = text.split("equivalent=", 1)[-1].strip()
        self._record(
            test,
            "skip",
            message=text,
            exclusion_reason=exclusion_reason,
            equivalent=equivalent,
        )
        super().addSkip(test, reason)

    def _record(
        self,
        test,
        outcome: str,
        *,
        err=None,
        message: str = "",
        exclusion_reason: str = "",
        equivalent: str = "",
    ) -> None:
        started = self._started.pop(id(test), time.perf_counter())
        elapsed = max(0.0, time.perf_counter() - started)
        msg = message
        if err is not None and not msg:
            msg = "".join(traceback.format_exception(*err))[-2000:]
        self.records.append(
            TestCaseRecord(
                id=test.id(),
                outcome=outcome,
                elapsedSec=round(elapsed, 4),
                message=msg,
                exclusionReason=exclusion_reason,
                equivalentCoverage=equivalent,
            )
        )


def run_matrix(
    *,
    verbosity: int = 2,
    include_existing: bool = True,
    include_matrix: bool = True,
    write_json: bool = True,
    summary_path: Optional[Path] = None,
    argv: Optional[Sequence[str]] = None,
) -> MatrixSummary:
    """Run the matrix and optionally write a JSON summary. Returns summary."""
    command = list(argv) if argv is not None else [sys.executable, *sys.argv]
    suite, labels = discover_suites(
        include_existing=include_existing,
        include_matrix=include_matrix,
    )
    exclusions = active_exclusions()
    suite = apply_exclusions(suite, exclusions)

    stream = sys.stderr
    runner = unittest.TextTestRunner(
        stream=stream,
        verbosity=verbosity,
        resultclass=_RecordingResult,
    )
    result = runner.run(suite)
    assert isinstance(result, _RecordingResult)

    counts = {
        "run": result.testsRun,
        "pass": len([r for r in result.records if r.outcome == "pass"]),
        "fail": len(result.failures),
        "error": len(result.errors),
        "skip": len(result.skipped),
    }
    # Prefer recorded outcomes for pass count when available.
    recorded_pass = sum(1 for r in result.records if r.outcome == "pass")
    if recorded_pass:
        counts["pass"] = recorded_pass

    exit_code = 0 if result.wasSuccessful() else 1
    notes: List[str] = []
    if exclusions:
        notes.append(
            f"Applied {len(exclusions)} platform exclusion rule(s) on {sys.platform}; "
            "each is paired with equivalentCoverage in exclusion_summary."
        )
    notes.append(
        "Shell-only suites (bash scripts) are out of scope for this Python matrix "
        "entrypoint on Windows; macOS/Linux CI still runs them via other workflows."
    )

    summary = MatrixSummary(
        generatedAt=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        platform=host_platform_info(),
        command=list(command),
        exitCode=exit_code,
        counts=counts,
        suites=labels,
        exclusions=exclusion_summary(exclusions),
        coverageAreas=default_coverage_areas(),
        tests=[
            {
                "id": r.id,
                "outcome": r.outcome,
                "elapsedSec": r.elapsedSec,
                "message": r.message,
                "exclusionReason": r.exclusionReason,
                "equivalentCoverage": r.equivalentCoverage,
            }
            for r in result.records
        ],
        notes=notes,
    )

    if write_json:
        path = write_summary(summary, summary_path)
        print(f"matrix summary written: {path}", file=sys.stderr)

    return summary
