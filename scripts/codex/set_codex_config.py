#!/usr/bin/env python3
"""Set a top-level string key in a Codex ``config.toml`` without changing TOML scope.

Appending ``key = "value"`` after a ``[table]`` header puts the key inside that table, so the
key is written before the first table header instead. Any earlier top-level definition is
replaced. Keys of the same name inside tables are left alone. The result is parsed with
``tomllib`` and must equal the original document plus the one key, otherwise nothing is written.

Usage: set_codex_config.py CONFIG [KEY VALUE]   (default: cli_auth_credentials_store "file")
"""

from __future__ import annotations

import json
import os
import re
import sys
import tomllib
from pathlib import Path

DEFAULT_KEY = "cli_auth_credentials_store"
DEFAULT_VALUE = "file"
TABLE_RE = re.compile(r"^\s*\[")


class ConfigError(RuntimeError):
    pass


def set_top_level(text: str, key: str, value: str) -> str:
    try:
        original = tomllib.loads(text)
    except tomllib.TOMLDecodeError as exc:
        raise ConfigError(f"existing config is not valid TOML: {exc}") from exc
    if original.get(key) == value:
        return text
    lines = text.splitlines(keepends=True)
    first_table = next((i for i, line in enumerate(lines) if TABLE_RE.match(line)), len(lines))
    key_re = re.compile(rf"^\s*{re.escape(key)}\s*=")
    top = [line for line in lines[:first_table] if not key_re.match(line)]
    updated = f"{key} = {json.dumps(value)}\n" + "".join(top) + "".join(lines[first_table:])
    try:
        parsed = tomllib.loads(updated)
    except tomllib.TOMLDecodeError as exc:
        raise ConfigError(f"refusing to write: update would not be valid TOML: {exc}") from exc
    expected = {**original, key: value}
    if parsed != expected:
        raise ConfigError("refusing to write: update would change other settings")
    return updated


def update_file(path: Path, key: str = DEFAULT_KEY, value: str = DEFAULT_VALUE) -> bool:
    text = path.read_text() if path.exists() else ""
    updated = set_top_level(text, key, value)
    if updated == text and path.exists():
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    fd = os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w") as handle:
        handle.write(updated)
    os.replace(tmp, path)
    os.chmod(path, 0o600)
    return True


def main(argv: list[str]) -> int:
    if len(argv) not in (1, 3):
        print(__doc__, file=sys.stderr)
        return 2
    key, value = (argv[1], argv[2]) if len(argv) == 3 else (DEFAULT_KEY, DEFAULT_VALUE)
    try:
        changed = update_file(Path(argv[0]), key, value)
    except (ConfigError, OSError) as exc:
        print(f"set_codex_config: {exc}", file=sys.stderr)
        return 1
    print(f"{argv[0]}: {key} = {json.dumps(value)} ({'updated' if changed else 'unchanged'})")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
