import assert from 'node:assert/strict'
import { test } from 'node:test'
import { LIBRARY_V2_SOURCE, LibraryV2Error, digest, pageCatalogue, selectV2, validateCatalogue, verifyCachedReceipt } from '../core/library/library-v2-client.mjs'

const throws = (fn, code) => assert.throws(fn, (error) => error instanceof LibraryV2Error && error.code === code)
const sha = (value) => digest(value)
const record = { schemaVersion: 2, schemaRevision: 2, recordType: 'catalogue_record', entryId: 'safe-kit', version: '1.0.0', artifactType: 'starter_kit', name: 'safe', summary: 'safe', gitTreeSha1: 'a'.repeat(40), lifecycle: 'admitted', selectability: 'selectable', compatibility: 'compatible', path: 'entries/safe-kit/1.0.0', tags: [] }
const inventory = { schemaVersion: 2, schemaRevision: 2, inventoryType: 'exhaustive_tree_inventory', root: '.', complete: true, symlinks: false, entries: [{ path: 'README.md', sha256: 'b'.repeat(64) }], treeSha1: record.gitTreeSha1 }
inventory.inventorySha256 = sha(inventory.entries)
const manifest = { schemaVersion: 2, schemaRevision: 2, manifestType: 'immutable_release', releaseId: 'safe-kit-1.0.0', entryId: record.entryId, artifactType: record.artifactType, version: record.version, libraryCommitSha: LIBRARY_V2_SOURCE.commit, gitTreeSha1: record.gitTreeSha1, payloadSha256: 'c'.repeat(64), inventorySha256: inventory.inventorySha256, dependencyLockSha256: 'd'.repeat(64), extension: {} }
record.inventorySha256 = inventory.inventorySha256
record.releaseManifestSha256 = sha(manifest)
const closure = { schemaVersion: 2, schemaRevision: 2, closureType: 'dependency_closure', dependencyLockSha256: manifest.dependencyLockSha256, members: [{ name: 'one', sha256: 'e'.repeat(64) }] }
const catalogue = { schemaVersion: 2, schemaRevision: 2, catalogueType: 'catalogue', records: [record] }
catalogue.recordsSha256 = sha(catalogue.records)

test('v2 progresses frozen catalogue page to selected receipt and verified cache', () => {
  const snapshot = validateCatalogue(catalogue)
  const page = pageCatalogue(snapshot, { limit: 1 })
  assert.equal(page.records[0].entryId, record.entryId)
  const selection = selectV2({ snapshot, entryId: record.entryId, version: record.version, manifest, inventory, closure, materializedTreeSha1: record.gitTreeSha1, consumerId: 'ide-test', consumptionMode: 'materialize', now: '2026-08-13T00:00:00.000Z', expiresAt: '2030-01-01T00:00:00.000Z' })
  assert.equal(verifyCachedReceipt(selection.receipt, { offline: true }).providerCommit, LIBRARY_V2_SOURCE.commit)
})

test('v2 fails closed on source, catalogue, cursor, lifecycle, chain and cache tamper', () => {
  throws(() => validateCatalogue({ ...catalogue, extra: true }), 'unknown_field')
  throws(() => validateCatalogue({ ...catalogue, recordsSha256: '0'.repeat(64) }), 'catalogue_digest_mismatch')
  const snapshot = validateCatalogue(catalogue)
  throws(() => pageCatalogue(snapshot, { cursor: Buffer.from(JSON.stringify({ commit: '0'.repeat(40), tree: LIBRARY_V2_SOURCE.tree, digest: snapshot.digest, offset: 0 })).toString('base64url') }), 'cursor_snapshot_mismatch')
  const blocked = structuredClone(catalogue); blocked.records[0].lifecycle = 'draft'; blocked.recordsSha256 = sha(blocked.records)
  throws(() => validateCatalogue(blocked), 'record_not_selectable')
  const badManifest = { ...manifest, libraryCommitSha: '0'.repeat(40) }
  throws(() => selectV2({ snapshot, entryId: record.entryId, version: record.version, manifest: badManifest, inventory, closure, materializedTreeSha1: record.gitTreeSha1, consumerId: 'ide-test', consumptionMode: 'materialize' }), 'manifest_record_mismatch')
  const receipt = selectV2({ snapshot, entryId: record.entryId, version: record.version, manifest, inventory, closure, materializedTreeSha1: record.gitTreeSha1, consumerId: 'ide-test', consumptionMode: 'materialize', now: '2026-08-13T00:00:00.000Z', expiresAt: '2030-01-01T00:00:00.000Z' }).receipt
  throws(() => verifyCachedReceipt({ ...receipt, providerTree: '0'.repeat(40) }), 'library_source_not_frozen')
  throws(() => verifyCachedReceipt({ ...receipt, authority: 'execute' }), 'unknown_field')
  throws(() => verifyCachedReceipt(receipt, { now: Date.parse('2031-01-01T00:00:00.000Z') }), 'cache_receipt_stale')
})
