# Canonical Laws

These laws are the durable foundation of the execution system. They are tool-independent and apply whether work is carried out by humans, Cursor, Codex, cloud agents, or future runtimes.

1. **The issue is the atomic executable unit.** All autonomous work is executed as issues, not as modules, phases, or agents.
2. **Programs, modules, and phases are control containers, not execution units.** They organize scope, checkpoints, and reporting, but execution occurs at issue level.
3. **Dependencies determine execution order.** Work becomes executable only when its declared dependencies are satisfied.
4. **Readiness is computed, not declared.** An issue is ready only when prerequisites, scope, and gates are actually satisfied.
5. **Concurrency emerges from dependency satisfaction.** Independent issues may proceed in parallel, subject to practical coordination limits.
6. **Planning must produce an executable graph.** A valid plan is a dependency-aware structure, not just a task list.
7. **Every issue must have explicit scope.** Allowed work, prohibited work, required inputs, and expected outputs must be bounded before execution begins.
8. **Every issue must have testable completion criteria.** Work is incomplete if success cannot be observed or verified.
9. **Completion requires evidence, not confidence.** Work is not done because an agent believes it is done; it is done when proof exists.
10. **Proof must be non-vacuous.** Completion claims must be backed by concrete artifacts, outputs, traces, or verifiable state changes.
11. **Blocked work must leave a trail.** When progress stops, the runtime must preserve what was attempted, what failed, and why.
12. **Review is separate from execution.** The actor that performs the work is not the final authority on whether it passes.
13. **Integration is separate from review.** Reviewed work is not yet integrated work; incorporation into the active line is a distinct step.
14. **Release is separate from integration.** Integrated work is not automatically releasable; release requires system-level validation.
15. **Higher-level completion is stricter than lower-level completion.** Module and program completion require more than all child issues being marked done.
16. **Quality gates must stop progression, not merely warn.** A blocking failure prevents downstream execution until resolved or explicitly waived.
17. **Definitions of done exist at every level.** Issues, phases, modules, and programs each require explicit completion semantics.
18. **Agents are resources, not the control structure.** Execution order should emerge from artifacts and dependencies, not from fixed agent choreography.
19. **Progressive disclosure is mandatory.** Agents should read only the minimum context required for the current unit of work.
20. **The system must remain tool-independent.** The execution model must survive changes in IDE, runtime, or automation surface because the laws live in artifacts, not software orchestration.
