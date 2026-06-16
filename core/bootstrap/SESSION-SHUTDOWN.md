# Session Shutdown

This document defines the canonical responsibilities for ending a working session safely.

## Purpose

End a session without losing execution state, proof status, review context, blockers, or the next clear step.

Natural-language triggers that should route here through `.cursor/session/` include:

- `That's it for today.`
- `I'm done for today.`
- `End the day.`
- `Calling it a day.`

## Shutdown Sequence

1. determine the active repository from the files visible to the current chat
2. if no active repository is clearly visible, stop and ask which repository is intended
3. inspect the active artifact tree
4. record the real current state of the active work unit
5. confirm whether proof, review, or integration is pending
6. record blockers explicitly if progress stopped
7. run `git status`
8. run `git add .`
9. run `git diff --cached`
10. stop and ask if obvious secrets, credentials, or suspicious files are detected
11. otherwise generate a meaningful commit message
12. commit
13. push
14. write `docs/handoff/YYYY-MM-DD.md`
15. leave the next required command or artifact obvious
16. stop only when the next operator can resume without hidden context

## Shutdown Responsibilities

- avoid leaving ambiguous partial completion
- distinguish `blocked` from unfinished
- preserve the current lifecycle stage
- ensure downstream operators know what to read next
- leave the repository in a pushed, resumable state when no safety trigger exists

## Minimum Shutdown Outputs

- current active artifact path
- current state
- pending gate, if any
- next command or next artifact to open
- explicit blockers if they exist
- handoff report path

## Runtime-Specific Shutdown Flows

### Human

- record the next action and any unresolved decisions

### Cursor

- update the active artifacts instead of relying on ephemeral chat context
- create the handoff report before ending the session

### Codex

- do the same as Cursor
- ensure repository state is inspectable before ending the session
- finish without requiring extra user confirmation unless a safety trigger exists

### Claude

- do the same as other AI runtimes
- preserve explicit artifact-based handoff

## Healthy Shutdown Criteria

A session ends well when:

- no work unit is falsely treated as complete
- the next operator can resume from artifacts alone
- hidden mental context is not required
- repository history and handoff both preserve the current state
