# Runtime Design

## Architecture

The runtime layer is a specification layer that sits above doctrine and below concrete tooling.

It defines how humans or AI tools should carry out:

- scope loading
- issue selection
- dependency resolution
- execution
- proof
- review
- integration
- completion

The runtime is intentionally:

- human-driven
- tool-independent
- artifact-governed
- non-automated

It assumes no daemon, scheduler, external service, or cloud control plane.

## State Transitions

Normative issue states:

- `draft`
- `planned`
- `blocked`
- `ready`
- `in_progress`
- `review_ready`
- `done`

Primary path:

- `draft -> planned -> ready -> in_progress -> review_ready -> done`

Recovery and failure handling:

- `blocked` may be entered from any non-complete state
- failed review typically returns work to `in_progress` or `blocked`
- failed integration returns work to `blocked`

## Lifecycle

The runtime lifecycle is:

1. load doctrine and indexes
2. load target artifact
3. reduce scope to issues
4. compute readiness
5. select ready issues
6. execute
7. produce proof
8. perform independent review
9. integrate passing work
10. recompute downstream readiness
11. repeat until complete or genuinely blocked

## Execution Flow

The execution flow remains aligned to:

- `Program -> Module -> Phase -> Issue`
- issue as the atomic executable unit
- `Proof -> Review -> Integration` as the mandatory completion chain

Concurrency is allowed only when dependencies and integration risk permit it.

Agents remain resources rather than the control structure. Control comes from:

- artifacts
- dependencies
- gates
- definitions of done

## Runtime Documents

The runtime layer is defined by:

- `.cursor/runtime/INDEX.yaml`
- `.cursor/runtime/README.md`
- `.cursor/runtime/RUNTIME.md`
- `.cursor/runtime/STATE-MODEL.md`
- `.cursor/runtime/EXECUTION-LOOP.md`
- `.cursor/runtime/DEPENDENCY-RESOLUTION.md`

## Remaining Work Before v1.0

1. Integrate the runtime layer into the top-level `.cursor` discovery path if broader entrypoint wiring is desired.

2. Validate the runtime specification against a real low-risk module execution in a live repository.

3. Decide whether a formal blocker artifact is needed or whether blocker trails inside issue, proof, review, and integration artifacts are sufficient.

4. Decide whether higher-level runtime status conventions for program, module, and phase should be standardized more explicitly.

5. Define the minimum review and integration expectations for program-level and release-level completion in more operational detail if future rollout requires it.
