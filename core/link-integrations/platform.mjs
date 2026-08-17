/**
 * Fail-closed LiNKplatform identity / permissions / capabilities validator.
 *
 * Consumes `FROZEN_PROVIDERS.platform` and `ConsumerContractError`. Accepts
 * only Platform-issued AuthClaims `platform.auth-claims/1.1.0`. This module
 * never mints claims, stores signing keys, calls Platform HTTP, or holds
 * runtime credentials.
 */

import { fail } from './errors.mjs'
import { FROZEN_PROVIDERS } from './pins.mjs'

export const PLATFORM_AUTH_CLAIMS_CONTRACT_VERSION = 'platform.auth-claims/1.1.0'
export const PLATFORM_PIN = FROZEN_PROVIDERS.platform

const ACTOR_KINDS = new Set(['human', 'persona', 'service', 'adapter', 'program_executor'])
const ISO_DATE_TIME = /^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d{1,9})?Z$/
const CLAIM_KEYS = new Set([
  'claimContractVersion',
  'actorId',
  'actorKind',
  'runtimeBindingId',
  'credentialId',
  'orgId',
  'internal',
  'serviceScopes',
  'permittedOperations',
  'issuedAt',
  'expiresAt',
  'issuer',
  'audience',
  'programRestrictions',
  'repositoryRestrictions',
  'correlationId',
])
const CONTEXT_KEYS = new Set([
  'expectedAudience',
  'requiredService',
  'requiredCapability',
  'expectedOrgId',
  'expectedRuntimeBindingId',
  'now',
  'identityServiceStatus',
  'credentialStatus',
  'actorLifecycleState',
  'bindingState',
  'providerPin',
])
const FORBIDDEN_COMPETING_KEYS = new Set([
  'claims',
  'payload',
  'secret',
  'token',
  'actor_id',
  'org_id',
  'credential_id',
  'runtime_binding_id',
  'https://linktrend.dev/claims/auth',
])
const SENSITIVE = /(?:secret|password|token|authorization|private.?key|prompt|transcript|raw(?:_|$)|full.?content|^body$)/i
const IDENTITY_MATERIAL = ['actorId', 'runtimeBindingId']

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
 * @param {unknown} value
 * @param {number} minItems
 * @returns {value is string[]}
 */
function isStringArray(value, minItems) {
  return Array.isArray(value) && value.length >= minItems && value.every((entry) => isNonEmptyString(entry))
}

/**
 * @param {unknown} value
 */
function isIsoDateTime(value) {
  return isNonEmptyString(value) && ISO_DATE_TIME.test(value) && Number.isFinite(Date.parse(value))
}

/**
 * @param {Record<string, unknown>} value
 * @param {number} [depth]
 */
function rejectSensitive(value, depth = 0) {
  if (depth > 5) fail('payload_too_deep', 'platform claim exceeded bounded depth')
  for (const [key, item] of Object.entries(value)) {
    if (SENSITIVE.test(key)) {
      fail('sensitive_field', `platform claim contains a sensitive field: ${key}`, {
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
    if (FORBIDDEN_COMPETING_KEYS.has(key)) {
      fail('competing_envelope', `${label} uses a competing envelope field: ${key}`, {
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
 * @param {unknown} pin
 */
function assertFrozenPin(pin) {
  if (pin === undefined) return
  const value = object(pin, 'incompatible_pin')
  if (value.commit !== PLATFORM_PIN.commit || value.tree !== PLATFORM_PIN.tree) {
    fail('incompatible_pin', 'context provider pin does not match the frozen LiNKplatform pin', {
      classification: 'fail_closed',
      provider: 'platform',
      frozenCommit: PLATFORM_PIN.commit,
      frozenTree: PLATFORM_PIN.tree,
    })
  }
}

/**
 * @param {Record<string, unknown>} context
 */
function assertContext(context) {
  rejectSensitive(context)
  rejectUnknown(context, CONTEXT_KEYS, 'platform context')
  if (!isNonEmptyString(context.expectedAudience)) {
    fail('invalid_context', 'expectedAudience must be a non-empty string', { classification: 'fail_closed' })
  }
  if (!isNonEmptyString(context.requiredService)) {
    fail('invalid_context', 'requiredService must be a non-empty string', { classification: 'fail_closed' })
  }
  if (!isNonEmptyString(context.requiredCapability)) {
    fail('invalid_context', 'requiredCapability must be a non-empty string', { classification: 'fail_closed' })
  }
  if (!isNonEmptyString(context.expectedRuntimeBindingId)) {
    fail('invalid_context', 'expectedRuntimeBindingId must be a non-empty string', {
      classification: 'fail_closed',
    })
  }
  if (!isIsoDateTime(context.now)) {
    fail('invalid_context', 'now must be an ISO-8601 date-time string', { classification: 'fail_closed' })
  }
  if (context.expectedOrgId !== undefined && context.expectedOrgId !== null && !isNonEmptyString(context.expectedOrgId)) {
    fail('invalid_context', 'expectedOrgId must be a non-empty string or null', { classification: 'fail_closed' })
  }
  assertFrozenPin(context.providerPin)
}

/**
 * @param {unknown} claim
 * @returns {boolean}
 */
function identityMaterialAbsent(claim) {
  if (claim === null || claim === undefined) return true
  if (!claim || typeof claim !== 'object' || Array.isArray(claim)) return false
  const record = /** @type {Record<string, unknown>} */ (claim)
  return IDENTITY_MATERIAL.some((field) => !isNonEmptyString(record[field]))
}

/**
 * @param {unknown} claim
 * @param {unknown} context
 * @returns {Readonly<{ actorId: string, runtimeBindingId: string, orgId: string | null }>}
 */
export function validatePlatformIdentity(claim, context) {
  const ctx = object(context, 'invalid_context')
  assertContext(ctx)

  if (ctx.identityServiceStatus === 'unavailable') {
    fail('identity_unavailable', 'platform identity service is unavailable', {
      classification: 'unavailable',
      provider: 'platform',
    })
  }
  if (ctx.identityServiceStatus === 'disabled') {
    fail('identity_disabled', 'platform identity service is disabled', {
      classification: 'fail_closed',
      provider: 'platform',
    })
  }
  if (ctx.identityServiceStatus !== undefined && ctx.identityServiceStatus !== 'available') {
    fail('incompatible_identity_status', 'platform identity service status is incompatible', {
      classification: 'fail_closed',
      provider: 'platform',
    })
  }

  if (identityMaterialAbsent(claim)) {
    fail('identity_unavailable', 'required platform claim material is absent', {
      classification: 'unavailable',
      provider: 'platform',
    })
  }

  const record = object(claim)
  rejectSensitive(record)
  rejectUnknown(record, CLAIM_KEYS, 'platform claim')

  if (record.claimContractVersion !== PLATFORM_AUTH_CLAIMS_CONTRACT_VERSION) {
    fail('wrong_claim_contract_version', 'claimContractVersion must be platform.auth-claims/1.1.0', {
      classification: 'fail_closed',
      field: 'claimContractVersion',
    })
  }
  if (!isNonEmptyString(record.actorKind) || !ACTOR_KINDS.has(record.actorKind)) {
    fail('auth_claims_shape_invalid', 'actorKind is not a Platform actor kind', {
      classification: 'fail_closed',
      field: 'actorKind',
    })
  }
  if (!isNonEmptyString(record.credentialId)) {
    fail('auth_claims_shape_invalid', 'credentialId must be a non-empty metadata id', {
      classification: 'fail_closed',
      field: 'credentialId',
    })
  }
  if (!(record.orgId === null || isNonEmptyString(record.orgId))) {
    fail('auth_claims_shape_invalid', 'orgId must be a non-empty string or null', {
      classification: 'fail_closed',
      field: 'orgId',
    })
  }
  if (typeof record.internal !== 'boolean') {
    fail('auth_claims_shape_invalid', 'internal must be a boolean', {
      classification: 'fail_closed',
      field: 'internal',
    })
  }
  if (!isStringArray(record.serviceScopes, 1)) {
    fail('auth_claims_shape_invalid', 'serviceScopes must be a non-empty string array', {
      classification: 'fail_closed',
      field: 'serviceScopes',
    })
  }
  if (!isStringArray(record.permittedOperations, 0)) {
    fail('auth_claims_shape_invalid', 'permittedOperations must be a string array', {
      classification: 'fail_closed',
      field: 'permittedOperations',
    })
  }
  if (!isIsoDateTime(record.issuedAt)) {
    fail('auth_claims_shape_invalid', 'issuedAt must be an ISO-8601 date-time string', {
      classification: 'fail_closed',
      field: 'issuedAt',
    })
  }
  if (!isIsoDateTime(record.expiresAt)) {
    fail('auth_claims_shape_invalid', 'expiresAt must be an ISO-8601 date-time string', {
      classification: 'fail_closed',
      field: 'expiresAt',
    })
  }
  if (!isNonEmptyString(record.issuer)) {
    fail('auth_claims_shape_invalid', 'issuer must be a non-empty string', {
      classification: 'fail_closed',
      field: 'issuer',
    })
  }
  if (!isStringArray(record.audience, 1)) {
    fail('auth_claims_shape_invalid', 'audience must be a non-empty string array', {
      classification: 'fail_closed',
      field: 'audience',
    })
  }
  if (record.programRestrictions !== undefined && record.programRestrictions !== null && !isStringArray(record.programRestrictions, 0)) {
    fail('auth_claims_shape_invalid', 'programRestrictions must be a string array, null, or omitted', {
      classification: 'fail_closed',
      field: 'programRestrictions',
    })
  }
  if (record.repositoryRestrictions !== undefined && record.repositoryRestrictions !== null && !isStringArray(record.repositoryRestrictions, 0)) {
    fail('auth_claims_shape_invalid', 'repositoryRestrictions must be a string array, null, or omitted', {
      classification: 'fail_closed',
      field: 'repositoryRestrictions',
    })
  }
  if (!isNonEmptyString(record.correlationId)) {
    fail('auth_claims_shape_invalid', 'correlationId must be a non-empty string', {
      classification: 'fail_closed',
      field: 'correlationId',
    })
  }

  const nowMs = Date.parse(/** @type {string} */ (ctx.now))
  if (nowMs < Date.parse(/** @type {string} */ (record.issuedAt))) {
    fail('not_yet_valid', 'platform claim is not yet valid', { classification: 'fail_closed' })
  }
  if (nowMs >= Date.parse(/** @type {string} */ (record.expiresAt)) || ctx.credentialStatus === 'expired') {
    fail('expired', 'platform claim is expired', { classification: 'fail_closed' })
  }
  if (ctx.credentialStatus === 'revoked' || ctx.credentialStatus === 'rotated') {
    fail('revoked', 'platform credential is revoked or rotated', { classification: 'fail_closed' })
  }
  if (ctx.bindingState === 'disabled') {
    fail('binding_disabled', 'platform runtime binding is disabled', { classification: 'fail_closed' })
  }
  if (ctx.actorLifecycleState !== undefined && ctx.actorLifecycleState !== 'active') {
    fail('inactive_actor', 'platform actor is not active', { classification: 'fail_closed' })
  }

  if (record.orgId === null && record.actorKind !== 'service') {
    fail('illegal_actor_combination', 'orgId may be null only when actorKind is service', {
      classification: 'denied',
      actorKind: record.actorKind,
      orgId: record.orgId,
    })
  }
  if (record.internal === true && record.actorKind === 'human') {
    fail('illegal_actor_combination', 'internal Platform principals cannot use actorKind human', {
      classification: 'denied',
      actorKind: record.actorKind,
      internal: record.internal,
    })
  }

  if (ctx.expectedOrgId !== undefined && record.orgId !== ctx.expectedOrgId) {
    fail('wrong_org', 'platform claim org does not match the requested context', {
      classification: 'denied',
      field: 'orgId',
    })
  }
  if (!/** @type {string[]} */ (record.audience).includes(/** @type {string} */ (ctx.expectedAudience))) {
    fail('wrong_audience', 'platform claim audience does not include the requested context', {
      classification: 'denied',
      field: 'audience',
    })
  }
  if (!/** @type {string[]} */ (record.serviceScopes).includes(/** @type {string} */ (ctx.requiredService))) {
    fail('wrong_service', 'platform claim service scope does not include the requested service', {
      classification: 'denied',
      field: 'serviceScopes',
    })
  }
  if (!/** @type {string[]} */ (record.permittedOperations).includes(/** @type {string} */ (ctx.requiredCapability))) {
    fail('capability_not_permitted', 'platform claim is missing the required capability', {
      classification: 'denied',
      field: 'permittedOperations',
    })
  }
  if (record.runtimeBindingId !== ctx.expectedRuntimeBindingId) {
    fail('wrong_binding', 'platform claim runtime binding does not match the requested context', {
      classification: 'denied',
      field: 'runtimeBindingId',
    })
  }
  if (ctx.bindingState !== undefined && ctx.bindingState !== 'active') {
    fail('inactive_binding', 'platform runtime binding is not active', {
      classification: 'denied',
      field: 'bindingState',
    })
  }

  return Object.freeze({
    actorId: /** @type {string} */ (record.actorId),
    runtimeBindingId: /** @type {string} */ (record.runtimeBindingId),
    orgId: /** @type {string | null} */ (record.orgId),
  })
}
