import json
from functools import lru_cache

from vgstation13_mcp.snapshot import snapshot_dir


@lru_cache(maxsize=1)
def _types() -> dict:
    f = snapshot_dir() / "index" / "types.json"
    if not f.exists():
        return {}
    return json.loads(f.read_text())


@lru_cache(maxsize=1)
def _procs() -> dict:
    f = snapshot_dir() / "index" / "procs.json"
    return json.loads(f.read_text()) if f.exists() else {}


@lru_cache(maxsize=1)
def _vars() -> dict:
    f = snapshot_dir() / "index" / "vars.json"
    return json.loads(f.read_text()) if f.exists() else {}


@lru_cache(maxsize=1)
def _paths() -> list[str]:
    f = snapshot_dir() / "index" / "paths.idx"
    return f.read_text().splitlines() if f.exists() else []


def get_type(path: str) -> dict:
    types = _types()
    if path not in types:
        raise KeyError(path)
    return {"path": path, **types[path]}


def list_subtypes(path: str, transitive: bool = False) -> list[str]:
    types = _types()
    if path not in types:
        raise KeyError(path)
    if not transitive:
        return list(types[path]["children"])
    out: list[str] = []
    stack = list(types[path]["children"])
    while stack:
        cur = stack.pop()
        out.append(cur)
        stack.extend(types.get(cur, {}).get("children", []))
    return sorted(out)
