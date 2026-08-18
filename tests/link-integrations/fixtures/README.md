# Consumer contract fixtures

Layout only for WP-I6-S0. Later packets own their subdirectories:

- `platform/` — WP-I6-S1
- `libraries/` — WP-I6-S2
- `brain/` — WP-I6-S3
- `skills/` — WP-I6-S4
- `autowork/` — WP-I6-S5

Fixtures are local and synthetic. Do not call live provider runtimes. Do not
store secrets, tokens, private keys, or customer data. Until `v2.4.0` Update 10
is installed, do not add realistic live-looking tokens.
