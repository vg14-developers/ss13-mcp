import base64
import mimetypes
from pathlib import Path

from vgstation13_mcp import dmi, rsi
from vgstation13_mcp.snapshot import cache_dir, snapshot_dir


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
    parsed = dmi.load_dmi(target)
    rel = Path(dmi_path).with_suffix("")
    state_part = state or "all"
    out_dir = cache_dir() / "conversions" / str(rel) / state_part
    out_dir.mkdir(parents=True, exist_ok=True)
    rsi.write_rsi(parsed, out_dir, state_filter=state)
    return {
        "rsi_path": str(out_dir),
        "states": [s.name for s in parsed.states if not state or s.name == state],
        "url": None,
    }
