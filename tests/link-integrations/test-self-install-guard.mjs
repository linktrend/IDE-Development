import assert from 'node:assert/strict'
import { existsSync, readdirSync, readFileSync, statSync } from 'node:fs'
import { dirname, join } from 'node:path'
import { fileURLToPath } from 'node:url'
import { test } from 'node:test'
import * as barrel from '../../core/link-integrations/index.mjs'

const HERE = dirname(fileURLToPath(import.meta.url))
const ROOT = join(HERE, '../..')
const LINK = join(ROOT, 'core/link-integrations')
const TESTS = join(ROOT, 'tests/link-integrations')

/** Issue 244 obsolete pin identities — must not be frozen consumer pins. */
const ISSUE_244_OBSOLETE = Object.freeze([
  '6a7114674c23fc6b9ba9ae2b3277b8aec7a3fb15',
  '91d565a988150da39a13b66c4bcd51f7bc47c9be',
  'b2d2bbb035c6e6a3f859480ce57f12e0882dd3f0',
  '2701e6a190468f437102946425a64e890eed6690',
  '43887ffc3b51ef2e54c30820d41cab67f54d5d0f',
  '40c7acfcd7b204f19a1278e6801033c4ee64b369',
  '93ec4b9df2ebe2a9d9b412fb8b3bcde2aa8e97f3',
  '1845b996a7ec4d217a57e6f66574d6c5d676bb67',
  '10f75a8d840160a10d131371e94a338dfd1ebb4a',
  'c433907818f2cd4adbfdd61549f9f91396e31819',
])

/**
 * @param {string} dir
 * @param {(name: string) => boolean} [filter]
 * @returns {string[]}
 */
function listFiles(dir, filter = () => true) {
  /** @type {string[]} */
  const out = []
  for (const name of readdirSync(dir)) {
    const path = join(dir, name)
    const st = statSync(path)
    if (st.isDirectory()) {
      out.push(...listFiles(path, filter))
      continue
    }
    if (filter(name)) out.push(path)
  }
  return out
}

test('AC-I6-REL-04: repo root has no nested .ide-development install', () => {
  assert.equal(existsSync(join(ROOT, '.ide-development')), false)
})

test('AC-I6-REL-05 / AC-I6-X-04: barrel has no self-install helper and stays on owned paths', () => {
  const indexSource = readFileSync(join(LINK, 'index.mjs'), 'utf8')
  assert.equal(/installSelf|install-self|selfInstall|ide-development\.py install/i.test(indexSource), false)
  assert.equal(typeof barrel.negotiateMcp, 'function')
  assert.equal(typeof barrel.validateOkfMapping, 'function')
  assert.equal(typeof barrel.validatePlatformIdentity, 'function')
  assert.equal(typeof barrel.validateLibraryReference, 'function')
  assert.equal(typeof barrel.validateBrainProjection, 'function')
  assert.equal(typeof barrel.validateSkillsRelease, 'function')
  assert.equal(typeof barrel.validateAutoworkReceipt, 'function')
  assert.equal('installSelf' in barrel, false)
  assert.equal('install' in barrel, false)

  const owned = listFiles(LINK, (name) => name.endsWith('.mjs') || name.endsWith('.md'))
  assert.ok(owned.some((path) => path.endsWith('mcp.mjs')))
  assert.ok(owned.some((path) => path.endsWith('index.mjs')))
  for (const path of owned) {
    assert.ok(path.startsWith(LINK))
  }
})

test('AC-I6-X-03: Item 6 source files omit Issue 244 pins and self-install instructions', () => {
  const sourceFiles = listFiles(LINK, (name) => name.endsWith('.mjs') || name === 'README.md')
  const pinsSource = readFileSync(join(LINK, 'pins.mjs'), 'utf8')
  for (const sha of ISSUE_244_OBSOLETE) {
    assert.equal(pinsSource.includes(sha), false, `pins.mjs must not freeze obsolete ${sha}`)
  }

  for (const path of sourceFiles) {
    const text = readFileSync(path, 'utf8')
    assert.equal(
      /scripts\/ide-development\.py\s+install[^\n]*IDE-Development/i.test(text),
      false,
      `${path} must not instruct installing into IDE Development`,
    )
    assert.equal(
      /install[^\n]*\.ide-development\/[^\n]*(this repository|IDE Development|IDE-Development)/i.test(
        text,
      ),
      false,
      `${path} must not instruct nested self-install into this repo`,
    )
    if (path.endsWith('pins.mjs')) {
      for (const sha of ISSUE_244_OBSOLETE) {
        assert.equal(text.includes(sha), false)
      }
    }
  }

  // Negative fixtures may mention obsolete SHAs or execute receipt types only
  // as refuse cases; production source modules must not pin them.
  const moduleSources = listFiles(LINK, (name) => name.endsWith('.mjs'))
  for (const path of moduleSources) {
    const text = readFileSync(path, 'utf8')
    if (path.endsWith('libraries.mjs')) {
      assert.equal(/receiptType:\s*['"]execute['"]/.test(text), false)
    }
  }

  assert.ok(existsSync(join(TESTS, 'test-mcp.mjs')))
  assert.ok(existsSync(join(TESTS, 'test-self-install-guard.mjs')))
})
