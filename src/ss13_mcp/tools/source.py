import re
from pathlib import Path

from ss13_mcp.snapshot import ss13_dir

_MAX_PER_FILE = 50  # cap per-file hits so a runaway match in one file can't drown out the result


def _resolve(path: str) -> Path:
    """Resolve `path` under the SS13 checkout; reject escapes."""
    root = ss13_dir().resolve()
    target = (root / path).resolve()
    if root not in target.parents and target != root:
        raise ValueError(f"path is outside SS13 checkout: {path}")
    return target


def list_dir(path: str) -> list[dict]:
    target = _resolve(path)
    if not target.exists():
        raise FileNotFoundError(path)
    if not target.is_dir():
        raise NotADirectoryError(path)
    out = []
    for entry in sorted(target.iterdir()):
        out.append(
            {
                "name": entry.name,
                "type": "dir" if entry.is_dir() else "file",
                "size": entry.stat().st_size if entry.is_file() else None,
            }
        )
    return out


def read_file(path: str, range: list[int] | None = None) -> str:
    """Read a file from the SS13 checkout. `range` is an optional [start, end] 1-indexed line range."""
    target = _resolve(path)
    if not target.exists():
        raise FileNotFoundError(path)
    if not target.is_file():
        raise IsADirectoryError(path)
    text = target.read_text(encoding="utf-8", errors="replace")
    if range is None:
        return text
    start, end = range
    lines = text.splitlines(keepends=True)
    return "".join(lines[start - 1 : end])


def search_files(pattern: str, glob: str | None = None, limit: int = 200) -> list[dict]:
    """Regex search across the SS13 checkout. Returns up to `limit` hits.

    `pattern` is a Python regex. `glob` is a pathlib-style glob relative to the
    checkout root (e.g. `code/**/*.dm`); without it, every file under the root is
    scanned. Binary files and files that can't be decoded as UTF-8 are skipped.
    """
    try:
        regex = re.compile(pattern)
    except re.error as e:
        raise ValueError(f"invalid regex {pattern!r}: {e}") from e

    root = ss13_dir().resolve()
    files = root.glob(glob) if glob else root.rglob("*")

    out: list[dict] = []
    for path in files:
        if not path.is_file():
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        rel = path.relative_to(root).as_posix()
        per_file = 0
        for lineno, line in enumerate(text.splitlines(), 1):
            if regex.search(line):
                out.append({"path": rel, "line": lineno, "text": line})
                per_file += 1
                if len(out) >= limit or per_file >= _MAX_PER_FILE:
                    break
        if len(out) >= limit:
            break
    return out
