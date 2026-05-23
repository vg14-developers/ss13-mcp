import json
import re
from functools import lru_cache

from vgstation13_mcp.snapshot import snapshot_dir


@lru_cache(maxsize=1)
def _index() -> list[dict]:
    f = snapshot_dir() / "wiki" / "index.json"
    return json.loads(f.read_text()) if f.exists() else []


def wiki_read(page: str) -> str:
    f = snapshot_dir() / "wiki" / f"{page}.md"
    if not f.exists():
        raise FileNotFoundError(page)
    return f.read_text()


def wiki_search(query: str, limit: int = 25) -> list[dict]:
    q = query.lower()
    pattern = re.compile(re.escape(q), re.IGNORECASE)
    out: list[dict] = []
    for entry in _index():
        page = entry["page"]
        try:
            text = wiki_read(page)
        except FileNotFoundError:
            continue
        m = pattern.search(text)
        if m:
            start = max(0, m.start() - 80)
            end = min(len(text), m.end() + 80)
            excerpt = text[start:end].replace("\n", " ").strip()
            out.append({"page": page, "title": entry["title"], "excerpt": excerpt})
        if len(out) >= limit:
            break
    return out
