/**
 * Fail-closed LiNKskills release and telemetry validator.
 *
 * Consumes `FROZEN_PROVIDERS.skills` and `ConsumerContractError`. Accepts only
 * published + qualified + available immutable releases whose provider
 * commit/tree match the S0 pin, with `sha256:` digests and discovery /
 * validation / execution addressing. Telemetry is a bounded completed-use
 * report. This module never executes a skill, calls Skills HTTP, loads a
 * local catalogue or full pack, or adds credentials / network adapters.
 */

import { fail } from './errors.mjs'
import { FROZEN_PROVIDERS } from './pins.mjs'

export const SKILLS_CONTRACT_VERSION = 'skills.api.v0.2'
export const SKILLS_PIN = FROZEN_PROVIDERS.skills

const GIT_SHA = /^[a-f0-9]{40}$/
const SHA256 = /^sha256:[a-f0-9]{64}$/
const SKILL_ID = /^[a-z0-9][a-z0-9-]{0,94}$/
const SKILL_VERSION = /^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)(?:-[0-9A-Za-z.-]+)?$/
const OPAQUE = /^opaque:[A-Za-z0-9][A-Za-z0-9._:/-]{1,94}$/
const SENSITIVE = /(?:secret|password|token|authorization|private.?key|credential|prompt|transcript|conversation|raw(?:_|$)|full.?content|^body$|narrative|notes|customer|consumer_data|^case$|^lead$|trading_order|portfolio|brokerage)/i

const ADDRESSING = Object.freeze(['discovery', 'validation', 'execution'])
const LIFECYCLES = new Set(['published', 'draft', 'deprecated', 'retired', 'eval_pending', 'unpublished'])
const QUALIFICATIONS = new Set(['qualified', 'unqualified', 'expired', 'withdrawn', 'not_applicable'])
const UNAVAILABLE = new Set([
  'unavailable',
  'offline',
  'degraded',
  'revoked',
  'quarantined',
  'withdrawn',
  'disabled',
  'stale',
  'unauthorized',
  'forbidden',
])
const INCOMPATIBLE_AVAILABILITY = new Set(['incompatible', 'contract_incompatible'])
const ISSUE_TYPES = new Set([
  'incorrect',
  'incomplete',
  'ambiguous',
  'unsafe',
  'incompatible',
  'unavailable',
  'latency',
  'other',
])
const ISSUE_SEVERITIES = new Set(['low', 'medium', 'high', 'critical'])

const DISCOVERY_OPERATIONS = Object.freeze([
  'skills_capabilities_get',
  'skills_catalog_list',
  'skills_catalog_search',
  'skills_release_list',
  'skills_release_describe',
])
const VALIDATION_OPERATIONS = Object.freeze([
  'skills_release_verify',
  'skills_qualification_get',
])
const EXECUTION_OPERATIONS = Object.freeze([
  'skills_release_entrypoint_get',
  'skills_release_sections_list',
  'skills_release_section_get',
  'skills_release_resources_list',
  'skills_release_resource_get',
  'skills_release_content_get',
])
const ADDRESSING_OPERATIONS = Object.freeze({
  discovery: new Set(DISCOVERY_OPERATIONS),
  validation: new Set(VALIDATION_OPERATIONS),
  execution: new Set(EXECUTION_OPERATIONS),
})
const LEGACY_OPERATIONS = new Set([
  'skills_run_start',
  'skills_run_update',
  'skills_run_complete',
  'skills_run_fail',
  'skills_tool_resolve',
  'skills_tool_invoke',
  'skills_list',
  'skills_search',
  'skills_describe',
  'skills_fragment_get',
  'skills_release_get',
  'skills_input_validate',
  'skills_output_validate',
  'skills_trace_candidate_submit',
])
const TELEMETRY_OPERATIONS = new Set([
  'skills_use_report_submit',
  'skills_use_report_status_get',
  'skills_feedback_submit',
  'skills_feedback_status_get',
])

const RELEASE_KEYS = new Set([
  'contractVersion',
  'providerCommit',
  'providerTree',
  'skillId',
  'version',
  'releaseHash',
  'bundleHash',
  'manifestHash',
  'lifecycle',
  'qualification',
  'availability',
  'fragmentLevel',
  'addressing',
  'operation',
  'compatibility',
])
const TELEMETRY_KEYS = new Set([
  'reportKind',
  'score',
  'issue',
  'skillReleaseRef',
  'actorRef',
  'idempotencyKey',
])
const ISSUE_KEYS = new Set(['type', 'severity', 'issueRef'])
const RELEASE_CROSS_FIELDS = new Set([
  'reportKind',
  'score',
  'issue',
  'skillReleaseRef',
  'actorRef',
  'idempotencyKey',
  'nonUseOutcome',
  'outcome',
  'opaqueRefs',
])
const TELEMETRY_CROSS_FIELDS = new Set([
  'contractVersion',
  'providerCommit',
  'providerTree',
  'skillId',
  'version',
  'releaseHash',
  'bundleHash',
  'manifestHash',
  'lifecycle',
  'qualification',
  'availability',
  'fragmentLevel',
  'addressing',
  'operation',
  'compatibility',
])
const RELEASE_COMPETING = new Set([
  'skill_id',
  'skill_version',
  'release_hash',
  'bundle_hash',
  'manifest_hash',
  'fragment_level',
  'provider_commit',
  'provider_tree',
  'contract_version',
  'report_kind',
])
const TELEMETRY_COMPETING = new Set([
  'report_kind',
  'skill_id',
  'skill_release_ref',
  'actor_ref',
  'idempotency_key',
  'server_idempotency_key',
  'non_use_outcome',
  'opaque_refs',
])

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
    fail('payload_too_deep', 'skills payload exceeded bounded depth', { classification: 'fail_closed' })
  }
  for (const [key, item] of Object.entries(value)) {
    if (SENSITIVE.test(key)) {
      fail('sensitive_field', `skills payload contains a sensitive field: ${key}`, {
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
 * @param {ReadonlySet<string>} competing
 * @param {ReadonlySet<string>} cross
 * @param {ReadonlySet<string>} allowed
 * @param {string} label
 */
function rejectShape(value, competing, cross, allowed, label) {
  for (const key of Object.keys(value)) {
    if (competing.has(key)) {
      fail('competing_envelope', `${label} uses a competing envelope field: ${key}`, {
        classification: 'fail_closed',
        field: key,
      })
    }
    if (cross.has(key)) {
      fail('cross_operation_field', `${label} mixes a cross-operation field: ${key}`, {
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
 * @returns {boolean}
 */
function isLegacyOperation(value) {
  if (typeof value !== 'string' || value === '') return false
  return LEGACY_OPERATIONS.has(value) || value.startsWith('skills_run_') || value.startsWith('skills_tool_')
}

/**
 * @param {unknown} value
 * @param {string} field
 */
function rejectLatestAlias(value, field) {
  if (typeof value === 'string' && (value === 'latest' || value.endsWith('/latest') || value.endsWith('@latest'))) {
    fail('skills_latest_alias', `skills ${field} must be an immutable identity, not latest`, {
      classification: 'fail_closed',
      field,
    })
  }
}

/**
 * @param {unknown} value
 * @returns {boolean}
 */
function pinMaterialAbsent(value) {
  if (value === null || value === undefined) return true
  if (!value || typeof value !== 'object' || Array.isArray(value)) return false
  const record = /** @type {Record<string, unknown>} */ (value)
  return !isNonEmptyString(record.providerCommit) || !isNonEmptyString(record.providerTree)
}

/**
 * @param {unknown} value
 * @returns {Readonly<{
 *   skillId: string,
 *   version: string,
 *   releaseHash: string,
 *   bundleHash: string,
 *   manifestHash: string,
 *   fragmentLevel: number,
 *   addressing: string,
 *   providerCommit: string,
 *   providerTree: string,
 * }>}
 */
export function validateSkillsRelease(value) {
  if (pinMaterialAbsent(value)) {
    fail('skills_release_unavailable', 'required skills provider pin material is absent', {
      classification: 'unavailable',
      provider: 'skills',
    })
  }

  const release = object(value)
  rejectSensitive(release)
  rejectShape(release, RELEASE_COMPETING, RELEASE_CROSS_FIELDS, RELEASE_KEYS, 'skills release')

  if (isLegacyOperation(release.operation)) {
    fail('skills_legacy_operation', 'legacy skills run/tool names are not on the v0.2 consumer surface', {
      classification: 'fail_closed',
      field: 'operation',
      operation: release.operation,
    })
  }
  if (TELEMETRY_OPERATIONS.has(/** @type {string} */ (release.operation))) {
    fail('cross_operation_field', 'skills release cannot carry a telemetry operation', {
      classification: 'fail_closed',
      field: 'operation',
      operation: release.operation,
    })
  }
  if (release.operation === 'skills_release_package_get') {
    fail('skills_full_pack_forbidden', 'skills consumer must not address a full remote pack', {
      classification: 'fail_closed',
      field: 'operation',
    })
  }

  if (release.contractVersion !== SKILLS_CONTRACT_VERSION) {
    fail('skills_contract_incompatible', 'contractVersion must be skills.api.v0.2', {
      classification: 'fail_closed',
      field: 'contractVersion',
    })
  }

  const providerCommit = release.providerCommit
  const providerTree = release.providerTree
  if (!GIT_SHA.test(/** @type {string} */ (providerCommit)) || !GIT_SHA.test(/** @type {string} */ (providerTree))) {
    fail('skills_pin_invalid', 'skills provider pin is malformed', {
      classification: 'fail_closed',
      provider: 'skills',
    })
  }
  if (providerCommit !== SKILLS_PIN.commit || providerTree !== SKILLS_PIN.tree) {
    fail('incompatible_pin', 'skills provider pin does not match the frozen LiNKskills pin', {
      classification: 'fail_closed',
      provider: 'skills',
      frozenCommit: SKILLS_PIN.commit,
      frozenTree: SKILLS_PIN.tree,
    })
  }

  rejectLatestAlias(release.skillId, 'skillId')
  rejectLatestAlias(release.version, 'version')
  if (typeof release.skillId !== 'string' || !SKILL_ID.test(release.skillId)) {
    fail('skills_identity_invalid', 'skillId must be a lowercase hyphenated identity', {
      classification: 'fail_closed',
      field: 'skillId',
    })
  }
  if (typeof release.version !== 'string' || !SKILL_VERSION.test(release.version)) {
    fail('skills_identity_invalid', 'version must be an immutable semver identity', {
      classification: 'fail_closed',
      field: 'version',
    })
  }

  for (const field of ['releaseHash', 'bundleHash', 'manifestHash']) {
    if (typeof release[field] !== 'string' || !SHA256.test(/** @type {string} */ (release[field]))) {
      fail('skills_digest_invalid', `skills digest is malformed: ${field}`, {
        classification: 'fail_closed',
        field,
      })
    }
  }

  if (!Number.isInteger(release.fragmentLevel) || /** @type {number} */ (release.fragmentLevel) < 0 || /** @type {number} */ (release.fragmentLevel) > 6) {
    fail('skills_fragment_invalid', 'fragmentLevel must be an integer in 0..6', {
      classification: 'fail_closed',
      field: 'fragmentLevel',
    })
  }

  if (typeof release.addressing !== 'string' || !ADDRESSING.includes(release.addressing)) {
    fail('skills_addressing_invalid', 'addressing must be discovery, validation, or execution', {
      classification: 'fail_closed',
      field: 'addressing',
    })
  }
  if (release.operation !== undefined) {
    const allowed = ADDRESSING_OPERATIONS[/** @type {'discovery' | 'validation' | 'execution'} */ (release.addressing)]
    if (typeof release.operation !== 'string' || !allowed.has(release.operation)) {
      fail('cross_operation_field', 'skills operation is not allowed for the declared addressing', {
        classification: 'fail_closed',
        field: 'operation',
        addressing: release.addressing,
        operation: release.operation,
      })
    }
  }

  if (typeof release.lifecycle !== 'string' || !LIFECYCLES.has(release.lifecycle)) {
    fail('skills_lifecycle_invalid', 'skills lifecycle is malformed', {
      classification: 'fail_closed',
      field: 'lifecycle',
    })
  }
  if (release.lifecycle !== 'published') {
    fail('skills_not_published', 'skills lifecycle is not published', {
      classification: 'denied',
      lifecycle: release.lifecycle,
    })
  }

  if (typeof release.qualification !== 'string' || !QUALIFICATIONS.has(release.qualification)) {
    fail('skills_qualification_invalid', 'skills qualification is malformed', {
      classification: 'fail_closed',
      field: 'qualification',
    })
  }
  if (release.qualification !== 'qualified') {
    fail('skills_not_qualified', 'skills qualification is not qualified', {
      classification: 'denied',
      qualification: release.qualification,
    })
  }

  if (release.compatibility !== undefined && release.compatibility !== 'compatible') {
    fail('skills_release_incompatible', 'skills compatibility is fail-closed', {
      classification: 'incompatible',
      compatibility: release.compatibility,
    })
  }

  if (typeof release.availability !== 'string') {
    fail('skills_availability_invalid', 'skills availability is malformed', {
      classification: 'fail_closed',
      field: 'availability',
    })
  }
  if (INCOMPATIBLE_AVAILABILITY.has(release.availability)) {
    fail('skills_release_incompatible', 'skills availability is incompatible', {
      classification: 'incompatible',
      availability: release.availability,
    })
  }
  if (release.availability !== 'available') {
    if (!UNAVAILABLE.has(release.availability)) {
      fail('skills_availability_invalid', 'skills availability is malformed', {
        classification: 'fail_closed',
        field: 'availability',
      })
    }
    fail('skills_release_unavailable', 'skills release is not available', {
      classification: 'unavailable',
      availability: release.availability,
    })
  }

  return Object.freeze({
    skillId: /** @type {string} */ (release.skillId),
    version: /** @type {string} */ (release.version),
    releaseHash: /** @type {string} */ (release.releaseHash),
    bundleHash: /** @type {string} */ (release.bundleHash),
    manifestHash: /** @type {string} */ (release.manifestHash),
    fragmentLevel: /** @type {number} */ (release.fragmentLevel),
    addressing: /** @type {string} */ (release.addressing),
    providerCommit: /** @type {string} */ (release.providerCommit),
    providerTree: /** @type {string} */ (release.providerTree),
  })
}

/**
 * @param {unknown} value
 * @returns {Readonly<{
 *   reportKind: 'completed_use',
 *   score: number,
 *   skillReleaseRef: string,
 *   actorRef: string,
 *   idempotencyKey: string,
 *   issue?: Readonly<{ type: string, severity: string, issueRef: string }>,
 * }>}
 */
export function validateSkillsTelemetry(value) {
  const report = object(value)
  rejectSensitive(report)
  rejectShape(report, TELEMETRY_COMPETING, TELEMETRY_CROSS_FIELDS, TELEMETRY_KEYS, 'skills telemetry')

  if (report.reportKind !== 'completed_use') {
    fail('skills_telemetry_invalid', 'reportKind must be completed_use', {
      classification: 'fail_closed',
      field: 'reportKind',
    })
  }
  if (!Number.isInteger(report.score) || /** @type {number} */ (report.score) < 0 || /** @type {number} */ (report.score) > 10) {
    fail('skills_telemetry_invalid', 'score must be an integer in 0..10', {
      classification: 'fail_closed',
      field: 'score',
    })
  }

  for (const field of ['skillReleaseRef', 'actorRef', 'idempotencyKey']) {
    if (typeof report[field] !== 'string' || !OPAQUE.test(/** @type {string} */ (report[field]))) {
      fail('skills_reference_invalid', `skills telemetry reference is malformed: ${field}`, {
        classification: 'fail_closed',
        field,
      })
    }
  }

  if (report.score === 10 && report.issue !== undefined) {
    fail('skills_perfect_use_has_issue', 'score 10 use reports must not include an issue object', {
      classification: 'fail_closed',
      field: 'issue',
    })
  }

  /** @type {Readonly<{ type: string, severity: string, issueRef: string }> | undefined} */
  let issue
  if (/** @type {number} */ (report.score) < 10) {
    const record = object(report.issue, 'skills_issue_required')
    rejectSensitive(record)
    rejectShape(record, new Set(), new Set(), ISSUE_KEYS, 'skills telemetry issue')
    if (typeof record.type !== 'string' || !ISSUE_TYPES.has(record.type)) {
      fail('skills_issue_invalid', 'skills issue type is malformed', {
        classification: 'fail_closed',
        field: 'type',
      })
    }
    if (typeof record.severity !== 'string' || !ISSUE_SEVERITIES.has(record.severity)) {
      fail('skills_issue_invalid', 'skills issue severity is malformed', {
        classification: 'fail_closed',
        field: 'severity',
      })
    }
    if (typeof record.issueRef !== 'string' || !OPAQUE.test(record.issueRef)) {
      fail('skills_reference_invalid', 'skills issueRef is malformed', {
        classification: 'fail_closed',
        field: 'issueRef',
      })
    }
    issue = Object.freeze({
      type: record.type,
      severity: record.severity,
      issueRef: record.issueRef,
    })
  }

  return Object.freeze({
    reportKind: 'completed_use',
    score: /** @type {number} */ (report.score),
    skillReleaseRef: /** @type {string} */ (report.skillReleaseRef),
    actorRef: /** @type {string} */ (report.actorRef),
    idempotencyKey: /** @type {string} */ (report.idempotencyKey),
    ...(issue ? { issue } : {}),
  })
}
