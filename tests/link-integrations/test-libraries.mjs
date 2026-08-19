import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
import { dirname, join } from 'node:path'
import { fileURLToPath } from 'node:url'
import { test } from 'node:test'
import { ConsumerContractError } from '../../core/link-integrations/errors.mjs'
import { FROZEN_PROVIDERS } from '../../core/link-integrations/pins.mjs'
import { validateLibraryReference } from '../../core/link-integrations/libraries.mjs'

const HERE = dirname(fileURLToPath(import.meta.url))
const FIXTURES = join(HERE, 'fixtures/libraries')
const MODULE_SOURCE = readFileSync(join(HERE, '../../core/link-integrations/libraries.mjs'), 'utf8')

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
    return error
  }
}

test('AC-I6-POS-libraries: accepts a frozen verified_cache reference', () => {
  const facts = load('positive-verified-cache.json')
  const accepted = validateLibraryReference(facts)
  assert.equal(accepted.entryId, 'synthetic-component')
  assert.equal(accepted.version, '1.0.0')
  assert.equal(accepted.receiptType, 'verified_cache')
  assert.equal(accepted.lifecycle, 'selectable')
  assert.equal(accepted.selectability, 'selectable')
  assert.equal(accepted.compatibility, 'compatible')
  assert.equal(accepted.sourceCommitSha, FROZEN_PROVIDERS.libraries.commit)
  assert.equal(accepted.sourceTreeSha, FROZEN_PROVIDERS.libraries.tree)
  assert.equal(accepted.releaseSourceTreeSha, 'f8f20316b62492b9b1d0363f1c7983fc64de58ec')
  assert.equal(accepted.artifactTreeSha1, '2107a410b1308048a138f2dcb80c9cc7d8b7867a')
  assert.equal(accepted.catalogueSha256, 'ab9dde0af419613e4a5a091b13a207d973242ad0546240452b7eb2924b56f05a')
  assert.equal(accepted.catalogueRecordsSha256, '03b52875dd3c2fcf5c8fa056560fd77e0986aca04ba69bd11ebf28c866b97f2c')
  assert.equal(accepted.releaseManifestSha256, '6b9979777561d1771294ff4ddd10159b543c3b3cdd699c82ad759ab04ea67212')
  assert.ok(Object.isFrozen(accepted))
  assert.ok(Object.isFrozen(accepted.catalogueRecord))
  assert.throws(() => {
    accepted.entryId = 'mutated'
  }, TypeError)
  assert.throws(() => {
    accepted.catalogueRecord.entryId = 'mutated'
  }, TypeError)
})

test('AC-I6-POS-libraries: accepts a frozen admitted consumption receipt', () => {
  const facts = load('positive-consumption.json')
  const accepted = validateLibraryReference(facts)
  assert.equal(accepted.receiptType, 'consumption')
  assert.equal(accepted.receiptId, 'consumption-synthetic-component-1.0.0')
  assert.equal(accepted.lifecycle, 'admitted')
  assert.equal(accepted.selectability, 'selectable')
  assert.equal(accepted.catalogueSha256, facts.catalogueSha256)
  assert.ok(Object.isFrozen(accepted))
})

test('AC-I6-POS-libraries: identity, digests, and receipt are sufficient without policy fields', () => {
  const { lifecycle, selectability, compatibility, catalogueRecord, ...facts } = load('positive-verified-cache.json')
  assert.equal(lifecycle, 'selectable')
  assert.equal(selectability, 'selectable')
  assert.equal(compatibility, 'compatible')
  assert.equal(catalogueRecord.entryId, 'synthetic-component')
  const accepted = validateLibraryReference(facts)
  assert.equal(accepted.receiptType, 'verified_cache')
  assert.equal(accepted.lifecycle, undefined)
  assert.equal(accepted.catalogueSha256, facts.catalogueSha256)
})

test('AC-I6-DEN-libraries: denies quarantined, superseded, and non-selectable', () => {
  throws(() => validateLibraryReference(load('denied-quarantined.json')), 'library_not_selectable')
  throws(() => validateLibraryReference(load('denied-superseded.json')), 'library_not_selectable')
  throws(() => validateLibraryReference(load('denied-non-selectable.json')), 'library_not_selectable')
})

test('AC-I6-DEN-libraries: metadata-only denial is the intended contentMode branch', () => {
  const facts = load('denied-metadata-only.json')
  assert.equal(facts.lifecycle, 'admitted')
  assert.equal(facts.selectability, 'selectable')
  assert.equal(facts.compatibility, 'compatible')
  assert.equal(facts.contentMode, 'metadata_only')
  const error = classify(
    () => validateLibraryReference(facts),
    'library_not_selectable',
    'denied',
  )
  assert.equal(error.details.contentMode, 'metadata_only')
  assert.equal(error.details.selectability, undefined)
  assert.equal(error.details.lifecycle, undefined)
})

test('AC-I6-UNA-libraries: missing source identity is unavailable, not success or stale', () => {
  throws(() => validateLibraryReference(load('unavailable-missing-source.json')), 'library_unavailable')
  try {
    validateLibraryReference(load('unavailable-missing-source.json'))
  } catch (error) {
    assert.equal(error.details.classification, 'unavailable')
    assert.notEqual(error.code, 'library_reference_not_frozen')
  }
})

test('AC-I6-FC-libraries: well-formed unpinned source is stale, not unavailable', () => {
  throws(() => validateLibraryReference(load('stale-unpinned-source.json')), 'library_reference_not_frozen')
  try {
    validateLibraryReference(load('stale-unpinned-source.json'))
  } catch (error) {
    assert.equal(error.details.classification, 'stale')
    assert.notEqual(error.code, 'library_unavailable')
    assert.equal(error.details.sourceCommitSha, 'b2d2bbb035c6e6a3f859480ce57f12e0882dd3f0')
  }
})

test('AC-I6-FC-libraries: incompatible compatibility is fail-closed', () => {
  throws(() => validateLibraryReference(load('fail-closed-incompatible.json')), 'library_incompatible')
  try {
    validateLibraryReference(load('fail-closed-incompatible.json'))
  } catch (error) {
    assert.equal(error.details.classification, 'incompatible')
    assert.notEqual(error.code, 'library_not_selectable')
  }
  const facts = load('positive-verified-cache.json')
  throws(() => validateLibraryReference({ ...facts, compatibility: 'unknown' }), 'library_incompatible')
})

test('AC-I6-FC-libraries: catalogue/entry identity mismatch is tamper', () => {
  throws(() => validateLibraryReference(load('fail-closed-tampered-entry.json')), 'library_tampered')
  try {
    validateLibraryReference(load('fail-closed-tampered-entry.json'))
  } catch (error) {
    assert.equal(error.details.classification, 'tamper')
    assert.equal(error.details.field, 'entryId')
  }
  const facts = load('positive-verified-cache.json')
  throws(() => validateLibraryReference({
    ...facts,
    catalogueRecord: {
      ...facts.catalogueRecord,
      payloadSha256: 'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa',
    },
  }), 'library_tampered')
})

test('AC-I6-FC-libraries: unknown field, execute receipt, unpinned/malformed identity, sensitive field, invalid digest', () => {
  const facts = load('positive-verified-cache.json')
  throws(() => validateLibraryReference({ ...facts, closureDigest: facts.dependencyLockSha256 }), 'unknown_field')
  throws(() => validateLibraryReference({ ...facts, receiptType: 'execute' }), 'library_receipt_invalid')
  throws(() => validateLibraryReference({ ...facts, entryId: 'NOT VALID' }), 'library_identity_invalid')
  throws(() => validateLibraryReference({ ...facts, sourceCommitSha: '0123456789abcdef0123456789abcdef0123456' }), 'library_git_identity_invalid')
  throws(() => validateLibraryReference({ ...facts, secret: 'redacted' }), 'sensitive_field')
  throws(() => validateLibraryReference({ ...facts, payloadSha256: 'not-a-digest' }), 'library_digest_invalid')
  throws(() => validateLibraryReference({ ...facts, catalogueSha256: 'not-a-digest' }), 'library_digest_invalid')
  const { catalogueSha256, ...missingCatalogue } = facts
  assert.equal(typeof catalogueSha256, 'string')
  throws(() => validateLibraryReference(missingCatalogue), 'library_digest_invalid')
  throws(() => validateLibraryReference(null), 'invalid_object')
  throws(() => validateLibraryReference([]), 'invalid_object')
})

test('AC-I6-FC-libraries: inherited prototype properties fail closed', () => {
  const facts = load('positive-verified-cache.json')
  const inheritedExtra = Object.assign(Object.create({ extraField: 'from-prototype' }), facts)
  classify(
    () => validateLibraryReference(inheritedExtra),
    'inherited_property',
    'fail_closed',
  )
  const { entryId, ...ownWithoutEntry } = facts
  const inheritedMaterial = Object.assign(Object.create({ entryId }), ownWithoutEntry)
  classify(
    () => validateLibraryReference(inheritedMaterial),
    'inherited_property',
    'fail_closed',
  )
  const nestedInherited = {
    ...facts,
    catalogueRecord: Object.assign(Object.create({ extraField: 'nested-proto' }), facts.catalogueRecord),
  }
  classify(
    () => validateLibraryReference(nestedInherited),
    'inherited_property',
    'fail_closed',
  )
})

test('AC-I6-FC-libraries: accessor getter and setter inputs fail closed before TOCTOU reads', () => {
  const facts = load('positive-verified-cache.json')
  const getterFacts = { ...facts }
  let reads = 0
  Object.defineProperty(getterFacts, 'entryId', {
    enumerable: true,
    configurable: true,
    get() {
      reads += 1
      return reads === 1 ? 'synthetic-component' : 'mutated-after-read'
    },
  })
  classify(
    () => validateLibraryReference(getterFacts),
    'accessor_property',
    'fail_closed',
  )
  assert.equal(reads, 0)
  const setterFacts = { ...facts }
  Object.defineProperty(setterFacts, 'trap', {
    enumerable: true,
    configurable: true,
    set() {},
  })
  classify(
    () => validateLibraryReference(setterFacts),
    'accessor_property',
    'fail_closed',
  )
  const nestedGetter = {
    ...facts,
    catalogueRecord: { ...facts.catalogueRecord },
  }
  Object.defineProperty(nestedGetter.catalogueRecord, 'entryId', {
    enumerable: true,
    configurable: true,
    get() {
      return 'synthetic-component'
    },
  })
  classify(
    () => validateLibraryReference(nestedGetter),
    'accessor_property',
    'fail_closed',
  )
})

test('AC-I6-FC-libraries: accepted nested catalogueRecord cannot be mutated', () => {
  const facts = load('positive-verified-cache.json')
  const accepted = validateLibraryReference(facts)
  assert.ok(Object.isFrozen(accepted))
  assert.ok(Object.isFrozen(accepted.catalogueRecord))
  assert.throws(() => {
    accepted.catalogueRecord.payloadSha256 = 'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa'
  }, TypeError)
  facts.entryId = 'mutated-after-snapshot'
  facts.catalogueRecord.entryId = 'mutated-after-snapshot'
  assert.equal(accepted.entryId, 'synthetic-component')
  assert.equal(accepted.catalogueRecord.entryId, 'synthetic-component')
})

test('validator has no transport, git fetch, or library-client coupling', () => {
  assert.doesNotMatch(MODULE_SOURCE, /\b(fetch|XMLHttpRequest|createServer|net\.connect)\b/)
  assert.doesNotMatch(MODULE_SOURCE, /from ['"]node:(http|https|net|child_process|tls)['"]/)
  assert.doesNotMatch(MODULE_SOURCE, /\bgit fetch\b/)
  assert.doesNotMatch(MODULE_SOURCE, /library-client/)
  assert.equal(typeof validateLibraryReference, 'function')
})
