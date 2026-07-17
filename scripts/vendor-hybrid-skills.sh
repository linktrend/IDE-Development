#!/usr/bin/env bash
# Refresh physical vendored hybrid skill copies from local upstream clones.
# Does not create cross-repo symlinks. Requires local checkouts of gstack and skills.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
GSTACK_SRC="${GSTACK_SRC:-/Users/linktrend/Projects/gstack}"
SKILLS_SRC="${SKILLS_SRC:-/Users/linktrend/Projects/skills/skills/engineering}"
DEST_G="$ROOT/core/runtime/skills/gstack"
DEST_M="$ROOT/core/runtime/skills/mattpocock"

if [[ ! -d "$GSTACK_SRC/.git" && ! -d "$GSTACK_SRC" ]]; then
  echo "GSTACK_SRC not found: $GSTACK_SRC" >&2
  exit 1
fi

mkdir -p "$DEST_G" "$DEST_M"
for d in spec plan-ceo-review health ship context-save context-restore review qa retro learn; do
  rm -rf "$DEST_G/$d"
  cp -R "$GSTACK_SRC/$d" "$DEST_G/$d"
done
for d in grill-with-docs to-spec to-tickets tdd diagnosing-bugs research triage setup-matt-pocock-skills improve-codebase-architecture; do
  rm -rf "$DEST_M/$d"
  cp -R "$SKILLS_SRC/$d" "$DEST_M/$d"
done

echo "Vendored into $DEST_G and $DEST_M"
echo "Regenerate VENDOR-MANIFEST.json and run scripts/verify-vendored-skills.sh"
