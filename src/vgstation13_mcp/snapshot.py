import json
import os
from pathlib import Path

from platformdirs import user_cache_dir

_APP_NAME = "vgstation13-mcp"


def _default_root() -> Path:
    return Path(user_cache_dir(_APP_NAME))


def snapshot_dir() -> Path:
    """Root directory of generated state (DM index, dmm-tools binary, config)."""
    return Path(os.environ.get("VG_SNAPSHOT_DIR", str(_default_root() / "snapshot")))


def cache_dir() -> Path:
    """Disk cache root for DMI conversions."""
    d = Path(os.environ.get("VG_CACHE_DIR", str(_default_root() / "conversions")))
    d.mkdir(parents=True, exist_ok=True)
    return d


def config_path() -> Path:
    return snapshot_dir() / "config.json"


def is_configured() -> bool:
    return config_path().exists()


def load_config() -> dict:
    """Return the persisted config. Raises if setup has not been run."""
    p = config_path()
    if not p.exists():
        raise RuntimeError(
            "vgstation13-mcp is not set up yet. Ask the user where their vgstation13 "
            "checkout lives (or where they'd like one cloned), then call the `setup` "
            "tool with vg13_path=<that path>."
        )
    return json.loads(p.read_text())


def write_config(cfg: dict) -> None:
    snapshot_dir().mkdir(parents=True, exist_ok=True)
    config_path().write_text(json.dumps(cfg, indent=2))


def vg13_dir() -> Path:
    """Path to the user's vgstation13 checkout. Env var wins for tests/overrides."""
    env = os.environ.get("VG13_PATH")
    if env:
        return Path(env)
    return Path(load_config()["vg13_path"])


def read_snapshot_sha() -> str:
    try:
        cfg = load_config()
    except RuntimeError:
        return "unknown"
    return cfg.get("vg13_sha", "unknown")
