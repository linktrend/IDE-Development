#!/usr/bin/env node
/**
 * IDE Development Shared Library client (Phase 8).
 *
 * Access pattern (same as LiNKdeveloper @linkdeveloper/shared-library):
 * 1. fetchCatalog — sparse-fetch indexes/catalog.json; cache with fetch commit SHA
 * 2. fetchEntry — sparse-fetch entries/<id>/ only; cache as entryId@commitSHA
 * 3. Cache is disposable; never authoritative over a fresh catalog fetch
 * 4. No fallback to a private/local Library
 *
 * CLI: sync | search | show | prepare-contribution | validate-contribution | publish-contribution
 */
import { execFileSync } from 'node:child_process'
import {
  cpSync,
  existsSync,
  mkdirSync,
  readFileSync,
  readdirSync,
  rmSync,
  writeFileSync,
} from 'node:fs'
import { dirname, join, resolve } from 'node:path'
import { fileURLToPath } from 'node:url'

const HERE = dirname(fileURLToPath(import.meta.url))
const DEFAULT_REPO = process.env.LINKTREND_SHARED_LIBRARY_REPO_URL ?? 'https://github.com/linktrend/LiNKlibraries.git'
const DEFAULT_BRANCH = process.env.LINKTREND_SHARED_LIBRARY_BASE_BRANCH ?? 'development'
const DEFAULT_CACHE =
  process.env.LINKTREND_SHARED_LIBRARY_CHECKOUT ?? join(HERE, '.cache', 'linklibraries')

function run(cmd, args, cwd) {
  return execFileSync(cmd, args, { cwd, encoding: 'utf8', stdio: ['ignore', 'pipe', 'pipe'] }).trim()
}

function ensureDir(p) {
  mkdirSync(p, { recursive: true })
}

export class LibraryClient {
  constructor({
    repoUrl = DEFAULT_REPO,
    baseBranch = DEFAULT_BRANCH,
    cacheRoot = DEFAULT_CACHE,
    offline = process.env.LINKTREND_SHARED_LIBRARY_OFFLINE === '1',
  } = {}) {
    this.repoUrl = repoUrl
    this.baseBranch = baseBranch
    this.cacheRoot = resolve(cacheRoot)
    this.offline = offline
    this.mirrorDir = join(this.cacheRoot, 'mirror')
    this.catalogCacheDir = join(this.cacheRoot, 'catalog')
    this.entryCacheDir = join(this.cacheRoot, 'entries')
    this.lastCatalog = null
    ensureDir(this.cacheRoot)
    ensureDir(this.catalogCacheDir)
    ensureDir(this.entryCacheDir)
  }

  ensureMirror() {
    if (this.offline) {
      if (!existsSync(join(this.mirrorDir, '.git'))) {
        throw new Error(`Offline: no mirror at ${this.mirrorDir}`)
      }
      return
    }
    if (!existsSync(join(this.mirrorDir, '.git'))) {
      ensureDir(this.mirrorDir)
      run('git', [
        'clone',
        '--filter=blob:none',
        '--sparse',
        '--branch',
        this.baseBranch,
        '--single-branch',
        this.repoUrl,
        this.mirrorDir,
      ])
      run('git', ['-C', this.mirrorDir, 'sparse-checkout', 'set', 'indexes'])
    } else {
      run('git', ['-C', this.mirrorDir, 'fetch', 'origin', this.baseBranch])
      run('git', ['-C', this.mirrorDir, 'checkout', `origin/${this.baseBranch}`])
    }
  }

  tipSha() {
    return run('git', ['-C', this.mirrorDir, 'rev-parse', 'HEAD'])
  }

  fetchCatalog() {
    if (this.offline) {
      const latest = join(this.catalogCacheDir, 'latest.json')
      if (!existsSync(latest)) throw new Error('Offline: no cached catalog')
      const snap = JSON.parse(readFileSync(latest, 'utf8'))
      snap.stale = true
      this.lastCatalog = snap
      return snap
    }
    this.ensureMirror()
    run('git', ['-C', this.mirrorDir, 'sparse-checkout', 'set', 'indexes'])
    run('git', [
      '-C',
      this.mirrorDir,
      'checkout',
      `origin/${this.baseBranch}`,
      '--',
      'indexes',
    ])
    const fetchCommitSha = this.tipSha()
    const catalog = JSON.parse(readFileSync(join(this.mirrorDir, 'indexes', 'catalog.json'), 'utf8'))
    const snapshot = {
      fetchCommitSha,
      catalog,
      cachePath: join(this.catalogCacheDir, `${fetchCommitSha}.json`),
      stale: false,
    }
    writeFileSync(snapshot.cachePath, `${JSON.stringify(snapshot, null, 2)}\n`)
    writeFileSync(join(this.catalogCacheDir, 'latest.json'), `${JSON.stringify(snapshot, null, 2)}\n`)
    this.lastCatalog = snapshot
    return snapshot
  }

  search({ query = '', kind } = {}) {
    const snapshot = this.lastCatalog ?? this.fetchCatalog()
    const q = query.toLowerCase().trim()
    const matches = snapshot.catalog.entries.filter((e) => {
      if (kind && e.kind !== kind) return false
      if (!q) return true
      const hay = `${e.entryId} ${e.name} ${e.summary} ${(e.problemDomains || []).join(' ')}`.toLowerCase()
      return hay.includes(q)
    })
    return { snapshot, matches }
  }

  fetchEntry(entryId, commitSha) {
    const sha = commitSha ?? this.lastCatalog?.fetchCommitSha ?? this.fetchCatalog().fetchCommitSha
    const cacheKey = `${entryId}@${sha}`
    const localPath = join(this.entryCacheDir, cacheKey)
    if (existsSync(join(localPath, 'entry.json'))) {
      return {
        entryId,
        fetchCommitSha: sha,
        localPath,
        entryJson: JSON.parse(readFileSync(join(localPath, 'entry.json'), 'utf8')),
      }
    }
    if (this.offline) throw new Error(`Offline cache miss: ${cacheKey}`)
    this.ensureMirror()
    run('git', ['-C', this.mirrorDir, 'sparse-checkout', 'set', `entries/${entryId}`])
    run('git', ['-C', this.mirrorDir, 'checkout', sha, '--', `entries/${entryId}`])
    const src = join(this.mirrorDir, 'entries', entryId)
    if (!existsSync(src)) throw new Error(`Entry not found: ${entryId}@${sha}`)
    if (existsSync(localPath)) rmSync(localPath, { recursive: true, force: true })
    ensureDir(localPath)
    cpSync(src, localPath, { recursive: true })
    return {
      entryId,
      fetchCommitSha: sha,
      localPath,
      entryJson: JSON.parse(readFileSync(join(localPath, 'entry.json'), 'utf8')),
    }
  }

  prepareContribution(bundlePath) {
    const abs = resolve(bundlePath)
    const entry = JSON.parse(readFileSync(join(abs, 'entry.json'), 'utf8'))
    if (!entry.entryId) throw new Error('bundle missing entryId')
    return { bundlePath: abs, entryId: entry.entryId }
  }

  validateContribution(bundlePath) {
    const abs = resolve(bundlePath)
    const errors = []
    if (!existsSync(join(abs, 'entry.json'))) return { ok: false, errors: ['missing entry.json'] }
    if (!existsSync(join(abs, 'README.md'))) errors.push('missing README.md')
    const entry = JSON.parse(readFileSync(join(abs, 'entry.json'), 'utf8'))
    if (entry.schemaVersion !== 1) errors.push('schemaVersion must be 1')
    if (!entry.integrationNotes || String(entry.integrationNotes).trim().length < 12) {
      errors.push('integrationNotes too short')
    }
    if (
      (entry.kind === 'custom_component' || entry.kind === 'code_pattern') &&
      (!Array.isArray(entry.gotchas) || entry.gotchas.length === 0)
    ) {
      errors.push('gotchas required')
    }
    return { ok: errors.length === 0, errors }
  }

  publishContribution(bundlePath) {
    const prepared = this.prepareContribution(bundlePath)
    const v = this.validateContribution(bundlePath)
    if (!v.ok) return { status: 'publication_pending', detail: v.errors.join('; ') }
    if (process.env.LINKTREND_SHARED_LIBRARY_PUBLISH !== '1') {
      return {
        status: 'publication_pending',
        detail: `Bundle ready for ${prepared.entryId}. Librarian merges PRs into LiNKlibraries development.`,
      }
    }
    return {
      status: 'publication_pending',
      detail: 'Set up gh auth and re-run with PUBLISH=1 from a contribution workflow; default stays pending.',
    }
  }
}

function printJson(value) {
  console.log(JSON.stringify(value, null, 2))
}

function main(argv) {
  const [cmd, ...rest] = argv
  const client = new LibraryClient()
  switch (cmd) {
    case 'sync': {
      printJson(client.fetchCatalog())
      break
    }
    case 'search': {
      let query = ''
      let kind
      for (let i = 0; i < rest.length; i += 1) {
        if (rest[i] === '--query') query = rest[++i]
        else if (rest[i] === '--kind') kind = rest[++i]
      }
      printJson(client.search({ query, kind }))
      break
    }
    case 'show': {
      let entry
      for (let i = 0; i < rest.length; i += 1) {
        if (rest[i] === '--entry') entry = rest[++i]
      }
      if (!entry) throw new Error('--entry required')
      printJson(client.fetchEntry(entry))
      break
    }
    case 'prepare-contribution': {
      let bundle
      for (let i = 0; i < rest.length; i += 1) {
        if (rest[i] === '--bundle') bundle = rest[++i]
      }
      if (!bundle) throw new Error('--bundle required')
      printJson(client.prepareContribution(bundle))
      break
    }
    case 'validate-contribution': {
      let bundle
      for (let i = 0; i < rest.length; i += 1) {
        if (rest[i] === '--bundle') bundle = rest[++i]
      }
      if (!bundle) throw new Error('--bundle required')
      const result = client.validateContribution(bundle)
      printJson(result)
      process.exit(result.ok ? 0 : 1)
      break
    }
    case 'publish-contribution': {
      let bundle
      for (let i = 0; i < rest.length; i += 1) {
        if (rest[i] === '--bundle') bundle = rest[++i]
      }
      if (!bundle) throw new Error('--bundle required')
      printJson(client.publishContribution(bundle))
      break
    }
    case 'help':
    case undefined: {
      console.log(`Usage: node library-client.mjs <sync|search|show|prepare-contribution|validate-contribution|publish-contribution>`)
      break
    }
    default:
      throw new Error(`Unknown command: ${cmd}`)
  }
}

const isMain = process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url)
if (isMain) {
  try {
    main(process.argv.slice(2))
  } catch (err) {
    console.error(err.message || err)
    process.exit(1)
  }
}
