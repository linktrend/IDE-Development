# Issue #72 Lane F — dead-code safety review (independent #2)

| Field | Value |
|-------|--------|
| **Reviewer role** | Lane F independent reviewer #2 (dead-code safety) |
| **Model** | cursor-grok-4.5-high |
| **Mode** | READ-ONLY (no deletions performed) |
| **Worktree** | `/Users/linktrend/Projects/IDE Development/.git/linktrend-worktrees/issue-72-pre-launch-ide-development-codebase-cleanup-arch` |
| **Branch** | `issue/72-pre-launch-ide-development-codebase-cleanup-arch` |
| **HEAD (committed)** | `e6301fc920a4bf841f6bb4d27c15dc4e1f655ef2` (uncommitted Lane A–E tree under review) |
| **Reviewed at** | 2026-08-02T05:13:21Z |
| **Primary evidence reviewed** | `docs/evidence/issue-72/lane-c/**`, live tree, `scripts/verify-platform-adoption.sh`, MANIFEST, portable harness |

## Verdict

**PASS**

No blockers. No majors. Minors are residual clarity items only; they do not reverse the safety of the Claude archive or retention decisions.

---

## Review questions

### 1. Was claude archive safe (no runtime/test/manifest/bootstrap break)?

**Yes — safe.**

| Check | Result | Evidence |
|-------|--------|----------|
| Root `claude/CLAUDE.md` absent | Pass | `test ! -e claude/CLAUDE.md` |
| Archive present (rename, not silent delete) | Pass | Staged `R claude/CLAUDE.md → docs/archive/platform-entrypoints/claude/CLAUDE.md` |
| `verify-platform-adoption.sh` required[] | Pass | Does **not** list `claude/`; lists `chatgpt/` + `codex/` only |
| Portable harness | Pass | `tests/test-portable-v2-integration.sh:230` treats absence as info-only OK |
| MANIFEST packaging | Pass | Zero root `claude/` / `chatgpt/` / `codex/` entries; 6× `platforms/codex/*` retained |
| RC exclusion guardrails | Pass | `release_candidate.py` excludes top-level `claude`; `manifest.py` rejects Claude surfaces |
| Installer / wire / sync | Pass | No `rg` hits installing/copying root `claude/` in wire/sync/installer surfaces |
| Active SOT wording | Pass | README / SETUP / INTENT / PRD retargeted to archive path |

Archive index: `docs/archive/platform-entrypoints/README.md`.

### 2. Were chatgpt/codex correctly retained?

**Yes — correctly retained as compatibility debt.**

| Path | Status | Why retain |
|------|--------|------------|
| `chatgpt/AGENTS.md` | Present + Review Ready language | Hard-required by `scripts/verify-platform-adoption.sh` (`required[]` + content grep) |
| `codex/AGENTS.md` | Present + Review Ready language | Same hard require |
| `codex/README.md` | Present | Paired folder docs; no separate verify gate, but folder must stay with AGENTS |
| Native Codex | Untouched | Root `AGENTS.md`, `.agents/skills/{agentsetup,agentcomply}/SKILL.md`, `core/managed-core/platforms/codex/` all present |

Independent presence+language gate (subset of verify-platform-adoption): **OK**.

Future removal of root `chatgpt/` / `codex/` **must** redesign `verify-platform-adoption.sh` first. Not safe in this issue without that redesign.

### 3. Were any unsafe deletions done?

**No unsafe deletions found.**

| Scope | Observation |
|-------|-------------|
| Pure deletes (`D`) | **0** in working tree status |
| Renames (`R`/`RM`) | Doc/evidence/handoff/work-packet archives (Lane B) + Claude entrypoint archive (Lane C) |
| Scripts / first-party code deletes | **None** |
| Lane D | `.gitignore` expand only; **no tracked file deletes** |
| Lane C | Prefer archive; **no deletes** |
| Wire/sync/backfill | All retained (`wire-repo.sh`, `backfill-managed-workflows.sh`, `sync-managed-*.sh`, `sync-agents-managed-section.sh`) |

`RM` on `docs/runbooks/LANE_F_RESULT.md` and one work-packet are archive-with-stub patterns (Lane B), not runtime dead-code deletes.

### 4. Any remaining first-party dead code that is proven removable without weakening Codex?

**None proven removable under the conservative / high-bar policy.**

Candidates still correctly classified as **retain**:

- Root `chatgpt/`, `codex/` — hard verify debt
- Legacy-named wire/sync/backfill scripts — live verify / migration dependencies
- Packaging guardrails that reject Claude — not debt; keep

Independent scan did not surface additional first-party temp/scratch code with reference-proof of zero dependency outside Lane D hygiene scope. Claiming further removals would weaken Codex or break platform-adoption verify.

### 5. Did anyone hand-edit generated manifests incorrectly?

**No incorrect hand-edit detected.**

| Check | Result |
|-------|--------|
| `env PYTHONPATH=scripts python3 -m ide_development.build_manifest --verify` | **MANIFEST verify OK** |
| Entry count | 227 → 227 (no add/remove) |
| Structural fields (`source` / `destination` / `mode` / `platform` / `ownershipClass`) | Unchanged |
| Diff | Hash-only for `doctrine-agent-completion-md` and `doctrine-managed-core-v2-md` |
| Disk hash match | Both changed `sourceHash` values **MATCH** file contents |
| Lead evidence | `manifest-verify.txt` shows prior FAIL then OK after official regen; `manifest-regen.txt`: `Wrote … 227 files`; `manifest-verify-final.txt`: OK |

Lane C correctly avoided regenerating for the Claude archive alone (archive is not a MANIFEST source). Later hash updates track doctrine content edits via official tooling — not a structural hand-edit.

### 6. Vendored gstack/mattpocock left alone?

**Yes.**

- Paths present: `core/runtime/skills/gstack`, `core/runtime/skills/mattpocock`
- `git status --porcelain` / diff against those trees: **clean**
- No dirty paths matching `gstack` / `mattpocock` / `superpowers` in the Issue #72 worktree status

---

## Findings inventory

### Blockers

None.

### Majors

None.

### Minors

| ID | Finding | Severity | Exact remediation |
|----|---------|----------|-------------------|
| M1 | Archived `docs/archive/platform-entrypoints/claude/CLAUDE.md` still contains relative links `../core/` and `../.cursor/` that **do not resolve** from the archive directory (historical snapshot fidelity). Archive README already marks content non-authoritative. | Minor | **Optional.** Either (a) leave as historical snapshot, or (b) prepend a one-line banner: “Archived path; relative links are historical and do not resolve from this location — see repo-root `core/` / `.cursor/`.” Do **not** “fix” relatives in a way that reintroduces an active Claude install path. |
| M2 | Portable harness comment at `tests/test-portable-v2-integration.sh:229–230` still says historical Claude files “may remain”; behavior already allows absence. Active SOT docs now point at the archive. | Minor | **Optional.** Update the comment to note packaging is archived under `docs/archive/platform-entrypoints/claude/` and root absence is expected; keep the non-failing absence check. |

### Observations (not scored as defects)

- O1: Root `chatgpt/` / `codex/` remain intentional compatibility debt until verify redesign — correctly retained.
- O2: Branch-prefix `codex/` in gitops allowlists is unrelated to root `codex/` folder — do not conflate when planning future cleanup.
- O3: Review tree is still uncommitted relative to `HEAD` `e6301fc`; re-run this review’s presence/MANIFEST checks after commit if the dead-code surface changes.

---

## Remediation summary

**Required before PASS can be used for merge gating:** none.

**Optional polish (≤1 cycle if lead wants clean minors):** M1 banner and/or M2 harness comment. Do **not** delete `chatgpt/`, `codex/`, wire/sync/backfill, or native Codex surfaces as part of that polish.

---

## Commands / checks performed (this reviewer)

```bash
# Path / rename state
test ! -e claude/CLAUDE.md
test -f docs/archive/platform-entrypoints/claude/CLAUDE.md
test -f chatgpt/AGENTS.md && test -f codex/AGENTS.md && test -f codex/README.md
git status --porcelain -- claude docs/archive/platform-entrypoints/claude

# Deletion audit
git status --porcelain | rg '^(D | D)'   # → 0
git status --porcelain | rg '^(R|RM).*claude'

# Verify gate (presence + Review Ready language subset)
# required[] from scripts/verify-platform-adoption.sh — all present

# Manifest
env PYTHONPATH=scripts python3 -m ide_development.build_manifest --verify
# + structural/hash comparison vs HEAD MANIFEST.json

# References
rg 'claude/CLAUDE\.md' tests scripts  # soft OK in portable harness only (active trees)
rg 'chatgpt/AGENTS|codex/AGENTS' scripts/verify-platform-adoption.sh

# Vendored
git status --porcelain -- core/runtime/skills/gstack core/runtime/skills/mattpocock
```

Machine-readable twin: [`dead-code-safety-review.json`](./dead-code-safety-review.json).
