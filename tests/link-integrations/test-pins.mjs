import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
import { dirname, join } from 'node:path'
import { fileURLToPath } from 'node:url'
import { test } from 'node:test'
import { ConsumerContractError, fail } from '../../core/link-integrations/errors.mjs'
import {
  FROZEN_PROVIDER_KEYS,
  FROZEN_PROVIDERS,
  PIN_AUTHORITY,
} from '../../core/link-integrations/pins.mjs'

const GIT_SHA = /^[a-f0-9]{40}$/
const HERE = dirname(fileURLToPath(import.meta.url))
const PINS_SOURCE = readFileSync(join(HERE, '../../core/link-integrations/pins.mjs'), 'utf8')
const ERRORS_SOURCE = readFileSync(join(HERE, '../../core/link-integrations/errors.mjs'), 'utf8')

/** Issue 244 table — refuse-only; not consumer pins. */
const ISSUE_244_OBSOLETE_PINS = Object.freeze({
  platform: Object.freeze({
    commit: '6a7114674c23fc6b9ba9ae2b3277b8aec7a3fb15',
    tree: '91d565a988150da39a13b66c4bcd51f7bc47c9be',
  }),
  libraries: Object.freeze({
    commit: 'b2d2bbb035c6e6a3f859480ce57f12e0882dd3f0',
    tree: '2701e6a190468f437102946425a64e890eed6690',
  }),
  brain: Object.freeze({
    commit: '43887ffc3b51ef2e54c30820d41cab67f54d5d0f',
    tree: '40c7acfcd7b204f19a1278e6801033c4ee64b369',
  }),
  skills: Object.freeze({
    commit: '93ec4b9df2ebe2a9d9b412fb8b3bcde2aa8e97f3',
    tree: '1845b996a7ec4d217a57e6f66574d6c5d676bb67',
  }),
  autowork: Object.freeze({
    commit: '10f75a8d840160a10d131371e94a338dfd1ebb4a',
    tree: 'c433907818f2cd4adbfdd61549f9f91396e31819',
  }),
})

const EXPECTED_REPOSITORIES = Object.freeze({
  platform: 'linktrend/LiNKplatform',
  libraries: 'linktrend/LiNKlibraries',
  brain: 'linktrend/LiNKbrain',
  skills: 'linktrend/LiNKskills',
  autowork: 'linktrend/LiNKautowork',
})

test('exports exactly five frozen provider pins', () => {
  assert.deepEqual([...FROZEN_PROVIDER_KEYS], ['platform', 'libraries', 'brain', 'skills', 'autowork'])
  assert.deepEqual(Object.keys(FROZEN_PROVIDERS).sort(), [...FROZEN_PROVIDER_KEYS].sort())
  assert.equal(Object.keys(FROZEN_PROVIDERS).length, 5)
  assert.ok(Object.isFrozen(FROZEN_PROVIDERS))
  assert.ok(Object.isFrozen(FROZEN_PROVIDER_KEYS))
  assert.ok(Object.isFrozen(PIN_AUTHORITY))
})

test('each pin records repository, commit, and tree from GitHub development', () => {
  for (const key of FROZEN_PROVIDER_KEYS) {
    const frozen = FROZEN_PROVIDERS[key]
    assert.ok(Object.isFrozen(frozen), `${key} pin must be frozen`)
    assert.deepEqual(Object.keys(frozen).sort(), ['commit', 'repository', 'tree'])
    assert.equal(frozen.repository, EXPECTED_REPOSITORIES[key])
    assert.match(frozen.commit, GIT_SHA, `${key} commit`)
    assert.match(frozen.tree, GIT_SHA, `${key} tree`)
  }
})

test('pins object is frozen against mutation', () => {
  assert.throws(() => {
    FROZEN_PROVIDERS.extra = { repository: 'linktrend/x', commit: 'a'.repeat(40), tree: 'b'.repeat(40) }
  }, TypeError)
  assert.throws(() => {
    FROZEN_PROVIDERS.platform.commit = 'c'.repeat(40)
  }, TypeError)
  assert.throws(() => {
    PIN_AUTHORITY.siblingCheckoutHeadsAreNotPins = false
  }, TypeError)
})

test('refuses Issue 244 pin SHAs', () => {
  for (const key of FROZEN_PROVIDER_KEYS) {
    const current = FROZEN_PROVIDERS[key]
    const obsolete = ISSUE_244_OBSOLETE_PINS[key]
    assert.notEqual(current.commit, obsolete.commit, `${key} commit must not be Issue 244`)
    assert.notEqual(current.tree, obsolete.tree, `${key} tree must not be Issue 244`)
    assert.equal(PINS_SOURCE.includes(obsolete.commit), false, `pins.mjs must not contain Issue 244 ${key} commit`)
    assert.equal(PINS_SOURCE.includes(obsolete.tree), false, `pins.mjs must not contain Issue 244 ${key} tree`)
  }
})

test('sibling checkout HEADs are not pins', () => {
  assert.equal(PIN_AUTHORITY.source, 'github_development_tip')
  assert.equal(PIN_AUTHORITY.ref, 'development')
  assert.equal(PIN_AUTHORITY.siblingCheckoutHeadsAreNotPins, true)
  assert.match(PINS_SOURCE, /sibling checkout HEADs are not pins/i)
})

test('ConsumerContractError exposes a stable non-writable code', () => {
  const error = new ConsumerContractError('stale_pin', 'pin is stale', { provider: 'platform' })
  assert.ok(error instanceof Error)
  assert.ok(error instanceof ConsumerContractError)
  assert.equal(error.name, 'ConsumerContractError')
  assert.equal(error.code, 'stale_pin')
  assert.equal(error.message, 'pin is stale')
  assert.deepEqual(error.details, { provider: 'platform' })
  assert.throws(() => {
    error.code = 'mutated'
  }, TypeError)
  assert.equal(error.code, 'stale_pin')
  const again = new ConsumerContractError('stale_pin')
  assert.equal(again.code, error.code)
  assert.throws(() => new ConsumerContractError(''), TypeError)
  assert.throws(() => fail('denied', 'not permitted'), (thrown) => {
    return thrown instanceof ConsumerContractError && thrown.code === 'denied'
  })
})

test('skeleton has no transport, credentials, Git write, Ledger, or Gate mutation APIs', () => {
  for (const [label, source] of [['pins.mjs', PINS_SOURCE], ['errors.mjs', ERRORS_SOURCE]]) {
    assert.equal(/\bimport\b/.test(source), false, `${label} must not import APIs`)
    assert.doesNotMatch(source, /\b(fetch|XMLHttpRequest|createServer|net\.connect)\b/, `${label} transport`)
    assert.doesNotMatch(source, /from ['"]node:(http|https|net|child_process|tls)['"]/, `${label} node transport`)
    assert.doesNotMatch(source, /\b(git push|git commit|spawnSync|execFileSync)\b/, `${label} git/process write`)
    assert.doesNotMatch(source, /\b(mutateLedger|closeGate|openGate|mintIdentity|storeSecret)\b/, `${label} mutation`)
  }
  assert.equal(typeof FROZEN_PROVIDERS, 'object')
  assert.equal(typeof ConsumerContractError, 'function')
  assert.equal(FROZEN_PROVIDERS.fetch, undefined)
  assert.equal(FROZEN_PROVIDERS.request, undefined)
  assert.equal(FROZEN_PROVIDERS.connect, undefined)
})
