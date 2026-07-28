#!/usr/bin/env bash
# Validate .linktrend/review-ready.json against current HEAD.
# Exit 0 if valid; non-zero with message if invalid/stale/missing.
set -euo pipefail

ROOT="$(git rev-parse --show-toplevel 2>/dev/null)" || {
  echo "FAIL: not a git repository" >&2
  exit 1
}
cd "$ROOT"

FILE="${1:-.linktrend/review-ready.json}"
if [ ! -f "$FILE" ]; then
  echo "FAIL: missing $FILE" >&2
  exit 1
fi

HEAD="$(git rev-parse HEAD)"
SHA="$(python3 - "$FILE" <<'PY'
import json, sys
from pathlib import Path
data = json.loads(Path(sys.argv[1]).read_text())
print(data.get("commitSha", ""))
PY
)"

if [ -z "$SHA" ]; then
  echo "FAIL: review-ready.json missing commitSha" >&2
  exit 1
fi

# Normalize short/long
if [ "${#SHA}" -lt 40 ]; then
  SHA="$(git rev-parse --verify "${SHA}^{commit}" 2>/dev/null || true)"
fi

if [ "$SHA" != "$HEAD" ]; then
  echo "FAIL: review-ready commitSha ($SHA) != HEAD ($HEAD) — record is stale" >&2
  exit 1
fi

GATE="$(python3 - "$FILE" <<'PY'
import json, sys
from pathlib import Path
data = json.loads(Path(sys.argv[1]).read_text())
print(data.get("deterministicGate", ""))
PY
)"
if [ "$GATE" != "pass" ]; then
  echo "FAIL: deterministicGate is not pass (got: $GATE)" >&2
  exit 1
fi

BRANCH="$(python3 - "$FILE" <<'PY'
import json, sys
from pathlib import Path
data = json.loads(Path(sys.argv[1]).read_text())
print(data.get("branch", ""))
PY
)"
CURRENT="$(git rev-parse --abbrev-ref HEAD)"
if [ -n "$BRANCH" ] && [ "$BRANCH" != "$CURRENT" ]; then
  echo "FAIL: review-ready branch ($BRANCH) != current ($CURRENT)" >&2
  exit 1
fi

echo "PASS: review-ready valid for $HEAD"
exit 0
