#!/usr/bin/env bash
# Run WP3 managed-core adapter tests only.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"
exec python3 "$ROOT/tests/adapters/test_managed_core_adapters.py"
