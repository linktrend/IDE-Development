#!/usr/bin/env bash
# Retired marker/status-based merge route. Exact-head independent review and
# sealed test receipts belong to delivery_controller.py; no implicit approval.
set -euo pipefail
python3 - <<'PYCODE'
import json
from pathlib import Path
payload = {"status": "blocked", "detail": "legacy_integrator_retired_use_delivery_controller"}
for name in ("integrator-result.json", "gitops-outcome.json"):
    Path(name).write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
print(json.dumps(payload))
PYCODE
exit 2
