import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
import { dirname, join } from 'node:path'
import { fileURLToPath } from 'node:url'
import { test } from 'node:test'
import { validateBrainProjection } from '../../core/link-integrations/brain.mjs'
import { ConsumerContractError } from '../../core/link-integrations/errors.mjs'
import {
  MCP_OPTION_KEYS,
  MCP_PROTOCOL_VERSION,
  OKF_FORMAT,
  OKF_VERSION,
  negotiateMcp,
  validateOkfMapping,
} from '../../core/link-integrations/mcp.mjs'
import { FROZEN_PROVIDERS } from '../../core/link-integrations/pins.mjs'

const HERE = dirname(fileURLToPath(import.meta.url))
const MCP_SOURCE = readFileSync(join(HERE, '../../core/link-integrations/mcp.mjs'), 'utf8')

/**
 * @param {() => unknown} fn
 * @param {string} code
 */
function throws(fn, code) {
  try {
    fn()
    assert.fail(`expected ${code}`)
  } catch (error) {
    assert.ok(error instanceof ConsumerContractError)
    assert.equal(error.code, code)
    assert.equal(error.details.classification, 'fail_closed')
  }
}

test('AC-I6-X-01: negotiateMcp accepts 2026-07-28 modern only', () => {
  assert.equal(negotiateMcp(MCP_PROTOCOL_VERSION, 'modern'), MCP_PROTOCOL_VERSION)
  assert.equal(negotiateMcp('2026-07-28', 'modern'), '2026-07-28')
  assert.equal(negotiateMcp(MCP_PROTOCOL_VERSION, 'modern', {}), MCP_PROTOCOL_VERSION)
  assert.equal(
    negotiateMcp(MCP_PROTOCOL_VERSION, 'modern', {
      method: 'tools/list',
      session: false,
      sessionRequired: false,
      sessionReliance: false,
      era: 'modern',
      sessionless: true,
    }),
    MCP_PROTOCOL_VERSION,
  )
  throws(() => negotiateMcp('2025-06-18', 'legacy'), 'mcp_negotiation_failed')
  throws(() => negotiateMcp(MCP_PROTOCOL_VERSION, 'legacy'), 'mcp_negotiation_failed')
  throws(() => negotiateMcp(MCP_PROTOCOL_VERSION, 'session'), 'mcp_negotiation_failed')
  throws(
    () => negotiateMcp(MCP_PROTOCOL_VERSION, 'modern', { method: 'initialize' }),
    'mcp_negotiation_failed',
  )
  throws(
    () => negotiateMcp(MCP_PROTOCOL_VERSION, 'modern', { session: true }),
    'mcp_negotiation_failed',
  )
  throws(
    () => negotiateMcp(MCP_PROTOCOL_VERSION, 'modern', { sessionRequired: true }),
    'mcp_negotiation_failed',
  )
  assert.match(MCP_SOURCE, /sessionless/)
  assert.equal(MCP_PROTOCOL_VERSION, '2026-07-28')
  assert.deepEqual([...MCP_OPTION_KEYS], [
    'method',
    'session',
    'sessionRequired',
    'sessionReliance',
    'era',
    'sessionless',
  ])
})

test('AC-I6-X-01 repair: negotiateMcp rejects alternate session/initialize encodings and unknown options', () => {
  const bypasses = [
    { method: 'Initialize' },
    { method: 'INITIALIZE' },
    { method: ' Initialize ' },
    { method: 'mcp/initialize' },
    { method: 'session/Initialize' },
    { session: 1 },
    { session: 'true' },
    { session: 'yes' },
    { session: 'session' },
    { sessionRequired: '1' },
    { sessionRequired: 2 },
    { sessionReliance: {} },
    { sessionReliance: 'on' },
    { era: 'Legacy' },
    { era: 'SESSION' },
    { era: ' Session ' },
    { sessionless: false },
    { sessionless: 'true' },
    { sessionless: 1 },
    { initialize: true },
    { foo: 'bar' },
    { method: 'tools/list', unknownFlag: false },
  ]

  for (const options of bypasses) {
    const code = Object.prototype.hasOwnProperty.call(options, 'initialize') ||
      Object.prototype.hasOwnProperty.call(options, 'foo') ||
      Object.prototype.hasOwnProperty.call(options, 'unknownFlag')
      ? 'unknown_field'
      : 'mcp_negotiation_failed'
    throws(() => negotiateMcp(MCP_PROTOCOL_VERSION, 'modern', options), code)
  }

  // Explicit false session flags and modern affirmations remain allowed.
  assert.equal(
    negotiateMcp(MCP_PROTOCOL_VERSION, 'modern', {
      session: false,
      sessionRequired: false,
      sessionReliance: false,
      era: 'Modern',
      sessionless: true,
      method: 'resources/list',
    }),
    MCP_PROTOCOL_VERSION,
  )
})

test('AC-I6-X-02: OKF 0.2 is optional mapping and cannot grant Brain execution', () => {
  const accepted = validateOkfMapping({
    format: OKF_FORMAT,
    version: OKF_VERSION,
    exchangeKind: 'canonical_projection',
    applicable: true,
    fieldMappings: {
      projectionId: 'id',
      title: 'title',
      summary: 'description',
    },
  })
  assert.deepEqual(accepted, {
    format: 'OKF',
    version: '0.2',
    exchangeKind: 'canonical_projection',
    applicable: true,
  })
  assert.ok(Object.isFrozen(accepted))
  assert.equal('authority' in accepted, false)
  assert.equal('executionAuthority' in accepted, false)

  throws(
    () =>
      validateOkfMapping({
        format: 'OKF',
        version: '0.2',
        exchangeKind: 'task_state',
        applicable: false,
      }),
    'okf_reason_required',
  )
  assert.equal(
    validateOkfMapping({
      format: 'OKF',
      version: '0.2',
      exchangeKind: 'task_state',
      applicable: false,
      nonApplicabilityReason: 'task_state is not an OKF v0.2 eligible exchange',
    }).applicable,
    false,
  )

  throws(
    () =>
      validateOkfMapping({
        format: 'OKF',
        version: '0.2',
        exchangeKind: 'canonical_projection',
        applicable: true,
        authority: 'execute',
      }),
    'okf_authority_bridge_forbidden',
  )
  throws(
    () =>
      validateOkfMapping({
        format: 'OKF',
        version: '0.2',
        exchangeKind: 'canonical_projection',
        applicable: true,
        executionAuthority: 'agent',
      }),
    'okf_authority_bridge_forbidden',
  )

  const brainWithOkf = validateBrainProjection(
    {
      contractVersion: '2.0.0',
      authority: 'advisory',
      executionAuthority: 'none',
      projectionRef: 'projection-ide-dev-s6-okf',
      okf: {
        format: 'OKF',
        version: '0.2',
        exchangeKind: 'canonical_projection',
        applicable: true,
      },
    },
    { providerPin: FROZEN_PROVIDERS.brain },
  )
  assert.deepEqual(brainWithOkf, { projectionRef: 'projection-ide-dev-s6-okf' })

  try {
    validateBrainProjection(
      {
        contractVersion: '2.0.0',
        authority: 'advisory',
        executionAuthority: 'execute',
        projectionRef: 'projection-ide-dev-s6-exec',
        okf: {
          format: 'OKF',
          version: '0.2',
          exchangeKind: 'canonical_projection',
          applicable: true,
        },
      },
      { providerPin: FROZEN_PROVIDERS.brain },
    )
    assert.fail('expected brain_execution_denied')
  } catch (error) {
    assert.ok(error instanceof ConsumerContractError)
    assert.equal(error.code, 'brain_execution_denied')
    assert.equal(error.details.classification, 'denied')
  }
})

test('AC-I6-X-02 repair: OKF fieldMappings reject authority vocabulary case-insensitively in keys and values', () => {
  const base = {
    format: 'OKF',
    version: '0.2',
    exchangeKind: 'canonical_projection',
    applicable: true,
  }

  const forbiddenMappings = [
    { Authority: 'id' },
    { EXECUTIONAUTHORITY: 'id' },
    { Execute: 'id' },
    { execution: 'id' },
    { Tools: 'id' },
    { toolRequest: 'id' },
    { skills_run: 'id' },
    { grant: 'id' },
    { capability: 'id' },
    { permittedOperations: 'id' },
    { title: 'Authority' },
    { title: 'executionAuthority' },
    { title: 'EXECUTE' },
    { title: 'Execution' },
    { title: 'Tools' },
    { title: 'toolCalls' },
    { title: 'skills_run' },
    { title: 'Grant' },
    { title: 'Capability' },
    { title: 'permittedOperations' },
  ]

  for (const fieldMappings of forbiddenMappings) {
    throws(() => validateOkfMapping({ ...base, fieldMappings }), 'okf_authority_bridge_forbidden')
  }

  // Positive allowlist: ordinary projection field names remain accepted.
  assert.deepEqual(
    validateOkfMapping({
      ...base,
      fieldMappings: {
        projectionId: 'id',
        title: 'title',
        summary: 'description',
        handoffRef: 'handoff',
      },
    }),
    {
      format: 'OKF',
      version: '0.2',
      exchangeKind: 'canonical_projection',
      applicable: true,
    },
  )
})
