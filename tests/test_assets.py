import base64
import json
from pathlib import Path as pathlib_Path

import pytest
from PIL import Image

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


def test_list_dmi_states_returns_all_three(fixture_snapshot):
    states = list_dmi_states("icons/test.dmi")
    by_name = {s["name"]: s for s in states}
    assert set(by_name) == {"idle", "active", "walk"}
    assert by_name["idle"]["dirs"] == 1 and by_name["idle"]["frames"] == 1
    assert by_name["active"]["dirs"] == 1 and by_name["active"]["frames"] == 1
    assert by_name["walk"]["dirs"] == 4 and by_name["walk"]["frames"] == 3


def test_convert_dmi_full(fixture_snapshot, tmp_path):
    result = convert_dmi("icons/test.dmi")
    rsi_dir = pathlib_Path(result["rsi_path"])
    assert (rsi_dir / "meta.json").exists()
    meta = json.loads((rsi_dir / "meta.json").read_text())
    assert meta["version"] == 1
    assert meta["size"] == {"x": 32, "y": 32}
    state_names = {s["name"] for s in meta["states"]}
    assert state_names == {"idle", "active", "walk"}
    assert (rsi_dir / "idle.png").exists()
    assert (rsi_dir / "active.png").exists()
    assert (rsi_dir / "walk.png").exists()


def test_convert_dmi_single_state(fixture_snapshot, tmp_path):
    result = convert_dmi("icons/test.dmi", state="idle")
    rsi_dir = pathlib_Path(result["rsi_path"])
    meta = json.loads((rsi_dir / "meta.json").read_text())
    state_names = {s["name"] for s in meta["states"]}
    assert state_names == {"idle"}


def test_convert_dmi_cache_hit(fixture_snapshot):
    first = convert_dmi("icons/test.dmi")
    second = convert_dmi("icons/test.dmi")
    assert first["rsi_path"] == second["rsi_path"]
    assert first["cache_hit"] is False
    assert second["cache_hit"] is True


def test_walk_state_rsi_layout(fixture_snapshot):
    """Walk has dirs=4 frames=3 -> RSI sheet is 3 cols x 4 rows.

    Each fixture DMI cell is painted (30 + direction*60, 30 + frame*60, 200);
    verify that RSI sheet position (col=frame, row=direction) decodes to those
    expected (frame, direction) coordinates.
    """
    result = convert_dmi("icons/test.dmi", state="walk")
    rsi_dir = pathlib_Path(result["rsi_path"])
    meta = json.loads((rsi_dir / "meta.json").read_text())
    walk_meta = next(s for s in meta["states"] if s["name"] == "walk")
    assert walk_meta["directions"] == 4
    assert walk_meta["delays"] == [[1.0, 1.5, 2.0]] * 4

    sheet = Image.open(rsi_dir / "walk.png").convert("RGBA")
    assert sheet.size == (32 * 3, 32 * 4)  # F=3 cols, N=4 rows
    for frame in range(3):
        for direction in range(4):
            px = sheet.getpixel((frame * 32 + 16, direction * 32 + 16))
            expected = (30 + direction * 60, 30 + frame * 60, 200, 255)
            assert px == expected, (
                f"RSI (col={frame},row={direction}) center pixel was {px}, "
                f"expected {expected} (frame={frame}, direction={direction})"
            )


def test_safe_name_keeps_slash_distinct():
    """States named 'foo/bar' and 'foo_bar' must not collide on disk."""
    from vgstation13_mcp.rsi import _safe

    assert _safe("foo/bar") != _safe("foo_bar")
