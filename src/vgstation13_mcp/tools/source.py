from pathlib import Path

from vgstation13_mcp.snapshot import snapshot_dir


def _resolve(path: str) -> Path:
    """Resolve `path` under the snapshot root; reject escapes."""
    root = snapshot_dir().resolve()
    target = (root / path).resolve()
    if root not in target.parents and target != root:
        raise ValueError(f"path is outside snapshot: {path}")
    return target


def list_dir(path: str) -> list[dict]:
    """List entries in a snapshot directory."""
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
    """Read a snapshot file. `range` is an optional [start, end] 1-indexed line range."""
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
