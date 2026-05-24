import os
from pathlib import Path

from platformdirs import user_cache_dir

_APP_NAME = "vgstation13-mcp"


def _default_root() -> Path:
    return Path(user_cache_dir(_APP_NAME))


def snapshot_dir() -> Path:
    """Root directory of the materialized vg13 snapshot."""
    return Path(os.environ.get("VG_SNAPSHOT_DIR", str(_default_root() / "snapshot")))


def cache_dir() -> Path:
    """Disk cache root for DMI conversions."""
    d = Path(os.environ.get("VG_CACHE_DIR", str(_default_root() / "conversions")))
    d.mkdir(parents=True, exist_ok=True)
    return d


def read_snapshot_sha() -> str:
    sha_file = snapshot_dir() / "SHA"
    if not sha_file.exists():
        return "unknown"
    return sha_file.read_text().strip()
