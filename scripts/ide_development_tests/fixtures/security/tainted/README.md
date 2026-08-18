# Tainted security fixtures

Intentional realistic credential vectors are **not** stored as tracked files.
Lane E / WP-U10 positive controls generate GitHub PAT and PEM headers at runtime
in isolated temp content so detector coverage remains without leaving approvable
realistic credentials in the factory tree.
