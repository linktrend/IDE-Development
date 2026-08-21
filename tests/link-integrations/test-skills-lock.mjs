import assert from 'node:assert/strict'
import { existsSync, readFileSync } from 'node:fs'
import { dirname, join } from 'node:path'
import { fileURLToPath } from 'node:url'
import { test } from 'node:test'
import { ConsumerContractError } from '../../core/link-integrations/errors.mjs'
import {
  ACTIVE_COPY_COUNT,
  SKILLS_LOCK_CONTRACT_VERSION,
  V24_ROLLBACK_COMMIT,
  V24_ROLLBACK_TREE,
  loadSkillsLock,
  planPhysicalSkillRemoval,
  recordSkillsTelemetry,
  retrieveSkillFragment,
} from '../../core/link-integrations/skills-loader.mjs'
import {
  retrieveSkillFragment as retrieveCodexFragment,
} from '../../core/managed-core/platforms/codex/skills-loader.mjs'
import {
  retrieveSkillFragment as retrieveCursorFragment,
} from '../../core/managed-core/platforms/cursor/skills-loader.mjs'

const HERE = dirname(fileURLToPath(import.meta.url))
const ROOT = join(HERE, '../..')
const LOADER_SOURCE = readFileSync(join(ROOT, 'core/link-integrations/skills-loader.mjs'), 'utf8')
const MANIFEST_SOURCE = readFileSync(join(ROOT, 'core/managed-core/MANIFEST.json'), 'utf8')
const DETAIL_KEYS = new Set(['classification', 'field', 'provider', 'frozenCommit', 'frozenTree'])

function classify(fn, code, classification) {
  try {
    fn()
    assert.fail(`expected ${code}`)
  } catch (error) {
    assert.ok(error instanceof ConsumerContractError)
    assert.equal(error.code, code)
    assert.equal(error.details.classification, classification)
    for (const [key, item] of Object.entries(error.details)) {
      assert.ok(DETAIL_KEYS.has(key), `details.${key} is not a bounded token`)
      if (item && typeof item === 'object') {
        assert.fail(`details.${key} must not carry a caller object`)
      }
    }
  }
}

test('ISS-04 lock inventories 88 active copies and qualifies or retires every unique skill', () => {
  const lock = loadSkillsLock()
  assert.equal(lock.contractVersion, SKILLS_LOCK_CONTRACT_VERSION)
  assert.equal(lock.copyCount, ACTIVE_COPY_COUNT)
  assert.equal(lock.copies.length, 88)
  assert.equal(lock.uniqueSkillCount, 43)
  assert.equal(lock.qualifiedCount + lock.retiredCount, 43)
  assert.equal(lock.provider.repository, 'linktrend/LiNKskills')
  assert.equal(lock.provider.commit, 'e3d80fd22a05a4f68207e130c50b772b5acffda4')
  assert.equal(lock.provider.tree, '69a131b46a73a4ef724694bfe240b1a11652bcc9')
  assert.equal(lock.rollbackCommit, V24_ROLLBACK_COMMIT)
  assert.equal(lock.rollbackTree, V24_ROLLBACK_TREE)
  assert.equal(lock.physicalRemovalAuthorized, false)
  const unique = new Set()
  for (const row of lock.skills) {
    unique.add(row.skillId)
    assert.ok(row.decision === 'qualified' || row.decision === 'retired')
  }
  assert.equal(unique.size, 43)
  for (const copy of lock.copies) {
    assert.equal(existsSync(join(ROOT, copy.path)), true, copy.path)
    assert.ok(copy.decision === 'qualified' || copy.decision === 'retired')
  }
  assert.deepEqual(
    lock.overlapWithLinkskills,
    ['git-safeguard', 'persistent-qa', 'repository-manager', 'skill-template', 'tool-architect'],
  )
})

test('ISS-04 Codex and Cursor retrieve a qualified LiNKskills release fragment', () => {
  const codex = retrieveSkillFragment({
    platform: 'codex',
    skillId: 'git-safeguard',
    fragmentLevel: 2,
    providerStatus: 'available',
  })
  const cursor = retrieveSkillFragment({
    platform: 'cursor',
    skillId: 'git-safeguard',
    fragmentLevel: 2,
    providerStatus: 'available',
  })
  assert.equal(codex.platform, 'codex')
  assert.equal(cursor.platform, 'cursor')
  assert.equal(codex.authority, 'linkskills')
  assert.equal(codex.addressing, 'validation')
  assert.match(codex.digest, /^sha256:[a-f0-9]{64}$/)
  assert.equal(codex.providerCommit, cursor.providerCommit)
  assert.ok(Object.isFrozen(codex))
  const fromCodexAdapter = retrieveCodexFragment({
    platform: 'codex',
    skillId: 'git-safeguard',
    fragmentLevel: 0,
    providerStatus: 'available',
  })
  const fromCursorAdapter = retrieveCursorFragment({
    platform: 'cursor',
    skillId: 'git-safeguard',
    fragmentLevel: 0,
    providerStatus: 'available',
  })
  assert.equal(fromCodexAdapter.source, 'skills-lock')
  assert.equal(fromCursorAdapter.source, 'skills-lock')
})

test('ISS-04 unavailable provider is refused even when physical copies exist', () => {
  assert.equal(existsSync(join(ROOT, 'core/skills/git-safeguard/SKILL.md')), true)
  assert.equal(existsSync(join(ROOT, '.cursor/skills/git-safeguard/SKILL.md')), true)
  classify(
    () => retrieveSkillFragment({
      platform: 'codex',
      skillId: 'git-safeguard',
      providerStatus: 'unavailable',
    }),
    'skills_release_unavailable',
    'unavailable',
  )
  classify(
    () => retrieveSkillFragment({
      platform: 'cursor',
      skillId: 'git-safeguard',
      providerStatus: 'offline',
    }),
    'skills_release_unavailable',
    'unavailable',
  )
})

test('ISS-04 required local adapters retrieve without a live provider', () => {
  const accepted = retrieveSkillFragment({
    platform: 'codex',
    skillId: 'agentsetup',
    fragmentLevel: 2,
    providerStatus: 'unavailable',
  })
  assert.equal(accepted.authority, 'required_local_adapter')
  assert.equal(accepted.skillId, 'agentsetup')
})

test('ISS-04 retired local-only copies are denied as provider authority', () => {
  classify(
    () => retrieveSkillFragment({
      platform: 'cursor',
      skillId: 'bash-linux',
      providerStatus: 'available',
    }),
    'skills_not_qualified',
    'denied',
  )
})

test('ISS-04 physical removal stays HOLD without dual-app proof', () => {
  const plan = planPhysicalSkillRemoval()
  assert.equal(plan.authorized, false)
  assert.equal(plan.reason, 'dual_app_proof_hold')
  assert.equal(plan.copiesRetained, 88)
  assert.equal(plan.dualAppProof.codex, 'HOLD')
  assert.equal(plan.dualAppProof.cursor, 'HOLD')
  assert.equal(plan.rollbackCommit, V24_ROLLBACK_COMMIT)
  assert.equal(existsSync(join(ROOT, '.ide-development')), false)
})

test('ISS-04 bounded telemetry still uses the pin-time use-report subset', () => {
  const accepted = recordSkillsTelemetry({
    report_kind: 'completed_use',
    score: 10,
    skill_release_ref: 'opaque:release-git-safeguard-1.1.0',
    actor_ref: 'opaque:actor-ide-iss04',
  })
  assert.equal(accepted.report_kind, 'completed_use')
  assert.ok(Object.isFrozen(accepted))
})

test('ISS-04 loader has no transport, skill execution, or nested install APIs', () => {
  assert.doesNotMatch(LOADER_SOURCE, /\b(fetch|XMLHttpRequest|createServer|net\.connect)\b/)
  assert.doesNotMatch(LOADER_SOURCE, /from ['"]node:(http|https|net|child_process|tls)['"]/)
  assert.doesNotMatch(LOADER_SOURCE, /rmSync|rmdirSync|unlinkSync/)
  assert.doesNotMatch(LOADER_SOURCE, /skills_run_start\(/)
  assert.equal(MANIFEST_SOURCE.includes('core/link-integrations/skills.mjs'), false)
  assert.equal(existsSync(join(ROOT, 'core/managed-core/platforms/codex/skills-loader.mjs')), true)
  assert.equal(existsSync(join(ROOT, 'core/managed-core/platforms/cursor/skills-loader.mjs')), true)
})
