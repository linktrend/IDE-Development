---
name: model-routing
description: >-
  Select the v3 IDE Development route. The orchestrator runs on a frontier
  model and sends routine jobs to cheap cursor-001 helpers. Issue execution
  uses Codex Luna, Codex Sol, cursor-002 Grok 4.7, or cursor-002 Opus 5.5.
  Model IDs resolve at dispatch time.
version: 2.5.2
status: active
---

# Model routing

The versioned route policy is
`core/managed-core/content/config/routing-registry.json`.
Cursor overflow dispatch is
`core/managed-core/content/config/cursor-cloud-dispatch.json`.

Model IDs are resolved at dispatch time and are never hard-trusted. Codex IDs
come from the app-server `model/list` (they look like `gpt-6-luna` /
`gpt-6-sol`; older `gpt-5.6-*` IDs are historical). cursor-002 IDs come from
`GET /v1/models`. The registry stores the family or tier and the required
parameters, not a frozen Codex version string.

## Orchestrator

One orchestrator per repo, on the cursor-001 Cursor Project, running a
frontier model. It never codes Issues.

Routine jobs go to cheap cursor-001 subagents, in order: `grok-4.7` medium,
then `composer-2.5`. Resolve the exact slug from the available model list at
hand-off. Use the frontier model for planning, Issue writing, judgement
reviews, and decisions. The full cheap-helper rule is
`.cursor/rules/07-orchestrator-helper-routing.mdc`.

## Issue execution

Exactly four execution models:

| Route | When | Provider | Family / tier and params |
|---|---|---|---|
| `codex-luna` | Everyday Issues, first choice | Codex CLI on the orchestrator VM | tier Luna, reasoning effort `high` |
| `codex-sol` | Hard Issues | Codex CLI | tier Sol, effort `medium` |
| `cursor002-grok` | Everyday overflow | cursor-002 `POST https://api.cursor.com/v1/agents` | `grok-4.7`, `context=500k`, `reasoning_effort=medium`, `fast=false` |
| `cursor002-opus` | Hard overflow | cursor-002, same API | `claude-opus-5-5`, `context=1m`, `effort=medium`, `fast=false` |

Aliases `opus` and `opus-latest` are forbidden. Unknown models or parameters
fail closed.

## Allowance

Codex is used only while every usage window the backend reports is below 75%
used (more than 25% left). The windows are the 5-hour primary window and the
weekly secondary window. A window the backend does not report does not block.
If no window is reported, the Issue goes to cursor-002. Otherwise everyday
overflow is cursor-002 Grok and hard overflow is cursor-002 Opus. Optional
strict mode requires both windows to be reported. The orchestrator checks
this before every hand-off:

`python3 scripts/codex/codex_orchestrator.py gate`

## Sign-in

Before every Codex hand-off the orchestrator runs the liveness check
(`codex cloud list --json --limit 1`, wrapped by the same `gate` command).
If Codex is logged out, stop dispatching to Codex and ask Carlos to approve
a new device-code sign-in.

## Review

Every PR gets one independent review of the exact head by a model from a
different family than the author's. A GPT model reviews Grok or Opus work. A
Claude or Grok model reviews Codex work. Bugbot is optional.

## Repair ladder

Reference only; the doctrine Issue writes the ladder in full. Luna or Grok,
three attempts, then Sol or Opus once. If the Issue started on Sol or Opus,
one attempt on the other of Opus and Sol. Then flag Carlos.

## Credentials and readback

The cursor-002 key is the Cursor runtime secret `CURSOR_002_API_KEY`. Never
print it or commit it.

The Cursor API reports neither the model that ran nor the cost. Do not
require `model` in provider readback. Record the requested model and
parameters, and the model's self-report (`MODEL-SELF-REPORT:`). For Codex,
the actual model and effort come from the session log (`cliModel` /
`cliEffort`).

Repository binding stays explicit: `repos[]` on the REST path, or the SDK
`CloudAgentOptions.repos` list. Readback must still match repository, ref,
commit, and tree. A mismatch is archived and rejected.
