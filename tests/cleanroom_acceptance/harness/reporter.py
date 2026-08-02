"""Pass/fail/skip reporting."""

from __future__ import annotations

import sys
from dataclasses import dataclass, field


@dataclass
class Reporter:
    passed: int = 0
    failed: int = 0
    skipped: int = 0
    failures: list[str] = field(default_factory=list)
    skips: list[str] = field(default_factory=list)

    def ok(self, name: str) -> None:
        self.passed += 1
        print(f"PASS: {name}")

    def fail(self, name: str, detail: str) -> None:
        self.failed += 1
        msg = f"{name}: {detail}"
        self.failures.append(msg)
        print(f"FAIL: {msg}", file=sys.stderr)

    def skip(self, name: str, detail: str) -> None:
        self.skipped += 1
        msg = f"{name}: {detail}"
        self.skips.append(msg)
        print(f"SKIP: {msg}")

    def summary_line(self) -> str:
        return f"passed={self.passed} failed={self.failed} skipped={self.skipped}"
