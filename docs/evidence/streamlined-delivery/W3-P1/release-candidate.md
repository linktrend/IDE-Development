# W3-P1 release-candidate evidence

This directory is the stable, committed evidence location for the W3-P1
release candidate. Binary archives and generated checksums remain under the
ignored `build/release-candidate/` directory and are never committed.

The final candidate must contain:

- `build/release-candidate/release-candidate.json`;
- `build/release-candidate/SHA256SUMS.json`;
- version, source commit, manifest SHA-256, archive sizes and archive SHA-256
  values from the official release-candidate CLI;
- the exact archive verification output and disposable-consumer result;
- no credentials, absolute checkout paths, host-only coordinator files, or
  nested `.ide-development/` install in this system repository.

The packet executor does not publish a tag or release. Terra owns live release
publication after independent verification of this evidence.
