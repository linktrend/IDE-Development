/**
 * IDE Development's local, non-executing boundary for frozen LiNK providers.
 *
 * This module validates references and bounded provider projections only. It
 * deliberately has no transport, credentials, provider execution, Git, gate,
 * or ledger mutation capability.
 */

export const MCP_PROTOCOL_VERSION = '2026-07-28'

export const FROZEN_PROVIDERS = Object.freeze({
  platform: Object.freeze({ commit: '6a7114674c23fc6b9ba9ae2b3277b8aec7a3fb15', tree: '91d565a988150da39a13b66c4bcd51f7bc47c9be' }),
  libraries: Object.freeze({ commit: '87dbb71da8b07be8f83eb82f8f769e16b062e7b2', tree: 'f258bf45d91a90fb4c818ee9012c7a85b1fa96da' }),
  brain: Object.freeze({ commit: '43887ffc3b51ef2e54c30820d41cab67f54d5d0f', tree: '40c7acfcd7b204f19a1278e6801033c4ee64b369' }),
  skills: Object.freeze({ commit: '93ec4b9df2ebe2a9d9b412fb8b3bcde2aa8e97f3', tree: '1845b996a7ec4d217a57e6f66574d6c5d676bb67' }),
  autowork: Object.freeze({ commit: '10f75a8d840160a10d131371e94a338dfd1ebb4a', tree: 'c433907818f2cd4adbfdd61549f9f91396e31819' }),
})

const SHA256 = /^sha256:[a-f0-9]{64}$/
const GIT_SHA = /^[a-f0-9]{40}$/
const OPAQUE = /^opaque:[A-Za-z0-9][A-Za-z0-9._:/-]{1,94}$/
const FORBIDDEN = /(?:secret|password|token|authorization|private.?key|prompt|transcript|conversation|raw(?:_|$)|full.?content|body)/i

export class ConsumerContractError extends Error {
  constructor(code) { super(code); this.name = 'ConsumerContractError'; this.code = code }
}

function fail(code) { throw new ConsumerContractError(code) }
function object(value, code = 'invalid_object') { if (!value || typeof value !== 'object' || Array.isArray(value)) fail(code); return value }
function text(value, code) { if (typeof value !== 'string' || !value) fail(code); return value }
function exactKeys(value, allowed) { for (const key of Object.keys(value)) if (!allowed.has(key)) fail('unknown_field') }
function isoFuture(value, now) { const date = Date.parse(value); if (!Number.isFinite(date) || date <= now) fail('expired') }
function safeBounded(value, depth = 0) {
  if (depth > 5) fail('payload_too_deep')
  if (typeof value === 'string') { if (value.length > 4096) fail('payload_too_large'); return }
  if (value === null || typeof value === 'number' || typeof value === 'boolean') return
  if (Array.isArray(value)) { if (value.length > 32) fail('payload_too_large'); for (const item of value) safeBounded(item, depth + 1); return }
  object(value, 'payload_invalid')
  for (const [key, item] of Object.entries(value)) { if (FORBIDDEN.test(key)) fail('sensitive_field'); safeBounded(item, depth + 1) }
}

export function validatePlatformIdentity(value, { now = Date.now(), audience, service, capability, organizationId } = {}) {
  const claim = object(value); exactKeys(claim, new Set(['claimContractVersion', 'actorId', 'actorKind', 'runtimeBindingId', 'credentialId', 'orgId', 'internal', 'audience', 'serviceScopes', 'permittedOperations', 'issuedAt', 'expiresAt', 'issuer', 'correlationId', 'programRestrictions', 'repositoryRestrictions']))
  if (claim.claimContractVersion !== 'platform.auth-claims/1.1.0') fail('identity_contract_incompatible')
  for (const key of ['actorId', 'actorKind', 'runtimeBindingId', 'credentialId', 'orgId', 'issuedAt', 'expiresAt', 'issuer', 'correlationId']) text(claim[key], 'identity_field_missing')
  if (!['human', 'persona', 'service', 'adapter', 'program_executor'].includes(claim.actorKind) || typeof claim.internal !== 'boolean') fail('identity_actor_invalid')
  if (!Array.isArray(claim.audience) || !Array.isArray(claim.serviceScopes) || !Array.isArray(claim.permittedOperations)) fail('identity_scope_invalid')
  if (audience && !claim.audience.includes(audience)) fail('wrong_audience')
  if (service && !claim.serviceScopes.includes(service)) fail('wrong_service')
  if (capability && !claim.permittedOperations.includes(capability)) fail('operation_not_permitted')
  if (organizationId && claim.orgId !== organizationId) fail('wrong_organization')
  if (!Number.isFinite(Date.parse(claim.issuedAt))) fail('identity_time_invalid')
  isoFuture(claim.expiresAt, now)
  return Object.freeze({ actorId: claim.actorId, runtimeBindingId: claim.runtimeBindingId, orgId: claim.orgId })
}

export function validateBrainProjection(value) {
  const projection = object(value); exactKeys(projection, new Set(['contractVersion', 'authority', 'executionAuthority', 'projectionRef', 'summary', 'handoffRef', 'okf']))
  if (projection.contractVersion !== '2.0.0' || projection.authority !== 'advisory' || projection.executionAuthority !== 'none') fail('brain_authority_invalid')
  text(projection.projectionRef, 'brain_projection_missing')
  if (projection.summary !== undefined) { text(projection.summary, 'brain_summary_invalid'); if (projection.summary.length > 4096) fail('brain_summary_too_large') }
  if (projection.handoffRef !== undefined) text(projection.handoffRef, 'brain_handoff_invalid')
  if (projection.okf !== undefined) validateOkfMapping(projection.okf)
  return Object.freeze({ projectionRef: projection.projectionRef, handoffRef: projection.handoffRef })
}

export function validateSkillsRelease(value) {
  const release = object(value); exactKeys(release, new Set(['skillId', 'version', 'releaseHash', 'bundleHash', 'manifestHash', 'lifecycle', 'qualification', 'availability', 'fragmentLevel']))
  for (const key of ['skillId', 'version', 'releaseHash', 'bundleHash', 'manifestHash']) text(release[key], 'skills_release_missing')
  if (![release.releaseHash, release.bundleHash, release.manifestHash].every((item) => SHA256.test(item))) fail('skills_digest_invalid')
  if (release.lifecycle !== 'published' || release.qualification !== 'qualified' || release.availability !== 'available') fail('skills_release_unavailable')
  if (!Number.isInteger(release.fragmentLevel) || release.fragmentLevel < 0 || release.fragmentLevel > 6) fail('skills_fragment_invalid')
  return Object.freeze({ skillId: release.skillId, version: release.version, releaseHash: release.releaseHash, fragmentLevel: release.fragmentLevel })
}

export function validateSkillsTelemetry(value) {
  const report = object(value); exactKeys(report, new Set(['reportKind', 'score', 'issue', 'skillReleaseRef', 'actorRef', 'idempotencyKey']))
  if (report.reportKind !== 'completed_use' || !Number.isInteger(report.score) || report.score < 0 || report.score > 10) fail('skills_telemetry_invalid')
  for (const key of ['skillReleaseRef', 'actorRef', 'idempotencyKey']) if (!OPAQUE.test(report[key] ?? '')) fail('skills_reference_invalid')
  if (report.score === 10 && report.issue !== undefined) fail('skills_perfect_use_has_issue')
  if (report.score < 10) { const issue = object(report.issue, 'skills_issue_required'); safeBounded(issue); }
  return true
}

export function validateAutoworkReceipt(value) {
  const receipt = object(value); exactKeys(receipt, new Set(['contractVersion', 'requestId', 'idempotencyKey', 'status', 'result']))
  if (receipt.contractVersion !== 'provider-contract/v1' || !OPAQUE.test(receipt.requestId ?? '') || !OPAQUE.test(receipt.idempotencyKey ?? '')) fail('autowork_receipt_invalid')
  if (!['accepted', 'completed', 'failed', 'unavailable'].includes(receipt.status)) fail('autowork_status_invalid')
  if (receipt.result !== undefined) safeBounded(receipt.result)
  return Object.freeze({ requestId: receipt.requestId, status: receipt.status })
}

export function validateLibraryReference(value) {
  const reference = object(value); exactKeys(reference, new Set(['commit', 'tree', 'cataloguePath', 'catalogueDigest', 'entryId', 'version', 'manifestDigest', 'inventoryDigest', 'closureDigest']))
  const frozen = FROZEN_PROVIDERS.libraries
  if (reference.commit !== frozen.commit || reference.tree !== frozen.tree || reference.cataloguePath !== 'indexes/v2/catalog.json') fail('library_reference_not_frozen')
  for (const field of ['catalogueDigest', 'manifestDigest', 'inventoryDigest', 'closureDigest']) if (!SHA256.test(reference[field] ?? '')) fail('library_digest_invalid')
  for (const field of ['entryId', 'version']) text(reference[field], 'library_reference_invalid')
  return Object.freeze({ ...reference })
}

export function negotiateMcp(version, era) { if (version !== MCP_PROTOCOL_VERSION || era !== 'modern') fail('mcp_negotiation_failed'); return MCP_PROTOCOL_VERSION }

export function validateOkfMapping(value) {
  const mapping = object(value); exactKeys(mapping, new Set(['format', 'version', 'exchangeKind', 'applicable', 'nonApplicabilityReason']))
  if (mapping.format !== 'OKF' || mapping.version !== '0.2') fail('okf_version_invalid')
  const eligible = ['canonical_knowledge', 'canonical_projection'].includes(mapping.exchangeKind)
  if (mapping.applicable !== eligible) fail('okf_applicability_invalid')
  if (!eligible && !text(mapping.nonApplicabilityReason, 'okf_reason_required')) fail('okf_reason_required')
  if (eligible && mapping.nonApplicabilityReason !== undefined) fail('okf_reason_forbidden')
  return true
}
