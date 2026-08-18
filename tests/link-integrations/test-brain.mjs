import assert from 'node:assert/strict'
import { existsSync, readFileSync } from 'node:fs'
import { dirname, join } from 'node:path'
import { fileURLToPath } from 'node:url'
import { test } from 'node:test'
import { ConsumerContractError } from '../../core/link-integrations/errors.mjs'
import { FROZEN_PROVIDERS } from '../../core/link-integrations/pins.mjs'
import {
  BRAIN_CONTRACT_VERSION,
  BRAIN_PIN,
  validateBrainProjection,
} from '../../core/link-integrations/brain.mjs'

const HERE = dirname(fileURLToPath(import.meta.url))
const ROOT = join(HERE, '../..')
const FIXTURES = join(HERE, 'fixtures/brain')
const MODULE_SOURCE = readFileSync(join(HERE, '../../core/link-integrations/brain.mjs'), 'utf8')

function load(name) {
  return JSON.parse(readFileSync(join(FIXTURES, name), 'utf8'))
}

function classify(fn, code, classification) {
  try {
    fn()
    assert.fail(`expected ${code}`)
  } catch (error) {
    assert.ok(error instanceof ConsumerContractError)
    assert.equal(error.code, code)
    assert.equal(error.details.classification, classification)
  }
}

test('AC-I6-POS-brain: accepts advisory 2.0.0 projection with bounded summary', () => {
  const fixture = load('positive-valid.json')
  const accepted = validateBrainProjection(fixture.projection, fixture.context)
  assert.deepEqual(accepted, { projectionRef: 'projection-ide-dev-s3' })
  assert.equal(accepted.handoffRef, undefined)
  assert.ok(Object.isFrozen(accepted))
  assert.throws(() => {
    accepted.projectionRef = 'mutated'
  }, TypeError)
  assert.equal(BRAIN_CONTRACT_VERSION, '2.0.0')
  assert.equal(BRAIN_PIN.commit, FROZEN_PROVIDERS.brain.commit)
  assert.equal(BRAIN_PIN.tree, FROZEN_PROVIDERS.brain.tree)
})

test('AC-I6-POS-brain: accepts optional opaque handoff reference', () => {
  const fixture = load('positive-with-handoff.json')
  const accepted = validateBrainProjection(fixture.projection, fixture.context)
  assert.deepEqual(accepted, {
    projectionRef: 'projection-ide-dev-s3-handoff',
    handoffRef: 'handoff-ide-dev-s3',
  })
  assert.ok(Object.isFrozen(accepted))
})

test('AC-I6-DEN-brain: denies non-advisory authority and non-none execution authority', () => {
  classify(
    () => {
      const fixture = load('denied-authority-not-advisory.json')
      validateBrainProjection(fixture.projection, fixture.context)
    },
    'brain_authority_denied',
    'denied',
  )
  classify(
    () => {
      const fixture = load('denied-execution-authority.json')
      validateBrainProjection(fixture.projection, fixture.context)
    },
    'brain_execution_denied',
    'denied',
  )
})

test('AC-I6-UNA-brain: missing projectionRef or unavailable provider is not success', () => {
  classify(
    () => {
      const fixture = load('unavailable-missing-projection-ref.json')
      validateBrainProjection(fixture.projection, fixture.context)
    },
    'brain_projection_unavailable',
    'unavailable',
  )
  classify(
    () => {
      const fixture = load('unavailable-provider-status.json')
      validateBrainProjection(fixture.projection, fixture.context)
    },
    'brain_unavailable',
    'unavailable',
  )
  const positive = load('positive-valid.json')
  classify(
    () => validateBrainProjection({ ...positive.projection, projectionRef: '' }, positive.context),
    'brain_projection_unavailable',
    'unavailable',
  )
  classify(
    () => validateBrainProjection(null, positive.context),
    'brain_projection_unavailable',
    'unavailable',
  )
})

test('AC-I6-FC-brain: transcript, prompt, unknown field, and wrong version fail closed', () => {
  const positive = load('positive-valid.json')
  classify(
    () => validateBrainProjection({ ...positive.projection, transcript: 'no' }, positive.context),
    'sensitive_field',
    'fail_closed',
  )
  classify(
    () => validateBrainProjection({ ...positive.projection, prompt: 'no' }, positive.context),
    'sensitive_field',
    'fail_closed',
  )
  classify(
    () => validateBrainProjection({ ...positive.projection, extraField: 'no' }, positive.context),
    'unknown_field',
    'fail_closed',
  )
  classify(
    () => validateBrainProjection(
      { ...positive.projection, contractVersion: '1.0.0' },
      positive.context,
    ),
    'wrong_contract_version',
    'fail_closed',
  )
})

test('AC-I6-FC-brain: raw conversation, secrets, and execution/tool requests fail closed', () => {
  const positive = load('positive-valid.json')
  classify(
    () => validateBrainProjection({ ...positive.projection, conversation: 'no' }, positive.context),
    'sensitive_field',
    'fail_closed',
  )
  classify(
    () => validateBrainProjection({ ...positive.projection, secret: 'redacted' }, positive.context),
    'sensitive_field',
    'fail_closed',
  )
  classify(
    () => validateBrainProjection({ ...positive.projection, tools: ['search'] }, positive.context),
    'brain_execution_request',
    'fail_closed',
  )
  classify(
    () => validateBrainProjection({ ...positive.projection, execute: true }, positive.context),
    'brain_execution_request',
    'fail_closed',
  )
})

test('AC-I6-FC-brain: malformed identities, stale pin, and incompatible provider fail closed', () => {
  classify(
    () => {
      const fixture = load('failclosed-stale-pin.json')
      validateBrainProjection(fixture.projection, fixture.context)
    },
    'incompatible_pin',
    'fail_closed',
  )
  classify(
    () => {
      const fixture = load('failclosed-incompatible-provider.json')
      validateBrainProjection(fixture.projection, fixture.context)
    },
    'incompatible_provider_state',
    'fail_closed',
  )
  const positive = load('positive-valid.json')
  classify(
    () => validateBrainProjection(
      { ...positive.projection, projectionRef: 'not a valid ref' },
      positive.context,
    ),
    'brain_identity_invalid',
    'fail_closed',
  )
  classify(
    () => validateBrainProjection(
      { ...positive.projection, handoffRef: 'handoff with spaces' },
      positive.context,
    ),
    'brain_identity_invalid',
    'fail_closed',
  )
  classify(() => validateBrainProjection([], positive.context), 'invalid_object', 'fail_closed')
  classify(
    () => validateBrainProjection(
      { ...positive.projection, summary: 'x'.repeat(2001) },
      positive.context,
    ),
    'brain_summary_invalid',
    'fail_closed',
  )
})

test('AC-I6-FC-brain: inherited prototype properties fail closed', () => {
  const positive = load('positive-valid.json')
  const inheritedExtra = Object.assign(Object.create({ extraField: 'from-prototype' }), positive.projection)
  classify(
    () => validateBrainProjection(inheritedExtra, positive.context),
    'inherited_property',
    'fail_closed',
  )
  const { projectionRef, ...ownWithoutRef } = positive.projection
  const inheritedMaterial = Object.assign(Object.create({ projectionRef }), ownWithoutRef)
  classify(
    () => validateBrainProjection(inheritedMaterial, positive.context),
    'inherited_property',
    'fail_closed',
  )
})

test('AC-I6-FC-brain: accessor getter and setter inputs fail closed', () => {
  const positive = load('positive-valid.json')
  const getterProjection = { ...positive.projection }
  Object.defineProperty(getterProjection, 'projectionRef', {
    enumerable: true,
    configurable: true,
    get() {
      return 'projection-ide-dev-s3'
    },
  })
  classify(
    () => validateBrainProjection(getterProjection, positive.context),
    'accessor_property',
    'fail_closed',
  )
  const setterProjection = { ...positive.projection }
  Object.defineProperty(setterProjection, 'trap', {
    enumerable: true,
    configurable: true,
    set() {},
  })
  classify(
    () => validateBrainProjection(setterProjection, positive.context),
    'accessor_property',
    'fail_closed',
  )
})

test('AC-I6-FC-brain: TOCTOU getter that changes between reads fails closed', () => {
  const positive = load('positive-valid.json')
  const toctouProjection = { ...positive.projection }
  let reads = 0
  Object.defineProperty(toctouProjection, 'projectionRef', {
    enumerable: true,
    configurable: true,
    get() {
      reads += 1
      return reads === 1 ? 'projection-ide-dev-s3' : 'mutated-after-first-read'
    },
  })
  classify(
    () => validateBrainProjection(toctouProjection, positive.context),
    'accessor_property',
    'fail_closed',
  )
  assert.equal(reads, 0)
})

test('AC-I6-POS-brain: accepts full S0 Brain pin repository, commit, and tree', () => {
  const fixture = load('positive-full-s0-pin.json')
  const accepted = validateBrainProjection(fixture.projection, fixture.context)
  assert.deepEqual(accepted, { projectionRef: 'projection-ide-dev-s3-full-pin' })
  assert.ok(Object.isFrozen(accepted))
  assert.equal(fixture.context.providerPin.repository, FROZEN_PROVIDERS.brain.repository)
  assert.equal(fixture.context.providerPin.commit, FROZEN_PROVIDERS.brain.commit)
  assert.equal(fixture.context.providerPin.tree, FROZEN_PROVIDERS.brain.tree)
  const live = { ...fixture.projection }
  const fromOfficialPin = validateBrainProjection(live, {
    ...fixture.context,
    providerPin: FROZEN_PROVIDERS.brain,
  })
  live.projectionRef = 'mutated-after-validate'
  assert.deepEqual(fromOfficialPin, { projectionRef: 'projection-ide-dev-s3-full-pin' })
  assert.throws(() => {
    fromOfficialPin.projectionRef = 'mutated'
  }, TypeError)
})

test('AC-I6-FC-brain: extra or confused providerPin keys fail closed', () => {
  const fixture = load('positive-valid.json')
  classify(
    () => validateBrainProjection(fixture.projection, {
      ...fixture.context,
      providerPin: {
        ...fixture.context.providerPin,
        extra: 'no',
      },
    }),
    'unknown_field',
    'fail_closed',
  )
  classify(
    () => validateBrainProjection(fixture.projection, {
      ...fixture.context,
      providerPin: {
        ...fixture.context.providerPin,
        repo: FROZEN_PROVIDERS.brain.repository,
      },
    }),
    'unknown_field',
    'fail_closed',
  )
  classify(
    () => validateBrainProjection(fixture.projection, {
      ...fixture.context,
      providerPin: {
        repository: FROZEN_PROVIDERS.platform.repository,
        commit: FROZEN_PROVIDERS.brain.commit,
        tree: FROZEN_PROVIDERS.brain.tree,
      },
    }),
    'incompatible_pin',
    'fail_closed',
  )
})

test('validator has no Brain call, tool execution, transport, or credential APIs', () => {
  assert.doesNotMatch(MODULE_SOURCE, /\b(fetch|XMLHttpRequest|createServer|net\.connect)\b/)
  assert.doesNotMatch(MODULE_SOURCE, /from ['"]node:(http|https|net|child_process|tls)['"]/)
  assert.doesNotMatch(MODULE_SOURCE, /\b(mintIdentity|storeSecret|copyTranscript)\b/)
  assert.doesNotMatch(MODULE_SOURCE, /from ['"].*LiNKbrain/)
  assert.doesNotMatch(MODULE_SOURCE, /\bskills_run_\w+\s*\(/)
  assert.equal(typeof validateBrainProjection, 'function')
  assert.equal(existsSync(join(ROOT, '.ide-development')), false)
})
