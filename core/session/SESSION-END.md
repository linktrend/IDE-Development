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
4. run `git add .`
5. run `git diff --cached`
6. inspect staged changes for obvious secrets, credentials, or suspicious files
7. if suspicious staged content is found, stop and ask
8. otherwise generate a meaningful commit message
9. commit staged work
10. push the active branch
11. generate `docs/handoff/YYYY-MM-DD.md`
12. finish only after the repository is in a resumable state

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
