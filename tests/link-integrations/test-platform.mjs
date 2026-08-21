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

test('AC-I6-FC-platform: orgId null plus non-service is a fail-closed shape error', () => {
  const fixture = load('positive-valid.json')
  classify(
    () => validatePlatformIdentity({ ...fixture.claim, orgId: null, actorKind: 'adapter' }, fixture.context),
    'auth_claims_shape_invalid',
    'fail_closed',
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
    () => validatePlatformIdentity({ ...positive.claim, secret: 'ltfx.redacted.v1' }, positive.context),
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

test('AC-I6-FC-platform: inherited prototype properties fail closed', () => {
  const positive = load('positive-valid.json')
  const inheritedExtra = Object.assign(Object.create({ extraField: 'from-prototype' }), positive.claim)
  classify(
    () => validatePlatformIdentity(inheritedExtra, positive.context),
    'inherited_property',
    'fail_closed',
  )
  const { actorId, ...ownWithoutActor } = positive.claim
  const inheritedMaterial = Object.assign(Object.create({ actorId }), ownWithoutActor)
  classify(
    () => validatePlatformIdentity(inheritedMaterial, positive.context),
    'inherited_property',
    'fail_closed',
  )
})

test('AC-I6-FC-platform: accessor getter and setter inputs fail closed', () => {
  const positive = load('positive-valid.json')
  const getterClaim = { ...positive.claim }
  let reads = 0
  Object.defineProperty(getterClaim, 'actorId', {
    enumerable: true,
    configurable: true,
    get() {
      reads += 1
      return reads === 1 ? 'actor-ide-dev-s1' : 'mutated-after-read'
    },
  })
  classify(
    () => validatePlatformIdentity(getterClaim, positive.context),
    'accessor_property',
    'fail_closed',
  )
  const setterClaim = { ...positive.claim }
  Object.defineProperty(setterClaim, 'trap', {
    enumerable: true,
    configurable: true,
    set() {},
  })
  classify(
    () => validatePlatformIdentity(setterClaim, positive.context),
    'accessor_property',
    'fail_closed',
  )
})

test('AC-I6-FC-platform: unknown or sensitive fields fail closed before missing-material unavailable', () => {
  const positive = load('positive-valid.json')
  classify(
    () => validatePlatformIdentity({ ...positive.claim, actorId: '', secret: 'ltfx.redacted.v1' }, positive.context),
    'sensitive_field',
    'fail_closed',
  )
  classify(
    () => validatePlatformIdentity(
      { ...positive.claim, runtimeBindingId: '', extraField: 'no' },
      positive.context,
    ),
    'unknown_field',
    'fail_closed',
  )
})

test('AC-I6-POS-platform: accepts full S0 platform pin repository, commit, and tree', () => {
  const fixture = load('positive-valid.json')
  const accepted = validatePlatformIdentity(fixture.claim, {
    ...fixture.context,
    providerPin: {
      repository: FROZEN_PROVIDERS.platform.repository,
      commit: FROZEN_PROVIDERS.platform.commit,
      tree: FROZEN_PROVIDERS.platform.tree,
    },
  })
  assert.deepEqual(accepted, {
    actorId: 'actor-ide-dev-s1',
    runtimeBindingId: 'bind-ide-dev-s1',
    orgId: 'org-synthetic-s1',
  })
  assert.ok(Object.isFrozen(accepted))
})

test('AC-I6-FC-platform: extra or confused providerPin keys fail closed', () => {
  const fixture = load('positive-valid.json')
  classify(
    () => validatePlatformIdentity(fixture.claim, {
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
    () => validatePlatformIdentity(fixture.claim, {
      ...fixture.context,
      providerPin: {
        ...fixture.context.providerPin,
        repo: FROZEN_PROVIDERS.platform.repository,
      },
    }),
    'unknown_field',
    'fail_closed',
  )
  classify(
    () => validatePlatformIdentity(fixture.claim, {
      ...fixture.context,
      providerPin: {
        repository: FROZEN_PROVIDERS.brain.repository,
        commit: FROZEN_PROVIDERS.platform.commit,
        tree: FROZEN_PROVIDERS.platform.tree,
      },
    }),
    'incompatible_pin',
    'fail_closed',
  )
})

test('AC-I6-FC-platform: non-string identity fields fail closed instead of unavailable', () => {
  const positive = load('positive-valid.json')
  classify(
    () => validatePlatformIdentity({ ...positive.claim, actorId: { extra: true } }, positive.context),
    'auth_claims_shape_invalid',
    'fail_closed',
  )
  classify(
    () => validatePlatformIdentity({ ...positive.claim, actorId: 123 }, positive.context),
    'auth_claims_shape_invalid',
    'fail_closed',
  )
  classify(
    () => validatePlatformIdentity(
      { ...positive.claim, runtimeBindingId: { id: 'bind-ide-dev-s1' } },
      positive.context,
    ),
    'auth_claims_shape_invalid',
    'fail_closed',
  )
})

test('AC-I6-FC-platform: nested array secrets fail closed before missing-material unavailable', () => {
  const positive = load('positive-valid.json')
  classify(
    () => validatePlatformIdentity(
      { ...positive.claim, actorId: '', serviceScopes: [{ secret: 'ltfx.redacted.v1' }] },
      positive.context,
    ),
    'sensitive_field',
    'fail_closed',
  )
})

test('AC-I6-FC-platform: claim poison fails closed before identity-service unavailable', () => {
  const positive = load('positive-valid.json')
  const unavailable = { ...positive.context, identityServiceStatus: 'unavailable' }
  classify(
    () => validatePlatformIdentity({ ...positive.claim, secret: 'ltfx.redacted.v1' }, unavailable),
    'sensitive_field',
    'fail_closed',
  )
  classify(
    () => validatePlatformIdentity({ ...positive.claim, extraField: 'no' }, unavailable),
    'unknown_field',
    'fail_closed',
  )
  const getterClaim = { ...positive.claim }
  Object.defineProperty(getterClaim, 'actorId', {
    enumerable: true,
    configurable: true,
    get() {
      return 'actor-ide-dev-s1'
    },
  })
  classify(
    () => validatePlatformIdentity(getterClaim, unavailable),
    'accessor_property',
    'fail_closed',
  )
})

test('AC-I6-FC-platform: enumerable symbol keys fail closed', () => {
  const positive = load('positive-valid.json')
  const secretSymbol = { ...positive.claim }
  Object.defineProperty(secretSymbol, Symbol('secret'), {
    enumerable: true,
    configurable: true,
    value: 'redacted',
  })
  classify(
    () => validatePlatformIdentity(secretSymbol, positive.context),
    'unknown_field',
    'fail_closed',
  )
  const extraSymbol = { ...positive.claim }
  Object.defineProperty(extraSymbol, Symbol('extraField'), {
    enumerable: true,
    configurable: true,
    value: 'no',
  })
  classify(
    () => validatePlatformIdentity(extraSymbol, positive.context),
    'unknown_field',
    'fail_closed',
  )
})

test('AC-I6-FC-platform: unknown credentialStatus and bindingState fail closed', () => {
  const positive = load('positive-valid.json')
  classify(
    () => validatePlatformIdentity(positive.claim, { ...positive.context, credentialStatus: 'pending' }),
    'incompatible_credential_status',
    'fail_closed',
  )
  classify(
    () => validatePlatformIdentity(positive.claim, { ...positive.context, bindingState: 'bogus' }),
    'incompatible_binding_state',
    'fail_closed',
  )
  classify(
    () => validatePlatformIdentity(positive.claim, { ...positive.context, bindingState: 'disabled' }),
    'incompatible_binding_state',
    'fail_closed',
  )
  classify(
    () => validatePlatformIdentity(positive.claim, { ...positive.context, bindingState: 'suspended' }),
    'inactive_binding',
    'fail_closed',
  )
})

test('AC-I6-FC-platform: payload_too_deep is classified fail_closed', () => {
  const positive = load('positive-valid.json')
  let nested = { secret: 'ltfx.redacted.v1' }
  for (let index = 0; index < 6; index += 1) {
    nested = { child: nested }
  }
  classify(
    () => validatePlatformIdentity({ ...positive.claim, extraDeep: nested }, positive.context),
    'payload_too_deep',
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
