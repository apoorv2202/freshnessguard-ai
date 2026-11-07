"""Explicit local env-file loading; never prints values or executes file contents."""
import os
from pathlib import Path

ALLOWED = {"TAVILY_API_KEY", "BIFROST_URL", "BIFROST_MODEL", "BIFROST_VIRTUAL_KEY", "FRESHNESSGUARD_TOKEN"}


def load_env(path):
    if path is None:
        return
    for line in Path(path).read_text(encoding="utf-8-sig").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        key, sep, value = line.partition("=")
        key, value = key.strip(), value.strip()
        if not sep or key not in ALLOWED:
            raise ValueError("Unsupported entry in environment file")
        if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
            value = value[1:-1]
        if value:
            os.environ[key] = value
