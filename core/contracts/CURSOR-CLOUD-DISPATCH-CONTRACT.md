# cursor-002 dispatch contract

**Control:** `cursor-cloud-dispatch-v3`

This contract is the cursor-002 overflow boundary. It does not run the live
canary. Codex Issue execution stays on the Codex CLI.

## Routes

Exactly two Cursor routes. Anything else fails closed before the API key is
read.

| Route | Family | Pinned params |
|---|---|---|
| `cursor002-grok` | `grok-4.7` | `context=500k`, `reasoning_effort=medium`, `fast=false` |
| `cursor002-opus` | `claude-opus-5-5` | `context=1m`, `effort=medium`, `fast=false` |

Aliases `opus` and `opus-latest` are refused. The config stores the family and
the required params. The live model id is resolved at dispatch time with
`GET /v1/models` and is not a frozen version string trusted from the file.

The API key is the Cursor runtime secret `CURSOR_002_API_KEY`. It is never
printed or committed. CLI login is not API authority.

## Repository binding

Every direct REST request carries:

```json
{
  "repos": [{"url": "https://github.com/owner/name", "startingRef": "issue/123-slug"}]
}
```

The SDK path carries the equivalent `CloudAgentOptions.repos` list. A named
saved environment is not a repository selector. The request URL must match the
logical repository, and the durable PREPARED intent stores the exact
40-character starting commit and tree.

## Readback

The Cursor API reports neither the model that ran nor the cost. Required
readback is repository, ref, commit, tree, and provider. `model` is not
required. Record the requested model and params, plus the worker
`MODEL-SELF-REPORT:` line. For Codex, the actual model and effort come from
the session log (`cliModel` / `cliEffort`).

A missing or mismatched identity is archived and marked `REJECTED`. It is not
counted as a worker.

## Durable behaviour

The intent is read back before creation. The idempotency key and the
client-supplied agent id bind the repository and the requested model. An
unknown API outcome is retried at most once with the same key. The SDK and
REST adapters share the same preflight, readback, archive-on-mismatch, and
commit path.

The first prompt is attestation-only. It forbids mutation and asks for the
repository, ref, commit, and tree, then a `MODEL-SELF-REPORT:` line. Tests use
fake HTTP. No live Cursor agent is created by source validation.

The program list in `core/managed-core/content/config/routing-registry.json`
stays empty until a program names every permitted repository.
