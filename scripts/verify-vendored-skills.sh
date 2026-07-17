#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
MANIFEST="$ROOT/core/runtime/skills/VENDOR-MANIFEST.json"
SKILLS_ROOT="$ROOT/core/runtime/skills"

if [[ ! -f "$MANIFEST" ]]; then
  echo "Missing manifest: $MANIFEST" >&2
  exit 1
fi

python3 - <<'PY' "$MANIFEST" "$SKILLS_ROOT" "$ROOT"
import hashlib, json, os, sys
from pathlib import Path

manifest_path = Path(sys.argv[1])
skills_root = Path(sys.argv[2])
repo_root = Path(sys.argv[3])
manifest = json.loads(manifest_path.read_text())
errors = []

# 1) no vendored path is a symlink (gstack/mattpocock trees)
for sub in ("gstack", "mattpocock"):
    base = skills_root / sub
    if not base.exists():
        errors.append(f"missing {base}")
        continue
    for p in base.rglob("*"):
        if p.is_symlink():
            errors.append(f"symlink not allowed: {p}")

# 2) every manifest file exists and hashes correctly
for rel, expected in manifest.get("files", {}).items():
    # adaptation exclusions skipped from byte-equality vs upstream, but still must exist if listed
    path = skills_root / rel
    if not path.is_file():
        errors.append(f"missing file: {rel}")
        continue
    if path.is_symlink():
        errors.append(f"manifest path is symlink: {rel}")
        continue
    h = hashlib.sha256(path.read_bytes()).hexdigest()
    if h != expected:
        errors.append(f"hash mismatch: {rel}")

# 3) no absolute upstream sibling paths in active runtime content under skills + hybrid commands
banned = [
    "/Users/linktrend/Projects/gstack",
    "/Users/linktrend/Projects/skills",
]
scan_roots = [
    skills_root,
    repo_root / "core" / "commands",
    repo_root / "core" / "runtime",
]
for root in scan_roots:
    if not root.exists():
        continue
    for p in root.rglob("*"):
        if not p.is_file() or p.is_symlink():
            continue
        if "VENDOR-MANIFEST.json" in p.name:
            continue
        try:
            text = p.read_text(errors="ignore")
        except Exception:
            continue
        for b in banned:
            if b in text:
                errors.append(f"absolute upstream path in {p.relative_to(repo_root)}: {b}")

if errors:
    print("FAIL: verify-vendored-skills")
    for e in errors:
        print(" -", e)
    sys.exit(1)
print(f"PASS: verify-vendored-skills ({len(manifest.get('files', {}))} files)")
PY
