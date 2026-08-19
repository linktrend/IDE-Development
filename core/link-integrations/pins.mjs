/**
 * Frozen consumer pins for the five LiNK providers.
 *
 * Each pin is the GitHub `development` tip of that provider repository at
 * WP-I6-S0 freeze time (read-only `gh api repos/linktrend/<Provider>/commits/development`).
 * Local sibling checkout HEADs are not pins. Live `HEAD` / `latest` is not a pin.
 *
 * This module is inventory only. It has no transport, credentials, Git write,
 * Ledger, or Gate mutation APIs.
 */

const GIT_SHA = /^[a-f0-9]{40}$/

/** @typedef {{ repository: string, commit: string, tree: string }} FrozenProviderPin */

/**
 * Pin authority. Sibling clones and other local checkouts must not replace these
 * identities, even when they are ahead of `origin/development`.
 */
export const PIN_AUTHORITY = Object.freeze({
  source: 'github_development_tip',
  owner: 'linktrend',
  ref: 'development',
  frozenOn: '2026-08-19',
  siblingCheckoutHeadsAreNotPins: true,
})

export const FROZEN_PROVIDER_KEYS = Object.freeze([
  'platform',
  'libraries',
  'brain',
  'skills',
  'autowork',
])

/**
 * @param {string} repository
 * @param {string} commit
 * @param {string} tree
 * @returns {FrozenProviderPin}
 */
function pin(repository, commit, tree) {
  if (typeof repository !== 'string' || !repository.startsWith('linktrend/')) {
    throw new Error('provider pin repository must be a linktrend GitHub identity')
  }
  if (!GIT_SHA.test(commit) || !GIT_SHA.test(tree)) {
    throw new Error(`provider pin ${repository} must use 40-character lowercase git SHAs`)
  }
  return Object.freeze({ repository, commit, tree })
}

export const FROZEN_PROVIDERS = Object.freeze({
  platform: pin(
    'linktrend/LiNKplatform',
    'adbabf7d399cbfe5c1056d275c3d98eb480397cc',
    'b76993f458b6dbed5d2c3e09c2c5e8ad87c6a45d',
  ),
  libraries: pin(
    'linktrend/LiNKlibraries',
    '4cbe7fb174aba4b159d6c37ba1ef65fd3221510f',
    '60e582fbd1ce988538b650c99878e700c6cfa0d2',
  ),
  brain: pin(
    'linktrend/LiNKbrain',
    '9042e668dd0c7cef232cb427ffc9c76f06a7a446',
    '303a15936932fb5a54b208c934a6d511045cc8e4',
  ),
  skills: pin(
    'linktrend/LiNKskills',
    'e3d80fd22a05a4f68207e130c50b772b5acffda4',
    '69a131b46a73a4ef724694bfe240b1a11652bcc9',
  ),
  autowork: pin(
    'linktrend/LiNKautowork',
    '79ee98eb3bd1ae0cce9d34872e90fe7101a9f353',
    'deb37e4f3a29339b35613ee799d461c74bb7b585',
  ),
})

if (Object.keys(FROZEN_PROVIDERS).length !== FROZEN_PROVIDER_KEYS.length) {
  throw new Error('FROZEN_PROVIDERS must contain exactly the five named providers')
}
for (const key of FROZEN_PROVIDER_KEYS) {
  if (!FROZEN_PROVIDERS[key]) {
    throw new Error(`FROZEN_PROVIDERS missing ${key}`)
  }
}
