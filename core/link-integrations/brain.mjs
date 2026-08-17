/**
 * Fail-closed LiNKbrain knowledge / coordination validator.
 *
 * Consumes `FROZEN_PROVIDERS.brain` and `ConsumerContractError`. Accepts only
 * advisory, metadata-first projections (`contractVersion` `2.0.0`) and returns
 * opaque `projectionRef` plus optional `handoffRef`. Brain remains advisory
 * (`authority=advisory`, `executionAuthority=none`). This module never calls
 * Brain, executes tools, copies raw conversation, or holds credentials.
 */

import { fail } from './errors.mjs'
import { FROZEN_PROVIDERS } from './pins.mjs'

export const BRAIN_CONTRACT_VERSION = '2.0.0'
export const BRAIN_PIN = FROZEN_PROVIDERS.brain

const OPAQUE_REF = /^[A-Za-z0-9][A-Za-z0-9._~:-]{0,159}$/
const GIT_SHA = /^[a-f0-9]{40}$/
const SUMMARY_MAX = 2000
const PROJECTION_KEYS = new Set([
  'contractVersion',
  'authority',
  'executionAuthority',
  'projectionRef',
  'summary',
  'handoffRef',
])
const CONTEXT_KEYS = new Set(['providerPin', 'providerStatus'])
const EXECUTION_REQUEST_KEYS = new Set([
  'tools',
  'tool',
  'toolRequest',
  'toolCalls',
  'tool_request',
  'execute',
  'execution',
  'skills_run',
])
const SENSITIVE = /(?:secret|password|token|authorization|private.?key|prompt|transcript|conversation|raw(?:_|$)|full.?content|^body$)/i

/**
 * @param {unknown} value
 * @param {string} [code]
 * @returns {Record<string, unknown>}
 */
function object(value, code = 'invalid_object') {
  if (!value || typeof value !== 'object' || Array.isArray(value)) {
    fail(code, 'value must be a non-array object', { classification: 'fail_closed' })
  }
  return /** @type {Record<string, unknown>} */ (value)
}

/**
 * @param {unknown} value
 * @returns {value is string}
 */
function isNonEmptyString(value) {
  return typeof value === 'string' && value.length > 0
}

/**
 * @param {Record<string, unknown>} value
 * @param {number} [depth]
 */
function rejectSensitive(value, depth = 0) {
  if (depth > 5) {
    fail('payload_too_deep', 'brain projection exceeded bounded depth', { classification: 'fail_closed' })
  }
  for (const [key, item] of Object.entries(value)) {
    if (SENSITIVE.test(key)) {
      fail('sensitive_field', `brain projection contains a sensitive field: ${key}`, {
        classification: 'fail_closed',
        field: key,
      })
    }
    if (item && typeof item === 'object' && !Array.isArray(item)) {
      rejectSensitive(/** @type {Record<string, unknown>} */ (item), depth + 1)
    }
  }
}

/**
 * @param {Record<string, unknown>} value
 * @param {Set<string>} allowed
 * @param {string} label
 */
function rejectUnknown(value, allowed, label) {
  for (const key of Object.keys(value)) {
    if (EXECUTION_REQUEST_KEYS.has(key)) {
      fail('brain_execution_request', `${label} requests Brain execution or tools: ${key}`, {
        classification: 'fail_closed',
        field: key,
      })
    }
    if (!allowed.has(key)) {
      fail('unknown_field', `${label} has an unknown field: ${key}`, {
        classification: 'fail_closed',
        field: key,
      })
    }
  }
}

/**
 * @param {unknown} value
 * @param {string} field
 * @returns {string}
 */
function opaqueRef(value, field) {
  if (typeof value !== 'string' || !OPAQUE_REF.test(value) || value.length > 160) {
    fail('brain_identity_invalid', `brain ${field} is malformed`, {
      classification: 'fail_closed',
      field,
    })
  }
  return value
}

/**
 * @param {unknown} pin
 */
function assertFrozenPin(pin) {
  if (pin === undefined) return
  const value = object(pin, 'incompatible_pin')
  rejectSensitive(value)
  for (const key of Object.keys(value)) {
    if (key !== 'commit' && key !== 'tree') {
      fail('unknown_field', `brain provider pin has an unknown field: ${key}`, {
        classification: 'fail_closed',
        field: key,
      })
    }
  }
  if (!isNonEmptyString(value.commit) || !isNonEmptyString(value.tree)) {
    fail('incompatible_pin', 'brain provider pin is missing commit or tree', {
      classification: 'fail_closed',
      provider: 'brain',
    })
  }
  if (!GIT_SHA.test(value.commit) || !GIT_SHA.test(value.tree)) {
    fail('brain_identity_invalid', 'brain provider pin identity is malformed', {
      classification: 'fail_closed',
      provider: 'brain',
    })
  }
  if (value.commit !== BRAIN_PIN.commit || value.tree !== BRAIN_PIN.tree) {
    fail('incompatible_pin', 'context provider pin does not match the frozen LiNKbrain pin', {
      classification: 'fail_closed',
      provider: 'brain',
      frozenCommit: BRAIN_PIN.commit,
      frozenTree: BRAIN_PIN.tree,
    })
  }
}

/**
 * @param {Record<string, unknown>} context
 */
function assertContext(context) {
  rejectSensitive(context)
  rejectUnknown(context, CONTEXT_KEYS, 'brain context')
  assertFrozenPin(context.providerPin)

  if (context.providerStatus === undefined) return
  if (context.providerStatus === 'unavailable') {
    fail('brain_unavailable', 'brain provider reports unavailability', {
      classification: 'unavailable',
      provider: 'brain',
    })
  }
  if (context.providerStatus === 'available') return
  fail('incompatible_provider_state', 'brain provider state is incompatible', {
    classification: 'fail_closed',
    provider: 'brain',
    providerStatus: context.providerStatus,
  })
}

/**
 * @param {unknown} value
 * @param {unknown} [context]
 * @returns {Readonly<{ projectionRef: string, handoffRef?: string }>}
 */
export function validateBrainProjection(value, context = {}) {
  const ctx = object(context, 'invalid_context')
  assertContext(ctx)

  if (value === null || value === undefined) {
    fail('brain_projection_unavailable', 'required brain projection material is absent', {
      classification: 'unavailable',
      provider: 'brain',
    })
  }

  const record = object(value)
  rejectSensitive(record)
  rejectUnknown(record, PROJECTION_KEYS, 'brain projection')

  if (record.contractVersion !== BRAIN_CONTRACT_VERSION) {
    fail('wrong_contract_version', 'contractVersion must be 2.0.0', {
      classification: 'fail_closed',
      field: 'contractVersion',
    })
  }

  const projectionRef = record.projectionRef
  if (projectionRef === undefined || projectionRef === null || projectionRef === '') {
    fail('brain_projection_unavailable', 'required brain projectionRef is missing', {
      classification: 'unavailable',
      provider: 'brain',
      field: 'projectionRef',
    })
  }
  const acceptedRef = opaqueRef(projectionRef, 'projectionRef')

  if (!isNonEmptyString(record.authority)) {
    fail('brain_identity_invalid', 'authority must be a non-empty string', {
      classification: 'fail_closed',
      field: 'authority',
    })
  }
  if (!isNonEmptyString(record.executionAuthority)) {
    fail('brain_identity_invalid', 'executionAuthority must be a non-empty string', {
      classification: 'fail_closed',
      field: 'executionAuthority',
    })
  }
  if (record.authority !== 'advisory') {
    fail('brain_authority_denied', 'brain authority must remain advisory', {
      classification: 'denied',
      field: 'authority',
      authority: record.authority,
    })
  }
  if (record.executionAuthority !== 'none') {
    fail('brain_execution_denied', 'brain executionAuthority must remain none', {
      classification: 'denied',
      field: 'executionAuthority',
      executionAuthority: record.executionAuthority,
    })
  }

  if (record.summary !== undefined) {
    if (!isNonEmptyString(record.summary)) {
      fail('brain_summary_invalid', 'brain summary must be a non-empty string', {
        classification: 'fail_closed',
        field: 'summary',
      })
    }
    if (record.summary.length > SUMMARY_MAX) {
      fail('brain_summary_invalid', 'brain summary exceeds the bounded size', {
        classification: 'fail_closed',
        field: 'summary',
      })
    }
  }

  /** @type {{ projectionRef: string, handoffRef?: string }} */
  const accepted = { projectionRef: acceptedRef }
  if (record.handoffRef !== undefined) {
    accepted.handoffRef = opaqueRef(record.handoffRef, 'handoffRef')
  }
  return Object.freeze(accepted)
}
