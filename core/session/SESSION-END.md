# Session End

## Purpose

Define the operational behavior for natural-language session end and close-out requests.

## Trigger Examples

- `That's it for today.`
- `I'm done for today.`
- `End the day.`
- `Calling it a day.`

## End Sequence

1. determine the active repository from the files visible to the current chat
2. if no active repository is clear, stop and ask which repository is intended
3. run `git status`
4. **Owned-path staging only** — never `git add .` / `git add -A` / `git add --all`:
   - Determine the paths this session owns or touched (from the session diff, handoff notes, and explicit task scope).
   - Stage with `git add -- <path> [<path> ...]` for those paths only.
   - Refuse broad add. Never stage credentials, `.env`, secrets, or dirty files owned by another session.
   - If ownership is ambiguous, stop and ask rather than staging everything.
5. generate or update `docs/handoff/YYYY-MM-DD.md` (owned path) **before** the final commit whenever a handoff is required
6. stage the handoff with owned-path staging
7. run `git diff --cached`
8. inspect staged changes for obvious secrets, credentials, or suspicious files
9. if suspicious staged content is found, stop and ask
10. otherwise generate a meaningful commit message
11. commit staged work
12. push the active branch (**checkpoint only** — do not open a PR; do not request Bugbot; do not mark review-ready unless the issue is actually finished)
13. optional unfinished path: `python3 scripts/gitops/completion_gate.py checkpoint`
14. finished path only:
    - write machine-readable evidence with `python3 scripts/gitops/completion_gate.py write-evidence`
    - then run `python3 scripts/gitops/completion_gate.py review-ready`
    - the gate validates first and **only then** publishes **Linktrend Review Ready**
    - do **not** require Review Ready to already be set before calling the gate
    - do **not** call `mark-review-ready.sh` as a pre-gate publisher
15. finish only after the repository is in a resumable state

## Commit Message Rule

The commit message should reflect the actual work completed during the session.

Avoid:

- vague messages
- purely temporal messages
- handoff-only wording when substantive repository work was performed

## Handoff Report Rule

Session end must write a handoff report under:

`docs/handoff/YYYY-MM-DD.md`

The handoff must include:

- date and time
- summary of completed work
- remaining work
- blockers
- recommended next action

## Safety Checks

Stop and ask before commit or push if:

- obvious secrets or credentials are staged
- staged files appear unrelated or suspicious for the current scope
- repository state is contradictory in a way that prevents a safe close-out

No extra confirmation is required when the repository is cleanly reviewable and no safety trigger is present.

## End Outputs

Minimum outputs:

- clean committed repository state
- pushed branch state
- handoff report path
- clear next action for the next session

## Integration With Existing System

- use `.cursor/bootstrap/SESSION-SHUTDOWN.md` for shutdown responsibilities
- preserve active artifact truth rather than relying on chat memory
- use the handoff report as a continuity layer above execution artifacts, not in place of them
- completion contract: `docs/contracts/AGENT-COMPLETION.md`
