# Session Lifecycle

## Purpose

Define how natural-language session start and session end requests are interpreted inside the existing operating model.

This capability exists so phrases such as:

- `Let's continue.`
- `Continue development.`
- `Pick up where we left off.`
- `Resume work.`

and:

- `That's it for today.`
- `I'm done for today.`
- `End the day.`
- `Calling it a day.`

route into the correct operational behavior without introducing a new command family.

## Scope

Session lifecycle is an operational capability layered on top of:

- bootstrap
- runtime
- workflows
- state
- contracts
- templates
- repository hygiene

It does not replace execution doctrine or create a new top-level execution lifecycle.

Workspace adoption remains a separate one-time capability under `.cursor/workspace/`. Session lifecycle continues to govern daily resume and close-out behavior after adoption is complete.

## Active Repository Rule

The active repository is the repository whose files the current chat can see.

If no repository is clearly active:

- stop
- ask which repository is intended
- do not guess

## Session Start Trigger

Natural-language resume requests map to session start behavior.

Session start must:

1. identify the active repository
2. pull latest changes
3. read the latest handoff report at `docs/handoff/YYYY-MM-DD.md`
4. reconstruct context from the handoff and current artifacts
5. identify completed work, remaining work, blockers, and recommended next action
6. determine the current module and ready issues where applicable
7. present the recommended next action
8. continue execution through the existing command, workflow, and artifact model

## Session End Trigger

Natural-language close-out requests map to session end behavior.

Session end must:

1. identify the active repository
2. inspect repository state
3. stage changes
4. inspect staged changes
5. stop and ask if obvious secrets, credentials, or suspicious files appear
6. otherwise generate a meaningful commit message
7. commit
8. push
9. generate `docs/handoff/YYYY-MM-DD.md`
10. stop only after the repository is resumable from artifacts and git history

## Handoff Principle

Session lifecycle depends on an explicit handoff artifact.

The handoff report is not a replacement for execution artifacts. It is a repository-level continuity artifact that summarizes:

- completed work
- remaining work
- blockers
- recommended next action

## Safety Principle

Session lifecycle should automate continuity, not trust hidden chat memory.

That means:

- repository state must be inspected directly
- handoff must be written to disk
- restart context must be reconstructed from files and git state
- suspicious staged content must interrupt session end

## Read Next

1. `SESSION-START.md`
2. `SESSION-END.md`
3. `HANDOFF-REPORT.md`
