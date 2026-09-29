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
  assert.equal(lock.provider.commit, '28334c4d409dc74a680bf4e09fa2dab22726e229')
  assert.equal(lock.provider.tree, '3038dfc1f24c256f9c7547f906a988ce222e2044')
  assert.match(lock.provider.syncedAt, /^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$/)
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
  const pinnedVersions = {
    'git-safeguard': '1.1.0',
    'persistent-qa': '1.0.0',
    'repository-manager': '1.0.0',
    'skill-template': '1.2.0',
    'tool-architect': '1.0.0',
  }
  for (const [skillId, version] of Object.entries(pinnedVersions)) {
    const row = lock.skills.find((item) => item.skillId === skillId)
    assert.equal(row.authority, 'linkskills')
    assert.equal(row.version, version)
    assert.ok(Array.isArray(row.files) && row.files.length > 1)
    const skillMd = row.files.find((file) => file.path === 'SKILL.md')
    assert.equal(row.entrypointDigest, skillMd.sha256)
    assert.match(skillMd.sha256, /^sha256:[a-f0-9]{64}$/)
  }
  const adapter = lock.skills.find((item) => item.skillId === 'agentsetup')
  const retired = lock.skills.find((item) => item.skillId === 'action-queue')
  assert.equal(adapter.authority, 'required_local_adapter')
  assert.equal(adapter.version, '1.3.0')
  assert.equal(adapter.entrypointDigest, 'sha256:932c1c7d28632449432c65bc8ce64461f60866eb2135a68f45bf475dcac63887')
  assert.equal(adapter.files, undefined)
  assert.equal(retired.authority, 'none')
  assert.equal(retired.decision, 'retired')
  assert.equal(retired.entrypointDigest, 'sha256:32aff5fd66bfe8d724377ded1a278b54258c07c3cb567a1a4369589d499f6ac2')
  assert.equal(retired.files, undefined)
  const cursorLock = JSON.parse(readFileSync(join(ROOT, 'core/managed-core/platforms/cursor/skills-lock.json'), 'utf8'))
  const codexLock = JSON.parse(readFileSync(join(ROOT, 'core/managed-core/platforms/codex/skills-lock.json'), 'utf8'))
  assert.deepEqual(cursorLock.provider, lock.provider)
  assert.deepEqual(codexLock.provider, lock.provider)
  assert.deepEqual(
    cursorLock.skills.find((item) => item.skillId === 'git-safeguard').files,
    lock.skills.find((item) => item.skillId === 'git-safeguard').files,
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
  assert.equal(LOADER_SOURCE.includes('link-integrations/skills.mjs'), false)
  const loaderRows = JSON.parse(MANIFEST_SOURCE).files.filter((row) => String(row.destination).endsWith('skills-loader.mjs'))
  assert.ok(loaderRows.length >= 2)
  assert.equal(loaderRows.some((row) => String(row.source).endsWith('/skills.mjs')), false)
  assert.equal(existsSync(join(ROOT, 'core/managed-core/platforms/codex/skills-loader.mjs')), true)
  assert.equal(existsSync(join(ROOT, 'core/managed-core/platforms/cursor/skills-loader.mjs')), true)
})
