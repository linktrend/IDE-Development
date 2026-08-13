# Actions cost controls

GitHub-hosted ARM64 is the approved compute profile for managed delivery.
Usage alerts are observability only: they do not create a spending cap, stop
workflows, or authorize a billing change.

## Required reporting

The operator records a monthly usage report containing the reporting period,
repositories in scope, hosted minutes, estimated cost if available from the
GitHub usage view, alert delivery result, and unresolved anomalies. Report
secret names only; never copy tokens or billing credentials into evidence.

Enable the available GitHub usage alerts through the authenticated operator
procedure in W3. The alert threshold is a notification threshold, not a stop
limit. GitHub Actions may continue after an alert and after a configured
budget estimate; the operator must review usage and decide what to do.

## Boundaries

Checks use the minimum workflow permissions required by the frozen interface.
Workflow execution, repository protection, and promotion remain separate
controls. This document does not authorize live settings or billing changes.
