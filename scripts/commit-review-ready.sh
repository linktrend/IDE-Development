#!/usr/bin/env bash
# Create (or refresh) a marker-only commit for .linktrend/review-ready.json.
# Parent of the new tip must be the recorded contentSha.
set -euo pipefail

ROOT="$(git rev-parse --show-toplevel 2>/dev/null)" || {
  echo "FAIL: not a git repository" >&2
  exit 1
}
cd "$ROOT"

FILE=".linktrend/review-ready.json"
[ -f "$FILE" ] || {
  echo "FAIL: missing $FILE — run scripts/mark-review-ready.sh first" >&2
  exit 1
}

CONTENT_SHA="$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["contentSha"])' "$FILE")"
HEAD="$(git rev-parse HEAD)"

# If HEAD is already a valid marker for this contentSha, succeed idempotently.
if python3 "${ROOT}/scripts/gitops/validate_review_ready.py" "$ROOT" >/dev/null 2>&1; then
  echo "PASS: already at valid marker tip $(git rev-parse HEAD)"
  exit 0
fi

# Functional tip must equal contentSha before we commit the marker.
if [ "$HEAD" != "$CONTENT_SHA" ]; then
  # Allow re-marking when HEAD is a previous marker whose parent is contentSha
  # but record was rewritten — reset soft is forbidden; require clean rewrite path.
  if git rev-parse --verify "${HEAD}^" >/dev/null 2>&1; then
    PARENT="$(git rev-parse HEAD^)"
    if [ "$PARENT" = "$CONTENT_SHA" ]; then
      # Amend-like replace: create a new marker commit on top of contentSha by
      # resetting soft to content and recommitting only readiness files.
      git reset --soft "$CONTENT_SHA"
    else
      echo "FAIL: HEAD ($HEAD) is not contentSha ($CONTENT_SHA) and not a marker on it" >&2
      exit 1
    fi
  else
    echo "FAIL: HEAD ($HEAD) != contentSha ($CONTENT_SHA)" >&2
    exit 1
  fi
fi

# Stage only readiness artifacts
git add -- "$FILE"
if [ -f .linktrend/review-freeze.json ]; then
  git add -- .linktrend/review-freeze.json
fi

# Refuse if other paths are staged
STAGED="$(git diff --cached --name-only)"
while IFS= read -r p || [ -n "$p" ]; do
  [ -z "$p" ] && continue
  case "$p" in
    .linktrend/review-ready.json|.linktrend/review-freeze.json) ;;
    *)
      echo "FAIL: refusing to include non-readiness path in marker commit: $p" >&2
      exit 1
      ;;
  esac
done <<< "$STAGED"

if [ -z "$(git diff --cached --name-only)" ]; then
  echo "FAIL: nothing to commit for review-ready marker" >&2
  exit 1
fi

git commit -m "chore(review): mark review-ready for ${CONTENT_SHA:0:12}"

python3 "${ROOT}/scripts/gitops/validate_review_ready.py" "$ROOT"
echo "PASS: marker commit $(git rev-parse HEAD) (contentSha=${CONTENT_SHA})"
echo "Next: git push. Review Packager will open a draft PR and run fast-gate before Bugbot."
