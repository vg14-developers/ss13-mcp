import json
from difflib import SequenceMatcher
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


def _in_scope(type_path: str, scope: str | None) -> bool:
    if scope is None:
        return True
    return type_path == scope or type_path.startswith(scope + "/")


def find_proc(name: str, scope: str | None = None) -> list[dict]:
    hits = _procs().get(name, [])
    return [h for h in hits if _in_scope(h["type"], scope)]


def find_var(name: str, scope: str | None = None) -> list[dict]:
    hits = _vars().get(name, [])
    return [h for h in hits if _in_scope(h["type"], scope)]


def path_lookup(query: str, limit: int = 50) -> list[dict]:
    paths = _paths()
    # Exact match first.
    out: list[dict] = []
    if query in paths:
        out.append({"path": query, "score": 1.0})
    # Then fuzzy ranked by ratio against the last path segment + full path.
    q_lower = query.lower().lstrip("/")
    scored: list[tuple[float, str]] = []
    for p in paths:
        if p == query:
            continue
        seg = p.rsplit("/", 1)[-1].lower()
        score = max(
            SequenceMatcher(None, q_lower, seg).ratio(),
            SequenceMatcher(None, q_lower, p.lower()).ratio() * 0.8,
        )
        if score >= 0.4:
            scored.append((score, p))
    scored.sort(reverse=True)
    for score, p in scored[: limit - len(out)]:
        out.append({"path": p, "score": round(score, 3)})
    return out[:limit]
