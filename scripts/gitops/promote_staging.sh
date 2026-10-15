#!/usr/bin/env bash
# Retained compatibility entrypoint: historical refs are preserved, no mutation.
set -euo pipefail
printf '%s\n' 'FAIL: staging promotion disabled; use reviewed development-to-main promotion with explicit Principal approval' >&2
exit 1
