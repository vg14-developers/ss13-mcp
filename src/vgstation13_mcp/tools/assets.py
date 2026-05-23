import base64
import json
import mimetypes
from pathlib import Path

from vgstation13_mcp import cache, dmi, rsi
from vgstation13_mcp.snapshot import snapshot_dir


def _resolve(path: str) -> Path:
    root = snapshot_dir().resolve()
    target = (root / path).resolve()
    if root not in target.parents and target != root:
        raise ValueError(f"path outside snapshot: {path}")
    return target


def read_asset(path: str) -> dict:
    target = _resolve(path)
    if not target.exists() or not target.is_file():
        raise FileNotFoundError(path)
    data = target.read_bytes()
    mime, _ = mimetypes.guess_type(str(target))
    if path.endswith(".dmi"):
        mime = "image/png"
    return {
        "size": len(data),
        "mime": mime or "application/octet-stream",
        "bytes_b64": base64.b64encode(data).decode("ascii"),
    }


def list_dmi_states(dmi_path: str) -> list[dict]:
    target = _resolve(dmi_path)
    if not target.exists():
        raise FileNotFoundError(dmi_path)
    return dmi.list_states(target)


def convert_dmi(dmi_path: str, state: str | None = None) -> dict:
    target = _resolve(dmi_path)
    if not target.exists():
        raise FileNotFoundError(dmi_path)

    slot = cache.slot(dmi_path, state)
    hit = cache.is_hit(dmi_path, state)

    if not hit:
        parsed = dmi.load_dmi(target)
        slot.mkdir(parents=True, exist_ok=True)
        rsi.write_rsi(parsed, slot, state_filter=state)
        cache.evict_if_needed()

    cache.touch(dmi_path, state)

    meta = json.loads((slot / "meta.json").read_text())
    return {
        "rsi_path": str(slot),
        "states": [s["name"] for s in meta["states"]],
        "url": None,
        "cache_hit": hit,
    }
