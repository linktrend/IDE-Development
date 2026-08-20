import assert from 'node:assert/strict'
import { test } from 'node:test'
import { createProviderClients } from '../../core/link-integrations/clients.mjs'
import { validateProviderRuntimeConfig } from '../../core/link-integrations/config.mjs'
import { ConsumerContractError } from '../../core/link-integrations/errors.mjs'
import {
  PROVIDER_REGISTRY,
  validateProviderRegistry,
} from '../../core/link-integrations/registry.mjs'
import { redact } from '../../core/link-integrations/redaction.mjs'
import {
  createAuthenticatedTransport,
  ProviderTransportError,
} from '../../core/link-integrations/transport.mjs'

const SHA = '0123456789abcdef'.repeat(4)
const GIT = '0123456789abcdef0123456789abcdef01234567'
const TREE = '89abcdef0123456789abcdef0123456789abcdef'
const NOW = Date.parse('2026-08-20T06:00:00.000Z')

const config = {
  schemaVersion: 'provider-runtime-config/v1',
  consumerRepository: 'linktrend/IDE-Development',
  environment: 'test',
  providers: {
    platform: {
      endpoint: 'https://platform.test',
      credentialRef: 'LINKTREND_PLATFORM_TEST_TOKEN',
      enabledCapabilities: ['platform.identity.resolve', 'platform.capabilities.read'],
    },
    brain: {
      endpoint: 'https://brain.test',
      credentialRef: 'LINKTREND_BRAIN_TEST_TOKEN',
      enabledCapabilities: ['brain.projection.read', 'brain.handoff.create'],
    },
    skills: {
      endpoint: 'https://skills.test',
      credentialRef: 'LINKTREND_SKILLS_TEST_TOKEN',
      enabledCapabilities: ['skills.release.read'],
    },
    libraries: {
      endpoint: 'https://libraries.test',
      credentialRef: 'LINKTREND_LIBRARIES_TEST_TOKEN',
      enabledCapabilities: ['libraries.entry.read'],
    },
    autowork: {
      endpoint: 'https://autowork.test',
      credentialRef: 'LINKTREND_AUTOWORK_TEST_TOKEN',
      enabledCapabilities: ['autowork.status.read'],
      availability: 'unavailable',
    },
  },
}

function throwsCode(fn, code) {
  assert.throws(fn, (error) => error instanceof ConsumerContractError && error.code === code)
}

function response(status, body, headers = {}) {
  return {
    status,
    headers: new Headers(headers),
    async text() {
      return JSON.stringify(body)
    },
  }
}

function platformClaim() {
  return {
    claimContractVersion: 'platform.auth-claims/1.1.0',
    actorId: 'actor-runtime-test',
    actorKind: 'service',
    runtimeBindingId: 'binding-runtime-test',
    credentialId: 'credential-runtime-test',
    orgId: 'org-runtime-test',
    internal: true,
    serviceScopes: ['lbrain'],
    permittedOperations: ['brain.projection.read'],
    issuedAt: '2026-08-20T05:00:00.000Z',
    expiresAt: '2026-08-20T07:00:00.000Z',
    issuer: 'platform://issuer',
    audience: ['ide-development'],
    programRestrictions: [],
    repositoryRestrictions: [],
    correlationId: 'correlation-runtime-test',
  }
}

function platformContext() {
  return {
    expectedAudience: 'ide-development',
    requiredService: 'lbrain',
    requiredCapability: 'brain.projection.read',
    expectedOrgId: 'org-runtime-test',
    expectedRuntimeBindingId: 'binding-runtime-test',
    now: '2026-08-20T06:00:00.000Z',
    identityServiceStatus: 'available',
    credentialStatus: 'active',
    actorLifecycleState: 'active',
    bindingState: 'active',
  }
}

function brainProjection(projectionRef = 'projection-runtime-test') {
  return {
    contractVersion: '2.0.0',
    authority: 'advisory',
    executionAuthority: 'none',
    projectionRef,
    summary: 'A bounded advisory projection.',
  }
}

function libraryReference() {
  return {
    sourceCommitSha: '5901d111309543ed0839938d7217475e5d4b8ac4',
    sourceTreeSha: '185d7cf714777d60a2d01a4881bf1a11bc5018d9',
    releaseSourceCommitSha: GIT,
    releaseSourceTreeSha: TREE,
    artifactTreeSha1: 'abcdef0123456789abcdef0123456789abcdef01',
    entryId: 'runtime-component',
    version: '1.0.0',
    releaseManifestSha256: SHA,
    inventorySha256: '1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef',
    payloadSha256: 'abcdef0123456789abcdef0123456789abcdef0123456789abcdef0123456789',
    dependencyLockSha256: 'fedcba9876543210fedcba9876543210fedcba9876543210fedcba9876543210',
    catalogueSha256: '2345678901abcdef2345678901abcdef2345678901abcdef2345678901abcdef',
    catalogueRecordsSha256: '3456789012abcdef3456789012abcdef3456789012abcdef3456789012abcdef',
    receiptType: 'consumption',
    receiptId: 'runtime-receipt-1',
  }
}

function autoworkStatus() {
  return {
    request_id: '00000000-0000-4000-8000-000000000010',
    state: 'accepted',
    attempt_count: 0,
    automation: {
      automation_id: 'runtime-automation',
      version: '1.0.0',
      definition_digest: `sha256:${'1'.repeat(64)}`,
      configuration_digest: `sha256:${'2'.repeat(64)}`,
    },
  }
}

test('runtime registry is complete, pinned, and grants no execution authority', () => {
  const accepted = validateProviderRegistry(PROVIDER_REGISTRY)
  assert.equal(Object.keys(accepted.providers).length, 5)
  for (const provider of Object.values(accepted.providers)) {
    assert.ok(provider.providerCommit)
    assert.ok(provider.providerTree)
    assert.ok(provider.timeouts.requestMs > 0)
    assert.equal(provider.executionAuthority, 'none')
    assert.equal(provider.redactionPolicy.allowRawBody, false)
    for (const tool of provider.tools) assert.equal(tool.executionAuthority, 'none')
  }
  assert.throws(() => {
    accepted.providers.brain.tools[0].executionAuthority = 'execute'
  }, TypeError)
})

test('runtime config accepts non-secret bindings and rejects values that could contain secrets', () => {
  const accepted = validateProviderRuntimeConfig(config)
  assert.equal(accepted.providers.platform.credentialRef, 'LINKTREND_PLATFORM_TEST_TOKEN')
  assert.equal(accepted.providers.autowork.availability, 'unavailable')
  assert.ok(Object.isFrozen(accepted))
  assert.ok(Object.isFrozen(accepted.providers.platform))
  throwsCode(
    () => validateProviderRuntimeConfig({ ...config, providers: { ...config.providers, platform: { ...config.providers.platform, token: 'secret' } } }),
    'config_sensitive_field',
  )
  throwsCode(
    () => validateProviderRuntimeConfig({ ...config, providers: { ...config.providers, platform: { ...config.providers.platform, endpoint: 'http://platform.test' } } }),
    'config_endpoint_invalid',
  )
  throwsCode(
    () => validateProviderRuntimeConfig({ ...config, unexpected: true }),
    'config_unknown_field',
  )
})

test('redaction removes credentials and raw provider bodies while bounding output', () => {
  const safe = redact({
    authorization: 'Bearer ltfx.auth_token.v1',
    nested: { password: 'ltfx.password.v1', answer: 'kept' },
    body: 'raw provider body',
    list: ['kept', { token: 'hidden' }],
  })
  assert.deepEqual(safe, {
    authorization: '[REDACTED]',
    nested: { password: '[REDACTED]', answer: 'kept' },
    body: '[REDACTED]',
    list: ['kept', { token: '[REDACTED]' }],
  })
  assert.equal(JSON.stringify(safe).includes('secret'), false)
  assert.equal(redact('x'.repeat(5000)).length, 2048)
  assert.equal(redact({ value: 'x'.repeat(5000) }).value.length, 2048)
})

test('authenticated transport sends bearer credentials and maps denied responses without leaking them', async () => {
  const calls = []
  const transport = createAuthenticatedTransport({
    provider: 'platform',
    endpoint: 'https://platform.test',
    getAccessToken: async () => 'secret-token',
    fetchImpl: async (url, options) => {
      calls.push({ url, options })
      return response(403, { error: 'forbidden', token: 'ltfx.response_secret.v1' })
    },
  })
  await assert.rejects(
    () => transport.request('platform.capabilities.read', { path: '/v1/capabilities' }),
    (error) => {
      assert.ok(error instanceof ProviderTransportError)
      assert.equal(error.code, 'provider_denied')
      assert.equal(error.details.body, undefined)
      assert.equal(error.message.includes('secret'), false)
      return true
    },
  )
  assert.equal(calls.length, 1)
  assert.equal(calls[0].url, 'https://platform.test/v1/capabilities')
  assert.equal(calls[0].options.headers.get('authorization'), 'Bearer secret-token')
})

test('transport retries one transient failure, times out, and refuses unsafe operations', async () => {
  let attempts = 0
  const transport = createAuthenticatedTransport({
    provider: 'brain',
    endpoint: 'https://brain.test',
    getAccessToken: () => 'token',
    timeoutMs: 100,
    fetchImpl: async () => {
      attempts += 1
      return attempts === 1
        ? response(503, { error: 'temporarily unavailable' })
        : response(200, { projection: brainProjection() })
    },
    sleep: async () => {},
  })
  const result = await transport.request('brain.projection.read', {
    path: '/v1/projections/runtime',
  })
  assert.deepEqual(result, { projection: brainProjection() })
  assert.equal(attempts, 2)

  const timeoutTransport = createAuthenticatedTransport({
    provider: 'brain',
    endpoint: 'https://brain.test',
    getAccessToken: () => 'token',
    timeoutMs: 5,
    fetchImpl: (_url, { signal }) => new Promise((resolve, reject) => {
      signal.addEventListener('abort', () => reject(Object.assign(new Error('aborted'), { name: 'AbortError' })))
    }),
    sleep: async () => {},
  })
  await assert.rejects(
    () => timeoutTransport.request('brain.projection.read', { path: '/v1/projections/runtime' }),
    (error) => error.code === 'provider_timeout',
  )
  await assert.rejects(
    () => transport.request('brain.unknown', { path: '/v1/projections/runtime' }),
    (error) => error.code === 'operation_not_allowed',
  )
})

test('provider clients perform bounded reads and preserve Brain advisory authority', async () => {
  const requests = []
  const transport = {
    async request(operation, request) {
      requests.push({ operation, request })
      if (operation === 'platform.identity.resolve') return { claim: platformClaim() }
      if (operation === 'platform.capabilities.read') return { capabilities: ['brain.projection.read'] }
      if (operation === 'brain.projection.search') return { projections: [brainProjection()] }
      if (operation === 'brain.handoff.create') {
        return {
          handoff: {
            contractVersion: '2.0.0',
            authority: 'advisory',
            executionAuthority: 'none',
            handoffRef: 'handoff://runtime-test',
            namespaceRef: 'namespace://runtime-test',
            status: 'open',
          },
        }
      }
      if (operation === 'libraries.entry.read') return { entry: libraryReference() }
      if (operation === 'autowork.status.read') return autoworkStatus()
      throw new Error(`unexpected operation ${operation}`)
    },
  }
  const clients = createProviderClients({
    transports: {
      platform: transport,
      brain: transport,
      libraries: transport,
      autowork: transport,
    },
    now: NOW,
  })
  const identity = await clients.platform.resolveIdentity(platformContext())
  assert.equal(identity.actorId, 'actor-runtime-test')
  assert.deepEqual(await clients.platform.readCapabilities(), ['brain.projection.read'])
  const projections = await clients.brain.search({ query: 'bounded' })
  assert.equal(projections[0].projectionRef, 'projection-runtime-test')
  const handoff = await clients.brain.createHandoff({ namespaceRef: 'namespace://runtime-test' })
  assert.equal(handoff.executionAuthority, 'none')
  assert.equal((await clients.libraries.read(libraryReference())).entryId, 'runtime-component')
  assert.equal((await clients.autowork.readStatus({ requestId: autoworkStatus().request_id })).status, 'accepted')
  assert.equal(requests.some(({ operation }) => operation === 'brain.handoff.create'), true)
})

test('Autowork unavailable is an explicit HOLD and never execution authority', async () => {
  const clients = createProviderClients({
    transports: {
      autowork: {
        async request() {
          throw new ProviderTransportError('provider_unavailable', 'Autowork runtime is unavailable', {
            provider: 'autowork',
            classification: 'unavailable',
          })
        },
      },
    },
  })
  const hold = await clients.autowork.readStatus({ requestId: autoworkStatus().request_id })
  assert.deepEqual(hold, {
    state: 'HOLD',
    provider: 'autowork',
    reason: 'live_runtime_unavailable',
    executionAuthority: 'none',
  })
})

test('provider client responses reject incompatible, malformed, tampered, replayed, and expired data', async () => {
  const transport = {
    async request(operation) {
      if (operation === 'brain.projection.search') {
        return { projections: [{ ...brainProjection(), executionAuthority: 'execute' }] }
      }
      if (operation === 'libraries.entry.read') {
        return { entry: { ...libraryReference(), catalogueRecord: { entryId: 'tampered' } } }
      }
      if (operation === 'autowork.status.read') return autoworkStatus()
      throw new Error('unexpected operation')
    },
  }
  const clients = createProviderClients({
    transports: { brain: transport, libraries: transport, autowork: transport },
  })
  await assert.rejects(() => clients.brain.search({ query: 'x' }), (error) => error.code === 'brain_execution_denied')
  await assert.rejects(() => clients.libraries.read(libraryReference()), (error) => error.code === 'library_tampered')
  await assert.rejects(() => clients.autowork.readStatus({
    requestId: autoworkStatus().request_id,
    previousStatus: 'succeeded',
  }), (error) => error.code === 'autowork_terminal_regression')
  throwsCode(
    () => validateProviderRuntimeConfig({ ...config, providers: { ...config.providers, brain: { ...config.providers.brain, contractVersion: 'legacy' } } }),
    'config_contract_incompatible',
  )
})
