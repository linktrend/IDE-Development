import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
import { dirname, join } from 'node:path'
import { fileURLToPath } from 'node:url'
import { test } from 'node:test'
import { validateBrainProjection } from '../../core/link-integrations/brain.mjs'
import { ConsumerContractError } from '../../core/link-integrations/errors.mjs'
import {
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
