# GitOps bootstrap activation smoke record

Date: 2026-07-30 (Asia/Taipei)

Purpose: Controlled Phase 4 default-branch activation smoke after issue #23
corrected Packager/promote workflows landed on `main`.

Facts (append-only; no doctrine or application change):

- Issue #23 bootstrap candidate PR #24 head `7eb41b2494faf6a7dc683b37d2b7334ddd517bee`
  tree `965ef30de915b1bfcdd568ac885eac4a4f79eff9` promoted through
  development → staging → main.
- Development merge: `3ea6ebadf46d2640f8035bbe7fc8a93e48881638`
- Staging merge: `a1c3444a8447efe65b30ce3997816c9ae2024d07`
- Main merge (PR #26): `c52b983716b02858fc37935e6e3ab422b7b3c6f8`
- Post-promote trees equal:
  `main` = `staging` = `development` = `965ef30de915b1bfcdd568ac885eac4a4f79eff9`
- Packager workflow_dispatch smoke run `30517509296`:
  `AUTOMATION_TOKEN_SOURCE=github_app`, credentials configured, outcome `packaged`.

This file is documentation-only evidence for the activation smoke PR.
