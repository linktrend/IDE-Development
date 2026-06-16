# Artifact Audit

## Scope

Reviewed only:

- `.cursor/templates/`
- `.cursor/execution/`
- `.cursor/templates/INDEX.yaml`
- `.cursor/execution/INDEX.yaml`

Artifacts of interest:

- `INTENT.md`
- `PROGRAM.md`
- `MODULE.md`
- `PHASE.md`
- `ISSUE.md`
- `PROOF.md`
- `REVIEW.md`
- `INTEGRATION.md`
- `COUNCIL-SUMMARY.md`
- `AGENT-REPORT.md`
- `MODULE-README.md`

## Findings

### 1. Canonical artifact flow is internally coherent

The core execution artifacts are aligned with the doctrine:

- `INTENT.md` exists before `PROGRAM.md`
- `PROGRAM.md` contains modules
- `MODULE.md` contains phases
- `PHASE.md` contains issues
- `ISSUE.md` is explicitly the atomic executable unit
- completion flow is explicitly `PROOF.md -> REVIEW.md -> INTEGRATION.md`

This matches the execution doctrine:

- `Program -> Module -> Phase -> Issue`
- issue as the atomic executable unit
- proof, review, and integration as separate required stages

### 2. Roll-up semantics are mostly clear

The templates define upward roll-up correctly:

- issue completion rolls into phase progress
- phase completion rolls into module progress
- module completion requires module definition of done and module review
- program completion requires program definition of done and does not automatically imply release readiness

This is consistent with the doctrine that higher-level completion is stricter than lower-level completion.

### 3. Compatibility artifacts are intentionally non-canonical, but overlap exists

Three templates clearly sit adjacent to the canonical execution layer:

- `AGENT-REPORT.md`
- `MODULE-README.md`
- `COUNCIL-SUMMARY.md`

Their intended boundaries are mostly clear:

- `AGENT-REPORT.md` is compatibility-only and references canonical artifacts
- `MODULE-README.md` is compatibility-only and explicitly subordinate to `MODULE.md`
- `COUNCIL-SUMMARY.md` is optional and explicitly not for ordinary issue review

Even so, all three overlap nearby canonical concepts:

- `AGENT-REPORT.md` overlaps proof, review, and integration summaries
- `MODULE-README.md` overlaps module orientation and module summary responsibilities
- `COUNCIL-SUMMARY.md` overlaps higher-level review and escalation activity already related to `REVIEW.md`

This overlap appears intentional rather than accidental, but it remains a maintenance risk.

### 4. Strict discoverability is incomplete

Indexed template files:

- all canonical execution templates in scope are indexed
- the compatibility artifacts in scope are indexed

Strict gaps remain in `.cursor/templates/`:

- `.cursor/templates/INDEX.yaml` is not represented inside the template index
- `.cursor/templates/README.md` is not represented inside the template index
- `.cursor/templates/INTENT-VERDICT.json` is not represented inside the template index

Strict gap remains in `.cursor/execution/`:

- `.cursor/execution/INDEX.yaml` is not represented inside the execution index

If the requirement is interpreted literally as "every file must be discoverable through the local index", both directories currently fail that requirement.

### 5. `INTENT-VERDICT.json` is the least integrated artifact in the template layer

`INTENT-VERDICT.json` exists in the templates directory, but:

- it is not indexed
- it is not referenced by the template index
- it is not referenced in the canonical template relationships
- its schema duplicates part of `INTENT.md`

This makes it the clearest orphan-like support artifact in the reviewed scope.

It may still be useful as an auxiliary machine-readable compatibility asset, but that purpose is not clearly wired into the indexed system.

### 6. `INTENT.md` has a format inconsistency relative to the other canonical artifacts

Most canonical execution artifacts use YAML frontmatter.

`INTENT.md` does not. It uses inline markdown fields instead.

This is not a doctrine violation, but it is a naming and structure inconsistency inside the artifact layer.

Because `INTENT.md` is pre-program rather than execution-proper, this may be acceptable. Still, it creates a small format discontinuity between:

- pre-execution artifact
- canonical execution artifacts

### 7. Execution doctrine files are coherent but minimally indexed

The execution index correctly exposes:

- `CANONICAL-LAWS.md`
- `MINIMUM-RUNTIME-MODEL.md`
- `AUTONOMOUS-MODULE-EXECUTION.md`

The dependency chain among those three files is coherent.

The only notable discoverability concern is that the index file itself is not self-described.

## Problems

### High

1. Strict discoverability is incomplete because these files are not indexed:
   - `.cursor/templates/INDEX.yaml`
   - `.cursor/templates/README.md`
   - `.cursor/templates/INTENT-VERDICT.json`
   - `.cursor/execution/INDEX.yaml`

2. `INTENT-VERDICT.json` behaves like an orphan support artifact because its role is not integrated into the indexed artifact system.

### Medium

1. Compatibility templates overlap nearby canonical responsibilities:
   - `AGENT-REPORT.md` with proof/review/integration summaries
   - `MODULE-README.md` with module summary/orientation
   - `COUNCIL-SUMMARY.md` with higher-level review/escalation

2. `INTENT.md` uses a different structural style than the rest of the canonical artifact layer.

3. `COUNCIL-SUMMARY.md` is marked active in the template index even though its role is optional governance rather than canonical execution.

### Low

1. `templates/README.md` is useful but currently depends on direct browsing rather than indexed discovery.

2. The template index uses `status: active` for `INTENT.md`, while its tags describe it as pre-execution. This is not wrong, but it slightly blurs the distinction between active canonical execution artifacts and active pre-execution artifacts.

## Recommended Changes

### High Value

1. Add discoverability entries for:
   - `.cursor/templates/INDEX.yaml`
   - `.cursor/templates/README.md`
   - `.cursor/templates/INTENT-VERDICT.json`
   - `.cursor/execution/INDEX.yaml`

2. Clarify the role of `INTENT-VERDICT.json` explicitly:
   - either as a compatibility-only machine-readable support artifact
   - or as deprecated if it is no longer part of the intended artifact layer

### Medium Value

1. Tighten index classifications so the difference is more explicit between:
   - canonical execution artifacts
   - active pre-execution artifacts
   - optional governance artifacts
   - compatibility-only artifacts

2. Consider whether `COUNCIL-SUMMARY.md` should be classified more explicitly as optional governance rather than simply active.

3. Consider whether `INTENT.md` should eventually adopt frontmatter for consistency, but only if that does not complicate its pre-execution role.

### Low Value

1. Reword template descriptions where necessary to reduce conceptual overlap while preserving backward compatibility.

2. Decide whether `templates/README.md` is meant to be navigational documentation or merely a lightweight directory note.

## Files Affected

Reviewed template files:

- `.cursor/templates/INDEX.yaml`
- `.cursor/templates/README.md`
- `.cursor/templates/INTENT.md`
- `.cursor/templates/PROGRAM.md`
- `.cursor/templates/MODULE.md`
- `.cursor/templates/PHASE.md`
- `.cursor/templates/ISSUE.md`
- `.cursor/templates/PROOF.md`
- `.cursor/templates/REVIEW.md`
- `.cursor/templates/INTEGRATION.md`
- `.cursor/templates/COUNCIL-SUMMARY.md`
- `.cursor/templates/AGENT-REPORT.md`
- `.cursor/templates/MODULE-README.md`
- `.cursor/templates/INTENT-VERDICT.json`

Reviewed execution files:

- `.cursor/execution/INDEX.yaml`
- `.cursor/execution/CANONICAL-LAWS.md`
- `.cursor/execution/MINIMUM-RUNTIME-MODEL.md`
- `.cursor/execution/AUTONOMOUS-MODULE-EXECUTION.md`

Report created:

- `.cursor/reports/ARTIFACT-AUDIT.md`

## Summary Verdict

The canonical execution doctrine and canonical artifact templates are internally consistent and align with the intended execution model.

The main stabilization issues are not doctrinal failures. They are:

- incomplete strict discoverability for support files and index files
- one weakly integrated auxiliary artifact: `INTENT-VERDICT.json`
- intentional but still meaningful overlap between compatibility artifacts and the canonical execution layer

No immediate evidence was found that the canonical artifacts violate the execution doctrine or that they displace issue-level execution as the atomic unit.
