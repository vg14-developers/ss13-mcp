"""Minimal DMI parser. Reads BYOND zTXt 'Description' metadata from a DMI."""

import re
import zlib
from dataclasses import dataclass
from pathlib import Path

from PIL import Image


@dataclass
class DmiState:
    name: str
    dirs: int
    frames: int
    delay: list[float]
    loop: int
    rewind: bool
    movement: bool


@dataclass
class Dmi:
    width: int
    height: int
    states: list[DmiState]
    image: Image.Image  # full sprite sheet


def _read_ztxt_description(png_bytes: bytes) -> str:
    """Extract the BYOND 'Description' zTXt chunk from a DMI."""
    i = 8  # skip PNG signature
    while i < len(png_bytes):
        length = int.from_bytes(png_bytes[i : i + 4], "big")
        ctype = png_bytes[i + 4 : i + 8]
        data = png_bytes[i + 8 : i + 8 + length]
        if ctype == b"zTXt":
            keyword, rest = data.split(b"\x00", 1)
            if keyword == b"Description":
                # rest = compression_method(1 byte) + compressed_text
                return zlib.decompress(rest[1:]).decode("latin-1")
        if ctype == b"IEND":
            break
        i += 8 + length + 4  # length + type + data + crc
    raise ValueError("DMI has no Description zTXt chunk")


_KV = re.compile(r"\s*(\w+)\s*=\s*(.+)")


def _parse_metadata(desc: str) -> tuple[int, int, list[DmiState]]:
    width = height = 32
    states: list[DmiState] = []
    cur: dict | None = None

    def flush():
        if cur is not None:
            states.append(
                DmiState(
                    name=cur["name"],
                    dirs=cur.get("dirs", 1),
                    frames=cur.get("frames", 1),
                    delay=cur.get("delay", []),
                    loop=cur.get("loop", 0),
                    rewind=cur.get("rewind", False),
                    movement=cur.get("movement", False),
                )
            )

    for line in desc.splitlines():
        if line.startswith("#") or not line.strip():
            continue
        if line.startswith("state"):
            flush()
            m = re.match(r'state\s*=\s*"(.*)"', line)
            cur = {"name": m.group(1)} if m else None
            continue
        m = _KV.match(line)
        if not m:
            continue
        k, v = m.group(1), m.group(2).strip()
        if k == "width":
            width = int(v)
        elif k == "height":
            height = int(v)
        elif cur is not None:
            if k in ("dirs", "frames", "loop"):
                cur[k] = int(v)
            elif k == "delay":
                cur[k] = [float(x) for x in v.split(",")]
            elif k in ("rewind", "movement"):
                cur[k] = v.strip() == "1"
    flush()
    return width, height, states


def load_dmi(path: Path) -> Dmi:
    raw = path.read_bytes()
    desc = _read_ztxt_description(raw)
    width, height, states = _parse_metadata(desc)
    img = Image.open(path).convert("RGBA")
    return Dmi(width=width, height=height, states=states, image=img)


def list_states(path: Path) -> list[dict]:
    dmi = load_dmi(path)
    return [
        {
            "name": s.name,
            "dirs": s.dirs,
            "frames": s.frames,
            "delay": s.delay,
            "loop": s.loop,
            "rewind": s.rewind,
            "movement": s.movement,
        }
        for s in dmi.states
    ]
