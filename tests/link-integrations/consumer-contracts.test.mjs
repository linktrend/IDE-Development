import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
import { fileURLToPath } from 'node:url'
import { test } from 'node:test'
import { ConsumerContractError, FROZEN_PROVIDERS, MCP_PROTOCOL_VERSION, negotiateMcp, validateAutoworkReceipt, validateBrainProjection, validateLibraryReference, validateOkfMapping, validatePlatformIdentity, validateSkillsRelease, validateSkillsTelemetry } from '../../core/link-integrations/consumer-contracts.mjs'

const throws = (fn, code) => assert.throws(fn, (error) => error instanceof ConsumerContractError && error.code === code)

test('pins the five frozen provider releases', () => {
  assert.equal(Object.keys(FROZEN_PROVIDERS).length, 5)
  assert.equal(FROZEN_PROVIDERS.platform.commit, '6a7114674c23fc6b9ba9ae2b3277b8aec7a3fb15')
})

test('materializes the provider boundary into every managed consumer', () => {
  const manifestPath = fileURLToPath(new URL('../../core/managed-core/MANIFEST.json', import.meta.url))
  const manifest = JSON.parse(readFileSync(manifestPath, 'utf8'))
  const entry = manifest.files.find((item) => item.destination === '.ide-development/providers/consumer-contracts.mjs')
  assert.equal(entry.source, 'core/managed-core/platforms/providers/consumer-contracts.mjs')
  assert.equal(entry.platform, 'all')
})

test('accepts only a bounded valid Platform identity', () => {
  const identity = validatePlatformIdentity({ claimContractVersion: 'platform.auth-claims/1.1.0', actorId: 'actor-1', actorKind: 'adapter', runtimeBindingId: 'binding-1', credentialId: 'credential-1', orgId: 'org-1', internal: true, audience: ['brain'], serviceScopes: ['brain'], permittedOperations: ['read'], issuedAt: '2026-01-01T00:00:00.000Z', expiresAt: '2030-01-01T00:00:00.000Z', issuer: 'platform', correlationId: 'corr-1' }, { now: 0, audience: 'brain', service: 'brain', capability: 'read', organizationId: 'org-1' })
  assert.equal(identity.actorId, 'actor-1')
  throws(() => validatePlatformIdentity({ claimContractVersion: 'platform.auth-claims/1.1.0', actorId: 'a', actorKind: 'adapter', runtimeBindingId: 'b', credentialId: 'c', orgId: 'o', internal: true, audience: [], serviceScopes: [], permittedOperations: [], issuedAt: '1999-01-01T00:00:00.000Z', expiresAt: '2000-01-01T00:00:00.000Z', issuer: 'platform', correlationId: 'corr' }, { now: Date.parse('2030-01-01T00:00:00.000Z') }), 'expired')
})

test('Brain stays advisory and metadata-first', () => {
  assert.equal(validateBrainProjection({ contractVersion: '2.0.0', authority: 'advisory', executionAuthority: 'none', projectionRef: 'projection-1', summary: 'bounded' }).projectionRef, 'projection-1')
  throws(() => validateBrainProjection({ contractVersion: '2.0.0', authority: 'advisory', executionAuthority: 'none', projectionRef: 'x', transcript: 'no' }), 'unknown_field')
})

test('Skills require a qualified exact release and bounded telemetry', () => {
  const digest = `sha256:${'a'.repeat(64)}`
  assert.equal(validateSkillsRelease({ skillId: 'safe-skill', version: '1.0.0', releaseHash: digest, bundleHash: digest, manifestHash: digest, lifecycle: 'published', qualification: 'qualified', availability: 'available', fragmentLevel: 2 }).fragmentLevel, 2)
  throws(() => validateSkillsRelease({ skillId: 'latest', version: 'latest', releaseHash: digest, bundleHash: digest, manifestHash: digest, lifecycle: 'published', qualification: 'qualified', availability: 'available', fragmentLevel: 7 }), 'skills_fragment_invalid')
  assert.equal(validateSkillsTelemetry({ reportKind: 'completed_use', score: 10, skillReleaseRef: 'opaque:release-1', actorRef: 'opaque:actor-1', idempotencyKey: 'opaque:key-1' }), true)
  throws(() => validateSkillsTelemetry({ reportKind: 'completed_use', score: 10, issue: { code: 'x' }, skillReleaseRef: 'opaque:release-1', actorRef: 'opaque:actor-1', idempotencyKey: 'opaque:key-1' }), 'skills_perfect_use_has_issue')
})

test('Autowork and Libraries receive bounded immutable Revision 2 references only', () => {
  assert.equal(validateAutoworkReceipt({ contractVersion: 'provider-contract/v1', requestId: 'opaque:request-1', idempotencyKey: 'opaque:key-1', status: 'completed', result: { count: 1 } }).status, 'completed')
  throws(() => validateAutoworkReceipt({ contractVersion: 'provider-contract/v1', requestId: 'opaque:request-1', idempotencyKey: 'opaque:key-1', status: 'completed', result: { secret: 'x' } }), 'sensitive_field')
  const facts = {
    sourceCommitSha: FROZEN_PROVIDERS.libraries.commit,
    sourceTreeSha: FROZEN_PROVIDERS.libraries.tree,
    releaseSourceCommitSha: '96d6972b836e8ccb51ea6fe1377ed6440ab7e1d9',
    releaseSourceTreeSha: 'f8f20316b62492b9b1d0363f1c7983fc64de58ec',
    artifactTreeSha1: '2107a410b1308048a138f2dcb80c9cc7d8b7867a',
    entryId: 'synthetic-component',
    version: '1.0.0',
    releaseManifestSha256: '6b9979777561d1771294ff4ddd10159b543c3b3cdd699c82ad759ab04ea67212',
    inventorySha256: 'deea48fd4fd547513f12216cd71191128eb8c3a78820d08862617d14498247a0',
    payloadSha256: '8cad275e50f5c468ee7bb53e0594dd4c4c53b49a78aa1da6e8cb1ab737fd7e37',
    dependencyLockSha256: '59f4db72af5de4731c68ee44b525f494c6cd067b42f8da310c345829f1b09c23',
    receiptType: 'verified_cache',
    receiptId: 'external-synthetic-component-1.0.0',
  }
  assert.equal(validateLibraryReference(facts).entryId, 'synthetic-component')
  throws(() => validateLibraryReference({ ...facts, closureDigest: facts.dependencyLockSha256 }), 'unknown_field')
  throws(() => validateLibraryReference({ ...facts, sourceCommitSha: '0123456789abcdef0123456789abcdef01234567' }), 'library_reference_not_frozen')
  throws(() => validateLibraryReference({ ...facts, receiptType: 'execute' }), 'library_receipt_invalid')
})

test('MCP and OKF transitions fail closed', () => {
  assert.equal(negotiateMcp(MCP_PROTOCOL_VERSION, 'modern'), MCP_PROTOCOL_VERSION)
  throws(() => negotiateMcp('2025-06-18', 'legacy'), 'mcp_negotiation_failed')
  assert.equal(validateOkfMapping({ format: 'OKF', version: '0.2', exchangeKind: 'canonical_projection', applicable: true }), true)
  throws(() => validateOkfMapping({ format: 'OKF', version: '0.2', exchangeKind: 'task_state', applicable: false }), 'okf_reason_required')
})
