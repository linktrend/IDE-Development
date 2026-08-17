import assert from 'node:assert/strict'
import { existsSync, readFileSync } from 'node:fs'
import { dirname, join } from 'node:path'
import { fileURLToPath } from 'node:url'
import { test } from 'node:test'
import { ConsumerContractError } from '../../core/link-integrations/errors.mjs'
import { FROZEN_PROVIDERS } from '../../core/link-integrations/pins.mjs'
import {
  AUTOWORK_AUDIENCE,
  AUTOWORK_CONTRACT_VERSION,
  AUTOWORK_EXECUTION_AUTHORITY,
  AUTOWORK_PIN,
  autoworkRequestFingerprint,
  validateAutoworkCallback,
  validateAutoworkHandoff,
  validateAutoworkReceipt,
  validateAutoworkRequest,
  validateAutoworkStatus,
} from '../../core/link-integrations/autowork.mjs'

const HERE = dirname(fileURLToPath(import.meta.url))
const ROOT = join(HERE, '../..')
const FIXTURES = join(HERE, 'fixtures/autowork')
const SOURCE = readFileSync(join(HERE, '../../core/link-integrations/autowork.mjs'), 'utf8')
const MANIFEST_SOURCE = readFileSync(join(HERE, '../../core/managed-core/MANIFEST.json'), 'utf8')
const NOW = Date.parse('2026-08-17T12:00:00.000Z')

const load = (name) => JSON.parse(readFileSync(join(FIXTURES, name), 'utf8'))
const clone = (value) => structuredClone(value)
const throws = (fn, code) => assert.throws(fn, (error) => error instanceof ConsumerContractError && error.code === code)
const classify = (fn, code, classification) => {
  try {
    fn()
    assert.fail(`expected ${code}`)
  } catch (error) {
    assert.ok(error instanceof ConsumerContractError)
    assert.equal(error.code, code)
    assert.equal(error.details.classification, classification)
  }
}

const requestFixture = () => load('positive-accepted-request.json')
const boundReceipt = (name, request = requestFixture()) => {
  const receipt = load(name)
  receipt.request_fingerprint = autoworkRequestFingerprint(request)
  return receipt
}
const boundCallback = (request = requestFixture()) => {
  const callback = load('positive-succeeded-callback.json')
  callback.receipt.request_fingerprint = autoworkRequestFingerprint(request)
  return callback
}

test('AC-I6-POS-autowork: pin-time contract identity is 2026-08-13.v1 with exact lautowork audience', () => {
  assert.equal(AUTOWORK_CONTRACT_VERSION, '2026-08-13.v1')
  assert.equal(AUTOWORK_AUDIENCE, 'lautowork')
  assert.equal(AUTOWORK_EXECUTION_AUTHORITY, 'none')
  assert.equal(AUTOWORK_PIN, FROZEN_PROVIDERS.autowork)
  assert.equal(AUTOWORK_PIN.repository, 'linktrend/LiNKautowork')
  assert.equal(AUTOWORK_PIN.commit, '9caab9aa33de5f96e33d67d880f2934dc6fd9fef')
  assert.equal(AUTOWORK_PIN.tree, '5f306d674780a5a26048017f916da6048d71e7a5')
  assert.notEqual(AUTOWORK_PIN.commit, '10f75a8d840160a10d131371e94a338dfd1ebb4a')
  assert.equal(SOURCE.includes('provider-contract/v1'), false)
  assert.equal(SOURCE.includes('10f75a8d840160a10d131371e94a338dfd1ebb4a'), false)
})

test('AC-I6-POS-autowork: accepted request and succeeded receipt return frozen bounded objects', () => {
  const request = validateAutoworkRequest(requestFixture(), { now: NOW, providerPin: AUTOWORK_PIN })
  assert.ok(Object.isFrozen(request))
  assert.equal(request.requestId, '00000000-0000-4000-8000-000000000010')
  assert.equal(request.idempotencyKey, 'autowork-idempotency-0001')
  assert.equal(request.audience, 'lautowork')
  assert.equal(request.version, '1.0.0')
  assert.equal(request.executionAuthority, 'none')
  assert.equal(request.pin, AUTOWORK_PIN)
  assert.match(request.fingerprint, /^sha256:[a-f0-9]{64}$/)
  assert.equal(autoworkRequestFingerprint(requestFixture()), request.fingerprint)

  const status = validateAutoworkStatus(load('positive-accepted-status.json'))
  assert.ok(Object.isFrozen(status))
  assert.equal(status.status, 'accepted')
  assert.equal(status.requestId, request.requestId)
  assert.equal(status.executionAuthority, 'none')

  const handoff = validateAutoworkHandoff(load('valid-handoff.json'))
  assert.ok(Object.isFrozen(handoff))
  assert.equal(handoff.handoffRef, 'brain://handoff/exact-precheck')

  const receipt = validateAutoworkReceipt(boundReceipt('positive-succeeded-receipt.json'), {
    request: requestFixture(),
    fingerprint: request.fingerprint,
    now: NOW,
  })
  assert.ok(Object.isFrozen(receipt))
  assert.equal(receipt.status, 'succeeded')
  assert.equal(receipt.requestId, request.requestId)
  assert.equal(receipt.fingerprint, request.fingerprint)
  assert.equal(receipt.executionAuthority, 'none')
  assert.notEqual(receipt.status, 'completed')

  const callback = validateAutoworkCallback(boundCallback(), {
    request: requestFixture(),
    fingerprint: request.fingerprint,
    now: NOW,
  })
  assert.ok(Object.isFrozen(callback))
  assert.equal(callback.status, 'succeeded')
  assert.equal(callback.requestId, request.requestId)
})

test('AC-I6-DEN-autowork: wrong audience and policy-failed receipts are not coerced to success', () => {
  const wrongAudience = requestFixture()
  wrongAudience.platform = { ...wrongAudience.platform, audience: 'wrong-audience' }
  classify(() => validateAutoworkRequest(wrongAudience, { now: NOW }), 'autowork_audience_denied', 'denied')

  const failed = validateAutoworkReceipt(boundReceipt('denied-failed-policy-receipt.json'), {
    request: requestFixture(),
    fingerprint: autoworkRequestFingerprint(requestFixture()),
    now: NOW,
  })
  assert.equal(failed.status, 'failed')
  assert.notEqual(failed.status, 'succeeded')
  assert.notEqual(failed.status, 'accepted')
  assert.notEqual(failed.status, 'completed')
})

test('AC-I6-DEN-autowork: authority, revoked identity, and denied work kinds are rejected', () => {
  classify(
    () => validateAutoworkRequest({ ...requestFixture(), authority: 'execute' }, { now: NOW }),
    'autowork_authority_denied',
    'denied',
  )
  classify(
    () => validateAutoworkRequest({ ...requestFixture(), internal: true }, { now: NOW }),
    'autowork_internal_mutation',
    'denied',
  )
  classify(() => validateAutoworkReceipt({
    ...boundReceipt('positive-succeeded-receipt.json'),
    ledger: 'mutate',
  }, {
    request: requestFixture(),
    fingerprint: autoworkRequestFingerprint(requestFixture()),
    now: NOW,
  }), 'autowork_authority_denied', 'denied')
  const revoked = requestFixture()
  revoked.platform = { ...revoked.platform, revocation_ref: 'platform://revocations/revoked' }
  classify(() => validateAutoworkRequest(revoked, { now: NOW }), 'autowork_identity_revoked', 'denied')
  classify(
    () => validateAutoworkRequest({ ...requestFixture(), operation_kind: 'order_placement' }, { now: NOW }),
    'autowork_work_kind_denied',
    'denied',
  )
  classify(
    () => validateAutoworkRequest({ ...requestFixture(), operation_kind: 'execute' }, { now: NOW }),
    'autowork_work_kind_denied',
    'denied',
  )
})

test('external assistance without an opaque Brain handoff fails closed', () => {
  throws(() => validateAutoworkRequest({ ...requestFixture(), operation_kind: 'external_assistance' }, { now: NOW }), 'autowork_handoff_invalid')
})

test('AC-I6-UNA-autowork: unavailable is preserved as unavailable and is not success', () => {
  const unavailable = validateAutoworkStatus(load('unavailable-status.json'))
  assert.equal(unavailable.status, 'unavailable')
  assert.notEqual(unavailable.status, 'accepted')
  assert.notEqual(unavailable.status, 'succeeded')

  const unavailableReceipt = validateAutoworkReceipt({
    ...boundReceipt('positive-succeeded-receipt.json'),
    state: 'unavailable',
    result_refs: [],
  }, {
    request: requestFixture(),
    fingerprint: autoworkRequestFingerprint(requestFixture()),
    now: NOW,
  })
  assert.equal(unavailableReceipt.status, 'unavailable')
  assert.notEqual(unavailableReceipt.status, 'succeeded')

  const incompatible = validateAutoworkStatus({
    ...load('unavailable-status.json'),
    state: 'contract_incompatible',
  })
  assert.equal(incompatible.status, 'contract_incompatible')
  assert.notEqual(incompatible.status, 'succeeded')
})

test('AC-I6-FC-autowork: malformed, unknown, sensitive, and accessor fields fail closed', () => {
  classify(() => validateAutoworkRequest(null, { now: NOW }), 'invalid_object', 'fail_closed')
  classify(() => validateAutoworkRequest({ ...requestFixture(), extra: true }, { now: NOW }), 'unknown_field', 'fail_closed')
  classify(
    () => validateAutoworkRequest({ ...requestFixture(), contract_version: 'legacy-receipt-v1' }, { now: NOW }),
    'autowork_contract_incompatible',
    'fail_closed',
  )
  classify(
    () => validateAutoworkRequest({ ...requestFixture(), request_id: 'opaque:request-1' }, { now: NOW }),
    'autowork_id_malformed',
    'fail_closed',
  )
  classify(
    () => validateAutoworkRequest({
      ...requestFixture(),
      automation: { ...requestFixture().automation, version: 'latest' },
    }, { now: NOW }),
    'autowork_request_invalid',
    'fail_closed',
  )
  classify(() => validateAutoworkReceipt({
    ...boundReceipt('positive-succeeded-receipt.json'),
    result_refs: [{
      ref: 'autowork://results/one',
      digest: `sha256:${'d'.repeat(64)}`,
      classification: 'internal',
      secret: 'x',
    }],
  }, {
    request: requestFixture(),
    fingerprint: autoworkRequestFingerprint(requestFixture()),
    now: NOW,
  }), 'sensitive_field', 'fail_closed')
  classify(
    () => validateAutoworkStatus({ ...load('positive-accepted-status.json'), input_ref: { ref: 'ide://inputs/status' } }),
    'accessor_field',
    'fail_closed',
  )
  classify(
    () => validateAutoworkStatus({ ...load('positive-accepted-status.json'), accessor: 'payload' }),
    'accessor_field',
    'fail_closed',
  )
  classify(
    () => validateAutoworkStatus({ ...load('positive-accepted-status.json'), state: 'completed' }),
    'autowork_status_invalid',
    'fail_closed',
  )
  classify(
    () => validateAutoworkHandoff({ ...load('valid-handoff.json'), prompt: 'raw' }),
    'sensitive_field',
    'fail_closed',
  )
  classify(
    () => validateAutoworkHandoff({
      ref: 'not-opaque',
      digest: `sha256:${'a'.repeat(64)}`,
      observed_at: '2026-08-17T00:00:00.000Z',
    }),
    'autowork_handoff_invalid',
    'fail_closed',
  )
  classify(
    () => validateAutoworkRequest({ ...requestFixture(), private_payload: 'hidden' }, { now: NOW }),
    'sensitive_field',
    'fail_closed',
  )
})

test('AC-I6-FC-autowork: pin mismatch, expiry, replay, and monotonic regression fail closed', () => {
  classify(() => validateAutoworkRequest(requestFixture(), {
    now: NOW,
    providerPin: {
      repository: 'linktrend/LiNKautowork',
      commit: '10f75a8d840160a10d131371e94a338dfd1ebb4a',
      tree: 'c433907818f2cd4adbfdd61549f9f91396e31819',
    },
  }), 'incompatible_pin', 'fail_closed')
  classify(() => validateAutoworkRequest(requestFixture(), { now: Date.parse('2028-01-01T00:00:00.000Z') }), 'expired', 'fail_closed')
  classify(() => validateAutoworkReceipt({
    ...boundReceipt('positive-succeeded-receipt.json'),
    freshness_at: '2026-08-17T00:00:00.000Z',
  }, {
    request: requestFixture(),
    fingerprint: autoworkRequestFingerprint(requestFixture()),
    now: NOW,
  }), 'expired', 'fail_closed')
  const stale = boundReceipt('positive-succeeded-receipt.json')
  delete stale.freshness_at
  classify(() => validateAutoworkReceipt(stale, {
    request: requestFixture(),
    fingerprint: autoworkRequestFingerprint(requestFixture()),
    now: NOW,
  }), 'expired', 'fail_closed')
  classify(
    () => validateAutoworkStatus(load('positive-accepted-status.json'), { previousStatus: 'succeeded' }),
    'autowork_terminal_regression',
    'fail_closed',
  )
  classify(
    () => validateAutoworkStatus(load('positive-accepted-status.json'), { previousStatus: 'unavailable' }),
    'autowork_terminal_regression',
    'fail_closed',
  )
  classify(() => validateAutoworkStatus(load('positive-accepted-status.json'), {
    previousStatus: { state: 'running', attempt_count: 3 },
  }), 'autowork_terminal_regression', 'fail_closed')
  classify(() => validateAutoworkReceipt(boundReceipt('positive-succeeded-receipt.json'), {
    request: requestFixture(),
    fingerprint: `sha256:${'e'.repeat(64)}`,
    now: NOW,
  }), 'autowork_fingerprint_conflict', 'fail_closed')
  const unbound = boundReceipt('positive-succeeded-receipt.json')
  unbound.request_id = '00000000-0000-4000-8000-000000000099'
  classify(() => validateAutoworkReceipt(unbound, {
    request: requestFixture(),
    fingerprint: autoworkRequestFingerprint(requestFixture()),
    now: NOW,
  }), 'autowork_receipt_unbound', 'fail_closed')
  classify(() => validateAutoworkRequest(requestFixture(), {
    now: NOW,
    priorFingerprint: `sha256:${'f'.repeat(64)}`,
  }), 'autowork_fingerprint_conflict', 'fail_closed')
  const laterCallback = boundCallback()
  laterCallback.source_timestamp = '2026-08-16T00:00:00.000Z'
  classify(() => validateAutoworkCallback(laterCallback, {
    request: requestFixture(),
    fingerprint: autoworkRequestFingerprint(requestFixture()),
    now: NOW,
    previous: boundCallback(),
  }), 'autowork_terminal_regression', 'fail_closed')
  const replayed = boundCallback()
  replayed.receipt = { ...replayed.receipt, state: 'accepted', result_refs: [] }
  classify(() => validateAutoworkCallback(replayed, {
    request: requestFixture(),
    fingerprint: autoworkRequestFingerprint(requestFixture()),
    now: NOW,
    previous: boundCallback(),
  }), 'autowork_terminal_regression', 'fail_closed')
})

test('idempotent validators return the same accept/reject code', () => {
  const first = validateAutoworkRequest(requestFixture(), { now: NOW })
  const second = validateAutoworkRequest(clone(requestFixture()), { now: NOW })
  assert.deepEqual(first, second)
  throws(() => validateAutoworkRequest({ ...requestFixture(), extra: 1 }, { now: NOW }), 'unknown_field')
  throws(() => validateAutoworkRequest({ ...requestFixture(), extra: 1 }, { now: NOW }), 'unknown_field')
})

test('consumer module has no transport, credentials, Git write, Ledger, or Gate mutation APIs', () => {
  assert.doesNotMatch(SOURCE, /\b(fetch|XMLHttpRequest|createServer|net\.connect)\b/)
  assert.doesNotMatch(SOURCE, /from ['"]node:(http|https|net|child_process|tls)['"]/)
  assert.doesNotMatch(SOURCE, /\b(git push|git commit|spawnSync|execFileSync)\b/)
  assert.doesNotMatch(SOURCE, /\b(mutateLedger|closeGate|openGate|mintIdentity|storeSecret)\b/)
  assert.equal(typeof validateAutoworkRequest, 'function')
  assert.equal(validateAutoworkRequest.fetch, undefined)
})

test('S0 pins remain frozen and MANIFEST is not a pre-rollout write', () => {
  assert.equal(FROZEN_PROVIDERS.autowork.repository, 'linktrend/LiNKautowork')
  assert.equal(FROZEN_PROVIDERS.autowork.commit, '9caab9aa33de5f96e33d67d880f2934dc6fd9fef')
  assert.equal(FROZEN_PROVIDERS.autowork.tree, '5f306d674780a5a26048017f916da6048d71e7a5')
  assert.equal(MANIFEST_SOURCE.includes('core/link-integrations/autowork.mjs'), false)
  assert.equal(MANIFEST_SOURCE.includes('.ide-development/providers/'), false)
  assert.equal(existsSync(join(ROOT, '.ide-development')), false)
})
