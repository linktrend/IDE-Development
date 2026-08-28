---
name: route-default
description: >-
  Default post-Gate-0 ordinary-development route: Grok 4.6 Medium through the
  direct Cursor SDK/API with explicit repository binding and Fast off.
model: grok-4.6[effort=medium,fast=false]
---

# Route: ordinary-development

Use this route for ordinary development after Gate 0. The dispatch request
must include the exact repository URL and starting ref in `repos[]` (or the
SDK-equivalent repository list), then read back repository, ref, commit, and
tree before crediting the worker.

Unsupported provider/model/effort combinations and Fast mode fail before
Cursor dispatch. A saved environment name is never a repository selector.

If the Principal instructs a Luna switch, use `route-escalation` through Codex
CLI. Do not start it concurrently unless the Principal explicitly authorizes
disjoint independent packets.
