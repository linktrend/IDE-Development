# Archive — platform entrypoints (historical)

Historical first-party platform entrypoint files retained for audit. **Not authoritative.** Not part of the portable managed-core package.

| Path | Origin | Why archived |
|------|--------|----------------|
| `claude/CLAUDE.md` | Repo-root `claude/CLAUDE.md` | Claude Code excluded from v2 support/roadmap; not in `MANIFEST.json`; RC packaging excludes `claude/`; `verify-platform-adoption.sh` does not require it; portable harness treats absence as OK |

**Active Codex / ChatGPT surfaces (do not confuse with this archive):**

- Root `AGENTS.md` + `.agents/skills/`
- `core/managed-core/platforms/codex/`
- Repo-root `codex/` and `chatgpt/` (still present; required by `scripts/verify-platform-adoption.sh` — see Issue #72 Lane C retained debt)
