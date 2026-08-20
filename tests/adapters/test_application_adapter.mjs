import assert from 'node:assert/strict'
import test from 'node:test'

import { ConsumerContractError } from '../../core/link-integrations/errors.mjs'
import { createApplicationAdapter as createCodexAdapter } from '../../core/managed-core/platforms/codex/adapter.mjs'
import { createApplicationAdapter as createCursorAdapter } from '../../core/managed-core/platforms/cursor/adapter.mjs'

function providerClients(overrides = {}) {
  return {
    platform: {
      resolveIdentity: async (input) => ({ kind: 'platform.identity', input }),
      readCapabilities: async () => ['platform.identity.resolve'],
      ...overrides.platform,
    },
    brain: {
      search: async (input) => [{ kind: 'brain.projection.search', input }],
      read: async (projectionRef) => ({ kind: 'brain.projection.read', projectionRef }),
      createHandoff: async (input) => ({ kind: 'brain.handoff.create', input }),
      readHandoff: async (handoffRef) => ({ kind: 'brain.handoff.read', handoffRef }),
      acceptHandoff: async (handoffRef) => ({ kind: 'brain.handoff.accept', handoffRef }),
      handoffStatus: async (handoffRef) => ({ kind: 'brain.handoff.status', handoffRef }),
      closeHandoff: async (handoffRef) => ({ kind: 'brain.handoff.close', handoffRef }),
      ...overrides.brain,
    },
    skills: {
      search: async (input) => [{ kind: 'skills.release.search', input }],
      read: async (release) => ({ kind: 'skills.release.read', release }),
      readFragment: async (release, fragmentLevel) => ({
        kind: 'skills.release.fragment.read',
        release,
        fragmentLevel,
      }),
      submitTelemetry: async (input) => ({ kind: 'skills.telemetry.submit', input }),
      ...overrides.skills,
    },
  }
}

function call(adapter, name, input) {
  return adapter.callTool(name, input)
}

test('Codex and Cursor expose equivalent canary tool contracts', () => {
  const codex = createCodexAdapter({ application: 'codex', profile: 'canary', clients: providerClients() })
  const cursor = createCursorAdapter({ application: 'cursor', profile: 'canary', clients: providerClients() })

  assert.deepEqual(codex.listTools(), cursor.listTools())
  assert.deepEqual(codex.listTools(), [
    'platform.identity.resolve',
    'brain.projection.read',
    'skills.release.read',
    'brain.handoff.create',
  ])
})

test('adapter routes equivalent tool inputs to provider clients', async () => {
  const adapters = [
    createCodexAdapter({ application: 'codex', profile: 'canary', clients: providerClients() }),
    createCursorAdapter({ application: 'cursor', profile: 'canary', clients: providerClients() }),
  ]

  for (const adapter of adapters) {
    assert.deepEqual(
      await call(adapter, 'platform.identity.resolve', { expectedAudience: 'canary' }),
      { kind: 'platform.identity', input: { expectedAudience: 'canary' } },
    )
    assert.deepEqual(
      await call(adapter, 'brain.projection.read', { projectionRef: 'projection-1' }),
      { kind: 'brain.projection.read', projectionRef: 'projection-1' },
    )
    assert.deepEqual(
      await call(adapter, 'skills.release.read', { release: { skillId: 'skill-1', version: '1.0.0' } }),
      { kind: 'skills.release.read', release: { skillId: 'skill-1', version: '1.0.0' } },
    )
    assert.deepEqual(
      await call(adapter, 'brain.handoff.create', { handoffRef: 'handoff-1' }),
      { kind: 'brain.handoff.create', input: { handoffRef: 'handoff-1' } },
    )
  }
})

test('profile allowlists reject tools outside the selected profile', async () => {
  const adapter = createCodexAdapter({ application: 'codex', profile: 'canary', clients: providerClients() })

  await assert.rejects(
    () => call(adapter, 'skills.release.search', {}),
    (error) => error instanceof ConsumerContractError
      && error.code === 'tool_not_allowed'
      && !('rawBody' in error.details),
  )
})

test('missing tools and malformed inputs use equivalent stable errors', async () => {
  const adapters = [
    createCodexAdapter({ application: 'codex', profile: 'canary', clients: providerClients() }),
    createCursorAdapter({ application: 'cursor', profile: 'canary', clients: providerClients() }),
  ]

  for (const adapter of adapters) {
    await assert.rejects(
      () => call(adapter, 'missing.tool', {}),
      (error) => error instanceof ConsumerContractError && error.code === 'tool_not_allowed',
    )
    await assert.rejects(
      () => call(adapter, 'brain.projection.read', { projectionRef: '' }),
      (error) => error instanceof ConsumerContractError && error.code === 'tool_input_invalid',
    )
  }
})

test('timeouts and provider failures are bounded and redacted', async () => {
  const adapter = createCursorAdapter({
    application: 'cursor',
    profile: 'canary',
    timeoutMs: 5,
    clients: providerClients({
      brain: {
        read: async () => new Promise(() => {}),
      },
      platform: {
        resolveIdentity: async () => {
          throw new Error('token=ltfx.adapter_token.v1')
        },
      },
    }),
  })

  await assert.rejects(
    () => call(adapter, 'brain.projection.read', { projectionRef: 'projection-1' }),
    (error) => error instanceof ConsumerContractError
      && error.code === 'tool_timeout'
      && error.details.application === 'cursor',
  )
  await assert.rejects(
    () => call(adapter, 'platform.identity.resolve', {}),
    (error) => error instanceof ConsumerContractError
      && error.code === 'adapter_tool_failed'
      && !JSON.stringify(error.details).includes('do-not-leak'),
  )
})
