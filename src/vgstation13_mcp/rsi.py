"""Writes a Robust SS14 RSI directory from a parsed DMI."""

import json
from pathlib import Path

from PIL import Image

from vgstation13_mcp.dmi import Dmi, DmiState

DIR_NAMES_4 = ["South", "North", "East", "West"]
DIR_NAMES_8 = [*DIR_NAMES_4, "SouthEast", "SouthWest", "NorthEast", "NorthWest"]


def _safe(name: str) -> str:
    return name.replace("/", "_").replace(" ", "_") or "_unnamed"


def _crop_state(dmi: Dmi, state_idx: int) -> list[Image.Image]:
    cells_per_row = dmi.image.width // dmi.width
    cells_consumed = 0
    for s in dmi.states[:state_idx]:
        cells_consumed += s.dirs * s.frames
    frames: list[Image.Image] = []
    state = dmi.states[state_idx]
    for i in range(state.dirs * state.frames):
        idx = cells_consumed + i
        x = (idx % cells_per_row) * dmi.width
        y = (idx // cells_per_row) * dmi.height
        frames.append(dmi.image.crop((x, y, x + dmi.width, y + dmi.height)))
    return frames


def _state_to_rsi(state: DmiState, frames: list[Image.Image]) -> tuple[dict, Image.Image]:
    w = frames[0].width
    h = frames[0].height
    out = Image.new("RGBA", (w * len(frames), h), (0, 0, 0, 0))
    for i, frm in enumerate(frames):
        out.paste(frm, (i * w, 0))
    if state.dirs == 1:
        directions = 1
        delays = [state.delay or [1.0] * state.frames]
    elif state.dirs == 4:
        directions = 4
        delays = [state.delay or [1.0] * state.frames] * 4
    else:
        directions = 8
        delays = [state.delay or [1.0] * state.frames] * 8
    meta: dict = {"name": state.name, "directions": directions}
    if state.frames > 1 or state.delay:
        meta["delays"] = delays
    return meta, out


def write_rsi(dmi: Dmi, out_dir: Path, state_filter: str | None = None) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    meta_states = []
    for i, s in enumerate(dmi.states):
        if state_filter and s.name != state_filter:
            continue
        frames = _crop_state(dmi, i)
        meta_entry, sheet = _state_to_rsi(s, frames)
        png_path = out_dir / f"{_safe(s.name)}.png"
        sheet.save(png_path, format="PNG")
        meta_states.append(meta_entry)
    meta = {
        "version": 1,
        "license": "CC-BY-SA-3.0",
        "copyright": "Ported from vgstation13",
        "size": {"x": dmi.width, "y": dmi.height},
        "states": meta_states,
    }
    (out_dir / "meta.json").write_text(json.dumps(meta, indent=2))
