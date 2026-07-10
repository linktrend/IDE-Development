# Session Lifecycle Design

## Assumptions Made

- the active repository is the repository whose files the current chat can see
- if no repository is clearly active, the runtime must stop and ask
- session lifecycle is an operational capability layered on top of the existing system, not a new doctrine or command family
- handoff continuity belongs at repository level and supplements, but does not replace, canonical execution artifacts
- `docs/handoff/YYYY-MM-DD.md` is the storage location for session handoff reports

## Active Repository Rules

- visible repository files determine the active repository
- no repository may be assumed implicitly if visibility is ambiguous
- session start and session end both stop immediately when repository identity is unclear

## Start-Session Behavior

Natural-language phrases such as:

- `Let's continue.`
- `Continue development.`
- `Pick up where we left off.`
- `Resume work.`

now map to the session lifecycle entrypoint.

Expected behavior:

1. determine active repository
2. `git pull`
3. load the newest handoff report
4. reconstruct completed work, remaining work, blockers, and recommended next action
5. determine current module and ready issues where possible
6. present the recommended next action
7. continue through the existing command, workflow, and artifact path

## End-Session Behavior

Natural-language phrases such as:

- `That's it for today.`
- `I'm done for today.`
- `End the day.`
- `Calling it a day.`

now map to the session lifecycle close-out entrypoint.

Expected behavior:

1. determine active repository
2. `git status`
3. `git add .`
4. `git diff --cached`
5. stop and ask if suspicious staged content appears
6. otherwise generate a meaningful commit message
7. commit
8. push
9. write `docs/handoff/YYYY-MM-DD.md`
10. stop only when the repository is resumable

## Handoff Mechanism

The handoff mechanism is defined through:

- `core/session/HANDOFF-REPORT.md`
- `docs/handoff/YYYY-MM-DD.md`

The handoff captures:

- date and time
- repository
- branch
- completed work
- remaining work
- blockers
- recommended next action

Optional continuity fields include active module, ready issues, pending gates, and key files changed.

## Safety Checks

- stop if the active repository is unclear
- stop if `git pull` fails
- stop if staged changes include obvious secrets, credentials, or suspicious files
- do not rely on hidden chat memory when a handoff report or repository state can be read directly
- do not finish session end until commit, push, and handoff are complete unless a safety trigger interrupts the flow

## Integration Points

Integrated with:

- `core/bootstrap/INDEX.yaml`
- `core/bootstrap/START-HERE.md`
- `core/bootstrap/SESSION-STARTUP.md`
- `core/bootstrap/SESSION-SHUTDOWN.md`
- `core/workflows/INDEX.yaml`
- `core/workflows/WORKFLOW-MODEL.md`
- `core/workflows/README.md`

New canonical session layer:

- `core/session/INDEX.yaml`
- `core/session/README.md`
- `core/session/SESSION-LIFECYCLE.md`
- `core/session/SESSION-START.md`
- `core/session/SESSION-END.md`
- `core/session/HANDOFF-REPORT.md`

Compatibility surface:

- `.cursor/session` is exposed as a compatibility path through the existing `.cursor` adapter layer

## Result

The system now supports natural-language session start and end behavior without:

- adding a new command family
- changing doctrine
- changing execution semantics
- changing the command surface
