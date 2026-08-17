import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
import { dirname, join } from 'node:path'
import { fileURLToPath } from 'node:url'
import { test } from 'node:test'
import { ConsumerContractError } from '../../core/link-integrations/errors.mjs'
import { FROZEN_PROVIDERS } from '../../core/link-integrations/pins.mjs'
import {
  PLATFORM_AUTH_CLAIMS_CONTRACT_VERSION,
  PLATFORM_PIN,
  validatePlatformIdentity,
} from '../../core/link-integrations/platform.mjs'

const HERE = dirname(fileURLToPath(import.meta.url))
const FIXTURES = join(HERE, 'fixtures/platform')
const MODULE_SOURCE = readFileSync(join(HERE, '../../core/link-integrations/platform.mjs'), 'utf8')

function load(name) {
  return JSON.parse(readFileSync(join(FIXTURES, name), 'utf8'))
}

function throws(fn, code) {
  assert.throws(fn, (error) => error instanceof ConsumerContractError && error.code === code)
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

test('AC-I6-POS-platform: accepts AuthClaims 1.1.0 with matching context', () => {
  const fixture = load('positive-valid.json')
  const accepted = validatePlatformIdentity(fixture.claim, fixture.context)
  assert.deepEqual(accepted, {
    actorId: 'actor-ide-dev-s1',
    runtimeBindingId: 'bind-ide-dev-s1',
    orgId: 'org-synthetic-s1',
  })
  assert.ok(Object.isFrozen(accepted))
  assert.throws(() => {
    accepted.actorId = 'mutated'
  }, TypeError)
  assert.equal(PLATFORM_AUTH_CLAIMS_CONTRACT_VERSION, 'platform.auth-claims/1.1.0')
  assert.equal(PLATFORM_PIN.commit, FROZEN_PROVIDERS.platform.commit)
  assert.equal(PLATFORM_PIN.tree, FROZEN_PROVIDERS.platform.tree)
})

test('AC-I6-DEN-platform: denies missing capability, wrong audience, wrong org, wrong service, illegal actor combination, and binding mismatch', () => {
  classify(
    () => {
      const fixture = load('denied-missing-capability.json')
      validatePlatformIdentity(fixture.claim, fixture.context)
    },
    'capability_not_permitted',
    'denied',
  )
  classify(
    () => {
      const fixture = load('denied-wrong-audience.json')
      validatePlatformIdentity(fixture.claim, fixture.context)
    },
    'wrong_audience',
    'denied',
  )
  classify(
    () => {
      const fixture = load('denied-wrong-org.json')
      validatePlatformIdentity(fixture.claim, fixture.context)
    },
    'wrong_org',
    'denied',
  )
  classify(
    () => {
      const fixture = load('positive-valid.json')
      validatePlatformIdentity(fixture.claim, { ...fixture.context, requiredService: 'lbrain' })
    },
    'wrong_service',
    'denied',
  )
  classify(
    () => {
      const fixture = load('denied-illegal-actor-combination.json')
      validatePlatformIdentity(fixture.claim, fixture.context)
    },
    'illegal_actor_combination',
    'denied',
  )
  classify(
    () => {
      const fixture = load('denied-wrong-binding.json')
      validatePlatformIdentity(fixture.claim, fixture.context)
    },
    'wrong_binding',
    'denied',
  )
})

test('AC-I6-DEN-platform: orgId null is denied for non-service actorKind', () => {
  const fixture = load('positive-valid.json')
  classify(
    () => validatePlatformIdentity({ ...fixture.claim, orgId: null, actorKind: 'adapter' }, fixture.context),
    'illegal_actor_combination',
    'denied',
  )
})

test('AC-I6-UNA-platform: missing claim material or unavailable identity service is not success', () => {
  classify(
    () => {
      const fixture = load('unavailable-missing-claim.json')
      validatePlatformIdentity(fixture.claim, fixture.context)
    },
    'identity_unavailable',
    'unavailable',
  )
  classify(
    () => {
      const fixture = load('unavailable-identity-service.json')
      validatePlatformIdentity(fixture.claim, fixture.context)
    },
    'identity_unavailable',
    'unavailable',
  )
  const positive = load('positive-valid.json')
  classify(
    () => validatePlatformIdentity({ ...positive.claim, actorId: '' }, positive.context),
    'identity_unavailable',
    'unavailable',
  )
})

test('AC-I6-FC-platform: expired, unknown field, sensitive key, wrong version, and non-object fail closed', () => {
  classify(
    () => {
      const fixture = load('failclosed-expired.json')
      validatePlatformIdentity(fixture.claim, fixture.context)
    },
    'expired',
    'fail_closed',
  )
  const positive = load('positive-valid.json')
  classify(
    () => validatePlatformIdentity({ ...positive.claim, extraField: 'no' }, positive.context),
    'unknown_field',
    'fail_closed',
  )
  classify(
    () => validatePlatformIdentity({ ...positive.claim, secret: 'redacted' }, positive.context),
    'sensitive_field',
    'fail_closed',
  )
  classify(
    () => validatePlatformIdentity(
      { ...positive.claim, claimContractVersion: 'platform.auth-claims/1.0.0' },
      positive.context,
    ),
    'wrong_claim_contract_version',
    'fail_closed',
  )
  classify(() => validatePlatformIdentity([], positive.context), 'invalid_object', 'fail_closed')
  classify(() => validatePlatformIdentity('claim', positive.context), 'invalid_object', 'fail_closed')
})

test('AC-I6-FC-platform: disabled identity service and incompatible pin fail closed', () => {
  classify(
    () => {
      const fixture = load('failclosed-disabled-identity.json')
      validatePlatformIdentity(fixture.claim, fixture.context)
    },
    'identity_disabled',
    'fail_closed',
  )
  classify(
    () => {
      const fixture = load('failclosed-incompatible-pin.json')
      validatePlatformIdentity(fixture.claim, fixture.context)
    },
    'incompatible_pin',
    'fail_closed',
  )
  const positive = load('positive-valid.json')
  classify(
    () => validatePlatformIdentity(
      { ...positive.claim, claims: { nested: true } },
      positive.context,
    ),
    'competing_envelope',
    'fail_closed',
  )
})

test('validator has no transport, mint, signing-key, or credential store APIs', () => {
  assert.doesNotMatch(MODULE_SOURCE, /\b(fetch|XMLHttpRequest|createServer|net\.connect)\b/)
  assert.doesNotMatch(MODULE_SOURCE, /from ['"]node:(http|https|net|child_process|tls|crypto)['"]/)
  assert.doesNotMatch(MODULE_SOURCE, /\b(jose|jsonwebtoken|mintJwt|mintIdentity|storeSecret|signClaim)\b/)
  assert.doesNotMatch(MODULE_SOURCE, /\b(privateKey|signingKey|apiKey|serviceRole)\b/)
  assert.equal(typeof validatePlatformIdentity, 'function')
  throws(() => validatePlatformIdentity(null, null), 'invalid_context')
})
