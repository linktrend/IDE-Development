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

test('validator has no Brain call, tool execution, transport, or credential APIs', () => {
  assert.doesNotMatch(MODULE_SOURCE, /\b(fetch|XMLHttpRequest|createServer|net\.connect)\b/)
  assert.doesNotMatch(MODULE_SOURCE, /from ['"]node:(http|https|net|child_process|tls)['"]/)
  assert.doesNotMatch(MODULE_SOURCE, /\b(mintIdentity|storeSecret|copyTranscript)\b/)
  assert.doesNotMatch(MODULE_SOURCE, /from ['"].*LiNKbrain/)
  assert.doesNotMatch(MODULE_SOURCE, /\bskills_run_\w+\s*\(/)
  assert.equal(typeof validateBrainProjection, 'function')
  assert.equal(existsSync(join(ROOT, '.ide-development')), false)
})
