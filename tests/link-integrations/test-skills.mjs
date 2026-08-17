import assert from 'node:assert/strict'
import { existsSync, readFileSync } from 'node:fs'
import { dirname, join } from 'node:path'
import { fileURLToPath } from 'node:url'
import { test } from 'node:test'
import { ConsumerContractError } from '../../core/link-integrations/errors.mjs'
import { FROZEN_PROVIDERS } from '../../core/link-integrations/pins.mjs'
import {
  SKILLS_CONTRACT_VERSION,
  SKILLS_PIN,
  validateSkillsRelease,
  validateSkillsTelemetry,
} from '../../core/link-integrations/skills.mjs'

const HERE = dirname(fileURLToPath(import.meta.url))
const ROOT = join(HERE, '../..')
const FIXTURES = join(HERE, 'fixtures/skills')
const MODULE_SOURCE = readFileSync(join(HERE, '../../core/link-integrations/skills.mjs'), 'utf8')
const MANIFEST_SOURCE = readFileSync(join(HERE, '../../core/managed-core/MANIFEST.json'), 'utf8')

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

test('AC-I6-POS-skills: accepts published qualified available discovery addressing', () => {
  const accepted = validateSkillsRelease(load('positive-discovery.json'))
  assert.equal(accepted.skillId, 'synthetic-skill')
  assert.equal(accepted.version, '1.0.0')
  assert.equal(accepted.fragmentLevel, 0)
  assert.equal(accepted.addressing, 'discovery')
  assert.equal(accepted.providerCommit, FROZEN_PROVIDERS.skills.commit)
  assert.equal(accepted.providerTree, FROZEN_PROVIDERS.skills.tree)
  assert.match(accepted.releaseHash, /^sha256:[a-f0-9]{64}$/)
  assert.ok(Object.isFrozen(accepted))
  assert.throws(() => {
    accepted.skillId = 'mutated'
  }, TypeError)
  assert.equal(SKILLS_CONTRACT_VERSION, 'skills.api.v0.2')
  assert.equal(SKILLS_PIN.commit, FROZEN_PROVIDERS.skills.commit)
  assert.equal(SKILLS_PIN.tree, FROZEN_PROVIDERS.skills.tree)
})

test('AC-I6-POS-skills: accepts validation and execution addressing of the same release', () => {
  const validated = validateSkillsRelease(load('positive-validation.json'))
  assert.equal(validated.addressing, 'validation')
  assert.equal(validated.fragmentLevel, 2)
  assert.equal(validated.releaseHash, load('positive-discovery.json').releaseHash)
  const addressed = validateSkillsRelease(load('positive-execution.json'))
  assert.equal(addressed.addressing, 'execution')
  assert.equal(addressed.fragmentLevel, 3)
  assert.ok(Object.isFrozen(validated))
  assert.ok(Object.isFrozen(addressed))
})

test('AC-I6-POS-skills: accepts bounded completed-use telemetry at score 10 without issue', () => {
  const accepted = validateSkillsTelemetry(load('positive-telemetry-score-10.json'))
  assert.deepEqual(accepted, {
    reportKind: 'completed_use',
    score: 10,
    skillReleaseRef: 'opaque:release-synthetic-skill-1.0.0',
    actorRef: 'opaque:actor-ide-dev-s4',
    idempotencyKey: 'opaque:use-report-s4-10',
  })
  assert.equal(accepted.issue, undefined)
  assert.ok(Object.isFrozen(accepted))
  assert.throws(() => {
    accepted.score = 0
  }, TypeError)
})

test('AC-I6-POS-skills: accepts bounded completed-use telemetry at score 9 with a typed issue', () => {
  const accepted = validateSkillsTelemetry(load('positive-telemetry-score-9.json'))
  assert.equal(accepted.score, 9)
  assert.deepEqual(accepted.issue, {
    type: 'incomplete',
    severity: 'low',
    issueRef: 'opaque:issue-telemetry-s4',
  })
  assert.ok(Object.isFrozen(accepted))
  assert.ok(Object.isFrozen(accepted.issue))
})

test('AC-I6-DEN-skills: denies unqualified and unpublished releases', () => {
  classify(() => validateSkillsRelease(load('denied-unqualified.json')), 'skills_not_qualified', 'denied')
  classify(() => validateSkillsRelease(load('denied-unpublished.json')), 'skills_not_published', 'denied')
})

test('AC-I6-UNA-skills: missing pin material or offline availability is not success', () => {
  classify(
    () => validateSkillsRelease(load('unavailable-missing-pin.json')),
    'skills_release_unavailable',
    'unavailable',
  )
  classify(
    () => validateSkillsRelease(load('unavailable-offline.json')),
    'skills_release_unavailable',
    'unavailable',
  )
  classify(
    () => validateSkillsRelease({ ...load('positive-validation.json'), availability: 'quarantined' }),
    'skills_release_unavailable',
    'unavailable',
  )
})

test('AC-I6-FC-skills: wrong pin, incompatible state, latest alias, and fragmentLevel 7 fail closed', () => {
  classify(() => validateSkillsRelease(load('failclosed-wrong-pin.json')), 'incompatible_pin', 'fail_closed')
  classify(
    () => validateSkillsRelease(load('failclosed-incompatible.json')),
    'skills_release_incompatible',
    'incompatible',
  )
  classify(
    () => validateSkillsRelease({ ...load('positive-validation.json'), compatibility: 'incompatible' }),
    'skills_release_incompatible',
    'incompatible',
  )
  classify(
    () => validateSkillsRelease({ ...load('positive-validation.json'), skillId: 'latest' }),
    'skills_latest_alias',
    'fail_closed',
  )
  classify(
    () => validateSkillsRelease({ ...load('positive-validation.json'), version: 'latest' }),
    'skills_latest_alias',
    'fail_closed',
  )
  classify(
    () => validateSkillsRelease({ ...load('positive-validation.json'), fragmentLevel: 7 }),
    'skills_fragment_invalid',
    'fail_closed',
  )
})

test('AC-I6-FC-skills: legacy run/tool names, cross-operation fields, raw/private payloads fail closed', () => {
  classify(
    () => validateSkillsRelease(load('failclosed-legacy-run.json')),
    'skills_legacy_operation',
    'fail_closed',
  )
  classify(
    () => validateSkillsRelease({ ...load('positive-execution.json'), operation: 'skills_tool_invoke' }),
    'skills_legacy_operation',
    'fail_closed',
  )
  classify(
    () => validateSkillsRelease(load('failclosed-cross-operation.json')),
    'cross_operation_field',
    'fail_closed',
  )
  classify(
    () => validateSkillsRelease({ ...load('positive-validation.json'), reportKind: 'completed_use' }),
    'cross_operation_field',
    'fail_closed',
  )
  classify(
    () => validateSkillsRelease({ ...load('positive-validation.json'), secret: 'redacted' }),
    'sensitive_field',
    'fail_closed',
  )
  classify(
    () => validateSkillsRelease({ ...load('positive-validation.json'), raw: { payload: 'no' } }),
    'sensitive_field',
    'fail_closed',
  )
  classify(
    () => validateSkillsRelease({ ...load('positive-validation.json'), extraField: 'no' }),
    'unknown_field',
    'fail_closed',
  )
  classify(
    () => validateSkillsRelease({ ...load('positive-validation.json'), skill_id: 'synthetic-skill' }),
    'competing_envelope',
    'fail_closed',
  )
  classify(
    () => validateSkillsRelease({ ...load('positive-validation.json'), contractVersion: 'skills.api.v0.1' }),
    'skills_contract_incompatible',
    'fail_closed',
  )
  classify(
    () => validateSkillsRelease({ ...load('positive-validation.json'), releaseHash: 'not-a-digest' }),
    'skills_digest_invalid',
    'fail_closed',
  )
  classify(() => validateSkillsRelease(null), 'skills_release_unavailable', 'unavailable')
  classify(() => validateSkillsRelease([]), 'invalid_object', 'fail_closed')
})

test('AC-I6-FC-skills: telemetry rejects score 10 with issue, cross-operation fields, and private payloads', () => {
  classify(
    () => validateSkillsTelemetry(load('failclosed-telemetry-score-10-issue.json')),
    'skills_perfect_use_has_issue',
    'fail_closed',
  )
  const positive = load('positive-telemetry-score-10.json')
  classify(
    () => validateSkillsTelemetry({ ...positive, fragmentLevel: 2 }),
    'cross_operation_field',
    'fail_closed',
  )
  classify(
    () => validateSkillsTelemetry({ ...positive, report_kind: 'completed_use' }),
    'competing_envelope',
    'fail_closed',
  )
  classify(
    () => validateSkillsTelemetry({ ...positive, transcript: 'no' }),
    'sensitive_field',
    'fail_closed',
  )
  classify(
    () => validateSkillsTelemetry({ ...positive, score: 11 }),
    'skills_telemetry_invalid',
    'fail_closed',
  )
  classify(
    () => validateSkillsTelemetry({ ...positive, skillReleaseRef: 'latest' }),
    'skills_reference_invalid',
    'fail_closed',
  )
  classify(
    () => validateSkillsTelemetry({ ...load('positive-telemetry-score-9.json'), issue: undefined }),
    'skills_issue_required',
    'fail_closed',
  )
  classify(() => validateSkillsTelemetry(null), 'invalid_object', 'fail_closed')
})

test('validator has no transport, skill execution, catalogue, or credential APIs', () => {
  assert.doesNotMatch(MODULE_SOURCE, /\b(fetch|XMLHttpRequest|createServer|net\.connect)\b/)
  assert.doesNotMatch(MODULE_SOURCE, /from ['"]node:(http|https|net|child_process|tls)['"]/)
  assert.doesNotMatch(MODULE_SOURCE, /skills_run_start\(/)
  assert.doesNotMatch(MODULE_SOURCE, /skills_tool_invoke\(/)
  assert.doesNotMatch(MODULE_SOURCE, /\b(mintIdentity|storeSecret|installNested|localCatalogue)\b/)
  assert.equal(typeof validateSkillsRelease, 'function')
  assert.equal(typeof validateSkillsTelemetry, 'function')
})

test('S0 pins remain frozen and MANIFEST is not a pre-rollout write', () => {
  assert.equal(FROZEN_PROVIDERS.skills.repository, 'linktrend/LiNKskills')
  assert.equal(FROZEN_PROVIDERS.skills.commit, '0d6bf34546f89c9beb7f05483a3ed4deeb3a5a67')
  assert.equal(FROZEN_PROVIDERS.skills.tree, '6c36e6c98f90e55d957fba781327b1b0ef90860a')
  assert.equal(MANIFEST_SOURCE.includes('core/link-integrations/skills.mjs'), false)
  assert.equal(MANIFEST_SOURCE.includes('.ide-development/providers/'), false)
  assert.equal(existsSync(join(ROOT, '.ide-development')), false)
})
