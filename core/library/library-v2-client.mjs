/**
 * LiNKlibraries Revision 2 consumer boundary.
 *
 * This is deliberately a local verifier/materializer, not a provider client:
 * callers supply only bytes already obtained at the frozen immutable source.
 * It never accepts a branch, "latest", or an unpinned catalogue.
 */
import { createHash } from 'node:crypto'

export const LIBRARY_V2_SOURCE = Object.freeze({
  commit: '87dbb71da8b07be8f83eb82f8f769e16b062e7b2',
  tree: 'f258bf45d91a90fb4c818ee9012c7a85b1fa96da',
  cataloguePath: 'indexes/v2/catalog.json',
})

export class LibraryV2Error extends Error { constructor(code) { super(code); this.code = code } }
const fail = (code) => { throw new LibraryV2Error(code) }
const SHA1 = /^[a-f0-9]{40}$/
const SHA256 = /^[a-f0-9]{64}$/
const object = (value, code = 'invalid_object') => { if (!value || typeof value !== 'object' || Array.isArray(value)) fail(code); return value }
const text = (value, code) => { if (typeof value !== 'string' || !value) fail(code); return value }
const keys = (value, allowed) => { for (const key of Object.keys(object(value))) if (!allowed.has(key)) fail('unknown_field') }
const stable = (value) => Array.isArray(value) ? value.map(stable) : value && typeof value === 'object' ? Object.fromEntries(Object.keys(value).sort().map((key) => [key, stable(value[key])])) : value
export const digest = (value) => createHash('sha256').update(JSON.stringify(stable(value))).digest('hex')
const digestField = (value, code) => { if (!SHA256.test(value ?? '')) fail(code); return value }

export function assertFrozenSource(value) {
  keys(value, new Set(['commit', 'tree', 'cataloguePath']))
  if (value.commit !== LIBRARY_V2_SOURCE.commit || value.tree !== LIBRARY_V2_SOURCE.tree || (value.cataloguePath !== undefined && value.cataloguePath !== LIBRARY_V2_SOURCE.cataloguePath)) fail('library_source_not_frozen')
  return LIBRARY_V2_SOURCE
}

const recordKeys = new Set(['schemaVersion', 'schemaRevision', 'recordType', 'entryId', 'version', 'artifactType', 'name', 'summary', 'releaseManifestSha256', 'gitTreeSha1', 'inventorySha256', 'lifecycle', 'selectability', 'compatibility', 'path', 'tags'])
export function validateRecord(record) {
  keys(record, recordKeys)
  if (record.schemaVersion !== 2 || record.schemaRevision !== 2 || record.recordType !== 'catalogue_record') fail('record_schema_invalid')
  for (const field of ['entryId', 'version', 'artifactType', 'path']) text(record[field], 'record_field_missing')
  digestField(record.releaseManifestSha256, 'record_manifest_digest_invalid'); digestField(record.inventorySha256, 'record_inventory_digest_invalid')
  if (!SHA1.test(record.gitTreeSha1 ?? '')) fail('record_tree_invalid')
  if (!['admitted', 'selectable'].includes(record.lifecycle) || record.selectability !== 'selectable' || record.compatibility !== 'compatible') fail('record_not_selectable')
  return Object.freeze({ ...record })
}

export function validateCatalogue(catalogue, source = LIBRARY_V2_SOURCE) {
  assertFrozenSource(source)
  keys(catalogue, new Set(['schemaVersion', 'schemaRevision', 'catalogueType', 'recordsSha256', 'records']))
  if (catalogue.schemaVersion !== 2 || catalogue.schemaRevision !== 2 || catalogue.catalogueType !== 'catalogue' || !Array.isArray(catalogue.records)) fail('catalogue_schema_invalid')
  digestField(catalogue.recordsSha256, 'catalogue_digest_invalid')
  if (digest(catalogue.records) !== catalogue.recordsSha256) fail('catalogue_digest_mismatch')
  const records = catalogue.records.map(validateRecord)
  if (new Set(records.map((record) => `${record.entryId}@${record.version}`)).size !== records.length) fail('catalogue_duplicate_record')
  return Object.freeze({ source: LIBRARY_V2_SOURCE, digest: catalogue.recordsSha256, records })
}

export function pageCatalogue(snapshot, { cursor = undefined, limit = 20 } = {}) {
  if (!snapshot?.source || snapshot.source.commit !== LIBRARY_V2_SOURCE.commit || snapshot.source.tree !== LIBRARY_V2_SOURCE.tree) fail('snapshot_source_mismatch')
  if (!Number.isInteger(limit) || limit < 1 || limit > 50) fail('page_limit_invalid')
  let offset = 0
  if (cursor !== undefined) {
    let parsed; try { parsed = JSON.parse(Buffer.from(cursor, 'base64url').toString('utf8')) } catch { fail('cursor_invalid') }
    keys(parsed, new Set(['commit', 'tree', 'digest', 'offset']))
    if (parsed.commit !== snapshot.source.commit || parsed.tree !== snapshot.source.tree || parsed.digest !== snapshot.digest || !Number.isInteger(parsed.offset) || parsed.offset < 0) fail('cursor_snapshot_mismatch')
    offset = parsed.offset
  }
  const records = snapshot.records.slice(offset, offset + limit).map(({ entryId, version, artifactType, name, summary, lifecycle, selectability, compatibility }) => ({ entryId, version, artifactType, name, summary, lifecycle, selectability, compatibility }))
  const next = offset + records.length < snapshot.records.length ? Buffer.from(JSON.stringify({ commit: snapshot.source.commit, tree: snapshot.source.tree, digest: snapshot.digest, offset: offset + records.length })).toString('base64url') : undefined
  return Object.freeze({ records, nextCursor: next, catalogueDigest: snapshot.digest })
}

const manifestKeys = new Set(['schemaVersion', 'schemaRevision', 'manifestType', 'releaseId', 'entryId', 'artifactType', 'version', 'libraryCommitSha', 'gitTreeSha1', 'payloadSha256', 'inventorySha256', 'dependencyLockSha256', 'extension', 'controlledMetadata', 'externalReferences'])
export function validateManifest(manifest, record) {
  keys(manifest, manifestKeys)
  if (manifest.schemaVersion !== 2 || manifest.schemaRevision !== 2 || manifest.manifestType !== 'immutable_release') fail('manifest_schema_invalid')
  for (const field of ['releaseId', 'entryId', 'artifactType', 'version']) text(manifest[field], 'manifest_field_missing')
  for (const field of ['payloadSha256', 'inventorySha256', 'dependencyLockSha256']) digestField(manifest[field], 'manifest_digest_invalid')
  if (manifest.libraryCommitSha !== LIBRARY_V2_SOURCE.commit || manifest.entryId !== record.entryId || manifest.version !== record.version || manifest.artifactType !== record.artifactType || manifest.gitTreeSha1 !== record.gitTreeSha1 || manifest.inventorySha256 !== record.inventorySha256) fail('manifest_record_mismatch')
  return Object.freeze({ ...manifest })
}

export function validateInventory(inventory, manifest) {
  keys(inventory, new Set(['schemaVersion', 'schemaRevision', 'inventoryType', 'root', 'complete', 'symlinks', 'entries', 'inventorySha256', 'treeSha1']))
  if (inventory.schemaVersion !== 2 || inventory.schemaRevision !== 2 || inventory.inventoryType !== 'exhaustive_tree_inventory' || inventory.complete !== true || inventory.symlinks !== false || !Array.isArray(inventory.entries)) fail('inventory_schema_invalid')
  if (inventory.treeSha1 !== manifest.gitTreeSha1 || inventory.inventorySha256 !== manifest.inventorySha256 || digest(inventory.entries) !== inventory.inventorySha256) fail('inventory_digest_mismatch')
  return Object.freeze({ ...inventory })
}

export function validateClosure(closure, manifest) {
  keys(closure, new Set(['schemaVersion', 'schemaRevision', 'closureType', 'dependencyLockSha256', 'members']))
  if (closure.schemaVersion !== 2 || closure.schemaRevision !== 2 || closure.closureType !== 'dependency_closure' || !Array.isArray(closure.members) || closure.dependencyLockSha256 !== manifest.dependencyLockSha256) fail('closure_schema_invalid')
  if (new Set(closure.members.map((member) => JSON.stringify(stable(member)))).size !== closure.members.length) fail('closure_duplicate_member')
  return Object.freeze({ ...closure })
}

export function selectV2({ snapshot, entryId, version, manifest, inventory, closure, materializedTreeSha1, consumerId, consumptionMode, now = new Date().toISOString(), expiresAt = new Date(Date.now() + 60 * 60 * 1000).toISOString() }) {
  const record = snapshot.records.find((item) => item.entryId === entryId && item.version === version)
  if (!record) fail('shortlist_record_missing')
  const checkedManifest = validateManifest(manifest, record)
  if (digest(manifest) !== record.releaseManifestSha256) fail('manifest_digest_mismatch')
  validateInventory(inventory, checkedManifest); validateClosure(closure, checkedManifest)
  if (materializedTreeSha1 !== checkedManifest.gitTreeSha1 || !SHA1.test(materializedTreeSha1 ?? '')) fail('materialized_tree_mismatch')
  text(consumerId, 'receipt_consumer_missing'); text(consumptionMode, 'receipt_mode_missing')
  if (!Number.isFinite(Date.parse(now)) || !Number.isFinite(Date.parse(expiresAt)) || Date.parse(expiresAt) <= Date.parse(now)) fail('receipt_expiry_invalid')
  const receipt = { schemaVersion: 2, schemaRevision: 2, receiptType: 'consumption', consumerId, consumptionMode, result: 'pass', issuedAt: now, expiresAt, providerCommit: snapshot.source.commit, providerTree: snapshot.source.tree, catalogueDigest: snapshot.digest, entryId, version, releaseManifestSha256: record.releaseManifestSha256, inventorySha256: checkedManifest.inventorySha256, dependencyLockSha256: checkedManifest.dependencyLockSha256, closureSha256: digest(closure), materializedTreeSha1 }
  return Object.freeze({ selected: Object.freeze({ record, manifest: checkedManifest, inventory, closure }), receipt: Object.freeze({ ...receipt, receiptSha256: digest(receipt) }) })
}

export function verifyCachedReceipt(receipt, { offline = false, now = Date.now() } = {}) {
  keys(receipt, new Set(['schemaVersion', 'schemaRevision', 'receiptType', 'consumerId', 'consumptionMode', 'result', 'issuedAt', 'expiresAt', 'providerCommit', 'providerTree', 'catalogueDigest', 'entryId', 'version', 'releaseManifestSha256', 'inventorySha256', 'dependencyLockSha256', 'closureSha256', 'materializedTreeSha1', 'receiptSha256']))
  if (receipt.schemaVersion !== 2 || receipt.schemaRevision !== 2 || receipt.receiptType !== 'consumption' || receipt.result !== 'pass') fail('cache_receipt_invalid')
  assertFrozenSource({ commit: receipt.providerCommit, tree: receipt.providerTree })
  if (!Number.isFinite(Date.parse(receipt.issuedAt)) || !Number.isFinite(Date.parse(receipt.expiresAt)) || Date.parse(receipt.expiresAt) <= now) fail('cache_receipt_stale')
  for (const field of ['catalogueDigest', 'releaseManifestSha256', 'inventorySha256', 'dependencyLockSha256', 'closureSha256']) digestField(receipt[field], 'cache_digest_invalid')
  const { receiptSha256, ...unsigned } = receipt
  if (digest(unsigned) !== receiptSha256) fail('cache_receipt_tampered')
  return Object.freeze({ ...receipt, offline })
}
