/**
 * Shared modern MCP negotiation and optional OKF v0.2 mapping for Item 6.
 *
 * Providers that advertise MCP `2026-07-28` sessionless semantics must negotiate
 * only the modern era. Legacy or session `initialize` negotiation fails closed
 * with no silent downgrade. OKF `0.2` is an optional field mapping only — never
 * a second source of truth and never an authority or Brain execution bridge.
 *
 * This module has no transport, credentials, Git write, Ledger, Gate mutation,
 * or MCP server runtime.
 */

import { fail } from './errors.mjs'

/** Modern sessionless MCP protocol version advertised by Brain / Skills. */
export const MCP_PROTOCOL_VERSION = '2026-07-28'

/** OKF mapping format and version accepted by this consumer. */
export const OKF_FORMAT = 'OKF'
export const OKF_VERSION = '0.2'

const OKF_EXCHANGE_KINDS = Object.freeze([
  'canonical_knowledge',
  'canonical_projection',
  'task_state',
  'auth',
  'private_memory',
  'raw_capture',
  'binary',
])

const OKF_ELIGIBLE = new Set(['canonical_knowledge', 'canonical_projection'])

const OKF_KEYS = new Set([
  'format',
  'version',
  'exchangeKind',
  'applicable',
  'fieldMappings',
  'nonApplicabilityReason',
])

const AUTHORITY_BRIDGE_KEYS = new Set([
  'authority',
  'executionAuthority',
  'execute',
  'execution',
  'tools',
  'tool',
  'toolRequest',
  'toolCalls',
  'skills_run',
  'grant',
  'capability',
  'permittedOperations',
])

const SENSITIVE = /(?:secret|password|token|authorization|private.?key|prompt|transcript|conversation|raw(?:_|$)|full.?content|^body$)/i
const FIELD_NAME = /^[A-Za-z][A-Za-z0-9_.-]{0,63}$/
const REASON_MAX = 400
const FIELD_MAP_MAX = 32

/**
 * @param {unknown} value
 * @param {string} [code]
 * @returns {Record<string, unknown>}
 */
function object(value, code = 'invalid_object') {
  if (value === null || typeof value !== 'object' || Array.isArray(value)) {
    fail(code, 'expected a plain object', { classification: 'fail_closed' })
  }
  return /** @type {Record<string, unknown>} */ (value)
}

/**
 * @param {Record<string, unknown>} value
 * @param {Set<string>} allowed
 * @param {string} label
 */
function rejectUnknown(value, allowed, label) {
  for (const key of Object.keys(value)) {
    if (!allowed.has(key)) {
      fail('unknown_field', `${label} contains unknown field ${key}`, {
        classification: 'fail_closed',
        field: key,
        surface: label,
      })
    }
  }
}

/**
 * @param {Record<string, unknown>} value
 * @param {string} label
 */
function rejectAuthorityBridge(value, label) {
  for (const key of Object.keys(value)) {
    if (AUTHORITY_BRIDGE_KEYS.has(key) || SENSITIVE.test(key)) {
      fail('okf_authority_bridge_forbidden', `${label} cannot carry authority or execution fields`, {
        classification: 'fail_closed',
        field: key,
        surface: label,
      })
    }
  }
}

/**
 * Negotiate the shared modern MCP boundary.
 *
 * Only `version === '2026-07-28'` with `era === 'modern'` succeeds. Legacy,
 * session, mismatched versions, and session `initialize` attempts fail closed.
 *
 * @param {unknown} version
 * @param {unknown} era
 * @param {unknown} [options]
 * @returns {typeof MCP_PROTOCOL_VERSION}
 */
export function negotiateMcp(version, era, options = undefined) {
  if (version !== MCP_PROTOCOL_VERSION || era !== 'modern') {
    fail('mcp_negotiation_failed', 'MCP negotiation requires 2026-07-28 modern sessionless', {
      classification: 'fail_closed',
      version,
      era,
      requiredVersion: MCP_PROTOCOL_VERSION,
      requiredEra: 'modern',
    })
  }

  if (options !== undefined && options !== null) {
    const opts = object(options, 'mcp_options_invalid')
    if (
      opts.method === 'initialize' ||
      opts.session === true ||
      opts.sessionRequired === true ||
      opts.sessionReliance === true ||
      opts.era === 'legacy' ||
      opts.era === 'session'
    ) {
      fail('mcp_negotiation_failed', 'legacy or session initialize negotiation is refused', {
        classification: 'fail_closed',
        version,
        era,
        options: {
          method: opts.method,
          session: opts.session,
          sessionRequired: opts.sessionRequired,
          sessionReliance: opts.sessionReliance,
          era: opts.era,
        },
      })
    }
  }

  return MCP_PROTOCOL_VERSION
}

/**
 * Validate optional OKF v0.2 mapping. Returns a frozen mapping summary.
 *
 * Applicable only for canonical knowledge/projection exchange kinds. Never
 * grants Brain execution authority or overrides provider authority fields.
 *
 * @param {unknown} value
 * @returns {Readonly<{ format: 'OKF', version: '0.2', exchangeKind: string, applicable: boolean }>}
 */
export function validateOkfMapping(value) {
  if (value === undefined) {
    fail('okf_mapping_required', 'OKF mapping value is required when validating OKF', {
      classification: 'fail_closed',
    })
  }

  const mapping = object(value, 'okf_mapping_invalid')
  rejectAuthorityBridge(mapping, 'okf mapping')
  rejectUnknown(mapping, OKF_KEYS, 'okf mapping')

  if (mapping.format !== OKF_FORMAT || mapping.version !== OKF_VERSION) {
    fail('okf_version_invalid', 'OKF mapping must be format OKF version 0.2', {
      classification: 'fail_closed',
      format: mapping.format,
      version: mapping.version,
    })
  }

  if (typeof mapping.exchangeKind !== 'string' || !OKF_EXCHANGE_KINDS.includes(mapping.exchangeKind)) {
    fail('okf_exchange_kind_invalid', 'OKF exchangeKind is not a known v0.2 kind', {
      classification: 'fail_closed',
      field: 'exchangeKind',
      exchangeKind: mapping.exchangeKind,
    })
  }

  if (typeof mapping.applicable !== 'boolean') {
    fail('okf_applicability_invalid', 'OKF applicable must be a boolean', {
      classification: 'fail_closed',
      field: 'applicable',
    })
  }

  const eligible = OKF_ELIGIBLE.has(mapping.exchangeKind)
  if (mapping.applicable !== eligible) {
    fail('okf_applicability_invalid', 'OKF v0.2 applies only to canonical knowledge and projections', {
      classification: 'fail_closed',
      field: 'applicable',
      exchangeKind: mapping.exchangeKind,
      applicable: mapping.applicable,
    })
  }

  if (!eligible) {
    if (typeof mapping.nonApplicabilityReason !== 'string' || mapping.nonApplicabilityReason.trim() === '') {
      fail('okf_reason_required', 'non-applicable OKF exchange kinds require an explicit reason', {
        classification: 'fail_closed',
        field: 'nonApplicabilityReason',
      })
    }
    if (mapping.nonApplicabilityReason.length > REASON_MAX) {
      fail('okf_reason_invalid', 'nonApplicabilityReason exceeds the bounded size', {
        classification: 'fail_closed',
        field: 'nonApplicabilityReason',
      })
    }
  } else if (mapping.nonApplicabilityReason !== undefined) {
    fail('okf_reason_forbidden', 'eligible OKF exchange kinds must not carry a non-applicability reason', {
      classification: 'fail_closed',
      field: 'nonApplicabilityReason',
    })
  }

  if (mapping.fieldMappings !== undefined) {
    const fields = object(mapping.fieldMappings, 'okf_field_mappings_invalid')
    rejectAuthorityBridge(fields, 'okf fieldMappings')
    const keys = Object.keys(fields)
    if (keys.length > FIELD_MAP_MAX) {
      fail('okf_field_mappings_invalid', 'OKF fieldMappings exceed the bounded size', {
        classification: 'fail_closed',
        field: 'fieldMappings',
      })
    }
    for (const key of keys) {
      if (!FIELD_NAME.test(key) || SENSITIVE.test(key)) {
        fail('okf_field_mappings_invalid', 'OKF fieldMappings key is invalid or sensitive', {
          classification: 'fail_closed',
          field: key,
        })
      }
      const target = fields[key]
      if (typeof target !== 'string' || !FIELD_NAME.test(target) || SENSITIVE.test(target)) {
        fail('okf_field_mappings_invalid', 'OKF fieldMappings value is invalid or sensitive', {
          classification: 'fail_closed',
          field: key,
        })
      }
    }
  }

  return Object.freeze({
    format: OKF_FORMAT,
    version: OKF_VERSION,
    exchangeKind: /** @type {string} */ (mapping.exchangeKind),
    applicable: /** @type {boolean} */ (mapping.applicable),
  })
}
