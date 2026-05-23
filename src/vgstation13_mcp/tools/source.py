import json
import shutil
import subprocess
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


def search_files(pattern: str, glob: str | None = None, limit: int = 200) -> list[dict]:
    """Ripgrep search across snapshot source. Returns up to `limit` hits."""
    rg = shutil.which("rg")
    if not rg:
        raise RuntimeError("ripgrep (rg) not installed")
    args = [rg, "--json", "--max-count", "50", pattern]
    if glob:
        args += ["--glob", glob]
    args.append(".")
    root = snapshot_dir().resolve()
    proc = subprocess.run(args, capture_output=True, text=True, check=False, cwd=str(root))
    if proc.returncode not in (0, 1):  # 1 = no matches, still success
        raise RuntimeError(f"ripgrep failed: {proc.stderr.strip()}")
    out: list[dict] = []
    for line in proc.stdout.splitlines():
        if not line:
            continue
        event = json.loads(line)
        if event.get("type") != "match":
            continue
        data = event["data"]
        raw_path = data["path"]["text"]
        # rg emits paths relative to its cwd (e.g. "./code/..." or "code\\...")
        rel_path = Path(raw_path)
        if rel_path.is_absolute():
            try:
                rel_path = rel_path.relative_to(root)
            except ValueError:
                continue
        rel = rel_path.as_posix().lstrip("./")
        out.append(
            {
                "path": rel,
                "line": data["line_number"],
                "text": data["lines"]["text"].rstrip("\n"),
            }
        )
        if len(out) >= limit:
            break
    return out
