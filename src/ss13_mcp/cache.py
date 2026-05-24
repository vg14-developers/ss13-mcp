"""Disk LRU cache for DMI conversions, keyed by (snapshot_sha, dmi_path, state)."""

import hashlib
import os
import time
from pathlib import Path

from ss13_mcp.snapshot import cache_dir, read_snapshot_sha

MAX_BYTES = int(os.environ.get("SS13_CACHE_MAX_BYTES", str(5 * 1024 * 1024 * 1024)))


def _key(dmi_path: str, state: str | None) -> str:
    raw = f"{read_snapshot_sha()}:{dmi_path}:{state or '*'}"
    return hashlib.sha256(raw.encode()).hexdigest()


def slot(dmi_path: str, state: str | None) -> Path:
    return cache_dir() / "conversions" / _key(dmi_path, state)


def is_hit(dmi_path: str, state: str | None) -> bool:
    s = slot(dmi_path, state)
    return (s / "meta.json").exists()


def touch(dmi_path: str, state: str | None) -> None:
    s = slot(dmi_path, state)
    (s / ".touch").write_text(str(time.time()))


def evict_if_needed() -> None:
    root = cache_dir() / "conversions"
    if not root.exists():
        return
    entries: list[tuple[float, Path, int]] = []
    total = 0
    for slot_dir in root.iterdir():
        if not slot_dir.is_dir():
            continue
        size = sum(p.stat().st_size for p in slot_dir.rglob("*") if p.is_file())
        touch_file = slot_dir / ".touch"
        last = touch_file.stat().st_mtime if touch_file.exists() else slot_dir.stat().st_mtime
        entries.append((last, slot_dir, size))
        total += size
    if total <= MAX_BYTES:
        return
    entries.sort()
    for _, slot_dir, size in entries:
        if total <= MAX_BYTES:
            break
        for p in slot_dir.rglob("*"):
            if p.is_file():
                p.unlink()
        slot_dir.rmdir()
        total -= size
