import os
from pathlib import Path


def snapshot_dir() -> Path:
    """Root directory of the baked vg13 snapshot."""
    return Path(os.environ.get("VG_SNAPSHOT_DIR", "/snapshot"))


def cache_dir() -> Path:
    """Disk cache root for DMI conversions."""
    d = Path(os.environ.get("VG_CACHE_DIR", "/var/cache/vgstation13-mcp"))
    d.mkdir(parents=True, exist_ok=True)
    return d


def read_snapshot_sha() -> str:
    sha_file = snapshot_dir() / "SHA"
    if not sha_file.exists():
        return "unknown"
    return sha_file.read_text().strip()
