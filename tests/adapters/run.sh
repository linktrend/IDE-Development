#!/usr/bin/env bash
# Run managed-core adapter fixture and contract tests.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"
python3 "$ROOT/tests/adapters/test_managed_core_adapters.py"
exec node --test "$ROOT/tests/adapters/test_application_adapter.mjs"
