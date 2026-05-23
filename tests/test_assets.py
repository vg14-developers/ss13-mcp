import base64
import json
import time
from pathlib import Path as pathlib_Path

import pytest

from vgstation13_mcp.tools.assets import convert_dmi, list_dmi_states, read_asset


def test_read_asset_returns_base64(fixture_snapshot):
    out = read_asset("sound/blip.ogg")
    decoded = base64.b64decode(out["bytes_b64"])
    assert decoded.startswith(b"OggS")
    assert out["size"] == len(decoded)
    assert out["mime"] == "audio/ogg"


def test_read_asset_missing(fixture_snapshot):
    with pytest.raises(FileNotFoundError):
        read_asset("sound/missing.ogg")


def test_list_dmi_states_returns_idle_and_active(fixture_snapshot):
    states = list_dmi_states("icons/test.dmi")
    names = {s["name"] for s in states}
    assert names == {"idle", "active"}
    for s in states:
        assert s["dirs"] == 1
        assert s["frames"] == 1


def test_convert_dmi_full(fixture_snapshot, tmp_path):
    result = convert_dmi("icons/test.dmi")
    rsi_dir = pathlib_Path(result["rsi_path"])
    assert (rsi_dir / "meta.json").exists()
    meta = json.loads((rsi_dir / "meta.json").read_text())
    assert meta["version"] == 1
    assert meta["size"] == {"x": 32, "y": 32}
    state_names = {s["name"] for s in meta["states"]}
    assert state_names == {"idle", "active"}
    assert (rsi_dir / "idle.png").exists()
    assert (rsi_dir / "active.png").exists()


def test_convert_dmi_single_state(fixture_snapshot, tmp_path):
    result = convert_dmi("icons/test.dmi", state="idle")
    rsi_dir = pathlib_Path(result["rsi_path"])
    meta = json.loads((rsi_dir / "meta.json").read_text())
    state_names = {s["name"] for s in meta["states"]}
    assert state_names == {"idle"}


def test_convert_dmi_cache_hit(fixture_snapshot):
    t0 = time.monotonic()
    first = convert_dmi("icons/test.dmi")
    t1 = time.monotonic()
    second = convert_dmi("icons/test.dmi")
    t2 = time.monotonic()
    assert first["rsi_path"] == second["rsi_path"]
    cold_ms = (t1 - t0) * 1000
    warm_ms = (t2 - t1) * 1000
    assert warm_ms * 5 < cold_ms or warm_ms < 5
    assert second["cache_hit"] is True
    assert first["cache_hit"] is False
